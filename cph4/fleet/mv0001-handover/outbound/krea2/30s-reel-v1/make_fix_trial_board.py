# -*- coding: utf-8 -*-
# make_fix_trial_board.py - 修正试验对比板（旧病帧 vs 修正帧·CEO 验看）
import os
from PIL import Image, ImageDraw

TRIAL = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\fix-trial"
OLD = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\style-probe"
KF = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\kf-v4"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\FIX-TRIAL-BOARD.jpg"

PAIRS = [
    ("torch S1", os.path.join(OLD, "S1_A_mono.png"), os.path.join(TRIAL, "S1_fire_bundle.png"),
     "OLD: thin matchstick flame | NEW: thick reed-bundle torch, broad flame"),
    ("torch S3", os.path.join(OLD, "S3_A_mono.png"), os.path.join(TRIAL, "S3_stele_bundle.png"),
     "OLD: wall torch dots | NEW: iron sconces with wide breathing flames"),
    ("her S9", os.path.join(TRIAL, "S9_her_tw01.png"), os.path.join(TRIAL, "S9_her_tw01.png"),
     "NEW: 2001 Taiwanese girl - full cheeks / large dark eyes / blunt fringe"),
    ("her S8", os.path.join(OLD, "S8_A_mono.png"), os.path.join(TRIAL, "S8_her_tw01.png"),
     "OLD: foreign profile | NEW: 2001 Taiwanese girl silhouette reflection"),
]

CW, CH, PAD, LBL = 600, 343, 10, 24
COLS = 2
W = COLS * (CW + PAD) + PAD
H = len(PAIRS) * (CH + LBL + PAD) + PAD + 26
sheet = Image.new("RGB", (W, H), (12, 12, 12))
draw = ImageDraw.Draw(sheet)
draw.text((PAD + 2, 4), "FIX TRIAL - left=old problem | right=fixed (low-res quick verification)", fill=(240, 200, 120))
for r, (label, oldf, newf, note) in enumerate(PAIRS):
    y = PAD + 26 + r * (CH + LBL + PAD)
    for c, f in enumerate((oldf, newf)):
        if f and os.path.isfile(f):
            im = Image.open(f).convert("RGB").resize((CW, CH), Image.LANCZOS)
            x = PAD + c * (CW + PAD)
            sheet.paste(im, (x, y))
    draw.text((PAD + 2, y - 18), label + "  --  " + note, fill=(220, 180, 90))
sheet.save(OUT, quality=88)
print("BOARD", OUT, sheet.size)
