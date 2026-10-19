# -*- coding: utf-8 -*-
"""C2120: locate board for r1017 sec-8 items 3/4/5 (three frames, quarter-scale grid w/ axes)."""
import os
from PIL import Image, ImageDraw

B = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
ITEMS = [
    ("A: S4-23 s20160 (handheld object)", os.path.join(B, "abatch", "S4-23_s20160.png")),
    ("B: S2-14 s20105 (left dark block)", os.path.join(B, "abatch", "S2-14_s20105.png")),
    ("C: S2-13 s21026 (two butterflies)", os.path.join(B, "t1r1", "S2-13_s21026.png")),
]
CW, CH = 672, 384
board = Image.new("RGB", (CW, CH * 3), (10, 10, 10))
dr = ImageDraw.Draw(board)
for i, (label, path) in enumerate(ITEMS):
    im = Image.open(path).convert("RGB").resize((CW, CH), Image.LANCZOS)
    y = i * CH
    board.paste(im, (0, y))
    dr.rectangle([4, y + 4, 4 + 8 * len(label) + 10, y + 26], fill=(0, 0, 0))
    dr.text((9, y + 8), label, fill=(255, 235, 160))
    # grid every 10% with tick labels along top edge of each cell
    for k in range(1, 10):
        x = int(CW * k / 10)
        dr.line([x, y, x, y + CH], fill=(255, 60, 60), width=1)
        dr.text((x + 2, y + 28), str(k * 10), fill=(255, 90, 90))
    for k in range(1, 10):
        yy = y + int(CH * k / 10)
        dr.line([0, yy, CW, yy], fill=(255, 60, 60), width=1)
out = os.path.join(B, "xq-S08-LOCATE-c2120.jpg")
board.save(out, quality=92)
print("WROTE", out, os.path.getsize(out), "B")