# -*- coding: utf-8 -*-
"""mv_rebuild_v718.py - v718: four-row source substitution on top of the v717 rebuild.

Changes vs Tools/mv_rebuild_from_edl.py (v713/v717 lineage):
  1. REPLACE_SRC forces four rows to new sources (substitution beats the old
     SRC_OVERRIDE, which only fired when a row's src was empty):
       - INT1_desk_breath / INT3_photo_stare / E01c_first_line -> the three
         micro-motion 768P reburns (director review V717-REVISE §六.1, D2 fix)
       - R05_gold_threads -> brightness-lifted copy (SJ 126.25s landing frame
         unreadable; luma 14.8 -> 46.1 per the D-03 readability floor)
  2. Final pass overlays the tail attribution card (CEO 2026-10-19 order,
     "转载需注明出处 @大喵没鱼吃") over the Z04 glyph-remains window (t>=231.0).
  3. No AIGC badge - CEO 2026-10-30 order "不要加 ai 标识".

Everything else is the v717 recipe: row table, --grade era split, minterpolate
for v<0.96 rows, lyric ASS re-burn, 5623-frame assertion. Cached segments are
reused except the four substituted rows (their cache files were deleted).

Usage: py mv_rebuild_v718.py <out.mp4> [--dry]
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
CRF = "10"

REPLACE_SRC = {
    "INT1_desk_breath": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v718-clips-768\V718_S1_OPEN.mp4",
    "INT3_photo_stare": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v718-clips-768\V718_S2_PHOTO.mp4",
    "E01c_first_line": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v718-clips-768\V718_S3_DESK_REPRISE.mp4",
    "R05_gold_threads": r"D:\FleetWorker\rebuild\R05_gold_threads_lift.mp4",
}
CREDIT_PNG = os.path.join(BASE, "tail_credit_v510.png")
CREDIT_FROM_S = 231.0

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--no-subs", action="store_true")
ap.add_argument("--dry", action="store_true")
ap.add_argument("--grade", action="store_true",
                help="split grade: ancient shots desaturated/cooler/heavier grain, modern kept")
a = ap.parse_args()

ANCIENT_PREFIX = ("S", "N", "C", "R", "D", "B", "T_", "KF", "SIL")


def era_of(sid):
    return "ancient" if sid.startswith(ANCIENT_PREFIX) else "modern"


def grade_chain(era):
    if era == "ancient":
        return ("eq=saturation=0.86:contrast=1.04,"
                "colorbalance=rs=-0.02:gs=-0.01:bs=0.035,"
                "noise=alls=6:allf=t+u,")
    return "eq=saturation=1.0:contrast=1.03:brightness=0.01,"


for sid, p in REPLACE_SRC.items():
    if not os.path.exists(p):
        print("REPLACE SRC MISSING %s :: %s" % (sid, p), flush=True)
        sys.exit(2)
if not os.path.exists(CREDIT_PNG):
    print("CREDIT PNG MISSING %s" % CREDIT_PNG, flush=True)
    sys.exit(2)

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
if a.dry:
    for sid, t0, t1, v, src, is_new in rows:
        mark = " <= REPLACE %s" % REPLACE_SRC[sid] if sid in REPLACE_SRC else ""
        print("  %8.3f %8.3f %-24s v=%.2f %s%s" % (t0, t1, sid, v, src, mark), flush=True)
    sys.exit(0)

os.makedirs(WORK, exist_ok=True)
if a.grade:
    WORK = WORK + "_grade3"
os.makedirs(WORK, exist_ok=True)
listfile = os.path.join(WORK, "segments_v718.txt")
seg_files = []

SRC_OVERRIDE = {
    "SIL4": r"D:\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\v51_SIL4_at_207.mp4",
}

for idx, (sid, t0, t1, v, src, is_new) in enumerate(rows):
    want = t1 - t0
    src = REPLACE_SRC.get(sid, src)
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
    if os.path.exists(dst) and sid not in REPLACE_SRC:
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
    if sid in REPLACE_SRC:
        print("  [REBUILT %s] %.2fs v=%.2f <- %s" % (sid, want, v, os.path.basename(src)), flush=True)
    elif idx % 10 == 0:
        print("  [%d/%d] %s %.2fs v=%.2f" % (idx + 1, len(rows), sid, want, v), flush=True)

with open(listfile, "w", encoding="utf-8") as f:
    for p in seg_files:
        f.write("file '%s'\n" % p.replace("\\", "/"))

silent = os.path.join(WORK, "silent_v718.mp4")
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", listfile, "-c", "copy", silent], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("concat failed: " + r.stderr[:300])

song = None
for attr in ("SONG_WAV", "SONG"):
    song = song or getattr(v5, attr, None)
print("song=%s" % song, flush=True)

subs = os.path.join(BASE, "lyric_track.ass")
ass_esc = subs.replace("\\", "/").replace(":", "\\:")
fc = ("[0:v]ass='%s',overlay=x=0:y=0:enable='gte(t,%.1f)',"
      "tpad=stop_mode=clone:stop_duration=0.21[v]" % (ass_esc, CREDIT_FROM_S))
if a.no_subs:
    fc = ("[0:v]overlay=x=0:y=0:enable='gte(t,%.1f)',"
          "tpad=stop_mode=clone:stop_duration=0.21[v]" % CREDIT_FROM_S)
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", song, "-i", CREDIT_PNG,
                   "-filter_complex", fc, "-map", "[v]", "-map", "1:a",
                   "-c:v", "libx264", "-preset", "fast", "-crf", CRF, "-pix_fmt", "yuv420p",
                   "-r", str(FPS), "-c:a", "copy", "-frames:v", str(TARGET_FRAMES),
                   "-movflags", "+faststart", a.out], capture_output=True, text=True, errors="replace")
if r.returncode != 0:
    sys.exit("mux+subs+credit failed: " + r.stderr[:400])

probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                        "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", a.out],
                       capture_output=True, text=True)
n = int(probe.stdout.strip() or 0)
print("frames=%d (target %d)" % (n, TARGET_FRAMES), flush=True)
print("DONE %s" % a.out)
