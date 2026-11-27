# -*- coding: utf-8 -*-
# audit_v54_final_r1017.py — V5.4.1 严格审核终验板（CEO 令「严格审核后给我终片」）
# 三专项：E04 提速罪窗复验（新窗 214.8-215.8·含 bloom 215.3·定格段 218.9+）
#        b33@172.50 D08 换源自愈复测（pre/post 对照）
#        D08 archived 新画面质感（168.5/169.5/171.0）
import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "full_mv_v54.mp4")
OUT = os.path.join(HERE, "v54_probe")

PTS = [
    ("E04_s0", 213.20), ("E04_a", 214.00), ("E04_b", 214.60), ("E04_c", 215.00),
    ("E04_bloom", 215.30), ("E04_d", 215.80), ("E04_e", 216.60), ("E04_freeze1", 218.90),
    ("E04_freeze2", 219.50),
    ("b33_pre", 172.36), ("b33_mid", 172.50), ("b33_post", 172.68),
    ("D08_a", 168.50), ("D08_b", 169.50), ("D08_c", 171.00),
]

def grab(t, path):
    subprocess.run(["ffmpeg", "-y", "-ss", "%.2f" % t, "-i", SRC, "-frames:v", "1",
                    "-q:v", "3", path], capture_output=True)
    return os.path.isfile(path)

# b33 quantitative retest (dLuma pre vs post, V53 baseline was 83->30 / dLuma 53.3)
from PIL import Image
import numpy as np
pre = np.asarray(Image.open(os.path.join(OUT, "v41_b33_pre.jpg")).convert("L").resize((160, 90))) if grab(172.36, os.path.join(OUT, "v41_b33_pre.jpg")) else None
post = np.asarray(Image.open(os.path.join(OUT, "v41_b33_post.jpg")).convert("L").resize((160, 90))) if grab(172.68, os.path.join(OUT, "v41_b33_post.jpg")) else None
if pre is not None and post is not None:
    dl = abs(post.mean() - pre.mean())
    print("B33-RETEST: pre=%.1f post=%.1f dLuma=%.1f  (V53 baseline dLuma=53.3 luma 83->30)" % (pre.mean(), post.mean(), dl))

from PIL import ImageDraw, ImageFont
per = 5
rows_n = (len(PTS) + per - 1) // per
cw, ch = 480, 274
im = Image.new("RGB", (per * (cw + 4), rows_n * (ch + 24) + 40), (12, 12, 14))
d = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
except Exception:
    fnt = ImageFont.load_default()
d.text((8, 6), "V5.4.1 FINAL AUDIT: E04 speed-fix window / b33 D08-swap retest / D08 archived texture", fill=(255, 220, 120), font=fnt)
for i, (tag, t) in enumerate(PTS):
    r_, c_ = divmod(i, per)
    y = 34 + r_ * (ch + 24)
    p = os.path.join(OUT, "v41_%s.jpg" % tag)
    if grab(t, p):
        d.text((c_ * (cw + 4) + 4, y + 2), "%s @%.2f" % (tag, t), fill=(200, 200, 210), font=fnt)
        im.paste(Image.open(p).convert("RGB").resize((cw, ch)), (c_ * (cw + 4), y + 20))
bp = os.path.join(OUT, "V541-FINAL-AUDIT.jpg")
im.save(bp, quality=88)
print("BOARD:", bp)
