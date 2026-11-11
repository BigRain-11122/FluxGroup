# -*- coding: utf-8 -*-
"""mv_master_v727.py - frame-exact 60fps master for the V727 two-shot
face-redesign rebuild.

Derived from mv_master_v723.py with:
  SRC   = full_mv_v727_768.mp4 (mv_rebuild_v727.py output)
  SEED  = master723 chunk cache = the signed v726 60fps chunks (11-10 render)
  V5_RESTORE (changed set) = only D03b_direct_gaze + E04_replay_faces --
  every chunk whose frame range contains neither slot is bit-identical to
  v726 and its 60fps render is copied from the seed cache (frame count
  re-verified; mismatch => re-render). The v724 lesson (dirty-set must cover
  every changed slot or stale chunks get reused) applies: the changed set
  here must equal the v727 REPLACE_SRC delta over v726 = exactly these two.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = r"D:\FleetWorker\rebuild_grade8_v722e\full_mv_v727_768.mp4"
OUT = r"D:\FleetWorker\rebuild_grade8_v722e\full_mv_v727_60fps_1080p.mp4"
WORK = r"D:\FleetWorker\master727"
SEED_DIR = r"D:\FleetWorker\master723"
TITLE_PNG = r"D:\FluxGroup\cph4\fleet\mv0001-handover\canon\title-design\title-v32.png"  # 定稿版（21:54 的 title-v3.png 是被否首版·v722g 用 v32）
VF = ("minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:"
      "scd=fdiff:scd_threshold=8,"
      "scale=1920:1096:flags=lanczos,unsharp=5:5:0.5:5:5:0.0")
WORKERS = 3
X264_THREADS = 3
FPS = 24
TARGET_FRAMES = 5623
GROUP_FRAMES = 480

# v727 changed slots (must equal the v727 REPLACE_SRC delta over the v726
# state -- D03b re-anchored take + E04 blonde priestess take)
V5_RESTORE = {
    "D03b_direct_gaze", "E04_replay_faces",
}

if not os.path.exists(SRC):
    sys.exit("SRC missing: %s (run mv_rebuild_v727.py first)" % SRC)
if not os.path.isfile(TITLE_PNG):
    sys.exit("TITLE PNG missing: %s" % TITLE_PNG)

spec = importlib.util.spec_from_file_location("v5", os.path.join(BASE, "build_full_mv_v5.py"))
v5 = importlib.util.module_from_spec(spec)
sys.argv = ["x"]
try:
    spec.loader.exec_module(v5)
except SystemExit:
    pass
rows = v5.build_rows_v5()
os.makedirs(WORK, exist_ok=True)

changed = [(t0, t1) for (sid, t0, t1, _v, _s, _n) in rows
           if sid.split("@")[0] in V5_RESTORE]

bounds = [int(round(t0 * FPS)) for (_sid, t0, _t1, _v, _s, _n) in rows if t0 > 0]
bounds = sorted(set(bounds))
bounds = [0] + bounds + [TARGET_FRAMES]
chunks = []
start = bounds[0]
for b in bounds[1:-1]:
    if b - start >= GROUP_FRAMES:
        chunks.append((start, b))
        start = b
chunks.append((start, TARGET_FRAMES))
exp_total = sum(b - a for a, b in chunks)
print("chunks=%d expected_video_frames=%.1f changed_ranges=%d"
      % (len(chunks), exp_total * 60.0 / FPS, len(changed)), flush=True)


def chunk_is_clean(f0, f1):
    t0, t1 = f0 / float(FPS), f1 / float(FPS)
    for c0, c1 in changed:
        if c0 < t1 and c1 > t0:
            return False
    return True


def probe_frames(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-count_frames", "-show_entries", "stream=nb_read_frames",
                        "-of", "default=nw=1:nk=1", path],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except Exception:
        return -1


def run_chunk(i, f0, f1, is_last=False):
    out = os.path.join(WORK, "chunk_%02d.mp4" % i)
    n_src = f1 - f0
    want = int(round(n_src * 60.0 / FPS))
    # v722 lesson: the last chunk's tpad clone tail legitimately over-delivers
    # ~6 frames (14057.5 -> 14064 total, matching the signed v722e/g masters).
    tol_hi = 12 if is_last else 1
    # self-reuse: an already-rendered chunk in this work dir with a matching
    # frame count is kept (makes resumed runs near-instant)
    if os.path.isfile(out):
        sf = probe_frames(out)
        if want - 1 <= sf <= want + tol_hi:
            print("  chunk %02d REUSED %d frames" % (i, sf), flush=True)
            return out
    if chunk_is_clean(f0, f1) and not is_last:
        seed = os.path.join(SEED_DIR, "chunk_%02d.mp4" % i)
        if os.path.isfile(seed):
            sf = probe_frames(seed)
            if sf == want:
                shutil.copyfile(seed, out)
                print("  chunk %02d SEEDED %d frames (v726)" % (i, sf), flush=True)
                return out
            print("  chunk %02d seed frame mismatch %s != %d -> render" % (i, sf, want), flush=True)
    vf = ("trim=end_frame=%d," % (n_src + 2)) + VF
    if is_last:
        vf += ",tpad=stop_mode=clone:stop_duration=0.2"
    if i == 0:
        # fold the v3 title card into this pass (chunk 0 = 0..~21.9s, card lives
        # 0.45-3.37s; fade in 0.45s from 0.45, fade out from 2.62 over 0.75s)
        fc = ("[0:v]%s,trim=end_frame=%d[base];"
              "[1:v]format=rgba,fade=t=in:st=0.45:d=0.45:alpha=1,"
              "fade=t=out:st=2.62:d=0.75:alpha=1[tit];"
              "[base][tit]overlay=0:0:eof_action=pass[v]"
              % (vf, want))
        cmd = ["ffmpeg", "-v", "error", "-y",
               "-ss", "%.6f" % (f0 / float(FPS)), "-i", SRC,
               "-loop", "1", "-t", "3.4", "-i", TITLE_PNG,
               "-filter_complex", fc, "-map", "[v]", "-an",
               "-c:v", "libx264", "-preset", "medium", "-crf", "17",
               "-threads", str(X264_THREADS), "-pix_fmt", "yuv420p", "-r", "60", out]
    else:
        vf += ",trim=end_frame=%d" % want
        cmd = ["ffmpeg", "-v", "error", "-y",
               "-ss", "%.6f" % (f0 / float(FPS)), "-i", SRC,
               "-vf", vf, "-an",
               "-c:v", "libx264", "-preset", "medium", "-crf", "17",
               "-threads", str(X264_THREADS), "-pix_fmt", "yuv420p", "-r", "60", out]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("CHUNK %d FAILED: %s" % (i, r.stderr[:300]), flush=True)
        raise SystemExit(3)
    got = probe_frames(out)
    ok = (want - 1) <= got <= (want + tol_hi)
    print("  chunk %02d frames=%s/%d src=%df %s" % (i, got, want, n_src, "OK" if ok else "OFF"), flush=True)
    if not ok:
        raise SystemExit(4)
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
