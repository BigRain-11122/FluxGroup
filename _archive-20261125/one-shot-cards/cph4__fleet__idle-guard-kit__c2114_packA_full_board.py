# -*- coding: utf-8 -*-
# c2114_packA_full_board.py -- 星晴 PACK-A 33/33 full contact board (3 frames per unit)
import os, subprocess, json
from PIL import Image, ImageDraw

REPO = r"K:\Fluxgroup\FluxGroup"
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay", "clips-packA-768")
TMP = os.path.join(CLIPS, "_fullboard_c2114")
OUT = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "xq-PACKA-33-FULL-BOARD-c2114.jpg")
NO_WINDOW = 0x08000000
os.makedirs(TMP, exist_ok=True)

files = sorted(f for f in os.listdir(CLIPS) if f.endswith(".mp4"))
FW, FH, GAP, LBL = 320, 183, 4, 14
rows = []
for fn in files:
    clip = os.path.join(CLIPS, fn)
    try:
        p = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", clip],
                           capture_output=True, text=True, creationflags=NO_WINDOW, timeout=60)
        dur = float(p.stdout.strip())
    except Exception:
        dur = 5.0
    frames = []
    for i, t in enumerate([0.3, dur / 2.0, max(0.15, dur - 0.3)]):
        fp = os.path.join(TMP, "%s_%d.png" % (fn[:-4], i))
        r = subprocess.run(["ffmpeg", "-y", "-ss", "%.3f" % t, "-i", clip, "-frames:v", "1", fp],
                           capture_output=True, creationflags=NO_WINDOW, timeout=120)
        if r.returncode == 0 and os.path.isfile(fp):
            frames.append(fp)
    if len(frames) < 2:
        continue
    rows.append((fn[:-4], frames))

W = 3 * (FW + GAP) + GAP
H = FH + LBL + GAP
board = Image.new("RGB", (W * 2 + 24, ((len(rows) + 1) // 2) * H + 20), (18, 16, 15))
dr = ImageDraw.Draw(board)
for idx, (label, frames) in enumerate(rows):
    col, row = idx % 2, idx // 2
    x0 = 8 + col * (W + 8)
    y0 = 12 + row * H
    x = x0 + GAP
    for fp in frames:
        im = Image.open(fp).convert("RGB").resize((FW, FH), Image.LANCZOS)
        board.paste(im, (x, y0))
        x += FW + GAP
    dr.text((x0 + GAP, y0 + FH + 2), label, fill=(214, 194, 152))
board.save(OUT, quality=82)
print("FULLBOARD DONE units=%d board=%s bytes=%d dims=%dx%d" % (len(rows), OUT, os.path.getsize(OUT), board.size[0], board.size[1]))
with open(os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "xq-PACKA-33-FULL-BOARD-c2114.json"), "w", encoding="utf-8") as f:
    json.dump({"units": len(rows), "labels": [r[0] for r in rows], "board": OUT}, f, ensure_ascii=False, indent=1)