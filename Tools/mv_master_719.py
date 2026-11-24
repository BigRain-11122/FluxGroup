# -*- coding: utf-8 -*-
"""mv_master_719.py - v719 24fps base -> 60fps 1920x1096 master (lanczos+unsharp, AAC -14 LUFS).

CEO 2026-11-02 order: 60fps + upscale precision + audible track.
Chain: chunked (row-boundary aligned) minterpolate 24->60 -> scale lanczos 1920x1096
-> unsharp -> x264 CRF17; concat; audio loudnorm -> AAC 320k; mux; verify.
"""
import importlib.util
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(BASE, "full_mv_v719.mp4")
OUT = os.path.join(BASE, "full_mv_v719_60fps_1080p.mp4")
WORK = r"D:\FleetWorker\master719"
VF = ("minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:"
      "scd=fdiff:scd_threshold=8,"
      "scale=1920:1096:flags=lanczos,unsharp=5:5:0.5:5:5:0.0")
WORKERS = 5
X264_THREADS = 3

spec = importlib.util.spec_from_file_location("v5", os.path.join(BASE, "build_full_mv_v5.py"))
v5 = importlib.util.module_from_spec(spec)
sys.argv = ["x"]
try:
    spec.loader.exec_module(v5)
except SystemExit:
    pass
rows = v5.build_rows_v5()
os.makedirs(WORK, exist_ok=True)

# group rows into chunks >= ~20s, boundaries strictly at row starts
chunks = []
cur_t0 = None
cur_t1 = None
for sid, t0, t1, v, src, is_new in rows:
    if cur_t0 is None:
        cur_t0 = t0
    cur_t1 = t1
    if cur_t1 - cur_t0 >= 20.0:
        chunks.append((cur_t0, cur_t1))
        cur_t0 = None
if cur_t0 is not None:
    chunks.append((cur_t0, cur_t1))
print("chunks=%d rows=%d span=%.3f-%.3f" % (len(chunks), len(rows), chunks[0][0], chunks[-1][1]), flush=True)


def run_chunk(i, t0, t1):
    out = os.path.join(WORK, "chunk_%02d.mp4" % i)
    if os.path.exists(out):
        got = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                              "-show_entries", "stream=nb_frames", "-of", "default=nw=1:nk=1", out],
                             capture_output=True, text=True).stdout.strip()
        want = round((t1 - t0) * 60)
        if got and abs(int(got) - want) <= 2:
            print("  chunk %d cached (%s frames)" % (i, got), flush=True)
            return out
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", "%.4f" % t0, "-to", "%.4f" % t1, "-i", SRC,
           "-vf", VF, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-threads", str(X264_THREADS), "-pix_fmt", "yuv420p", "-r", "60", out]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("CHUNK %d FAILED: %s" % (i, r.stderr[:200]), flush=True)
        raise SystemExit(3)
    print("  chunk %d done (%.1fs src)" % (i, t1 - t0), flush=True)
    return out


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    parts = list(ex.map(lambda c: run_chunk(c[0], c[1], c[2]), [(i, t0, t1) for i, (t0, t1) in enumerate(chunks)]))

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
