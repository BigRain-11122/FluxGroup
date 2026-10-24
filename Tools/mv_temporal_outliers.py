# -*- coding: utf-8 -*-
"""mv_temporal_outliers.py - find frames that disagree with BOTH neighbours after motion
compensation (the signature of an i2v pop / local teleport / one-frame seam).

Score(i) = 0.5 * ( resid(warp(i-1 -> i)) + resid(warp(i+1 -> i)) )  after dense-flow warp.
A normal moving frame aligns with at least one side; a popped frame aligns with neither.
A hard cut also scores high, so cuts are excluded using the return test (sim i-8 vs i+8).

Usage:
  py mv_temporal_outliers.py <video> [--json out.json] [--thr 7]
"""
import argparse
import json
import sys

import cv2
import numpy as np

W, H = 256, 144


def flow(a, b):
    return cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 21, 4, 7, 1.5, 0)


def warp(img, fl):
    h, w = img.shape
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    mx = gx + fl[..., 0]
    my = gy + fl[..., 1]
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def sim(a, b):
    a = a.astype(np.float32) - a.mean()
    b = b.astype(np.float32) - b.mean()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na < 1e-6 or nb < 1e-6 else float((a * b).sum() / (na * nb))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default=None)
    ap.add_argument("--thr", type=float, default=7.0)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA),
                                    cv2.COLOR_BGR2GRAY))
    cap.release()
    n = len(frames)

    scores = np.zeros(n)
    for i in range(1, n - 1):
        p, c, q = frames[i - 1], frames[i], frames[i + 1]
        try:
            r1 = float(np.mean(np.abs(warp(p.astype(np.float32), flow(p, c)) - c)))
            r2 = float(np.mean(np.abs(warp(q.astype(np.float32), flow(q, c)) - c)))
        except cv2.error:
            continue
        scores[i] = 0.5 * (r1 + r2)

    out = []
    for i in range(9, n - 9):
        if scores[i] < a.thr:
            continue
        s = sim(frames[i - 8], frames[i + 8])
        kind = "CUT" if s < 0.72 else "POP"
        out.append({"t": round(i / fps, 3), "frame": int(i), "kind": kind,
                    "score": round(float(scores[i]), 2), "sim": round(s, 3)})

    # cluster: keep local max within 3 frames
    kept = []
    for e in sorted(out, key=lambda x: -x["score"]):
        if all(abs(e["frame"] - k["frame"]) > 3 for k in kept):
            kept.append(e)
    kept.sort(key=lambda x: x["t"])

    pops = [e for e in kept if e["kind"] == "POP"]
    print("frames=%d  outlier frames=%d  POP=%d  CUT=%d" % (n, len(kept), len(pops), len(kept) - len(pops)))
    print("%-9s %-7s %-5s %7s %6s" % ("time", "frame", "kind", "score", "sim"))
    for e in kept:
        print("%-9.3f %-7d %-5s %7.2f %6.3f" % (e["t"], e["frame"], e["kind"], e["score"], e["sim"]))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"fps": fps, "frames": n, "events": kept}, fh, ensure_ascii=False, indent=1)
        print("json ->", a.json)


if __name__ == "__main__":
    main()