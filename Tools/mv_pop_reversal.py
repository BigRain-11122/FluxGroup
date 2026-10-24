# -*- coding: utf-8 -*-
"""mv_pop_reversal.py - detect one-frame displacement pops by shift reversal.

Signature: |shift(i-1 -> i)| and |shift(i -> i+1)| are both large, but they cancel:
shift(i-1 -> i) + shift(i -> i+1) ~= 0. The frame is displaced and snaps back.
This is content-independent: fast pans never reverse by the same amount in one frame.

Usage:
  py mv_pop_reversal.py <video> [--json out.json]
"""
import argparse
import json

import cv2
import numpy as np

W, H = 336, 188


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default=None)
    ap.add_argument("--min-shift", type=float, default=4.0)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    prev = None
    shifts = []
    n = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            (dx, dy), resp = cv2.phaseCorrelate(prev, g)
            shifts.append((dx, dy, resp))
        prev = g
        n += 1
    cap.release()

    events = []
    for i in range(1, len(shifts) - 1):
        ax, ay, ar = shifts[i - 1]
        bx, by, br = shifts[i]
        if ar < 0.02 or br < 0.02:
            continue
        ma = (ax * ax + ay * ay) ** 0.5
        mb = (bx * bx + by * by) ** 0.5
        if ma < a.min_shift or mb < a.min_shift:
            continue
        cancel = ((ax + bx) ** 2 + (ay + by) ** 2) ** 0.5
        if cancel < max(2.0, 0.30 * min(ma, mb)):
            # frame index i is the displaced one (shift i-1->i is the jump)
            events.append({"t": round(i / fps, 3), "frame": i,
                           "jump_px": round(ma * 1344.0 / W, 1),
                           "return_px": round(mb * 1344.0 / W, 1),
                           "cancel_px": round(cancel * 1344.0 / W, 1)})

    # cluster within 2 frames
    kept = []
    for e in sorted(events, key=lambda x: -x["jump_px"]):
        if all(abs(e["frame"] - k["frame"]) > 2 for k in kept):
            kept.append(e)
    kept.sort(key=lambda x: x["t"])

    print("frames=%d  one-frame pops=%d" % (n, len(kept)))
    print("%-9s %-7s %10s %11s %10s" % ("time", "frame", "jump_px", "return_px", "cancel_px"))
    for e in kept:
        print("%-9.3f %-7d %10.1f %11.1f %10.1f" % (
            e["t"], e["frame"], e["jump_px"], e["return_px"], e["cancel_px"]))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"fps": fps, "frames": n, "pops": kept}, fh, ensure_ascii=False, indent=1)
        print("json ->", a.json)


if __name__ == "__main__":
    main()