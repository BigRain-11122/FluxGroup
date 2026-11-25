# -*- coding: utf-8 -*-
"""C2120d: 1:1 butterfly crop board (eye adjudication) - replaces the failed mask-fit board."""
import os
import numpy as np
from PIL import Image, ImageDraw

B = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
p = os.path.join(B, "t1r1", "S2-13_s21026.png")
a = np.asarray(Image.open(p).convert("RGB"))
H, W = a.shape[:2]
BOXES = [("upper-right butterfly 1:1 x3", int(.60 * W), int(.13 * H), 62),
         ("lower-left butterfly 1:1 x3", int(.38 * W), int(.40 * H), 62)]
tiles = []
for lab, cx, cy, half in BOXES:
    x0, x1 = max(0, cx - half), min(W, cx + half)
    y0, y1 = max(0, cy - half), min(H, cy + half)
    im = Image.fromarray(a[y0:y1, x0:x1]).resize(((x1 - x0) * 3, (y1 - y0) * 3), Image.NEAREST)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 8 * len(lab) + 8, 16], fill=(0, 0, 0))
    d.text((4, 3), lab, fill=(255, 230, 150))
    tiles.append(im)
w = max(t.width for t in tiles); h = max(t.height for t in tiles)
bd = Image.new("RGB", (w * 2, h), (8, 8, 8))
for i, t in enumerate(tiles):
    bd.paste(t, (i * w, 0))
out = os.path.join(B, "xq-S08-S213-BUTTERFLY-1TO1-c2120.jpg")
bd.save(out, quality=93)
stale = os.path.join(B, "xq-S08-S213-MASKFIT-c2120.jpg")
if os.path.exists(stale):
    os.remove(stale)
    print("REMOVED stale mask-fit board (invalid mask, misleading)")
print("WROTE", out, os.path.getsize(out), "B")