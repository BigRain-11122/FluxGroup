# -*- coding: utf-8 -*-
"""mv_thaw.py - replace frozen runs with optical-flow interpolated frames.

The picture is interpolated between the frame before and after the run; the subtitle band
is copied from the original frame so burned text is untouched.

Usage:
  py mv_thaw.py <in> <out> --runs 1054:4,4558:3
"""
import argparse
import subprocess

import cv2
import numpy as np

W, H, FPS = 1344, 768, 24
BAND, FEATHER = 0.84, 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--runs", required=True)
    a = ap.parse_args()
    runs = []
    for p in a.runs.split(","):
        s, r = p.split(":")
        runs.append((int(s), int(r)))

    cap = cv2.VideoCapture(a.src)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    n = len(frames)
    ycut = int(H * BAND)

    for s, r in runs:
        if s - 1 < 0 or s + r >= n:
            continue
        A = frames[s - 1]
        B = frames[s + r]
        ga = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY).astype(np.float32)
        gb = cv2.cvtColor(B, cv2.COLOR_BGR2GRAY).astype(np.float32)
        flow = cv2.calcOpticalFlowFarneback(ga, gb, None, 0.5, 3, 21, 4, 7, 1.5, 0)

        def warp(img, fl):
            gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
            return cv2.remap(img, gx + fl[..., 0], gy + fl[..., 1], cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REPLICATE)

        for k in range(r):
            t = (k + 1) / float(r + 1)
            wa = warp(A.astype(np.float32), flow * t)
            wb = warp(B.astype(np.float32), -flow * (1 - t))
            mid = np.clip(wa * (1 - t) + wb * t, 0, 255).astype(np.uint8)
            fr = frames[s + k]
            mid[ycut:] = fr[ycut:]
            for j in range(FEATHER):
                y = ycut - FEATHER + j
                tt = j / float(FEATHER)
                mid[y] = (mid[y].astype(np.float32) * tt +
                          fr[y].astype(np.float32) * (1 - tt)).astype(np.uint8)
            frames[s + k] = mid

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-crf", "17", "-preset", "fast",
         "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), a.out],
        stdin=subprocess.PIPE)
    for f in frames:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", len(frames), "->", a.out)


if __name__ == "__main__":
    main()