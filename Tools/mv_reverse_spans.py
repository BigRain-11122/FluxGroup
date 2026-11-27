# -*- coding: utf-8 -*-
"""mv_reverse_spans.py - play given spans backwards (used to fix camera-direction reversals).

Only carving / texture shots are safe to reverse: no faces, no text, no directional action.
Frame count is unchanged.

Usage:
  py mv_reverse_spans.py <src> <out> --spans "102.833,108.5;126.208,131.7"
"""
import argparse
import os
import subprocess
import sys

import numpy as np

W, H, FPS = 1344, 768, 24
TOTAL = 5623


def parse(spec):
    out = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        t0, t1 = [float(x) for x in part.split(",")]
        out.append((int(round(t0 * FPS)), int(round(t1 * FPS))))
    return out


ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--spans", required=True)
a = ap.parse_args()
spans = parse(a.spans)

fs = W * H * 3
frames = {}
for s0, s1 in spans:
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", "%.4f" % (s0 / FPS),
                          "-i", a.src, "-frames:v", str(s1 - s0),
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE, bufsize=10**8)
    buf = []
    while len(buf) < (s1 - s0):
        b = p.stdout.read(fs)
        if len(b) < fs:
            break
        buf.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
    p.stdout.close()
    p.wait()
    if len(buf) != s1 - s0:
        sys.exit("span read short: %d/%d" % (len(buf), s1 - s0))
    for i, im in enumerate(reversed(buf)):
        frames[s0 + i] = im
    print("reversed %.3f-%.3f (%d frames)" % (s0 / FPS, s1 / FPS, len(buf)), flush=True)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.src, "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10**8)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-an",
                        "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-profile:v", "high",
                        "-g", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), a.out],
                       stdin=subprocess.PIPE)
i = 0
while True:
    b = dec.stdout.read(fs)
    if len(b) < fs:
        break
    out = frames.get(i)
    if out is None:
        out = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    enc.stdin.write(out.tobytes())
    i += 1
enc.stdin.close()
enc.wait()
dec.stdout.close()
dec.wait()
print("encoded %d" % i, flush=True)
if i != TOTAL:
    sys.exit("FATAL frames %d" % i)

tmp = a.out + ".v.mp4"
os.replace(a.out, tmp)
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", a.src, "-map", "0:v", "-map", "1:a",
                    "-c", "copy", "-movflags", "+faststart", a.out], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("mux failed: " + r.stderr[:300])
os.remove(tmp)
print("DONE", a.out)