# -*- coding: utf-8 -*-
"""mv_lift_windows.py - exposure lift on measured-dark windows, ramped, single encode.

Only the exposure changes: no re-timing, no re-framing, no frame count change. Windows are
given as start,end,gain triples and are ramped over 12 frames at both edges, because a hard
on/off switch is itself a frame-diff spike.

Usage:
  py mv_lift_windows.py <src> <out> --lifts "102.83,109.00,1.45;126.20,132.00,1.25"
"""
import argparse
import os
import subprocess
import sys

import numpy as np

W, H, FPS = 1344, 768, 24
TOTAL = 5623
RAMP = 12


def parse(spec):
    out = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        t0, t1, g = [float(x) for x in part.split(",")]
        out.append((int(round(t0 * FPS)), int(round(t1 * FPS)), g))
    return out


ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--lifts", required=True)
a = ap.parse_args()

wins = parse(a.lifts)
print("windows=%s" % ", ".join("%.2f-%.2f x%.2f" % (w0 / FPS, w1 / FPS, g) for w0, w1, g in wins),
      flush=True)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.src, "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10**8)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-an",
                        "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-profile:v", "high",
                        "-g", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), a.out],
                       stdin=subprocess.PIPE)
fs = W * H * 3
i = 0
while True:
    b = dec.stdout.read(fs)
    if len(b) < fs:
        break
    out = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    for w0, w1, gain in wins:
        if w0 <= i < w1:
            if i - w0 < RAMP:
                g = (i - w0 + 1) / float(RAMP)
            elif w1 - i <= RAMP:
                g = (w1 - i) / float(RAMP)
            else:
                g = 1.0
            f = out.astype(np.float32) / 255.0
            lifted = np.clip((f ** 0.84) * gain, 0, 1)
            out = ((f * (1 - g) + lifted * g) * 255.0).astype(np.uint8)
            break
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