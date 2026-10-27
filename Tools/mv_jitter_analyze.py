# -*- coding: utf-8 -*-
"""mv_jitter_analyze.py - classify every frame anomaly in a cut as CUT / JUMP / POP / FLASH / FREEZE.

Rationale: a fixed scene-detect threshold misses dark cuts (MAD 10-27) and therefore reports
them as "jitter". A camera jump and a hard cut look identical in MAD, but differ in one test:
after aligning frame t-1 to t by the global shift, a camera move still matches (low residual),
while a cut does not (high residual). Frames that return to the previous image are a flash,
not a cut.

Metrics per frame:
  mad    mean abs luma diff
  shift  phase-correlation global displacement
  resid  residual after warping previous frame by shift  (cut detector)
  sim    similarity between t-k and t+k  (return test)

Usage:
  py mv_jitter_analyze.py <video> --json out.json [--cuts-thr 15]
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

AN_W = 336
THUMB_W = 168
POP_K = 6.0
SHIFT_K = 6.0
FREEZE_MAD = 0.20
FREEZE_RUN = 3
SIM_RETURN = 0.72     # >= this -> the shot returned (flash/pop), not a cut
RESID_CUT = 12.0      # aligned residual above this -> structural change (cut)


def robust_thr(x, k, floor):
    x = np.asarray(x, dtype=np.float64)
    if x.size < 8:
        return floor
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))
    return max(floor, med + k * 1.4826 * mad)


def sim(a, b):
    if a is None or b is None:
        return 0.0
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    a -= a.mean()
    b -= b.mean()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-6 or nb < 1e-6:
        return 0.0
    return float((a * b).sum() / (na * nb))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default=None)
    ap.add_argument("--cuts-thr", type=float, default=15.0)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    if not cap.isOpened():
        sys.exit("cannot open " + a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    mad = []
    shift = []
    resid = []
    thumbs = []
    prev = None
    n = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        h, w = fr.shape[:2]
        aw = AN_W
        ah = max(2, int(round(h * aw / float(w))))
        g = cv2.cvtColor(cv2.resize(fr, (aw, ah), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY).astype(np.float32)
        th = cv2.cvtColor(cv2.resize(fr, (THUMB_W, max(2, int(round(h * THUMB_W / float(w))))),
                                     interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        thumbs.append(th)
        if prev is None:
            mad.append(0.0); shift.append((0.0, 0.0, 0.0)); resid.append(0.0)
        else:
            mad.append(float(np.mean(np.abs(g - prev))))
            try:
                (dx, dy), resp = cv2.phaseCorrelate(prev, g)
            except cv2.error:
                (dx, dy), resp = 0.0, 0.0, 0.0
            shift.append((float(dx), float(dy), float(resp)))
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            warped = cv2.warpAffine(prev, M, (aw, ah), flags=cv2.INTER_LINEAR,
                                    borderMode=cv2.BORDER_REPLICATE)
            resid.append(float(np.mean(np.abs(warped - g))))
        prev = g
        n += 1
    cap.release()

    mad = np.asarray(mad); shift = np.asarray(shift); resid = np.asarray(resid)
    mag = np.hypot(shift[:, 0], shift[:, 1])

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import release_gate as RG
    cuts, err = RG.detect_cuts(a.video, threshold=a.cuts_thr)
    cuts = cuts or []
    cut_idx = set()
    for t in cuts:
        c = int(round(t * fps))
        for d in range(-2, 3):
            cut_idx.add(c + d)

    ts = [0.0] + list(cuts) + [n / fps]
    shots = []
    for x, y in zip(ts[:-1], ts[1:]):
        ia, ib = max(0, int(round(x * fps))), min(n, int(round(y * fps)))
        if ib - ia >= 3:
            shots.append((ia, ib))

    candidates = set()
    for ia, ib in shots:
        m = mad[ia + 1:ib]
        s = mag[ia + 1:ib]
        r = resid[ia + 1:ib]
        if m.size < 4:
            continue
        tm = robust_thr(m, POP_K, 3.0)
        ts_ = robust_thr(s, SHIFT_K, 2.5)
        tr = robust_thr(r, 6.0, 8.0)
        for idx in range(ia + 1, ib):
            if idx in cut_idx:
                continue
            if mad[idx] > tm or mag[idx] > ts_ or resid[idx] > tr:
                candidates.add(idx)

    # freeze runs
    freezes = []
    for ia, ib in shots:
        run = 0
        for idx in range(ia + 1, ib):
            if idx in cut_idx:
                run = 0
                continue
            if mad[idx] < FREEZE_MAD:
                run += 1
            else:
                if run >= FREEZE_RUN:
                    freezes.append((idx - run, run))
                run = 0
        if run >= FREEZE_RUN:
            freezes.append((ib - run, run))

    # classify candidates
    K = 6
    events = []
    for idx in sorted(candidates):
        before = thumbs[max(0, idx - K)]
        after = thumbs[min(n - 1, idx + K)]
        near_before = thumbs[max(0, idx - 1)]
        near_after = thumbs[min(n - 1, idx + 1)]
        s_ret = sim(before, after)
        s_local = sim(near_before, near_after)
        r = float(resid[idx])
        m_ = float(mad[idx])
        sh = float(mag[idx])

        if r > RESID_CUT and s_ret < SIM_RETURN:
            kind = "CUT"
        elif sh > 3.0 and s_ret >= SIM_RETURN:
            kind = "JUMP"
        elif sh > 3.0:
            kind = "JUMP?"
        elif m_ > 0 and s_local >= SIM_RETURN:
            kind = "FLASH"
        else:
            kind = "POP"

        events.append({
            "t": round(idx / fps, 3), "frame": int(idx), "kind": kind,
            "mad": round(m_, 2), "shift": round(sh, 2), "resid": round(r, 2),
            "sim_return": round(s_ret, 3),
        })

    for f0, run in freezes:
        events.append({"t": round(f0 / fps, 3), "frame": int(f0), "kind": "FREEZE",
                       "run": run, "mad": round(float(mad[f0:f0 + run].mean()), 3)})

    events.sort(key=lambda e: e["t"])

    from collections import Counter
    c = Counter(e["kind"] for e in events)
    out = {"path": os.path.abspath(a.video), "fps": fps, "frames": n,
           "shots": len(shots), "cuts": len(cuts), "summary": dict(c), "events": events}
    print("frames=%d fps=%.3f shots=%d cuts=%d" % (n, fps, len(shots), len(cuts)))
    print("summary:", dict(c))
    print("")
    print("%-9s %-7s %-8s %7s %7s %7s %7s" % ("time", "frame", "kind", "mad", "shift", "resid", "sim"))
    for e in events:
        print("%-9.3f %-7d %-8s %7.2f %7.2f %7.2f %7.3f" % (
            e["t"], e["frame"], e["kind"], e.get("mad", 0), e.get("shift", 0),
            e.get("resid", 0), e.get("sim_return", 0)))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
        print("json ->", a.json)


if __name__ == "__main__":
    main()