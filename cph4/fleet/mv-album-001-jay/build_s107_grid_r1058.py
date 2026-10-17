# -*- coding: ascii -*-
# build_s107_grid_r1058.py - 4x4 labeled grid of the 16 S1-07 T1-1R expansion
# seeds (s21000..s21015, 672x384) for multimodal TRIAGE adjudication.
# bm-c r1058, CEO idle-fill order 2026-10-17. ASCII prints only.

import os
import time

SRC = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\t1r1"
OUT = os.path.join(SRC, "s107_grid_r1058.png")
SEEDS = ["s21%03d" % i for i in range(0, 16)]  # s21000..s21015
CW, CH = 504, 288


def main():
    from PIL import Image, ImageDraw
    cells = []
    for s in SEEDS:
        p = os.path.join(SRC, "S1-07_%s.png" % s)
        img = Image.open(p).convert("RGB")
        cell = img.resize((CW, CH), Image.LANCZOS)
        d = ImageDraw.Draw(cell)
        d.rectangle((0, 0, CW, 18), fill=(0, 0, 0))
        d.text((5, 4), "S1-07_" + s, fill=(255, 255, 255))
        cells.append(cell)
    grid = Image.new("RGB", (CW * 4, CH * 4), (24, 24, 24))
    for i, cell in enumerate(cells):
        grid.paste(cell, ((i % 4) * CW, (i // 4) * CH))
    grid.save(OUT)
    print("GRID-OK %s %dB" % (OUT, os.path.getsize(OUT)))


if __name__ == "__main__":
    main()
