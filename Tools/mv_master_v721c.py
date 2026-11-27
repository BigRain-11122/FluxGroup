# -*- coding: utf-8 -*-
"""mv_master_v721c.py - frame-exact 60fps master, corrected chunking.

v721b lesson: -frames:v is an OUTPUT cap (clipped the 60fps interpolation back to
source-count = 93.7s broken film). Correct: limit source frames with a trim
filter BEFORE minterpolate; output is a full 60fps span of exactly n_src frames.

Chunk boundaries at row frame indices (b = round(t0*24)), grouped to ~480 frames
(20s); final chunk bounded by TARGET_FRAMES=5623. Expected total ~=14057.5 frames.
"""
import importlib.util
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(BASE, "full_mv_v721.mp4")
OUT = os.path.join(BASE, "full_mv_v721_60fps_1080p.mp4")
WORK = r"D:\FleetWorker\master721d"
VF = ("minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:"
      "scd=fdiff:scd_threshold=8,"
      "scale=1920:1096:flags=lanczos,unsharp=5:5:0.5:5:5:0.0")
WORKERS = 5
X264_THREADS = 3
FPS = 24
TARGET_FRAMES = 5623
GROUP_FRAMES = 480

spec = importlib.util.spec_from_file_location("v5", os.path.join(BASE, "build_full_mv_v5.py"))
v5 = importlib.util.module_from_spec(spec)
sys.argv = ["x"]
try:
    spec.loader.exec_module(v5)
except SystemExit:
    pass
rows = v5.build_rows_v5()
os.makedirs(WORK, exist_ok=True)

bounds = [int(round(t0 * FPS)) for (_sid, t0, _t1, _v, _s, _n) in rows if t0 > 0]
bounds = sorted(set(bounds))
bounds = [0] + bounds + [TARGET_FRAMES]

# group to ~GROUP_FRAMES
chunks = []
start = bounds[0]
for b in bounds[1:-1]:
    if b - start >= GROUP_FRAMES:
        chunks.append((start, b))
        start = b
chunks.append((start, TARGET_FRAMES))
exp_total = sum(b - a for a, b in chunks)
print("chunks=%d expected_video_frames=%.1f" % (len(chunks), exp_total * 60.0 / FPS), flush=True)


def run_chunk(i, f0, f1, is_last=False):
    out = os.path.join(WORK, "chunk_%02d.mp4" % i)
    n_src = f1 - f0
    want = int(round(n_src * 60.0 / FPS))
    # +2 source frames overlap feeds motion estimation past the span end; the
    # output trim keeps exactly `want` frames = [t0, t0+n_src/24) with zero
    # gap/overlap vs the next chunk. Last chunk: static-card tpad covers the
    # film-end frames beyond the last source frame.
    vf = ("trim=end_frame=%d," % (n_src + 2)) + VF
    if is_last:
        vf += ",tpad=stop_mode=clone:stop_duration=0.2"
    vf += ",trim=end_frame=%d" % want
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", "%.6f" % (f0 / float(FPS)), "-i", SRC,
           "-vf", vf, "-an",
           "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-threads", str(X264_THREADS), "-pix_fmt", "yuv420p", "-r", "60", out]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("CHUNK %d FAILED: %s" % (i, r.stderr[:200]), flush=True)
        raise SystemExit(3)
    got = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-count_frames", "-show_entries", "stream=nb_read_frames",
                          "-of", "default=nw=1:nk=1", out], capture_output=True, text=True).stdout.strip()
    ok = abs(int(got or 0) - want) <= 1
    print("  chunk %02d frames=%s/%d src=%df %s" % (i, got, want, n_src, "OK" if ok else "OFF"), flush=True)
    return out


jobs = []
for idx, (a, b) in enumerate(chunks):
    jobs.append((idx, a, b, idx == len(chunks) - 1))
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    parts = list(ex.map(lambda c: run_chunk(c[0], c[1], c[2], c[3]), jobs))

listfile = os.path.join(WORK, "concat.txt")
with open(listfile, "w", encoding="utf-8") as f:
    for p in parts:
        f.write("file '%s'\n" % p.replace("\\", "/"))

video = os.path.join(WORK, "master_video.mp4")
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", listfile, "-c", "copy", video], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("concat failed: " + r.stderr[:300])

audio = os.path.join(WORK, "master_audio.m4a")
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-map", "0:a",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-c:a", "aac", "-b:a", "320k", "-ar", "44100", audio],
                   capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("audio failed: " + r.stderr[:300])

r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio,
                   "-map", "0:v", "-map", "1:a", "-c", "copy",
                   "-movflags", "+faststart", OUT], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("mux failed: " + r.stderr[:300])

p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "stream=codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels:"
                    "format=duration,size", "-of", "default=nw=1", OUT],
                   capture_output=True, text=True)
print(p.stdout, flush=True)
nf = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                     "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", OUT],
                    capture_output=True, text=True).stdout.strip()
print("video_frames=%s (expect ~14057)" % nf, flush=True)
vol = subprocess.run(["ffmpeg", "-hide_banner", "-i", OUT, "-map", "0:a", "-af", "volumedetect",
                      "-f", "null", "-"], capture_output=True, text=True, errors="replace")
for line in vol.stderr.splitlines():
    if "mean_volume" in line or "max_volume" in line:
        print(line.strip(), flush=True)
print("MASTER-DONE %s" % OUT, flush=True)
