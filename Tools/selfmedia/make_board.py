#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_board.py — 审片板：块面中位帧网格 + 切点前后帧对。

为什么：席位要判「空间建立 / 视线匹配 / 银幕方向 / 动作连接 / 道具连续」，
必须先有无损、可对照的画面。整片看一遍抓不住切点，逐张看又太散。
产物：
  BOARD-BLOCKS.jpg  每块一帧（中间时刻），2 行 x N 列，带块号
  BOARD-CUTS.jpg    每个切点的「前一帧 | 后一帧」成对贴，带时间码
两张板都按 384 宽单格，保证人脸与道具可辨。
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = "ffmpeg"
CELL_W = 384


def grab(film, t, out, w=CELL_W):
    subprocess.run([FF, "-y", "-ss", "%.3f" % max(0.0, t), "-i", film,
                    "-frames:v", "1", "-vf", "scale=%d:-2" % w, out],
                   capture_output=True)
    return os.path.exists(out) and os.path.getsize(out) > 0


def label(img, text):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, max(60, 8 * len(text)), 18], fill=(0, 0, 0))
    d.text((4, 3), text, fill=(255, 255, 255))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True)
    ap.add_argument("--edl", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    edl = json.load(open(a.edl, encoding="utf-8"))
    blocks = edl["blocks"]
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp()

    # ---- 块面板：2 行 N 列 ----
    cells = []
    for b in blocks:
        mid = (float(b["t0"]) + float(b["t1"])) / 2
        p = os.path.join(tmp, "b%02d.png" % b["i"])
        if grab(a.film, mid, p):
            im = label(Image.open(p).convert("RGB"),
                       "B%02d %.1fs %s" % (b["i"], mid, b.get("desc", "")[:14]))
            cells.append(im)
    if cells:
        cols = (len(cells) + 1) // 2
        cw, ch = cells[0].size
        board = Image.new("RGB", (cw * cols, ch * 2), (10, 10, 10))
        for i, im in enumerate(cells):
            board.paste(im, ((i % cols) * cw, (i // cols) * ch))
        bp = os.path.join(a.out, "BOARD-BLOCKS.jpg")
        board.save(bp, quality=92)
        print("BOARD-BLOCKS ->", bp, board.size)

    # ---- 切点板：每切点 前|后 ----
    pairs = []
    for i, b in enumerate(blocks[:-1]):
        t = float(b["t1"])
        p1, p2 = os.path.join(tmp, "c%d_a.png" % i), os.path.join(tmp, "c%d_b.png" % i)
        ok1 = grab(a.film, t - 0.06, p1)
        ok2 = grab(a.film, t + 0.06, p2)
        row = []
        for p, ok, tag in ((p1, ok1, "%.2f PRE  B%02d" % (t, b["i"])),
                           (p2, ok2, "%.2f POST B%02d" % (t, blocks[i + 1]["i"]))):
            if ok:
                row.append(label(Image.open(p).convert("RGB"), tag))
            else:
                row.append(Image.new("RGB", (CELL_W, 216), (40, 0, 0)))
        pairs.append(row)
    if pairs:
        rows = (len(pairs) + 1) // 2
        cw, ch = pairs[0][0].size
        board = Image.new("RGB", (cw * 4, ch * rows), (10, 10, 10))
        for i, (l, r) in enumerate(pairs):
            x = (i % 2) * cw * 2
            y = (i // 2) * ch
            board.paste(l, (x, y))
            board.paste(r, (x + cw, y))
        cp = os.path.join(a.out, "BOARD-CUTS.jpg")
        board.save(cp, quality=92)
        print("BOARD-CUTS ->", cp, board.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
