# -*- coding: utf-8 -*-
"""pool_contact.py — 把镜头池 40 个镜头各抽 1 帧，拼成带标签的对照板。"""
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = r"K:\Fluxgroup\FluxGroup"
POOL = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "pool", "SHOT-POOL.json")
TMP = r"K:\Fluxgroup\.codely-cli\tmp\poolfr"
OUT = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "pool", "POOL-CONTACT.jpg")
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FONT = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

os.makedirs(TMP, exist_ok=True)
shots = json.load(open(POOL, encoding="utf-8"))["shots"]
shots.sort(key=lambda s: s["id"])

TW, TH = 300, 172
COLS = 6
rows = (len(shots) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * (TW + 8) + 8, rows * (TH + 30) + 8), (18, 18, 18))
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype(FONT, 20)

for i, s in enumerate(shots):
    src = os.path.join(ROOT, "media", "MV", "mv0001", s["path"])
    mid = os.path.join(TMP, s["id"].replace(os.sep, "_") + ".jpg")
    t = min(1.0, s["dur"] * 0.5)
    subprocess.run([FF, "-y", "-ss", "%.2f" % t, "-i", src, "-frames:v", "1",
                    "-update", "1", "-q:v", "3", mid], capture_output=True)
    if not os.path.exists(mid):
        continue
    im = Image.open(mid).convert("RGB").resize((TW, TH))
    x = 8 + (i % COLS) * (TW + 8)
    y = 8 + (i // COLS) * (TH + 30)
    sheet.paste(im, (x, y))
    d.text((x + 4, y + TH + 2), "%s  %.1fs %s" % (s["id"], s["dur"], "768" if s["w"] >= 1200 else "480"),
           font=font, fill=(235, 220, 190))

sheet.save(OUT, "JPEG", quality=88)
print("CONTACT", OUT, sheet.size)
