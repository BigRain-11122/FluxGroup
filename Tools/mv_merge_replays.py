# -*- coding: utf-8 -*-
"""mv_merge_replays.py - collapse replay slices into one continuous shot.

The master cuts some continuous shots into 0.3-0.6 s slices that restart at nearly the same
frame (20 adjacent pairs measured by mv_replay_scan). On screen that reads as strobing.

For every run of such slices the whole span is replaced by one continuous extract from the
shot's own source file, at the shot's own speed, with the exact same number of frames - so the
timeline, the burned subtitles and every downstream cut stay where they are.

Usage:
  py mv_merge_replays.py <src.mp4> <out.mp4> [--no-subs] [--only 012,013]
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_gate as RG

W, H = 1344, 768
FPS = 24
TOTAL = 5623


def rows_v5():
    p = os.path.join(r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1",
                     "build_full_mv_v5.py")
    import importlib.util
    spec = importlib.util.spec_from_file_location("v5m", p)
    m = importlib.util.module_from_spec(spec)
    argv = sys.argv
    sys.argv = ["x"]
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass
    finally:
        sys.argv = argv
    return m.build_rows_v5(), m


def detect_runs(video):
    cuts, err = RG.detect_cuts(video)
    if err:
        sys.exit("scene detect failed: " + err)
    ts = [0.0] + cuts + [TOTAL / FPS]
    shots = [(i + 1, ts[i], ts[i + 1]) for i in range(len(ts) - 1) if ts[i + 1] - ts[i] >= 0.2]

    Wl, Hl, fsl = 160, 90, 160 * 90 * 3
    want = {}
    for n, t0, t1 in shots:
        want[int(round(t0 * FPS))] = n
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", "scale=%dx%d" % (Wl, Hl),
                          "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE, bufsize=10**8)
    got = {}
    k = 0
    while True:
        b = p.stdout.read(fsl)
        if len(b) < fsl:
            break
        if k in want:
            got[want[k]] = np.frombuffer(b, np.uint8).reshape(Hl, Wl, 3).astype(np.int16)
        k += 1
    p.stdout.close()
    p.wait()

    def dh(a):
        y = a.astype(np.float32).mean(axis=2)
        y = y[:: max(1, Hl // 8), :: max(1, Wl // 8)][:8, :8]
        return (y[:, 1:] > y[:, :-1]).flatten()

    def dist(a, b):
        return int((dh(a) != dh(b)).sum())

    runs = []
    cur = None
    for i in range(len(shots) - 1):
        n1, t01, t11 = shots[i]
        n2, t02, t12 = shots[i + 1]
        if n1 in got and n2 in got and dist(got[n1], got[n2]) <= 10:
            if cur is None:
                cur = [n1, t01, t12]
            else:
                cur[2] = t12
        else:
            if cur:
                runs.append(tuple(cur))
                cur = None
    if cur:
        runs.append(tuple(cur))
    return runs


ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--only", default="")
a = ap.parse_args()
SRC = a.src

rows, v5m = rows_v5()
runs = detect_runs(SRC)
print("runs=%d" % len(runs), flush=True)

# build replacement frame arrays
repl = []          # (f0, f1, [frames])
for n1, t0, t1 in runs:
    f0, f1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    span = f1 - f0
    if span < 6:
        continue
    row = None
    for sid, r0, r1, v, src, _new in rows:
        # a merge is only valid when the whole span lives inside ONE row: a run that crosses
        # row boundaries is several different shots and must not be replaced by a single source
        if r0 - 0.08 <= t0 and t1 <= r1 + 0.08:
            row = (sid, v, src)
            break
    if not row or not row[2]:
        print("  SKIP %.2f-%.2f (no row)" % (t0, t1), flush=True)
        continue
    sid, v, src = row
    if not os.path.exists(src):
        try:
            src, _kind = v5m.find_src_v5(os.path.basename(src))
        except Exception:
            src = None
    if not src or not os.path.exists(src):
        print("  SKIP %.2f-%.2f (source missing: %s)" % (t0, t1, os.path.basename(str(row[2]))), flush=True)
        continue
    want_sec = span / float(FPS)
    vf = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24"
          % (W, H, W, H))
    if v < 0.96:
        vf = "minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % v + vf
    else:
        vf = "setpts=PTS/%.4f," % v + vf
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-an", "-vf", vf, "-t", "%.4f" % want_sec,
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)
    frames = []
    fs = W * H * 3
    while len(frames) < span:
        b = p.stdout.read(fs)
        if len(b) < fs:
            break
        frames.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
    p.stdout.close()
    p.wait()
    if len(frames) < span:
        # hold the last frame if the source is short - never overspeed a shot
        while frames and len(frames) < span:
            frames.append(frames[-1])
    frames = frames[:span]
    if len(frames) < span:
        print("  SKIP %.2f-%.2f (source too short %d/%d)" % (t0, t1, len(frames), span), flush=True)
        continue
    repl.append((f0, f1, frames))
    print("  merge %.2f-%.2f (%d frames, %s v=%.2f)" % (t0, t1, span, sid, v), flush=True)

lookup = {}
for f0, f1, frames in repl:
    for i, im in enumerate(frames):
        lookup[f0 + i] = im

print("replacing %d frames in single pass ..." % len(lookup), flush=True)
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE, bufsize=10**8)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-an",
                        "-c:v", "libx264", "-crf", "17", "-preset", "fast", "-profile:v", "high",
                        "-g", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), a.out],
                       stdin=subprocess.PIPE)
fs = W * H * 3
i = 0
while True:
    b = dec.stdout.read(fs)
    if len(b) < fs:
        break
    if i in lookup:
        out = lookup[i]
    else:
        out = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    enc.stdin.write(out.tobytes())
    i += 1
enc.stdin.close()
enc.wait()
dec.stdout.close()
dec.wait()
print("encoded %d" % i, flush=True)
if i != TOTAL:
    sys.exit("FATAL frame count %d" % i)

tmp = a.out + ".v.mp4"
os.replace(a.out, tmp)
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", SRC, "-map", "0:v", "-map", "1:a",
                    "-c", "copy", "-movflags", "+faststart", a.out], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("mux failed: " + r.stderr[:300])
os.remove(tmp)
print("DONE", a.out)