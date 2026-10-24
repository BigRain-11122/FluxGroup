# -*- coding: utf-8 -*-
"""C2200c probe: full-resolution streak detection on one frame.

The downscaled detector (c2200_kn16_streaks.py) missed the thinnest lines: a
1-2 px streak averaged over a 4x4 block falls under the threshold, so only the
heavier lines were removed. Correcting the rest needs the baseline at native
resolution. This probe runs the same idea at 1:1 on a single frame and writes
sky crops so the result can be judged by eye before any rebuild is fired.
"""
import io
import os
import subprocess
import sys

import numpy as np
from PIL import Image

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
SRC = os.path.join(MEDIA, "clips-local-768", "KN_A-KN16.mp4")
BAK = os.path.join(MEDIA, "clip-archive-c2200", "KN_A-KN16-c2200-fresh.mp4")
OUT = os.path.join(MEDIA, "qc-frames-c2200")

HMED = 9
THR = 3.0
RUN = 25
RUN_FRAC = 0.5
GAIN = 1.0
T = 9.0


def frame(path, t):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path,
                        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True)
    return np.asarray(Image.open(io.BytesIO(p.stdout)).convert("RGB")).astype(np.float32)


def hmedian(y, width):
    pad = width // 2
    p = np.pad(y, ((0, 0), (pad, pad)), mode="edge")
    win = np.lib.stride_tricks.sliding_window_view(p, width, axis=1)
    return np.partition(win, width // 2, axis=2)[:, :, width // 2]


def vmean(m, rows):
    pad = rows // 2
    p = np.pad(m, ((pad, pad), (0, 0)), mode="edge")
    c = np.cumsum(p, axis=0)
    c = np.vstack([np.zeros((1, c.shape[1])), c])
    return (c[rows:] - c[:-rows]) / float(rows)


def main():
    a = frame(SRC, T)
    y = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    base = hmedian(y, HMED)
    excess = y - base
    hit = (excess > THR).astype(np.float32)
    wide = np.maximum.reduce([np.roll(hit, k, axis=1) for k in (-1, 0, 1)])
    coh = vmean(wide, RUN)
    mask = np.clip((coh - RUN_FRAC) / 0.2, 0.0, 1.0)
    cut = (mask * np.clip(excess, 0.0, 45.0) * GAIN)[:, :, None]
    out = np.clip(a - cut, 0, 255).astype(np.uint8)
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(out).save(os.path.join(OUT, "c2200c_t9_after.png"))
    # sky-only crops, 2x zoom, for judging at native detail
    crop = (0, 0, 672, 384)
    Image.fromarray(a.astype(np.uint8)).crop(crop).resize((1344, 768), Image.LANCZOS).save(
        os.path.join(OUT, "c2200c_t9_before_sky2x.png"))
    Image.fromarray(out).crop(crop).resize((1344, 768), Image.LANCZOS).save(
        os.path.join(OUT, "c2200c_t9_after_sky2x.png"))
    print("mask px %d | mean excess on mask %.2f | yavg %.2f -> %.2f"
          % (int((mask > 0.5).sum()),
             float(excess[mask > 0.5].mean()) if (mask > 0.5).any() else 0.0,
             float(y.mean()), float(out.mean())))
    return 0


if __name__ == "__main__":
    sys.exit(main())