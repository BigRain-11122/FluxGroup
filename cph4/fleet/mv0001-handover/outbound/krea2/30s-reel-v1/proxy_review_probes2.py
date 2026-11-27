# -*- coding: utf-8 -*-
# proxy_review_probes2.py — V5 PROXY 补充探针：D03b 真尾段（蓝焰带入终判）+ C01 微动帧差量化
# 背景：首轮探针 152.00 已落到下一镜（实际切点早于 spec 窗尾），真尾段未采样；
#       C01 防塑料感需帧差实证（单帧不可证运动，E04 帧差曲线法同构）。
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROXY = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\full_mv_v5_proxy.mp4"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\qc-v5redo-17\proxy_probes"
FF = "ffmpeg"

# D03b 可见区约 150.54-152.00（0.25s 步进 + 最后一帧贴切点）
D03B = [(151.30, "d03b_t1"), (151.55, "d03b_t2"), (151.80, "d03b_t3"), (151.99, "d03b_t4")]
# C01 可见区 77.34-78.00（0.25s 步进 + 贴尾帧；另算 77.40->77.98 宽对）
C01 = [(77.40, "c01_m1"), (77.65, "c01_m2"), (77.90, "c01_m3"), (77.98, "c01_m4")]

def grab(t, tag):
    p = os.path.join(OUT, "probe2_%s.jpg" % tag)
    subprocess.run([FF, "-y", "-ss", str(t), "-i", PROXY, "-frames:v", "1", "-q:v", "2", p], capture_output=True)
    return p

def madiff(a, b):
    ia, ib = Image.open(a).convert("L"), Image.open(b).convert("L")
    h = ImageChops.difference(ia, ib).histogram()
    n = sum(h)
    return sum(i * c for i, c in enumerate(h)) / n

paths = {}
for t, tag in D03B + C01:
    paths[tag] = grab(t, tag)
    print("OK", tag, t)

print("== frame-diff (mean abs gray diff, consecutive pairs) ==")
for series, pairs in (
    ("D03B tail", [("d03b_t1", "d03b_t2", 0.25), ("d03b_t2", "d03b_t3", 0.25), ("d03b_t3", "d03b_t4", 0.19)]),
    ("C01 motion", [("c01_m1", "c01_m2", 0.25), ("c01_m2", "c01_m3", 0.25), ("c01_m3", "c01_m4", 0.08)]),
):
    for a, b, dt in pairs:
        print("%s %s->%s (dt=%.2fs): %.3f" % (series, a, b, dt, madiff(paths[a], paths[b])))
print("C01 wide pair c01_m1->c01_m4 (dt=0.58s): %.3f" % madiff(paths["c01_m1"], paths["c01_m4"]))

# 拼 PROXY-REVIEW-5 板：row1=D03B 4 帧，row2=C01 4 帧
cw, ch = 960, 540
im = Image.new("RGB", (4 * cw, 2 * (ch + 24) + 30), (16, 16, 18))
d = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
except Exception:
    fnt = ImageFont.load_default()
d.text((8, 6), "V5 proxy supplemental: D03b true tail (blue-flame bleed) + C01 micro-motion", fill=(255, 220, 120), font=fnt)
order = ["d03b_t1", "d03b_t2", "d03b_t3", "d03b_t4", "c01_m1", "c01_m2", "c01_m3", "c01_m4"]
labels = ["d03b_t1 t=151.30", "d03b_t2 t=151.55", "d03b_t3 t=151.80", "d03b_t4 t=151.99",
          "c01_m1 t=77.40", "c01_m2 t=77.65", "c01_m3 t=77.90", "c01_m4 t=77.98"]
for i, tag in enumerate(order):
    r, c = divmod(i, 4)
    x, y = c * cw, 30 + r * (ch + 24)
    d.text((x + 4, y + 2), labels[i], fill=(200, 200, 210), font=fnt)
    fr = Image.open(paths[tag]).convert("RGB").resize((cw, ch))
    im.paste(fr, (x, y + 22))
im.save(os.path.join(OUT, "PROXY-REVIEW-5.jpg"), quality=90)
print("BOARD: PROXY-REVIEW-5.jpg")
print("DONE")
