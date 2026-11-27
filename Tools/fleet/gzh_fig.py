#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_fig.py — 公众号配图：可复算的色阶对照图（不编车机截图）。

为什么不用 AI 生成：这篇文章的论点是「L 值差 3 点以内人眼分不出来」，
图必须是**精确色值**，AI 生成会给近似色，一量就露。所以用标准库直接算像素。

图里没有文字（本机没有绘图库，也不装）：三块面板各四级表面，
左中右分别是 L 差 2 点 / 4 点 / 6 点，底色统一 #121212。图注写在正文里。

用法：
  python3 Tools/fleet/gzh_fig.py --out <path.png>
  python3 Tools/fleet/gzh_fig.py --self-test
退出码：0 成功 / 4 自检失败
"""
from __future__ import annotations

import argparse
import struct
import sys
import zlib

BASE_L = 18 / 255 * 100      # #121212 的 HSL 明度 ≈ 7.06%


def _gray(L):
    """L(0-100) → RGB 灰阶。纯灰所以三个通道同值，量的时候不会被色相干扰。"""
    v = max(0, min(255, round(L / 100 * 255)))
    return (v, v, v)


def _png(path, w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def build(path, deltas=(2, 4, 6), levels=4, pad=30, panel=360, band=120):
    """三块面板，每块 levels 级表面；panel 宽、band 高、pad 边距与间隙。"""
    w = len(deltas) * panel + (len(deltas) + 1) * pad
    h = levels * band + 2 * pad
    bg = (0, 0, 0)
    img = [bytearray(bg * w) for _ in range(h)]
    for pi, d in enumerate(deltas):
        x0 = pad + pi * (panel + pad)
        for li in range(levels):
            y0 = pad + li * band
            color = _gray(BASE_L + d * li)
            line = bytes(color) * panel
            for y in range(y0, y0 + band):
                if 0 <= y < h:
                    img[y][x0 * 3:(x0 + panel) * 3] = line
    _png(path, w, h, img)
    return w, h


def self_test():
    import tempfile
    import os
    fails = []
    d = tempfile.mkdtemp(prefix="gzhfig-")
    p = os.path.join(d, "t.png")
    w, h = build(p, deltas=(2,), levels=2, panel=10, band=10, pad=2)
    blob = open(p, "rb").read()
    if not blob.startswith(b"\x89PNG\r\n\x1a\n"):
        fails.append("产出的不是 PNG")
    if b"IHDR" not in blob:
        fails.append("缺 IHDR 块")
    # 负控：两级表面必须真的不同色（差 2 点也要有差）
    a, b = _gray(BASE_L), _gray(BASE_L + 2)
    if a == b:
        fails.append("L 差 2 点算出了同一个像素值——图会骗人")
    # 正控：差 6 点必须比差 2 点更明显
    if (_gray(BASE_L + 6)[0] - _gray(BASE_L)[0]) <= (_gray(BASE_L + 2)[0] - _gray(BASE_L)[0]):
        fails.append("L 差 6 点没有比 2 点更亮——色阶映射写反了")
    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for x in fails:
            print("  - " + x, file=sys.stderr)
        return 4
    print("SELF-TEST OK 3/3（是PNG/两点有差/六点更亮）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    out = a.out or "fig-lstep.png"
    w, h = build(out)
    print("已生成 %s（%dx%d）｜底色 #121212，三块面板 L 差 2/4/6 点，各四级" % (out, w, h))
    return 0


if __name__ == "__main__":
    sys.exit(main())
