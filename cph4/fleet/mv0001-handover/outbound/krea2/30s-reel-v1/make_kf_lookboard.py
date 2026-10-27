# -*- coding: utf-8 -*-
# 拼关键帧总板 (3列x4行·镜头序·ASCII标注防字体坑)
import os
from PIL import Image, ImageDraw

D = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\kf-v4"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\KF-V4-LOOKBOARD.jpg"
ORDER = [
    ("KF1_fire_wake", "S1 0-4.4s"),
    ("KF2_sweep", "S2 4.4-8.4s"),
    ("KF3_stele", "S3 8.4-11.9s"),
    ("KF4_crown", "S4 11.9-13.6s"),
    ("KF5_columns", "S5 13.6-17.2s"),
    ("KF6_chisel", "S6 17.2-19.4s"),
    ("KF7_hall", "S7 19.4-21.7s"),
    ("KFT_glyphs", "T 21.7-22.7s"),
    ("KF8_case", "S8 22.7-24.7s"),
    ("KF9_profile", "S9 24.7-28.1s"),
    ("KF10_walkaway", "S10 28.1-30.0s"),
]
CW, CH, PAD, LBL = 440, 251, 8, 22
COLS = 3
ROWS = (len(ORDER) + COLS - 1) // COLS
W = COLS * (CW + PAD) + PAD
H = ROWS * (CH + LBL + PAD) + PAD
sheet = Image.new("RGB", (W, H), (12, 12, 12))
draw = ImageDraw.Draw(sheet)
for i, (name, slot) in enumerate(ORDER):
    r, c = divmod(i, COLS)
    im = Image.open(os.path.join(D, name + ".png")).convert("RGB").resize((CW, CH), Image.LANCZOS)
    x = PAD + c * (CW + PAD)
    y = PAD + r * (CH + LBL + PAD)
    sheet.paste(im, (x, y))
    draw.text((x + 2, y + CH + 4), "%s  %s  %s" % (name, slot, "lyric:" + (
        ["intro","intro","intro","vocal-in","law text","carve","3700yrs","bridge","at the case","his gaze","walk away"][i])),
        fill=(220, 180, 90))
sheet.save(OUT, quality=88)
print("SHEET", OUT, sheet.size)
