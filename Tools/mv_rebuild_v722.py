# -*- coding: utf-8 -*-
"""mv_rebuild_v722.py - v722 base builder.
v721: v720 (even-cadence rows + R01 deflicker + E03 fix) + R03 12fps-source
decimation fix. v722: era/grade split fixed (modern blue-grey vs ancient amber).
v723 (2026-11-06): restore the 13 director-signed v5redo takes that the v7-line
rebuilders silently swapped for legacy/jayredo takes by resolving sources by
row-table NAME instead of V5_SOURCE_MAP. Edit-layer fix only, no re-burns.

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
import re
import subprocess
import sys

BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
WORK = r"D:\FleetWorker\rebuild_grade8_v722e"
W, H, FPS = 1344, 768, 24
TARGET_FRAMES = 5623
CRF = "10"

REPLACE_SRC = {
    # 2026-11-09 v724: performance-wave officials (8-dim acting, blind-validated
    # 3/3, CEO cloud order). These take highest priority over v718/v719 re-burns
    # and the v5 restores for their slots.
    "INT1_desk_breath": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\INT1_B_cloud768.mp4",  # cloud MiniMax H3 take
    "INT3_photo_stare": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\INT3_B_s20261609_768.mp4",
    "C01_carver_face": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\C01_B_s20261610_768.mp4",
    "D01_carver_words": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\D01_B_s20261611_768.mp4",
    "R06_museum_verse": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\R06_B_s20261612_768.mp4",
    "E03_gaze_meet": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\E03_B_s20261613_768.mp4",
    "INT5_head_bow": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\INT5_B_s20261614_768.mp4",
    "E04_replay_faces": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\E04_B_s20261615_768.mp4",
    "B01_weary": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns\B01_B_s20261119_768.mp4",
    "E01c_first_line": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v718-clips-768\V718_S3_DESK_REPRISE.mp4",
    "R05_gold_threads": r"D:\FleetWorker\rebuild\R05_gold_threads_lift.mp4",
}

# 2026-11-06 V723 source restoration (CEO 2026-11-06 order: fix transitions/fusion/
# narrative by re-cutting BURNED material, no re-burns, no overturn).
# Root cause: the v7-line rebuilders call build_rows_v5() directly and resolve
# sources by the v3 row-table NAME, skipping V5_SOURCE_MAP. Every v5redo file is
# named *_v5.mp4, so find_src_v5() misses the V5REDO dir and falls back to the
# v2 search order (JAYREDO first). Result: 13 director-signed v5redo takes were
# silently replaced by legacy/jayredo takes -- the root of the known-defect list
# (INT4 giant-hand hallucination, per-lead mixed faces, D01 latin-letter wall,
# D04 bamboo-slip form error, C04 glyph-disc, B01 posture). Fix: point the 13
# slots back at their burned, QC-passed v5redo takes in the library.
V5RESTORE_DIR = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo"
V5_RESTORE = {
    "INT2_paper_fight": "INT2_paper_v5.mp4",
    "INT4_rubbing_glow": "INT4_rubbing_v5.mp4",
    "INT5_head_bow": "INT5_head_bow_v5.mp4",
    "C01_carver_face": "C01_carver_face_v5.mp4",
    "C04_words_alive": "C04_words_alive_v5.mp4",
    "R06_museum_verse": "R06_museum_verse_v5.mp4",
    "D01_carver_words": "D01_carver_words_v5.mp4",
    "D03b_direct_gaze": "D03b_direct_gaze_v5.mp4",
    "D04_her_brush": "D04_her_brush_v5.mp4",
    "D05_words_warm": "D05_words_warm_v5.mp4",
    "B01_weary": "B01_weary_v5.mp4",
    "SIL4": "SIL4_crowd_edge_v5.mp4",
    "E04_replay_faces": "E04_replay_faces_v5.mp4",
    # 2026-11-06 addendum: E04a is the D05 reprise row but still pointed at the
    # legacy D05 take, which carries a real ~0.4s dead hold at 203.4s (measured
    # 1.34%->0.27% frame-diff, persistent across v722g/v723). The v5 take has
    # the verified slow push (r955) and restores the D05<->E04a reprise pair
    # to identical content, as the whitelist design intends.
    "E04a_words_warm": "D05_words_warm_v5.mp4",
}
for _sid, _f in V5_RESTORE.items():
    _p = os.path.join(V5RESTORE_DIR, _f)
    if not os.path.isfile(_p):
        print("V5 RESTORE SRC MISSING %s :: %s" % (_sid, _p), flush=True)
        sys.exit(2)

# 2026-11-06 V723 addendum: two CEO-complained slots whose signed replacements
# also got reverted by the same name-resolution regression.
#  SING3b_v4@197-199: CEO order "后段边写歌边唱镜逻辑问题可换" -> V5.6 replaced it
#    with a torch-tail reprise; the v7 line silently reverted to the convicted
#    desk-writing take. v56src/ was deleted, so the reprise is re-derived from
#    SING1_torch_song_v2_s9013.mp4 t=2.88-4.88 punch-in 1.12x slight darken
#    (media/MV/mv0001/v723-clips/V56_SING1_reprise_v723.mp4, edit-layer only).
#  D08_world_flip@167.2-172.5: CEO order "乱入动画镜头" -> V5.4 swapped in the
#    cloudv2 live-action take; name resolution cannot see _w2_archived, so the
#    film fell back to the convicted CG-texture/gallery take (= the frozen-doc
#    "2D 格" defect). Restore the signed live-action take.
V56_RESTORE = {
    "SING3b_v4": r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\V56_SING1_reprise_v723.mp4",
    "D08_world_flip": r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\cloudv2\_w2_archived\D08_world_flip.mp4",
}
for _sid, _p in V56_RESTORE.items():
    if not os.path.isfile(_p):
        print("V56 RESTORE SRC MISSING %s :: %s" % (_sid, _p), flush=True)
        sys.exit(2)
# 2026-11-06 A-组转场光桥（导演席裁决·两处，余下切点全数「保持」）：
#  R06→R07 @138.54 断崖 59.6 单位（全片最大）——"方向对、手法糙"：R07 段头
#    0.3s 火起渐显（焰从暗升到正常，眼睛随焰适应），不挪切点；
#  Z03_lights_out 熄灯拍点错位——拍「动作之后」：段尾 0.8s 渐黑=灯灭之后的馆，
#    直落 Z04 黑底字卡。两处皆段内物质光变化，非风格化闪白。
SEG_EXTRA_VF = {
    "R07_flame": ("fade=t=in:st=0:d=0.3,", "A3 光桥·火起渐显"),
    "Z03_lights_out": ("fade=t=out:st=2.2:d=0.8,", "A1 熄灯渐黑"),
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

# 2026-11-05 V7.22: era split fixed - see DIRECTOR-REVIEW-V721-REVISE-20261105.md.
# v721 keyed the era off the first letter, so D* (modern reading / brush) and
# R06_museum_verse were graded as ancient, and the "modern" chain was a no-op
# (eq=saturation=1.0). The v721 master measured R-B +20..+44 at ten sample points:
# no cool segment existed at all, while the 10-19 order asks modern blue-grey / ancient amber.
MODERN_IDS = {"R06_museum_verse"}
# D08_world_flip is the shot where the two worlds cross: warm by design, not a
# "modern" shot that should be cooled.
TRANSITION_IDS = {"D08_world_flip"}
# sources whose saturation still lands above the ancient baseline after the standard
# desat (measured on v722b: 186-213 vs ancient median 195)
DESAT_IDS = {"D01_carver_words", "D04_her_brush", "D05_words_warm", "Z01_words_alone",
             "Z03_lights_out", "Z04_glyph_remains", "E04a_words_warm",
             "D05_words_warm", "S7_hall", "S10_walk"}
MODERN_PREFIX = ("S7_", "S8_", "S9_", "S10_", "D", "E03", "E04a", "Z")
# 2026-11-05: desk-at-night interiors (INT*) must not be pushed cool - the light
# source is a tungsten desk lamp. Calibrated on one segment: pushing them to R-B -1
# reads as an implausible blue-grey desk. Night keeps its colour, loses saturation.
NIGHT_PREFIX = ("INT",)
ANCIENT_PREFIX = ("S", "N", "C", "R", "B", "T_", "KF", "SIL", "E0", "E1")


def era_of(sid):
    if sid in TRANSITION_IDS:
        return "transition"
    if sid.startswith(NIGHT_PREFIX):
        return "modern_night"
    if sid in MODERN_IDS or sid.startswith(MODERN_PREFIX):
        return "modern"
    return "ancient" if sid.startswith(ANCIENT_PREFIX) else "modern"


def grade_chain(era):
    if era == "ancient":
        return ("eq=saturation=0.86:contrast=1.04,"
                "colorbalance=rs=-0.02:gs=-0.01:bs=0.035,"
                "noise=alls=6:allf=t+u,")
    # modern = blue-grey, desaturated (CEO 2026-10-19 spec: modern cool / ancient amber)
    if era == "transition":
        # world-crossing shot: keep the ancient amber, it is the hinge
        return ("eq=saturation=0.86:contrast=1.04,"
                "colorbalance=rs=-0.02:gs=-0.01:bs=0.035,")
    if era == "modern_night":
        # keep the tungsten colour, only pull saturation down
        return "eq=saturation=0.80:contrast=1.03:brightness=0.01,"
    # museum / modern-day reading: blue-grey, desaturated (CEO 2026-10-19 spec).
    # strength from the 2026-11-05 single-segment calibration (rs/bs 0.22 -> R-B +2.0).
    return ("colorbalance=rs=-0.22:gs=-0.04:bs=0.22:rm=-0.13:bm=0.13:rh=-0.15:bh=0.15,"
            "eq=saturation=0.58:contrast=1.03:brightness=0.01,")


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
        print("  %8.3f %8.3f %-24s v=%.2f %-7s %s" % (t0, t1, sid, v, era_of(sid), src), flush=True)
    sys.exit(0)

os.makedirs(WORK, exist_ok=True)
listfile = os.path.join(WORK, "segments_v723.txt")
seg_files = []

n_v5restore = 0

SRC_OVERRIDE = {
    "SIL4": r"D:\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\v51_SIL4_at_207.mp4",
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


for idx, (sid, t0, t1, v, src, is_new) in enumerate(rows):
    want = t1 - t0
    base_sid = sid.split("@")[0]
    if sid not in REPLACE_SRC and base_sid in V5_RESTORE:
        src = os.path.join(V5RESTORE_DIR, V5_RESTORE[base_sid])
        n_v5restore += 1
    elif sid not in REPLACE_SRC and base_sid in V56_RESTORE:
        src = V56_RESTORE[base_sid]
        n_v5restore += 1
    else:
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
    if (os.path.exists(dst) and base_sid not in V5_RESTORE and base_sid not in V56_RESTORE
            and base_sid not in SEG_EXTRA_VF
            and sid not in REPLACE_SRC and sid not in ("R01_war_later",) and sid not in DECIMATE_ROWS):
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
        gchain = grade_chain(era_of(sid))
        if sid in DESAT_IDS and "saturation=" in gchain:
            gchain = re.sub(r"saturation=[0-9.]+", "saturation=0.30", gchain)
        if base_sid in SEG_EXTRA_VF:
            gchain = gchain + SEG_EXTRA_VF[base_sid][0]
        base_vf = gchain + base_vf
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
    if sid in REPLACE_SRC or base_sid in V5_RESTORE or base_sid in V56_RESTORE:
        _tag = ("  [V5-RESTORE]" if base_sid in V5_RESTORE
                else ("  [V56-RESTORE]" if base_sid in V56_RESTORE else ""))
        print("  [REBUILT %s] %.2fs v=%.2f <- %s%s"
              % (sid, want, v, os.path.basename(src), _tag), flush=True)

if n_v5restore != len(V5_RESTORE) + len(V56_RESTORE):
    print("FATAL restore count %d != %d" % (n_v5restore, len(V5_RESTORE) + len(V56_RESTORE)), flush=True)
    sys.exit(2)

with open(listfile, "w", encoding="utf-8") as f:
    for p in seg_files:
        f.write("file '%s'\n" % p.replace("\\", "/"))

silent = os.path.join(WORK, "silent_v723.mp4")
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
