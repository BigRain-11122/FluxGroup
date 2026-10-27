# -*- coding: utf-8 -*-
# audit_v542_transitions_r1017.py — V5.4.2 转场顶级升格终验板（CEO「转场务必顶级」令验收面）
# 三新升格点抽帧：44.00 hblur 过门 / 126.32 fade+leak 漏光 / 191.60 fade+echo2 跨千年残像
# +基线对照（21.90 微叠化/80.18 hblur 正典/219.84 收束）
import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "full_mv_v54.mp4")
OUT = os.path.join(HERE, "v54_probe")

PTS = [
    ("hblur_pre", 43.78), ("hblur_mid", 43.98), ("hblur_post", 44.22),
    ("leak_pre", 126.08), ("leak_mid", 126.32), ("leak_on", 126.70), ("leak_off", 127.35),
    ("echo2_pre", 191.15), ("echo2_mid", 191.45), ("echo2_on", 191.85), ("echo2_fade", 192.40),
    ("xf2190", 22.00), ("xf8018", 80.10), ("xf21984", 219.90),
]

def grab(t, path):
    subprocess.run(["ffmpeg", "-y", "-ss", "%.2f" % t, "-i", SRC, "-frames:v", "1",
                    "-q:v", "3", path], capture_output=True)
    return os.path.isfile(path)

from PIL import Image, ImageDraw, ImageFont
per = 5
rows_n = (len(PTS) + per - 1) // per
cw, ch = 480, 274
im = Image.new("RGB", (per * (cw + 4), rows_n * (ch + 24) + 40), (12, 12, 14))
d = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
except Exception:
    fnt = ImageFont.load_default()
d.text((8, 6), "V5.4.2 transition-craft audit: 44.00 hblur door | 126.32 fade+leak | 191.60 fade+echo2 | baselines", fill=(255, 220, 120), font=fnt)
for i, (tag, t) in enumerate(PTS):
    r_, c_ = divmod(i, per)
    y = 34 + r_ * (ch + 24)
    p = os.path.join(OUT, "v42_%s.jpg" % tag)
    if grab(t, p):
        d.text((c_ * (cw + 4) + 4, y + 2), "%s @%.2f" % (tag, t), fill=(200, 200, 210), font=fnt)
        im.paste(Image.open(p).convert("RGB").resize((cw, ch)), (c_ * (cw + 4), y + 20))
bp = os.path.join(OUT, "V542-TRANSITION-AUDIT.jpg")
im.save(bp, quality=88)
print("BOARD:", bp)
