# -*- coding: utf-8 -*-
"""mv_stabilize_locked.py - remove global displacement/drift from locked-off shots.

Why: the i2v sources for these shots are static, but the assembled cut shows a 20-30 px
step plus a slow return (measured on R06: source 0.02 px/frame, output +26.8 px in one
frame). That is an assembly/retiming artefact, not an AI take defect.

Constraint: subtitles are already burned in, so the frame cannot simply be warped.
Solution: stabilise the picture above the subtitle band and composite the bottom band
(where burned text lives) from the original frame, with a feathered seam. Locked-off shots
have a static band behind the text, so this is safe.

Usage:
  py mv_stabilize_locked.py <in.mp4> <out.mp4> --windows 47.5:50.52,83.56:87.74,...
"""
import argparse
import os
import subprocess
import sys

import cv2
import numpy as np

W, H = 1344, 768
FPS = 24
BAND = 0.84          # picture area above this fraction; below is the subtitle band
FEATHER = 24         # px of vertical feather at the seam
MAX_SHIFT = 60


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--windows", required=True, help="t0:t1,t0:t1,...")
    a = ap.parse_args()

    wins = []
    for part in a.windows.split(","):
        t0, t1 = part.split(":")
        wins.append((float(t0), float(t1)))

    cap = cv2.VideoCapture(a.src)
    if not cap.isOpened():
        sys.exit("cannot open " + a.src)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    ycut = int(H * BAND)

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-crf", "17", "-preset", "fast",
         "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), a.out],
        stdin=subprocess.PIPE)

    # per-window state
    win_idx = -1
    win_start = 0
    ref = None
    prev_shift = None
    written = 0

    for i in range(n):
        ok, fr = cap.read()
        if not ok:
            break
        t = i / fps
        # find active window
        active = -1
        for k, (t0, t1) in enumerate(wins):
            if t0 - 1e-6 <= t < t1 - 1e-6:
                active = k
                break
        if active < 0:
            enc.stdin.write(fr.tobytes())
            written += 1
            ref = None
            prev_shift = None
            continue

        if active != win_idx:
            win_idx = active
            win_start = i
            ref = None
            prev_shift = (0.0, 0.0)

        gray = np.ascontiguousarray(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY))
        if ref is None and (i - win_start) < 12:
            # let the shot settle before choosing the reference patch (fades/dark heads)
            enc.stdin.write(fr.tobytes())
            written += 1
            continue
        if ref is None:
            # choose the highest-variance cell as template (avoids periodic cuneiform aliasing)
            best = None
            patches = []
            cw, ch = W // 6, ycut // 3
            for gy in range(3):
                for gx in range(6):
                    x0, y0 = gx * cw, gy * ch
                    patch = gray[y0:y0 + ch, x0:x0 + cw]
                    if patch.size == 0 or patch.std() < 12:
                        continue
                    patches.append((float(patch.std()), x0, y0, patch.copy()))
            patches.sort(key=lambda z: -z[0])
            patches = patches[:4]
            if not patches:
                patches = [(0.0, 0, 0, gray[0:ch, 0:cw].copy())]
            refs = patches
            prev_shift = (0.0, 0.0)
            dx, dy, resp = 0.0, 0.0, 1.0
        else:
            offs = []
            scores = []
            for _, x0, y0, tpl in refs:
                th, tw = tpl.shape
                try:
                    res = cv2.matchTemplate(gray[:ycut], tpl, cv2.TM_CCOEFF_NORMED)
                    _, score, _, loc = cv2.minMaxLoc(res)
                except cv2.error:
                    continue
                if score >= 0.45:
                    offs.append((loc[0] - x0, loc[1] - y0))
                    scores.append(score)
            if offs:
                ox = float(np.median([o[0] for o in offs]))
                oy = float(np.median([o[1] for o in offs]))
                dx, dy, resp = ox, oy, float(np.mean(scores))
            else:
                dx, dy, resp = prev_shift[0], prev_shift[1], 0.0
        dx = float(np.clip(dx, -MAX_SHIFT, MAX_SHIFT))
        dy = float(np.clip(dy, -MAX_SHIFT, MAX_SHIFT))
        # light temporal smoothing
        if prev_shift is not None:
            dx = 0.6 * dx + 0.4 * prev_shift[0]
            dy = 0.6 * dy + 0.4 * prev_shift[1]
        prev_shift = (dx, dy)

        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        warped = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REPLICATE)
        out = warped.copy()
        # composite the subtitle band from the untouched original
        out[ycut:] = fr[ycut:]
        # feather the seam
        for k in range(FEATHER):
            y = ycut - FEATHER + k
            alpha = k / float(FEATHER)
            out[y] = (warped[y].astype(np.float32) * alpha +
                      fr[y].astype(np.float32) * (1 - alpha)).astype(np.uint8)
        enc.stdin.write(out.tobytes())
        written += 1

    cap.release()
    enc.stdin.close()
    enc.wait()
    print("wrote %d frames -> %s" % (written, a.out))
    if written != n:
        sys.exit("FATAL frame count %d != %d" % (written, n))


if __name__ == "__main__":
    main()