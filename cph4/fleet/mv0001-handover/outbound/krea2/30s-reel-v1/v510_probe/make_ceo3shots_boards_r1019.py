# -*- coding: utf-8 -*-
# make_ceo3shots_boards_r1019.py — CEO 三镜定位②：三族身份帧板（刻字/唱歌/女主鬼影）
# 修：弃 xstack+drawtext（0xC0000005 崩）→ PIL 拼板+PIL 标签。
import os, subprocess, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "full_mv_v510.mp4")
FF = r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
OUT = os.path.join(HERE, "v510_probe", "ceo3shots")
os.makedirs(OUT, exist_ok=True)
os.chdir(HERE)
from PIL import Image, ImageDraw

BOARDS = {
    "A_carve": [("S6_chisel", 35.8), ("C01_carver_face", 78.8), ("C08_strike", 101.4),
                ("D01_carver_words", 143.2), ("D06_fingertip", 161.4), ("E06_strike", 210.4)],
    "B_sing": [("SING2_fire_sing", 180.0), ("SING2_fire_sing", 181.2), ("SING2_fire_sing", 182.0),
               ("E03_gaze(SING3b)", 198.4), ("E03_gaze(SING3b)", 199.4), ("E03_gaze(SING3b)", 200.4)],
    "C_her":  [("E04_replay", 213.5), ("E04_replay", 215.5), ("E04_replay", 217.5),
               ("E04_replay", 219.0), ("echo@188", 188.0), ("echo2@191.5", 191.5)],
}

TW, TH = 560, 320
for board, items in BOARDS.items():
    tiles = []
    for i, (lab, t) in enumerate(items):
        jp = os.path.join(OUT, "%s_%02d.jpg" % (board, i))
        subprocess.run([FF, "-y", "-v", "error", "-ss", "%.2f" % t, "-i", SRC,
                        "-frames:v", "1", "-q:v", "3", jp], check=True)
        im = Image.open(jp).convert("RGB").resize((TW, TH))
        d = ImageDraw.Draw(im)
        tag = "%s @%ss" % (lab, t)
        d.rectangle([0, 0, 8 * len(tag) + 16, 26], fill=(0, 0, 0))
        d.text((8, 6), tag, fill=(255, 255, 0))
        tiles.append(im)
    sheet = Image.new("RGB", (TW * 3, TH * 2))
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % 3) * TW, (k // 3) * TH))
    tile_path = os.path.join(OUT, "BOARD-%s.jpg" % board)
    sheet.save(tile_path, quality=88)
    print("BOARD -> " + tile_path)
print("DONE")
