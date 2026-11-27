# -*- coding: utf-8 -*-
# probe_e04_src_r1017.py — E04_replay_faces v5 素材帧位细查（CEO「女孩的镜头还是有穿帮和 AI 鬼影鬼畜」）
# 已定罪（HER-SHOT-BOARD 判读）：片上 216.2-217.8 贴面融合 + 215.1 后右人物 identity drift。
# 素材时刻换算（speed 0.72·窗 212.66-219.84）：片上 t -> 素材 (t-212.66)/0.72
#   215.1 -> 3.39s | 216.2 -> 4.92s | 217.8 -> 7.14s
# 目的：素材头段（0-3.39）/中段（3.39-4.92）/贴面段（4.92-7.14）/尾段（7.14-end）质量四象限
#       -> 裁避/降速/定格收 方案账
import os, subprocess, sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo\E04_replay_faces_v5.mp4"
OUT = os.path.join(HERE, "v54_probe")

r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", SRC],
                   capture_output=True, text=True)
D = float(json.loads(r.stdout)["format"]["duration"])
print("E04 src: %.2fMB  dur=%.2fs  (speed0.72 consumption need = 7.18/0.72 = %.2fs)" % (
    os.path.getsize(SRC) / 1048576.0, D, 7.18 / 0.72))

# 素材关键帧位：头段采样 + 定罪段加密 + 尾段采样
PTS = [0.3, 1.2, 2.2, 3.0, 3.39, 3.9, 4.4, 4.92, 5.3, 5.7, 6.1, 6.5, 6.9, 7.14,
       7.6, 8.2, 8.8, 9.4, min(9.9, D - 0.2)]
def grab(t, path):
    subprocess.run(["ffmpeg", "-y", "-ss", "%.2f" % t, "-i", SRC, "-frames:v", "1",
                    "-q:v", "3", path], capture_output=True)
    return os.path.isfile(path)

from PIL import Image, ImageDraw, ImageFont
cw, ch = 480, 274
per = 5
rows_n = (len(PTS) + per - 1) // per
im = Image.new("RGB", (per * (cw + 4), rows_n * (ch + 24) + 40), (12, 12, 14))
d = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
except Exception:
    fnt = ImageFont.load_default()
d.text((8, 6), "E04 v5 source dense frames (t=source sec; convicted film 216.2-217.8 -> src 4.92-7.14)", fill=(255, 220, 120), font=fnt)
for i, t in enumerate(PTS):
    r_, c_ = divmod(i, per)
    y = 34 + r_ * (ch + 24)
    p = os.path.join(OUT, "e04_%02d.jpg" % i)
    if grab(t, p):
        tag = "SRC@%.2f" % t
        if 4.92 <= t <= 7.14:
            tag += " **FUSION**"
        d.text((c_ * (cw + 4) + 4, y + 2), tag, fill=(255, 255, 160) if 4.92 <= t <= 7.14 else (200, 200, 210), font=fnt)
        im.paste(Image.open(p).convert("RGB").resize((cw, ch)), (c_ * (cw + 4), y + 20))
bp = os.path.join(OUT, "E04-SRC-DENSE-BOARD.jpg")
im.save(bp, quality=88)
print("BOARD:", bp)
