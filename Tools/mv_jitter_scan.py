# -*- coding: utf-8 -*-
"""mv_jitter_scan.py - locate *visible* shot jitter in a finished cut.

Why this exists: frame-diff spikes alone cannot separate a planned cut, a single-frame
pop, a frozen i2v tail and a real intra-shot camera jump. This tool measures four things
per frame and reports them per shot so the repair decision is evidence-based:

  1. MAD       mean abs luma difference to previous frame      -> pop / freeze / cut
  2. SHIFT     phase-correlation global motion (dx, dy)        -> camera jump / drift
  3. ACCEL     frame-to-frame change of |SHIFT|                -> judder / snap
  4. FREEZE    consecutive near-identical frames               -> frozen i2v tail

Cuts are detected independently and excluded (a cut is supposed to jump).

Usage:
  py mv_jitter_scan.py <video> [--json out.json] [--top 40]

Output: console table + optional JSON. Exit code is always 0 (diagnostic only).
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

SCAN_W = 336          # analysis width; 1344/4, keeps phase correlation stable and fast
POP_K = 7.0           # robust z for MAD spikes inside a shot
SHIFT_K = 7.0         # robust z for |shift| spikes inside a shot
ACCEL_K = 8.0         # robust z for |shift| acceleration
FREEZE_MAD = 0.20     # below this a frame is "static"
FREEZE_RUN = 3        # >= this many static frames in a row = frozen run
CUT_THRESHOLD = 27.0  # same default as release_gate.detect_cuts


def robust_thr(x, k, floor):
    x = np.asarray(x, dtype=np.float64)
    if x.size < 8:
        return floor
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))
    return max(floor, med + k * 1.4826 * mad)


def scan(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        sys.exit("cannot open " + path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    gray_prev = None
    mad = [0.0]
    shift = [(0.0, 0.0, 0.0)]   # dx, dy, response
    frames = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        h, w = fr.shape[:2]
        sw = SCAN_W
        sh = max(2, int(round(h * sw / float(w))))
        g = cv2.cvtColor(cv2.resize(fr, (sw, sh), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY).astype(np.float32)
        if gray_prev is not None and gray_prev.shape == g.shape:
            mad.append(float(np.mean(np.abs(g - gray_prev))))
            try:
                (dx, dy), resp = cv2.phaseCorrelate(gray_prev, g)
            except cv2.error:
                (dx, dy), resp = (0.0, 0.0), 0.0
            shift.append((float(dx), float(dy), float(resp)))
        else:
            mad.append(0.0)
            shift.append((0.0, 0.0, 0.0))
        gray_prev = g
        frames += 1
    cap.release()

    mad = np.asarray(mad[:frames], dtype=np.float64)
    shift = np.asarray(shift[:frames], dtype=np.float64)
    mag = np.hypot(shift[:, 0], shift[:, 1])
    accel = np.abs(np.diff(mag, prepend=mag[0]))

    # cuts: reuse release_gate's detector
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import release_gate as RG
    cuts, err = RG.detect_cuts(path, threshold=CUT_THRESHOLD)
    cut_idx = set()
    for t in (cuts or []):
        ci = int(round(t * fps))
        for d in range(-2, 3):
            cut_idx.add(ci + d)

    # build shot windows from cuts
    ts = [0.0] + list(cuts or []) + [frames / fps]
    shots = []
    for a, b in zip(ts[:-1], ts[1:]):
        ia, ib = int(round(a * fps)), int(round(b * fps))
        ia, ib = max(0, ia), min(frames, ib)
        if ib - ia >= 3:
            shots.append((ia, ib))

    report = {"path": os.path.abspath(path), "fps": fps, "frames": frames,
              "cuts": len(cuts or []), "shots": len(shots), "flags": []}

    for si, (ia, ib) in enumerate(shots):
        sl = slice(ia + 1, ib)  # skip first frame of shot
        m = mad[sl]
        s = mag[sl]
        ac = accel[sl]
        if m.size < 4:
            continue
        thr_m = robust_thr(m, POP_K, 3.0)
        thr_s = robust_thr(s, SHIFT_K, 2.0)
        thr_a = robust_thr(ac, ACCEL_K, 2.0)

        for j in range(m.size):
            idx = ia + 1 + j
            if idx in cut_idx:
                continue
            t = idx / fps
            tags = []
            if mad[idx] > thr_m:
                tags.append("POP")
            if mag[idx] > thr_s and shift[idx, 2] > 0.05:
                tags.append("JUMP")
            if accel[idx] > thr_a and mag[idx] > 1.0:
                tags.append("SNAP")
            if tags:
                report["flags"].append({
                    "shot": si, "t": round(t, 3), "frame": int(idx),
                    "tags": tags,
                    "mad": round(float(mad[idx]), 3),
                    "shift": round(float(mag[idx]), 2),
                    "accel": round(float(accel[idx]), 2),
                    "resp": round(float(shift[idx, 2]), 3),
                    "thr_mad": round(thr_m, 2),
                    "thr_shift": round(thr_s, 2),
                })

        # freeze runs (inside shot)
        run = 0
        for idx in range(ia + 1, ib):
            if idx in cut_idx:
                run = 0
                continue
            if mad[idx] < FREEZE_MAD:
                run += 1
            else:
                if run >= FREEZE_RUN:
                    report["flags"].append({
                        "shot": si, "t": round((idx - run) / fps, 3), "frame": idx - run,
                        "tags": ["FREEZE"], "run": run,
                        "mad": round(float(mad[idx - run:idx].mean()), 3),
                    })
                run = 0
        if run >= FREEZE_RUN:
            report["flags"].append({
                "shot": si, "t": round((ib - run) / fps, 3), "frame": ib - run,
                "tags": ["FREEZE"], "run": run,
                "mad": round(float(mad[ib - run:ib].mean()), 3),
            })

    report["flags"].sort(key=lambda x: x["t"])
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default=None)
    ap.add_argument("--top", type=int, default=60)
    a = ap.parse_args()

    r = scan(a.video)
    print("file   :", r["path"])
    print("frames : %d @ %.3f fps  shots=%d cuts=%d" % (r["frames"], r["fps"], r["shots"], r["cuts"]))
    print("flags  : %d" % len(r["flags"]))
    print("")
    print("%-9s %-9s %-6s %-16s %8s %8s %8s" % ("time", "frame", "shot", "tags", "mad", "shift", "accel"))
    for f in r["flags"][:a.top]:
        print("%-9.3f %-9d %-6d %-16s %8.2f %8.2f %8.2f" % (
            f["t"], f["frame"], f["shot"], "+".join(f["tags"]),
            f.get("mad", 0), f.get("shift", 0), f.get("accel", 0)))
    # per-tag summary
    from collections import Counter
    c = Counter()
    for f in r["flags"]:
        for t in f["tags"]:
            c[t] += 1
    print("")
    print("summary:", dict(c))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1)
        print("json ->", a.json)


if __name__ == "__main__":
    main()