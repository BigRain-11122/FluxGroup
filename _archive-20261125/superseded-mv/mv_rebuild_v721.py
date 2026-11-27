# -*- coding: utf-8 -*-
"""mv_rebuild_v721.py - v721: v720 (even-cadence rows + R01 deflicker + E03 fix) +
R03_goddess_dim 12fps-source decimation fix.

R03's source take is 12fps motion doubled into a 24fps wrapper (strict period-2
diff pattern measured across all 124 frames: dup+grain 0.2-1.5 / motion 5-9).
Fix: decimate to true 12fps (select even frames), then minterpolate from 12fps
to 48/v -> setpts -> 24fps = smooth even steps. No human face in this shot
(goddess statue + fire), so mci morph risk is low.

Usage: py mv_rebuild_v721.py <out.mp4> [--dry]
"""
import argparse
import importlib.util
import os
import subprocess
import sys

BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
WORK = r"D:\FleetWorker\rebuild_grade3_v720"
W, H, FPS = 1344, 768, 24
TARGET_FRAMES = 5623
CRF = "10"

REPLACE_SRC = {
    "INT1_desk_breath": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v718-clips-768\V718_S1_OPEN.mp4",
    "INT3_photo_stare": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v718-clips-768\V718_S2_PHOTO.mp4",
    "E01c_first_line": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v718-clips-768\V718_S3_DESK_REPRISE.mp4",
    "R05_gold_threads": r"D:\FleetWorker\rebuild\R05_gold_threads_lift.mp4",
    "E03_gaze_meet": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v719-clips-768\V719_E03_gaze_meet.mp4",
}
CREDIT_PNG = os.path.join(BASE, "tail_credit_v510.png")
CREDIT_FROM_S = 231.0

R01_SPLIT_FRAME = 98
DECIMATE_ROWS = {"R03_goddess_dim"}  # 12fps-doubled sources: drop dups first

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--no-subs", action="store_true")
ap.add_argument("--dry", action="store_true")
ap.add_argument("--grade", action="store_true")
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
if a.dry:
    for sid, t0, t1, v, src, is_new in rows:
        print("  %8.3f %8.3f %-24s v=%.2f %s" % (t0, t1, sid, v, src), flush=True)
    sys.exit(0)

os.makedirs(WORK, exist_ok=True)
listfile = os.path.join(WORK, "segments_v721.txt")
seg_files = []

SRC_OVERRIDE = {
    "SIL4": r"D:\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\v51_SIL4_at_207.mp4",
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


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
    if os.path.exists(dst) and sid not in REPLACE_SRC and sid not in ("R01_war_later",) and sid not in DECIMATE_ROWS:
        pd = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=nw=1:nk=1", dst])
        try:
            if abs(float(pd.stdout.strip()) - want) < 0.06:
                seg_files.append(dst)
                continue
        except Exception:
            pass

    base_vf = ("scale=%d:%d:force_original_aspect_ratio=decrease,"
               "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=%d" % (W, H, W, H, FPS))
    if a.grade:
        base_vf = grade_chain(era_of(sid)) + base_vf
    pre = "select='not(mod(n\\,2))'," if sid in DECIMATE_ROWS else ""
    if abs(v - 1.0) > 0.005:
        vf = pre + "minterpolate=fps=%.6f:mi_mode=mci,setpts=PTS/%.4f," % (48.0 / v, v) + base_vf
    else:
        vf = pre + "setpts=PTS/%.4f," % v + base_vf
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-vf", vf,
           "-t", "%.4f" % want, "-c:v", "libx264", "-preset", "fast", "-crf", CRF,
           "-pix_fmt", "yuv420p", "-r", str(FPS), dst]
    r = run(cmd)
    if r.returncode != 0:
        print("FAIL %s :: %s" % (sid, r.stderr[:200]), flush=True)
        sys.exit(3)
    if sid in DECIMATE_ROWS:
        print("  [DECIMATE+REINTERP %s] v=%.2f" % (sid, v), flush=True)

    if sid == "R01_war_later":
        pa = dst.replace(".mp4", "_A.mp4")
        pb = dst.replace(".mp4", "_B.mp4")
        r = run(["ffmpeg", "-v", "error", "-y", "-i", dst, "-frames:v", str(R01_SPLIT_FRAME),
                 "-vf", "deflicker=size=5:mode=am", "-an", "-c:v", "libx264", "-preset", "fast",
                 "-crf", CRF, "-pix_fmt", "yuv420p", "-r", str(FPS), pa])
        if r.returncode != 0:
            print("FAIL R01 A :: %s" % r.stderr[:200], flush=True)
            sys.exit(3)
        r = run(["ffmpeg", "-v", "error", "-y", "-ss", "%.6f" % (R01_SPLIT_FRAME / float(FPS)),
                 "-i", dst, "-an", "-c:v", "libx264", "-preset", "fast", "-crf", CRF,
                 "-pix_fmt", "yuv420p", "-r", str(FPS), pb])
        if r.returncode != 0:
            print("FAIL R01 B :: %s" % r.stderr[:200], flush=True)
            sys.exit(3)
        lst = dst.replace(".mp4", "_list.txt")
        with open(lst, "w", encoding="utf-8") as f:
            f.write("file '%s'\nfile '%s'\n" % (pa.replace("\\", "/"), pb.replace("\\", "/")))
        r = run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                 "-c", "copy", dst])
        if r.returncode != 0:
            print("FAIL R01 splice :: %s" % r.stderr[:200], flush=True)
            sys.exit(3)
        print("  [R01 deflicker split A/B spliced at frame %d]" % R01_SPLIT_FRAME, flush=True)

    seg_files.append(dst)
    if sid in REPLACE_SRC:
        print("  [REBUILT %s] %.2fs v=%.2f <- %s" % (sid, want, v, os.path.basename(src)), flush=True)

with open(listfile, "w", encoding="utf-8") as f:
    for p in seg_files:
        f.write("file '%s'\n" % p.replace("\\", "/"))

silent = os.path.join(WORK, "silent_v721.mp4")
r = run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", listfile, "-c", "copy", silent])
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
r = run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", song, "-i", CREDIT_PNG,
         "-filter_complex", fc, "-map", "[v]", "-map", "1:a",
         "-c:v", "libx264", "-preset", "fast", "-crf", CRF, "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "copy", "-frames:v", str(TARGET_FRAMES),
         "-movflags", "+faststart", a.out])
if r.returncode != 0:
    sys.exit("mux+subs+credit failed: " + r.stderr[:400])

probe = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
             "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", a.out])
n = int(probe.stdout.strip() or 0)
print("frames=%d (target %d)" % (n, TARGET_FRAMES), flush=True)
if n != TARGET_FRAMES:
    sys.exit("FRAME ASSERTION FAILED")
print("DONE %s" % a.out)
