# -*- coding: utf-8 -*-
"""mv_step_lock.py - remove a persistent picture step in a locked-off shot.

A step jump (picture shifts and STAYS) cannot be fixed by neighbour averaging. But the
template frame 12 frames before the step is the correct framing; matching it in every
later frame recovers the cumulative offset, and shifting back restores the shot.

Subtitle band is copied from the original frame, so burned text does not move.

Usage:
  py mv_step_lock.py <in> <out> --spec 2025:2105,3244:3325
  (spec entries are seam_frame:window_end_frame)
"""
import argparse
import subprocess

import cv2
import numpy as np

W, H, FPS = 1344, 768, 24
BAND, FEATHER, MAX_SHIFT, PRE = 0.84, 24, 60, 12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--spec", required=True)
    a = ap.parse_args()

    specs = []
    for part in a.spec.split(","):
        s, e = part.split(":")
        specs.append((int(s), int(e)))

    cap = cv2.VideoCapture(a.src)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    ycut = int(H * BAND)

    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    n = len(frames)

    # template frames
    tpls = []
    for seam, end in specs:
        ti = max(0, seam - PRE)
        g = cv2.cvtColor(frames[ti], cv2.COLOR_BGR2GRAY)[:ycut]
        # pick a high-variance patch that fits inside the search area (not the whole frame,
        # otherwise matchTemplate has a 1x1 result and always returns zero offset)
        cw, ch = W // 5, ycut // 4
        best = None
        for gy in range(4):
            for gx in range(5):
                x0, y0 = gx * cw, gy * ch
                p = g[y0:y0 + ch, x0:x0 + cw]
                if p.size == 0:
                    continue
                if best is None or p.std() > best[0]:
                    best = (float(p.std()), x0, y0, p.copy())
        tpls.append((seam, end, best[1], best[2], best[3]))

    out = list(frames)
    for seam, end, x0, y0, tpl in tpls:
        for i in range(seam, min(end, n)):
            cur = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)[:ycut]
            res = cv2.matchTemplate(cur, tpl, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(res)
            if score < 0.35:
                continue
            dx = float(np.clip(loc[0] - x0, -MAX_SHIFT, MAX_SHIFT))
            dy = float(np.clip(loc[1] - y0, -MAX_SHIFT, MAX_SHIFT))
            if abs(dx) < 0.5 and abs(dy) < 0.5:
                continue
            M = np.float32([[1, 0, -dx], [0, 1, -dy]])
            fr = frames[i]
            w = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_REPLICATE)
            w[ycut:] = fr[ycut:]
            for k in range(FEATHER):
                y = ycut - FEATHER + k
                t = k / float(FEATHER)
                w[y] = (w[y].astype(np.float32) * t + fr[y].astype(np.float32) * (1 - t)).astype(np.uint8)
            out[i] = w

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-crf", "17", "-preset", "fast",
         "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), a.out],
        stdin=subprocess.PIPE)
    for f in out:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", len(out), "->", a.out)


if __name__ == "__main__":
    main()