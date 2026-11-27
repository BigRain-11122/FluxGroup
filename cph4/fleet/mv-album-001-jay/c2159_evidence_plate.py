# -*- coding: utf-8 -*-
# Build the R4 evidence plate: 2x2 (original vs picture-side mitigation).
import os

from PIL import Image, ImageDraw, ImageFont

BASE = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
SRC = os.path.join(BASE, "qc-r4-c2159", "srcframes")
OUT = os.path.join(BASE, "qc-r4-c2159", "outframes")
DST = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\evidence-c2159"
os.makedirs(DST, exist_ok=True)

frames = [("00037", "sky section 1.5s"), ("00170", "field section 7.1s")]
SC = 0.5
w, h = int(1344 * SC), int(768 * SC)
pad = 8
sheet = Image.new("RGB", (w * 2 + pad * 3, (h + 26) * 2 + pad * 3), (18, 18, 18))
dr = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", 18)
except Exception:
    font = None

for r, (fn, label) in enumerate(frames):
    for c, (src, tag) in enumerate(((SRC, "original"), (OUT, "mitigation"))):
        im = Image.open(os.path.join(src, fn + ".png")).convert("RGB").resize((w, h), Image.LANCZOS)
        x = pad + c * (w + pad)
        y = pad + r * (h + 26 + pad)
        sheet.paste(im, (x, y))
        if font:
            dr.text((x, y + h + 3), "%s / %s" % (tag, label), fill=(235, 235, 235), font=font)

p = os.path.join(DST, "R4-BEFORE-AFTER-c2159.jpg")
sheet.save(p, quality=88)
print("WROTE", p, os.path.getsize(p))