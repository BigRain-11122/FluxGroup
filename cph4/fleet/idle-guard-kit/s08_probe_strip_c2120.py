# -*- coding: utf-8 -*-
"""C2120: build a compact contact strip for r1017 sec-8 items 2-5 inspection."""
import os
from PIL import Image, ImageDraw

B = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
ITEMS = [
    ("S0-04 s20033 s7rB", os.path.join(B, "abatch_s7r", "S0-04_s20033_s7rB.jpg")),
    ("S0-04 s20039 s7rB", os.path.join(B, "abatch_s7r", "S0-04_s20039_s7rB.jpg")),
    ("S0-05 s20043 s7rB", os.path.join(B, "abatch_s7r", "S0-05_s20043_s7rB.jpg")),
    ("S0-05 s20044 s7rB", os.path.join(B, "abatch_s7r", "S0-05_s20044_s7rB.jpg")),
]
CW, CH = 672, 384
board = Image.new("RGB", (CW * 2, CH * 2), (12, 12, 12))
dr = ImageDraw.Draw(board)
for i, (label, path) in enumerate(ITEMS):
    im = Image.open(path).convert("RGB").resize((CW, CH), Image.LANCZOS)
    x, y = (i % 2) * CW, (i // 2) * CH
    board.paste(im, (x, y))
    dr.rectangle([x + 4, y + 4, x + 4 + 8 * len(label) + 10, y + 26], fill=(0, 0, 0))
    dr.text((x + 9, y + 8), label, fill=(255, 235, 160))
out = os.path.join(B, "xq-S08-STRIP-c2120.jpg")
board.save(out, quality=90)
print("WROTE", out, os.path.getsize(out), "B")