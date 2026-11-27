# -*- coding: utf-8 -*-
# probe_n03r03_r1017.py — N03/R03 雕像 morph 窗密集抽帧定级（CEO「女孩镜头鬼影」六连整改最后一项）
# V53 HER-SHOT 判读定罪：N03_goddess_pass(54.22-58.44) / R03_goddess_dim(118.46-122.82)
# 雕像五官帧间 morph=明显。窗口不受 E04/D08/XF 改动影响——从 full_mv_v54.mp4 抽帧即 V5.4.1 等效证据。
# 定级目的：A=morph 穿帮级（须修：提速去插值 or FX 遮罩 or 重烧）/ B=可见但容忍 / C=干净可过
import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "full_mv_v54.mp4")
OUT = os.path.join(HERE, "v54_probe")

WINS = [("N03", 54.22, 58.44), ("R03", 118.46, 122.82)]

def grab(t, path):
    subprocess.run(["ffmpeg", "-y", "-ss", "%.2f" % t, "-i", SRC, "-frames:v", "1",
                    "-q:v", "3", path], capture_output=True)
    return os.path.isfile(path)

from PIL import Image, ImageDraw, ImageFont
cells = []
for name, a, b in WINS:
    step = 0.30
    n = int((b - a) / step)
    for k in range(n):
        t = a + step * (k + 0.5)
        p = os.path.join(OUT, "n03r03_%s_%02d.jpg" % (name, k))
        if grab(t, p):
            cells.append((p, "%s %.2fs" % (name, t)))

per = 5
rows_n = (len(cells) + per - 1) // per
cw, ch = 480, 274
im = Image.new("RGB", (per * (cw + 4), rows_n * (ch + 24) + 40), (12, 12, 14))
d = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
except Exception:
    fnt = ImageFont.load_default()
d.text((8, 6), "N03/R03 goddess-statue morph audit (dense 0.30s frames from v54 film)", fill=(255, 220, 120), font=fnt)
for i, (p, label) in enumerate(cells):
    r_, c_ = divmod(i, per)
    y = 34 + r_ * (ch + 24)
    d.text((c_ * (cw + 4) + 4, y + 2), label, fill=(200, 200, 210), font=fnt)
    im.paste(Image.open(p).convert("RGB").resize((cw, ch)), (c_ * (cw + 4), y + 20))
bp = os.path.join(OUT, "N03R03-MORPH-BOARD.jpg")
im.save(bp, quality=88)
print("cells=%d BOARD: %s" % (len(cells), bp))
