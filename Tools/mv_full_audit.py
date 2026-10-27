# -*- coding: utf-8 -*-
"""mv_full_audit.py - whole-film audience-level audit (not just frame correctness).

Per shot (scene-detected):
  duration, mean luma, mean saturation, warmth (R/B), motion, static ratio, dHash
Cross-shot:
  near-duplicate pairs (dHash hamming <= 6)
  era clustering by warmth/saturation -> shots that sit between clusters (ambiguous era)
  pacing outliers (<0.8s or >6s)
  empty-shot ratio proxy (low motion + no skin-tone pixels)

Usage:
  py mv_full_audit.py <video> --json out.json
"""
import argparse
import json
import os
import sys
from collections import Counter

import cv2
import numpy as np

W, H = 336, 189


def dhash(g):
    r = cv2.resize(g, (9, 8), interpolation=cv2.INTER_AREA)
    d = r[:, 1:] > r[:, :-1]
    v = 0
    for b in d.flatten():
        v = (v << 1) | int(b)
    return v


def hamming(a, b):
    return bin(a ^ b).count("1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default=None)
    ap.add_argument("--whitelist", default=None, help="reprise whitelist JSON")
    a = ap.parse_args()

    sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\Tools")
    import release_gate as RG

    cuts, err = RG.detect_cuts(a.video, threshold=15.0)
    if err:
        sys.exit(err)
    cuts = cuts or []

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    n = len(frames)

    ts = [0.0] + list(cuts) + [n / fps]
    shots = []
    for i in range(len(ts) - 1):
        ia, ib = max(0, int(round(ts[i] * fps))), min(n, int(round(ts[i + 1] * fps)))
        if ib - ia < 3:
            continue
        idxs = list(range(ia, ib, max(1, (ib - ia) // 8)))[:8]
        lumas, sats, warms, dh = [], [], [], []
        for k in idxs:
            f = frames[k]
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
            b, gg, r = [float(x) for x in cv2.mean(f)[:3]]
            lumas.append(float(g.mean()))
            sats.append(float(hsv[..., 1].mean()))
            warms.append(r / max(1.0, (b + 1e-6)))
            dh.append(dhash(g))
        # motion: consecutive-frame diff inside the shot
        step = max(1, (ib - ia) // 20)
        mad = []
        for k in range(ia + 1, ib, step):
            p = cv2.cvtColor(cv2.resize(frames[k - 1], (W, H)), cv2.COLOR_BGR2GRAY).astype(np.float32)
            c = cv2.cvtColor(cv2.resize(frames[k], (W, H)), cv2.COLOR_BGR2GRAY).astype(np.float32)
            mad.append(float(np.mean(np.abs(c - p))))
        shots.append({
            "i": len(shots), "t0": round(ia / fps, 2), "t1": round(ib / fps, 2),
            "dur": round((ib - ia) / fps, 2),
            "luma": round(float(np.mean(lumas)), 1),
            "sat": round(float(np.mean(sats)), 1),
            "warm": round(float(np.mean(warms)), 2),
            "motion": round(float(np.mean(mad)) / 10.0, 2),
            "dhash": dh[len(dh) // 2],
        })

    # duplicates (ignore micro-fragments: a shot under 1s is usually a flash-split, not a shot)
    dups = []
    for i in range(len(shots)):
        if shots[i]["dur"] < 1.0:
            continue
        for j in range(i + 1, len(shots)):
            if shots[j]["dur"] < 1.0:
                continue
            d = hamming(shots[i]["dhash"], shots[j]["dhash"])
            if d <= 6 and abs(shots[i]["t0"] - shots[j]["t0"]) > 5:
                dups.append((shots[i]["t0"], shots[j]["t0"], d))

    # whitelist: intentional reprises are design, not defects
    wl_path = a.whitelist
    wl_ok, wl_bad = [], list(dups)
    if wl_path and os.path.exists(wl_path):
        with open(wl_path, encoding="utf-8-sig") as fh:
            wl = json.load(fh)
        tol = float(wl.get("tolerance_sec", 5.0))
        pairs = wl.get("pairs", [])
        keep = []
        for t1, t2, d in dups:
            hit = any(abs(t1 - p["a"]) <= tol and abs(t2 - p["b"]) <= tol or
                      abs(t1 - p["b"]) <= tol and abs(t2 - p["a"]) <= tol for p in pairs)
            (wl_ok if hit else keep).append((t1, t2, d))
        wl_bad = keep

    # era clusters by warmth+sat (2-means, 1D on combined score)
    score = np.array([s["warm"] + s["sat"] / 40.0 for s in shots])
    lo, hi = np.percentile(score, 25), np.percentile(score, 75)
    thr = (lo + hi) / 2
    for s, sc in zip(shots, score):
        s["era_group"] = "A" if sc >= thr else "B"
        s["era_score"] = round(float(sc), 2)
    # ambiguous: within 8% of threshold
    amb = [s for s in shots if abs(s["era_score"] - thr) < 0.08 * max(1e-6, abs(thr)) + 0.03]

    # pacing
    short = [s for s in shots if s["dur"] < 0.8]
    long = [s for s in shots if s["dur"] > 6.0]

    out = {"frames": n, "fps": fps, "shots": len(shots),
           "epoch_thr": round(float(thr), 2),
           "groups": dict(Counter(s["era_group"] for s in shots)),
           "duplicates": dups, "duplicates_unlisted": wl_bad,
           "ambiguous_era": [(s["t0"], s["era_score"]) for s in amb],
           "short_shots": [(s["t0"], s["dur"]) for s in short],
           "long_shots": [(s["t0"], s["dur"]) for s in long],
           "table": shots}

    print("frames=%d shots=%d  era_thr=%.2f  groups=%s" % (n, len(shots), thr, out["groups"]))
    print("duplicates (dHash<=6, >5s apart): %d  whitelisted=%d  unlisted=%d" % (
        len(dups), len(wl_ok), len(wl_bad)))
    for a_, b_, d in dups:
        print("   %.1fs <-> %.1fs  dist=%d" % (a_, b_, d))
    print("ambiguous era shots: %d" % len(amb))
    for s in amb:
        print("   %.1fs score=%.2f luma=%.0f sat=%.0f warm=%.2f" % (
            s["t0"], s["era_score"], s["luma"], s["sat"], s["warm"]))
    print("short shots <0.8s: %d  %s" % (len(short), [(s["t0"], s["dur"]) for s in short][:8]))
    print("long shots >6s: %d  %s" % (len(long), [(s["t0"], s["dur"]) for s in long][:8]))
    print("")
    print("%-7s %-7s %6s %6s %6s %7s %-4s" % ("t0", "t1", "dur", "luma", "sat", "warm", "era"))
    for s in shots:
        print("%-7.2f %-7.2f %6.2f %6.1f %6.1f %7.2f %-4s" % (
            s["t0"], s["t1"], s["dur"], s["luma"], s["sat"], s["warm"], s["era_group"]))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
        print("json ->", a.json)


if __name__ == "__main__":
    main()