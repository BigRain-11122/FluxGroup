# -*- coding: utf-8 -*-
"""mv_rebuild_from_edl.py - rebuild the cut from the EDL rows, with no patching.

Why: the v6xx/v7xx masters were repaired layer on layer, and the repairs themselves created
new seams and replay slices. This rebuilds from the row table (73 rows), one continuous
segment per row, same speed, exact duration, then concatenates, restores the original song and
burns the lyric ASS. Frame count is asserted against the 5623-frame target.

Usage:
  py mv_rebuild_from_edl.py <out.mp4> [--no-subs] [--dry]
"""
import argparse
import importlib.util
import os
import subprocess
import sys

BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
WORK = r"D:\FleetWorker\rebuild"
W, H, FPS = 1344, 768, 24
TARGET_FRAMES = 5623
CRF = "12"

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--no-subs", action="store_true")
ap.add_argument("--dry", action="store_true")
ap.add_argument("--grade", action="store_true",
                help="split grade: ancient shots desaturated/cooler/heavier grain, modern kept")
a = ap.parse_args()

# era split from the row id (measured on the sheets: everything reads as one amber palette)
ANCIENT_PREFIX = ("S", "N", "C", "R", "D", "B", "T_", "KF", "SIL")


def era_of(sid):
    return "ancient" if sid.startswith(ANCIENT_PREFIX) else "modern"


def grade_chain(era):
    if era == "ancient":
        return ("eq=saturation=0.86:contrast=1.04,"
                "colorbalance=rs=-0.02:gs=-0.01:bs=0.035,"
                "noise=alls=6:allf=t+u,")
    return "eq=saturation=1.0:contrast=1.03:brightness=0.01,"

spec = importlib.util.spec_from_file_location("v5", os.path.join(BASE, "build_full_mv_v5.py"))
v5 = importlib.util.module_from_spec(spec)
argv = sys.argv
sys.argv = ["x"]
try:
    spec.loader.exec_module(v5)
except SystemExit:
    pass
finally:
    sys.argv = argv

rows = v5.build_rows_v5()
print("rows=%d" % len(rows), flush=True)
total = sum(r[2] - r[1] for r in rows)
print("planned duration=%.3fs  frames~%d" % (total, round(total * FPS)), flush=True)

os.makedirs(WORK, exist_ok=True)
if a.grade:
    WORK = WORK + "_grade2"
os.makedirs(WORK, exist_ok=True)
listfile = os.path.join(WORK, "segments.txt")
seg_files = []

SRC_OVERRIDE = {
    "SIL4": r"D:\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\v51_SIL4_at_207.mp4",
}

for idx, (sid, t0, t1, v, src, is_new) in enumerate(rows):
    want = t1 - t0
    if not src:
        src = next((p for k, p in SRC_OVERRIDE.items() if sid.startswith(k)), None)
    if not src:
        print("MISSING SRC %s" % sid, flush=True)
        sys.exit(2)
    if not os.path.exists(src):
        try:
            src, _k = v5.find_src_v5(os.path.basename(src))
        except Exception:
            src = None
    if not src or not os.path.exists(src):
        src = next((p for k, p in SRC_OVERRIDE.items() if sid.startswith(k)), None)
    if not src or not os.path.exists(src):
        print("MISSING SRC %s :: %s" % (sid, src), flush=True)
        sys.exit(2)

    dst = os.path.join(WORK, "seg_%03d_%s.mp4" % (idx, "".join(ch if ch.isalnum() else "_" for ch in sid)))
    if os.path.exists(dst):
        # reuse a segment already built for the same row (cache survives re-runs)
        pd = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=nw=1:nk=1", dst], capture_output=True, text=True)
        try:
            if abs(float(pd.stdout.strip()) - want) < 0.06:
                seg_files.append(dst)
                continue
        except Exception:
            pass
    vf = ("scale=%d:%d:force_original_aspect_ratio=decrease,"
          "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=%d" % (W, H, W, H, FPS))
    if a.grade:
        vf = grade_chain(era_of(sid)) + vf
    if v < 0.96:
        vf = "minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % v + vf
    else:
        vf = "setpts=PTS/%.4f," % v + vf
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-vf", vf,
           "-t", "%.4f" % want, "-c:v", "libx264", "-preset", "fast", "-crf", CRF,
           "-pix_fmt", "yuv420p", "-r", str(FPS), dst]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("FAIL %s :: %s" % (sid, r.stderr[:200]), flush=True)
        sys.exit(3)
    seg_files.append(dst)
    if idx % 10 == 0:
        print("  [%d/%d] %s %.2fs v=%.2f" % (idx + 1, len(rows), sid, want, v), flush=True)

with open(listfile, "w", encoding="utf-8") as f:
    for p in seg_files:
        f.write("file '%s'\n" % p.replace("\\", "/"))

silent = os.path.join(WORK, "silent.mp4")
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", listfile, "-c", "copy", silent], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("concat failed: " + r.stderr[:300])

song = None
for attr in ("SONG_WAV", "SONG"):
    song = song or getattr(v5, attr, None)
print("song=%s" % song, flush=True)

stage = os.path.join(WORK, "with_audio.mp4")
subs = os.path.join(BASE, "lyric_track.ass")
if a.no_subs:
    vf = "null"
else:
    vf = "ass='%s'" % subs.replace("\\", "/").replace(":", "\\:")
vf_final = vf + ",tpad=stop_mode=clone:stop_duration=0.21" if vf != "null" \
        else "tpad=stop_mode=clone:stop_duration=0.21"
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", song,
                    "-vf", vf_final,
                    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "fast",
                    "-crf", CRF, "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "copy",
                    "-frames:v", str(TARGET_FRAMES),
                    "-movflags", "+faststart", a.out], capture_output=True, text=True, errors="replace")
if r.returncode != 0:
    sys.exit("mux+subs failed: " + r.stderr[:400])

probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                        "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", a.out],
                       capture_output=True, text=True)
n = int(probe.stdout.strip() or 0)
print("frames=%d (target %d)" % (n, TARGET_FRAMES), flush=True)
print("DONE %s" % a.out)