# -*- coding: utf-8 -*-
# qc_clip_s2fix.py — P1 修件 clip_S2fix QC 板：9 帧运动轨迹（0.5s 步进）选 trim 窗 + 物理正锚核验面
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = sys.argv[1]
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\meme-daily-v1\outbound\v1-zunjie-brake\fixwork"
os.makedirs(OUT, exist_ok=True)
FF = "ffmpeg"

TS = [0.4, 0.9, 1.4, 1.9, 2.4, 2.9, 3.4, 3.9, 4.4]
frames = []
for t in TS:
    p = os.path.join(OUT, "s2fix_f%d.jpg" % int(t * 10))
    subprocess.run([FF, "-y", "-ss", str(t), "-i", SRC, "-frames:v", "1", "-q:v", "2", p], capture_output=True)
    if os.path.exists(p):
        frames.append((p, "t=%.1fs" % t))
        print("OK", t)

cw, ch = 240, 420
cols = 5
rows = (len(frames) + cols - 1) // cols
im = Image.new("RGB", (cols * cw, rows * (ch + 22) + 28), (16, 16, 18))
d = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
except Exception:
    fnt = ImageFont.load_default()
d.text((8, 5), "clip_S2fix motion sweep (5s H3) — pick C2a 1.2s trim window", fill=(255, 220, 120), font=fnt)
for i, (p, label) in enumerate(frames):
    r, c = divmod(i, cols)
    x, y = c * cw, 28 + r * (ch + 22)
    d.text((x + 4, y + 2), label, fill=(200, 200, 210), font=fnt)
    fr = Image.open(p).convert("RGB").resize((cw, ch))
    im.paste(fr, (x, y + 20))
out = os.path.join(OUT, "S2FIX-QC-BOARD.jpg")
im.save(out, quality=90)
print("BOARD:", out)
