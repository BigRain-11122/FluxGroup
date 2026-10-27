# -*- coding: utf-8 -*-
# make_style_probe_board.py - 风格对比总板（3镜×4档·CEO 多看多评估用）
import os
from PIL import Image, ImageDraw

D = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\style-probe"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\STYLE-PROBE-BOARD.jpg"

SCENES = [("S1", "S1 fire-wake | S1 fire awakening engraved lines"),
          ("S3", "S3 stele | full view of the stele"),
          ("S8", "S8 case+her | glass cabinet + her reflection")]
GRADES = [("A_mono", "A amber monochrome torch deep black 5279 (current canon)"),
          ("B_tw2001", "B 2001 telecine milky floated blacks highlight bloom"),
          ("C_lowkey", "C minimal light source 80% pure black mist halo"),
          ("D_doc", "D archival documentary cool fluorescent + warm leak faded tones")]

CW, CH, PAD, LBL = 480, 274, 10, 22
COLS, ROWS = 4, 3
W = COLS * (CW + PAD) + PAD
H = ROWS * (CH + LBL + PAD) + PAD + 30
sheet = Image.new("RGB", (W, H), (12, 12, 12))
draw = ImageDraw.Draw(sheet)
draw.text((PAD + 2, 4), "STYLE PROBE - 3 shots x 4 grade frameworks - 672x384 quick (pick per COLUMN)", fill=(240, 200, 120))
for r, (sc, sc_label) in enumerate(SCENES):
    y0 = PAD + 30 + r * (CH + LBL + PAD)
    draw.text((PAD + 2, y0 - 20), sc_label, fill=(200, 200, 200))
    for c, (g, g_label) in enumerate(GRADES):
        fn = os.path.join(D, "%s_%s.png" % (sc, g))
        im = Image.open(fn).convert("RGB").resize((CW, CH), Image.LANCZOS)
        x = PAD + c * (CW + PAD)
        sheet.paste(im, (x, y0))
        draw.text((x + 2, y0 + CH + 4), g_label, fill=(220, 180, 90))
sheet.save(OUT, quality=88)
print("BOARD", OUT, sheet.size)
