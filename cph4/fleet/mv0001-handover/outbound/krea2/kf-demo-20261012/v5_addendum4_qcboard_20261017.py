# -*- coding: utf-8 -*-
# v5_addendum4_qcboard_20261017.py — 4-shot reburn QC: dense frames + 4x3 t-grid board
# 正身: V5-REBURN-ADDENDUM-4shot-20261017.md 验收线 · 板名 V5-ADDENDUM4-QC-BOARD-20261017.jpg (铁字复用律: PIL/JPEG88/暗底/红框 convention from v5redo_phase2_r1054.py)
# t-grid: 每镜 3 帧 (t=0.0 / 2.5 / 4.9) · cell 640x360; dense: E01c 8帧发力窗口 + INT5 背线窗 + D01 拉丁窗 + C04 字形窗
import os, sys, time, subprocess

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
OUTDIR = os.path.join(BASE, "bmc", "i2v", "v5redo")
MEDIA = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001"
QC = os.path.join(MEDIA, "v5redo", "qc_add4_dense")
BOARD = os.path.join(BASE, "bmc", "V5-ADDENDUM4-QC-BOARD-20261017.jpg")
SHOTS = ["D01_carver_words_v5", "C04_words_alive_v5", "E01c_first_line_v5", "INT5_head_bow_v5"]
TGRID = [0.0, 2.5, 4.9]  # 768P 5.17s clips
DENSE = {
    "E01c_first_line_v5": [1.2, 1.8, 2.1, 2.4, 2.7, 3.0, 3.6, 4.2],  # 发力窗口·一凿落定+石屑
    "INT5_head_bow_v5": [0.0, 1.3, 2.6, 4.5],  # 背线不塌 (旧病灶 t=2.6+)
    "D01_carver_words_v5": [0.0, 2.6, 3.4, 4.9],  # 拉丁 F/G 稳在场窗 + 褶纸窗 t=3.4+
    "C04_words_alive_v5": [0.0, 2.6, 5.0],  # 字形稳定窗
}

def grab(mp4, t, out):
    subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", mp4, "-frames:v", "1", out],
                   capture_output=True, timeout=120)
    return os.path.isfile(out)

missing = [s for s in SHOTS if not (os.path.isfile(os.path.join(OUTDIR, s + ".mp4")) and os.path.getsize(os.path.join(OUTDIR, s + ".mp4")) > 400000)]
if missing:
    print("MISSING officials:", missing); sys.exit(1)

for s in SHOTS:
    mp4 = os.path.join(OUTDIR, s + ".mp4")
    d = os.path.join(QC, s); os.makedirs(d, exist_ok=True)
    for t in TGRID:
        grab(mp4, t, os.path.join(d, "t%04d.png" % int(t * 100)))
    for t in DENSE[s]:
        grab(mp4, t, os.path.join(d, "d%04d.png" % int(t * 100)))
print("dense frames extracted ->", QC)

from PIL import Image, ImageDraw
tw, thh, lab, cols, rows_n = 640, 360, 26, 3, 4
sheet = Image.new("RGB", (cols * (tw + 6) + 6, rows_n * (thh + lab + 6) + 36), (24, 20, 16))
dr = ImageDraw.Draw(sheet)
dr.text((10, 6), "V5 ADDENDUM4 official 768P INT8 -- 4 shots x t-grid -- bm-c 20261017 -- %s" % time.strftime("%Y-%m-%d %H:%M"), fill=(240, 200, 120))
for ri, s in enumerate(SHOTS):
    for ci, t in enumerate(TGRID):
        th = os.path.join(QC, s, "t%04d.png" % int(t * 100))
        pic = Image.open(th).convert("RGB").resize((tw, thh)) if os.path.isfile(th) else Image.new("RGB", (tw, thh), (40, 36, 30))
        x = 6 + ci * (tw + 6); y = 36 + ri * (thh + lab + 6)
        dr.text((x + 4, y + 3), "%s  t=%.1fs" % (s, t), fill=(225, 205, 150))
        sheet.paste(pic, (x, y + lab))
        dr.rectangle([x, y + lab, x + tw, y + lab + thh], outline=(90, 40, 40))
sheet.save(BOARD, "JPEG", quality=88)
print("board -> %s" % BOARD)
