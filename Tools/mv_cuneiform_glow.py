#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_cuneiform_glow.py — 真楔文「发光刻痕」版（替代 21.4-22.75s 的伪符号板）。

为什么要换（专家群审四席同指）：
  原镜是 8 个大号发光三角/竖条符，形态与「◀◀ ▮ ▶▶▶」媒体播放器按键高度重合，
  受众席原话「像播放器的快退/播放/快进键，出戏」；文字席判「臆造符文、破坏楔文连续性」。
  本工具改用真 Unicode 楔文（U+12000-123FF）渲染成「沟槽透出的火光」，同拍点、同亮度感。

输出：黑底 + 金色楔文行 + 多尺度泛光 + 轻微呼吸（由 build 侧的 eq 完成）。
自检：可用码点 <200 直接 abort。
"""
import argparse
import random
import sys
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = os.path.join(r"K:\Fluxgroup\.tools\fonts", "NotoSansCuneiform-Regular.ttf")


def usable(font_path, lo=0x12000, hi=0x123FF, probe=72, size=40):
    f = ImageFont.truetype(font_path, size)

    def bmp(cp):
        im = Image.new("L", (probe, probe), 0)
        ImageDraw.Draw(im).text((4, 4), chr(cp), font=f, fill=255)
        return im.tobytes()

    notdef = bmp(0x10FFFE)
    blank = bytes([0]) * (probe * probe)
    return [cp for cp in range(lo, hi + 1)
            if (b := bmp(cp)) != blank and b != notdef]


def render(w, h, seed, rows, rows_visible_frac=0.72):
    rng = random.Random(seed)
    cps = usable(FONT)
    print("usable codepoints=%d" % len(cps), flush=True)
    if len(cps) < 200:
        return None

    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)

    margin_x = int(w * 0.16)
    margin_y = int(h * 0.10)
    usable_w = w - margin_x * 2
    usable_h = h - margin_y * 2
    row_h = usable_h / rows

    for r in range(rows):
        # 越靠下的行越暗（像光从上方渗下）
        depth = r / max(1, rows - 1)
        base_alpha = int(255 * max(0.18, 1.0 - 0.55 * depth))
        yy = margin_y + r * row_h + row_h * rng.uniform(0.18, 0.30)
        size = max(16, int(row_h * rng.uniform(0.40, 0.52)))
        font = ImageFont.truetype(FONT, size)
        x = margin_x + rng.uniform(-8, 8)
        rng.shuffle(cps)
        i = 0
        while i < len(cps) - 6:
            n = rng.randint(2, 5)
            s = "".join(chr(c) for c in cps[i:i + n])
            i += n
            wd = font.getlength(s)
            if x + wd > margin_x + usable_w:
                break
            md.text((x, yy), s, font=font, fill=base_alpha)
            x += wd + font.getlength(" ") * rng.uniform(1.0, 2.2)

    # 底部再压一层暗，避免"满屏"
    fade = Image.new("L", (w, h), 0)
    fd = ImageDraw.Draw(fade)
    for y in range(h):
        k = y / float(h)
        v = int(255 * max(0.10, 1.0 - 0.62 * max(0.0, (k - 0.55) / 0.45)))
        fd.line([(0, y), (w, y)], fill=v)
    mask = Image.composite(mask, Image.new("L", (w, h), 0), fade)

    # ---- 金色 + 多尺度泛光 ----
    gold_core = (255, 214, 150)
    gold_drift = (226, 150, 74)

    glow_far = mask.filter(ImageFilter.GaussianBlur(w / 26.0))
    glow_mid = mask.filter(ImageFilter.GaussianBlur(w / 90.0))
    sharp = mask.filter(ImageFilter.GaussianBlur(0.9))

    out = Image.new("RGB", (w, h), (0, 0, 0))
    # 远泛光（暖橘）
    far = Image.new("RGB", (w, h), gold_drift)
    out = Image.composite(far, out, glow_far.point(lambda v: int(v * 0.55)))
    # 中泛光
    mid = Image.new("RGB", (w, h), (250, 180, 110))
    out = Image.composite(mid, out, glow_mid.point(lambda v: int(v * 0.75)))
    # 字心
    core = Image.new("RGB", (w, h), gold_core)
    out = Image.composite(core, out, sharp)

    # 极轻颗粒，避免纯数字渐变带
    grain = Image.effect_noise((w, h), 9).convert("L")
    out = Image.blend(out, Image.merge("RGB", (grain, grain, grain)), 0.035)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--w", type=int, default=1344)
    ap.add_argument("--h", type=int, default=768)
    ap.add_argument("--seed", type=int, default=9121)
    ap.add_argument("--rows", type=int, default=9)
    a = ap.parse_args(argv)
    im = render(a.w, a.h, a.seed, a.rows)
    if im is None:
        return 2
    d = os.path.dirname(os.path.abspath(a.out))
    if d:
        os.makedirs(d, exist_ok=True)
    im.save(a.out, "PNG")
    print("GLOW OK %s %dx%d %dB" % (a.out, im.width, im.height, os.path.getsize(a.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
