# -*- coding: utf-8 -*-
# probe_v54_r1017.py — V5.4 整改取证板生成器（CEO 终审反馈 21:1x 五连）
# ① 裸硬切跳变对照板：46 裸切 pre/post 双帧拼板（判跳变最刺眼切）
# ② 女主镜逐帧扫描板：12 女主镜密集抽帧（找穿帮/AI 鬼影鬼畜/morph）
import os, re, subprocess, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "full_mv_v53.mp4")
OUT = os.path.join(HERE, "v54_probe")
os.makedirs(OUT, exist_ok=True)
FF = "ffmpeg"

# 71 切（build_rows_v51 实测导出）
CUTS = [3.50,7.50,11.50,14.60,17.50,21.90,25.90,29.00,31.14,34.74,36.92,38.82,40.22,42.22,44.00,
45.22,47.50,50.52,54.22,58.44,61.98,68.86,74.60,77.34,78.00,80.18,83.56,87.74,91.06,92.62,95.22,
100.14,102.88,108.22,110.52,114.70,118.46,122.82,126.32,131.72,138.56,141.76,144.56,147.84,150.54,
152.00,153.60,155.40,159.66,163.04,167.22,172.50,177.00,180.00,182.00,184.08,187.26,190.00,191.60,
193.12,197.00,199.00,200.80,205.10,207.00,208.80,212.66,219.84,224.00,227.50,230.50]

# 10 XF 软切锚
XF = {21.90,38.82,40.22,47.50,80.18,102.88,110.52,131.72,187.26,219.84}

# V5.3 FX_EVENTS 26 位点（st）
FX = [17.42,28.76,38.62,40.02,47.30,58.20,68.62,77.30,80.05,91.02,92.56,102.80,110.42,110.62,
131.62,141.72,150.34,159.42,168.30,176.76,187.24,193.04,199.30,212.62,219.80,231.90]

def covered(t):
    if t in XF:
        return "xf"
    for f in FX:
        if abs(f - t) <= 0.60:
            return "fx"
    return "bare"

bare = [t for t in CUTS if covered(t) == "bare"]
print("bare cuts: %d -> %s" % (len(bare), bare), flush=True)

def grab(tt, path):
    subprocess.run([FF, "-y", "-ss", "%.3f" % max(0.0, tt), "-i", SRC, "-frames:v", "1",
                    "-q:v", "3", path], capture_output=True)
    return os.path.isfile(path)

# ① 裸硬切 pre/post 双帧
fr = os.path.join(OUT, "bare_cuts"); os.makedirs(fr, exist_ok=True)
for i, t in enumerate(bare):
    grab(t - 0.10, os.path.join(fr, "b%02d_pre.jpg" % i))
    grab(t + 0.06, os.path.join(fr, "b%02d_post.jpg" % i))
# 拼板 2 列（pre|post 一行一切·640 宽格）
from PIL import Image, ImageDraw, ImageFont
cw, ch = 480, 274
rows_n = len(bare)
cols = 2
im = Image.new("RGB", (cols * (cw + 4), rows_n * (ch + 22) + 30), (12, 12, 14))
d = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
except Exception:
    fnt = ImageFont.load_default()
d.text((8, 6), "BARE-CUT jump audit: PRE | POST  (t=cut sec)", fill=(255, 220, 120), font=fnt)
for i, t in enumerate(bare):
    y = 30 + i * (ch + 22)
    d.text((4, y + 2), "cut@%.2f" % t, fill=(200, 200, 210), font=fnt)
    for c, tag in ((0, "pre"), (1, "post")):
        p = os.path.join(fr, "b%02d_%s.jpg" % (i, tag))
        if os.path.isfile(p):
            f = Image.open(p).convert("RGB").resize((cw, ch))
            im.paste(f, (c * (cw + 4), y + 20))
sheet = os.path.join(OUT, "BARE-CUT-BOARD.jpg")
im.save(sheet, quality=88)
print("BOARD:", sheet, flush=True)

# ② 女主镜密集扫描（窗内每 ~0.55s 一帧）
HER_SHOTS = [
    ("N02_crowd_her", 50.52, 54.22), ("N03_goddess_pass", 54.22, 58.44),
    ("R02_she_turns", 114.70, 118.46), ("R03_goddess_dim", 118.46, 122.82),
    ("D02_she_reads", 144.56, 147.84), ("D03_two_worlds", 147.84, 150.54),
    ("D03b_direct_gaze", 150.54, 152.00), ("D04_her_brush", 153.60, 155.40),
    ("D05_words_warm", 155.40, 159.66), ("E03_gaze_meet", 199.00, 200.80),
    ("E04_replay_faces", 212.66, 219.84), ("B03_last_look", 182.00, 184.08),
]
hf = os.path.join(OUT, "her_frames"); os.makedirs(hf, exist_ok=True)
cells = []
for name, a, b in HER_SHOTS:
    step = 0.55 if (b - a) > 3.0 else (b - a) / 4.0
    tt = a + step * 0.35
    k = 0
    while tt < b - 0.15 and k < 10:
        p = os.path.join(hf, "%s_%02d.jpg" % (name, k))
        grab(tt, p)
        if os.path.isfile(p):
            cells.append((p, "%s %.1fs" % (name.replace("E04_replay_faces", "E04"), tt)))
        tt += step; k += 1
# 拼板 4 列
per = 4
rows_n2 = (len(cells) + per - 1) // per
cw2, ch2 = 480, 274
im2 = Image.new("RGB", (per * (cw2 + 4), rows_n2 * (ch2 + 22) + 30), (12, 12, 14))
d2 = ImageDraw.Draw(im2)
try:
    fnt2 = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
except Exception:
    fnt2 = ImageFont.load_default()
d2.text((8, 6), "HER-SHOT ghost/glitch audit (dense frames)", fill=(255, 220, 120), font=fnt2)
for i, (p, label) in enumerate(cells):
    r, c = divmod(i, per)
    x, y = c * (cw2 + 4), 30 + r * (ch2 + 22)
    d2.text((x + 4, y + 2), label, fill=(200, 200, 210), font=fnt2)
    f = Image.open(p).convert("RGB").resize((cw2, ch2))
    im2.paste(f, (x, y + 20))
sheet2 = os.path.join(OUT, "HER-SHOT-BOARD.jpg")
im2.save(sheet2, quality=88)
print("BOARD:", sheet2, flush=True)
print("DONE", flush=True)
