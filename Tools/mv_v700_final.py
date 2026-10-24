# -*- coding: utf-8 -*-
"""mv_v700_final.py - one-pass final repair of the mv0001 cut (frame count unchanged).

A. single-frame pops  -> replace the pop frame with the previous frame (no frame deleted,
                         so the timeline and every planned cut stay put)
B. dark shot (#69)    -> local lift + slight contrast on that window only
C. duplicate shots    -> re-frame the whole second occurrence at 1.34x with a small lateral
                         offset, so it stops reading as the same frame twice

Positions:
  pops come from Tools/mv_pop_scan.py (verified: 11 pops).
  duplicate second-occurrences come from SHOT-AUDIT-AND-REPAIR-PLAN-20261023.md.
  shot windows come from scene detection on the source (not from a stale plan table).

Usage:
  py mv_v700_final.py <src.mp4> <out.mp4>
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_gate as RG

W, H = 1344, 768
FPS = 24
TOTAL = 5623

POP_TIMES = [17.50, 44.00, 44.04, 77.33, 77.38, 91.08, 108.21,
             138.54, 190.00, 205.08, 216.29, 224.00]
DUP_TIMES = [205.08, 138.54, 193.10, 108.21, 208.79, 224.00]
DARK_WIN = (226.0, 231.0)
# Underexposed windows measured on the cut (mean luma 21-34 of 255). E04's modern half is
# too dark for the lead's profile to read, which is exactly what reads as "the lead changed".
# Lift only, never re-shoot; edges are ramped so the lift itself adds no frame-diff spike.
LIFT_WINS = [(216.40, 219.85, 1.42), (226.0, 231.0, 1.22)]


def shot_windows(video):
    cuts, err = RG.detect_cuts(video)
    if err:
        sys.exit("scene detect failed: " + err)
    ts = [0.0] + cuts + [TOTAL / FPS]
    wins = []
    for i in range(len(ts) - 1):
        a, b = int(round(ts[i] * FPS)), int(round(ts[i + 1] * FPS))
        if b - a >= 2:
            wins.append((a, b))
    return wins, cuts


ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--no-dup", action="store_true", help="skip duplicate re-framing (pass 2+)")
ap.add_argument("--no-dark", action="store_true", help="skip dark-shot lift (pass 2+)")
a = ap.parse_args()
SRC = a.src

print("[1/4] scene detection ...", flush=True)
wins, cuts = shot_windows(SRC)
print("      shots=%d cuts=%d" % (len(wins), len(cuts)), flush=True)

# only single-frame pops are repairable this way: a multi-frame in-shot jump would freeze
# the motion and create a new artefact at its tail (measured on v701: 14 unplanned spikes,
# several of them created by the repair itself). Multi-frame jumps are source defects.
spikes = RG.islands(RG.frame_diffs(SRC))[1]


def grab_low(idx):
    want = set(idx)
    out = {}
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf",
                          "scale=%d:%d" % (RG.W, RG.H), "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE, bufsize=10**8)
    sz = RG.W * RG.H * 3
    k = 0
    while True:
        b = p.stdout.read(sz)
        if len(b) < sz:
            break
        if k in want:
            out[k] = np.frombuffer(b, np.uint8).reshape(RG.H, RG.W, 3).astype(np.int16)
        k += 1
    p.stdout.close()
    p.wait()
    return out


need = set()
for i in spikes:
    need.update([i - 1, i, i + 1])
_low = grab_low(need)
auto = []
for i in spikes:
    if i - 1 not in _low or i + 1 not in _low:
        continue
    d1 = float(np.abs(_low[i] - _low[i - 1]).mean())
    d2 = float(np.abs(_low[i + 1] - _low[i]).mean())
    d3 = float(np.abs(_low[i + 1] - _low[i - 1]).mean())
    denom = d1 + d2
    if denom > 1e-6 and (denom - d3) / denom >= 0.45:
        auto.append(i)
pop_frames = sorted(set(auto) | {int(round(t * FPS)) for t in POP_TIMES})
print("      single-frame pops=%d" % len(pop_frames), flush=True)
dup_wins = []
for t in DUP_TIMES:
    fr = int(round(t * FPS))
    for lo, hi in wins:
        if lo <= fr < hi:
            dup_wins.append((lo, hi))
            break
if a.no_dup:
    dup_wins = []
print("[2/4] pops=%d  dup windows=%s" % (
    len(pop_frames), ", ".join("%.2f-%.2f" % (l / FPS, h / FPS) for l, h in dup_wins)), flush=True)

dark_lo, dark_hi = int(DARK_WIN[0] * FPS), int(DARK_WIN[1] * FPS)

print("[3/4] single-pass re-encode ...", flush=True)
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10**8)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
                        "-i", "-", "-an", "-c:v", "libx264", "-crf", "17", "-preset", "fast",
                        "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p",
                        "-r", str(FPS), a.out], stdin=subprocess.PIPE)

fs = W * H * 3
popset = set(pop_frames)
prev = None
i = 0
while True:
    b = dec.stdout.read(fs)
    if len(b) < fs:
        break
    fr = np.frombuffer(b, np.uint8).reshape(H, W, 3)

    if i in popset and prev is not None:
        out = prev
    else:
        out = fr.copy()
        for lo, hi in dup_wins:
            if lo <= i < hi:
                cw, ch = int(W / 1.34), int(H / 1.34)
                x = (W - cw) // 2 + 12
                y = (H - ch) // 2
                crop = out[y:y + ch, x:x + cw]
                out = np.asarray(Image.fromarray(crop).resize((W, H), Image.LANCZOS))
                break
        hit = None
        for w0, w1, gain in LIFT_WINS:
            lo, hi = int(w0 * FPS), int(w1 * FPS)
            if lo <= i < hi:
                hit = (lo, hi, gain)
                break
        if hit:
            lo, hi, gain = hit
            # ramp the lift in/out over 12 frames: a hard on/off at the window edge is itself
            # a frame-diff spike (measured at 226.00 / 231.00 on v701)
            ramp = 12
            if i - lo < ramp:
                g = (i - lo + 1) / float(ramp)
            elif hi - i <= ramp:
                g = (hi - i) / float(ramp)
            else:
                g = 1.0
            f = out.astype(np.float32) / 255.0
            lifted = np.clip((f ** 0.82) * gain, 0, 1)
            out = ((f * (1 - g) + lifted * g) * 255.0).astype(np.uint8)

    enc.stdin.write(out.tobytes())
    prev = out
    i += 1

enc.stdin.close()
enc.wait()
dec.stdout.close()
dec.wait()
print("      encoded %d frames" % i, flush=True)
if i != TOTAL:
    sys.exit("FATAL frame count %d != %d" % (i, TOTAL))

print("[4/4] muxing original audio ...", flush=True)
tmp = a.out + ".v.mp4"
os.replace(a.out, tmp)
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", SRC,
                    "-map", "0:v", "-map", "1:a", "-c", "copy",
                    "-movflags", "+faststart", a.out], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("mux failed: " + r.stderr[:400])
os.remove(tmp)
json.dump({"pops": [p / FPS for p in pop_frames],
           "dup_windows": [[l / FPS, h / FPS] for l, h in dup_wins],
           "dark": list(DARK_WIN)},
          open(a.out + ".repair.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE %s" % a.out)