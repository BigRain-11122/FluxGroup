# -*- coding: utf-8 -*-
"""mv_shot_sheets.py - per-shot review sheets for the director pass.

Samples 5 frames per shot (0/25/50/75/100%) and lays each shot out as a labelled row;
eight shots per sheet. Decodes the film once for the whole job.

Usage:
  py mv_shot_sheets.py <video> [--sheets DIR] [--per-sheet 8]
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_gate as RG

W, H = 1344, 768
FPS = 24
THUMB = (352, 201)


def decode_thumbs(video, want_frames):
    """Decode once; return {frame_index: thumbnail}."""
    fs = W * H * 3
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10**8)
    out = {}
    k = 0
    nxt = 0
    while True:
        b = p.stdout.read(fs)
        if len(b) < fs:
            break
        if k in want_frames:
            a = np.frombuffer(b, np.uint8).reshape(H, W, 3)
            out[k] = Image.fromarray(a).resize(THUMB, Image.LANCZOS)
            nxt += 1
            if nxt == len(want_frames):
                # keep draining is unnecessary; stop early
                break
        k += 1
    p.stdout.close()
    p.kill()
    return out


ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--sheets", default=r"D:\FleetWorker\review\sheets")
ap.add_argument("--per-sheet", type=int, default=8)
a = ap.parse_args()

os.makedirs(a.sheets, exist_ok=True)
cuts, err = RG.detect_cuts(a.video)
if err:
    sys.exit("scene detect failed: " + err)
ts = [0.0] + cuts + [5623 / FPS]
shots = []
for i in range(len(ts) - 1):
    t0, t1 = ts[i], ts[i + 1]
    if t1 - t0 < 0.2:
        continue
    shots.append((i + 1, t0, t1))

want = set()
plan = []
for n, t0, t1 in shots:
    d = t1 - t0
    row = [t0 + 0.02, t0 + d * 0.25, t0 + d * 0.5, t0 + d * 0.75, max(t0 + 0.02, t1 - 0.06)]
    plan.append((n, t0, t1, d, row))
    for t in row:
        want.add(int(round(t * FPS)))

print("shots=%d frames=%d" % (len(shots), len(want)), flush=True)
frames = decode_thumbs(a.video, want)
print("decoded=%d" % len(frames), flush=True)

ROW_H = 232
for s in range(0, len(plan), a.per_sheet):
    batch = plan[s:s + a.per_sheet]
    sheet = Image.new("RGB", (352 * 5, ROW_H * len(batch)), (12, 12, 12))
    dr = ImageDraw.Draw(sheet)
    for r, (n, t0, t1, d, row) in enumerate(batch):
        for c, t in enumerate(row):
            im = frames.get(int(round(t * FPS)))
            if im is not None:
                sheet.paste(im, (c * 352, r * ROW_H + 26))
        dr.text((6, r * ROW_H + 6),
                "#%03d  %6.2f-%6.2f  d=%.2fs" % (n, t0, t1, d), fill=(240, 220, 160))
    dst = os.path.join(a.sheets, "sheet_%03d-%03d.jpg" % (batch[0][0], batch[-1][0]))
    sheet.save(dst, quality=88)
    print("wrote", dst, flush=True)