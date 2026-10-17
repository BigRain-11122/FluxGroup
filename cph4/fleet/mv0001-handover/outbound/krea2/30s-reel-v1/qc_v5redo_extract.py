# -*- coding: utf-8 -*-
# qc_v5redo_extract.py — 17 件 v5redo i2v 收件 QC 拼板提取器
# 产出：3 张主拼板（17 镜×3 帧·帧级六检用）+ 4 张专项板
#   anchor 板（E03/R06/E04 女主锚跨镜比对·CHK-E2）/ INT4 重影板 / B01 凿槌道具板 / INT2 歌名卡选位参照板
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

V5 = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\qc-v5redo-17"
FF = "ffmpeg"
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)

CLIPS = [
    "INT1_desk_breath_v5.mp4", "INT2_paper_v5.mp4", "INT3_photo_stare_v5.mp4",
    "INT4_rubbing_v5.mp4", "INT5_head_bow_v5.mp4", "C01_carver_face_v5.mp4",
    "D01_carver_words_v5.mp4", "D03b_direct_gaze_v5.mp4", "B01_weary_v5.mp4",
    "E01c_first_line_v5.mp4", "E03_gaze_meet_v5.mp4", "R06_museum_verse_v5.mp4",
    "E04_replay_faces_v5.mp4", "C04_words_alive_v5.mp4", "D05_words_warm_v5.mp4",
    "SIL1_babylon_v5.mp4", "SIL4_crowd_edge_v5.mp4",
]

CW, CH, LBL = 640, 360, 26

def grab(clip, t, tag):
    name = "%s_%s.jpg" % (clip.replace("_v5.mp4", ""), tag)
    p = os.path.join(OUT, "frames", name)
    subprocess.run([FF, "-y", "-ss", str(t), "-i", os.path.join(V5, clip),
                    "-frames:v", "1", "-vf", "scale=%d:%d" % (CW, CH),
                    "-q:v", "2", p], capture_output=True)
    return p if os.path.exists(p) else None

def board(fname, rows, cols, cells, header):
    """cells: list of rows; each row = list of (img_path, label)"""
    W, H = cols * CW, len(rows) * (CH + LBL) + 34
    im = Image.new("RGB", (W, H), (16, 16, 18))
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
    except Exception:
        fnt = ImageFont.load_default()
    d.text((10, 6), header, fill=(255, 220, 120), font=fnt)
    y = 34
    for row in rows:
        for c, (path, label) in enumerate(row):
            x = c * CW
            d.rectangle([x, y, x + CW, y + LBL], fill=(40, 40, 46))
            d.text((x + 6, y + 4), label, fill=(200, 200, 210), font=fnt)
            if path and os.path.exists(path):
                fr = Image.open(path).convert("RGB").resize((CW, CH))
                im.paste(fr, (x, y + LBL))
        y += CH + LBL
    im.save(os.path.join(OUT, fname), quality=90)
    print("BOARD:", fname)

# ---- 主拼板：17 镜 × 3 帧（0.5 / 2.6 / 4.7s）----
MAIN_TS = [(0.5, "f1"), (2.6, "f2"), (4.7, "f3")]
for clip in CLIPS:
    for t, tag in MAIN_TS:
        grab(clip, t, tag)

for bi in range(3):
    chunk = CLIPS[bi * 6:(bi + 1) * 6]
    rows = []
    for clip in chunk:
        base = clip.replace("_v5.mp4", "")
        rows.append([(os.path.join(OUT, "frames", "%s_%s.jpg" % (base, tag)),
                      "%s  t=%ss" % (base, t)) for t, tag in MAIN_TS])
    board("V5REDO-QC-BOARD-%d.jpg" % (bi + 1), rows, 3, None,
          "v5redo 17-shot QC board %d/3 (frames 0.5/2.6/4.7s)" % (bi + 1))

# ---- 女主锚比对板：E03 / R06 / E04 × 5 帧（CHK-E2 跨镜一致性）----
ANCHOR = ["E03_gaze_meet_v5.mp4", "R06_museum_verse_v5.mp4", "E04_replay_faces_v5.mp4"]
A_TS = [(0.3, "a1"), (1.3, "a2"), (2.6, "a3"), (3.8, "a4"), (4.9, "a5")]
rows = []
for clip in ANCHOR:
    base = clip.replace("_v5.mp4", "")
    for t, tag in A_TS:
        grab(clip, t, tag)
    rows.append([(os.path.join(OUT, "frames", "%s_%s.jpg" % (base, tag)),
                  "%s t=%s" % (base, t)) for t, tag in A_TS])
board("V5REDO-ANCHOR-E03R06E04.jpg", rows, 5, None,
      "female-lead anchor board: E03/R06/E04 cross-shot (ID_F_2001)")

# ---- INT4 重影复核板：6 帧 ----
for t, tag in [(0.2, "g1"), (1.0, "g2"), (2.0, "g3"), (3.0, "g4"), (4.0, "g5"), (4.9, "g6")]:
    grab("INT4_rubbing_v5.mp4", t, tag)
rows = [[(os.path.join(OUT, "frames", "INT4_rubbing_%s.jpg" % tag), "INT4 t=%s" % t)
         for t, tag in [(0.2, "g1"), (1.0, "g2"), (2.0, "g3")]],
        [(os.path.join(OUT, "frames", "INT4_rubbing_%s.jpg" % tag), "INT4 t=%s" % t)
         for t, tag in [(3.0, "g4"), (4.0, "g5"), (4.9, "g6")]]]
board("V5REDO-INT4-GHOSTCHECK.jpg", rows, 3, None, "INT4 ghost/double-outline 100% check")

# ---- B01 凿槌道具复核板：6 帧 ----
for t, tag in [(0.2, "p1"), (1.0, "p2"), (2.0, "p3"), (3.0, "p4"), (4.0, "p5"), (4.9, "p6")]:
    grab("B01_weary_v5.mp4", t, tag)
rows = [[(os.path.join(OUT, "frames", "B01_weary_%s.jpg" % tag), "B01 t=%s" % t)
         for t, tag in [(0.2, "p1"), (1.0, "p2"), (2.0, "p3")]],
        [(os.path.join(OUT, "frames", "B01_weary_%s.jpg" % tag), "B01 t=%s" % t)
         for t, tag in [(3.0, "p4"), (4.0, "p5"), (4.9, "p6")]]]
board("V5REDO-B01-PROPCHECK.jpg", rows, 3, None, "B01 mallet/chisel prop logic check")

# ---- INT2 歌名卡选位参照板：5 帧 ----
for t, tag in [(0.5, "t1"), (2.0, "t2"), (3.3, "t3"), (4.0, "t4"), (4.9, "t5")]:
    grab("INT2_paper_v5.mp4", t, tag)
rows = [[(os.path.join(OUT, "frames", "INT2_paper_%s.jpg" % tag), "INT2 t=%s" % t)
         for t, tag in [(0.5, "t1"), (2.0, "t2"), (3.3, "t3")]],
        [(os.path.join(OUT, "frames", "INT2_paper_%s.jpg" % tag), "INT2 t=%s" % t)
         for t, tag in [(4.0, "t4"), (4.9, "t5")]]]
board("V5REDO-INT2-TITLEPOS-REF.jpg", rows, 3, None, "INT2 title-card placement reference")

print("DONE all boards ->", OUT)
