# -*- coding: utf-8 -*-
"""mv_replay_scan.py - find spans where the same source frame is replayed as several cuts.

Why: the current master cuts some continuous shots into 0.3-0.6 s slices that each restart at
almost the same frame. On screen it reads as strobing / "same shot twice", which is one of the
defects the director flagged.

Method: for every detected shot, take its first frame and its mid frame; compare adjacent
shots with dHash. If shot N+1 starts within a few bits of shot N's start, the cut is a replay.

Usage:
  py mv_replay_scan.py <video> [--json out.json]
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_gate as RG

W, H = 160, 90
FS = W * H * 3
FPS = 24


def dhash(a, b):
    """a, b: (H, W, 3) int16 -> 64-bit dhash on grayscale."""
    def g(x):
        y = x.astype(np.float32).mean(axis=2)
        y = y[:: max(1, H // 8), :: max(1, W // 8)][:8, :8]
        return (y[:, 1:] > y[:, :-1]).flatten()
    return int("".join("1" if v else "0" for v in g(a)), 2) ^ int("".join("1" if v else "0" for v in g(b)), 2)


def popcount(x):
    return bin(x).count("1")


ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--json", default=r"D:\FleetWorker\review\replay_scan.json")
a = ap.parse_args()

cuts, err = RG.detect_cuts(a.video)
if err:
    sys.exit("scene detect failed: " + err)
ts = [0.0] + cuts + [5623 / FPS]
shots = [(i + 1, ts[i], ts[i + 1]) for i in range(len(ts) - 1) if ts[i + 1] - ts[i] >= 0.2]

want = {}
for n, t0, t1 in shots:
    want[int(round(t0 * FPS))] = ("first", n)
    want[int(round((t0 + (t1 - t0) / 2) * FPS))] = ("mid", n)

p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.video, "-vf", "scale=%d:%d" % (W, H),
                      "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     stdout=subprocess.PIPE, bufsize=10**8)
got = {}
k = 0
while True:
    b = p.stdout.read(FS)
    if len(b) < FS:
        break
    if k in want:
        got[want[k]] = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.int16)
    k += 1
p.stdout.close()
p.wait()

pairs = []
for i in range(len(shots) - 1):
    n1, t01, t11 = shots[i]
    n2, t02, t12 = shots[i + 1]
    f1 = got.get(("first", n1))
    f2 = got.get(("first", n2))
    if f1 is None or f2 is None:
        continue
    dist = popcount(dhash(f1, f2))
    if dist <= 10:
        pairs.append({"a": n1, "b": n2, "t_a": round(t01, 2), "t_b": round(t02, 2),
                      "d_a": round(t11 - t01, 2), "d_b": round(t12 - t02, 2), "dhash": dist})

print("shots=%d  replay-adjacent pairs=%d" % (len(shots), len(pairs)))
for x in pairs:
    print("  #%03d(%5.2fs,%.2fs) -> #%03d(%5.2fs,%.2fs)  dHash=%d"
          % (x["a"], x["t_a"], x["d_a"], x["b"], x["t_b"], x["d_b"], x["dhash"]))
json.dump({"shots": [[n, round(t0, 2), round(t1, 2)] for n, t0, t1 in shots], "pairs": pairs},
          open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", a.json)