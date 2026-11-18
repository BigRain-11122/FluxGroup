# -*- coding: utf-8 -*-
"""mv_master_v721b.py - frame-exact chunked 60fps master (fixes per-chunk minterpolate
tail loss that left v1 27 frames / 0.45s shorter than the audio).

Chunk boundaries at row-start frame indices b_i = round(t0*24); each chunk takes
exactly (b_next - b) source frames via -frames:v, so chunks tile the 5623-frame
film with zero gap/overlap. Final chunk bounded by TARGET_FRAMES=5623.
"""
import importlib.util
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(BASE, "full_mv_v721.mp4")
OUT = os.path.join(BASE, "full_mv_v721_60fps_1080p.mp4")
WORK = r"D:\FleetWorker\master721b"
VF = ("minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:"
      "scd=fdiff:scd_threshold=8,"
      "scale=1920:1096:flags=lanczos,unsharp=5:5:0.5:5:5:0.0")
WORKERS = 5
X264_THREADS = 3
FPS = 24
TARGET_FRAMES = 5623

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
bounds = [0] + bounds + [TARGET_FRAMES]
chunks = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
print("chunks=%d span_frames=%d..%d (total %d)" % (len(chunks), bounds[0], bounds[-1], bounds[-1] - bounds[0]), flush=True)
exp_total = sum(b - a for a, b in chunks)
print("expected_video_frames=%.1f" % (exp_total * 60.0 / FPS), flush=True)


def run_chunk(i, f0, f1):
    out = os.path.join(WORK, "chunk_%02d.mp4" % i)
    n_src = f1 - f0
    want = int(round(n_src * 60.0 / FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", "%.6f" % (f0 / float(FPS)), "-i", SRC,
           "-frames:v", str(n_src), "-vf", VF, "-an",
           "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-threads", str(X264_THREADS), "-pix_fmt", "yuv420p", "-r", "60", out]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("CHUNK %d FAILED: %s" % (i, r.stderr[:200]), flush=True)
        raise SystemExit(3)
    got = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-count_frames", "-show_entries", "stream=nb_read_frames",
                          "-of", "default=nw=1:nk=1", out], capture_output=True, text=True).stdout.strip()
    print("  chunk %02d frames=%s/%d src=%df %s" % (i, got, want, n_src, "OK" if abs(int(got or 0) - want) <= 2 else "OFF"), flush=True)
    return out


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    parts = list(ex.map(lambda c: run_chunk(c[0], c[1], c[2]), [(i, a, b) for i, (a, b) in enumerate(chunks)]))

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
