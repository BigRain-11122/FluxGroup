#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_cuneiform_texture.py — 真楔形文字石板纹理生成器（v731 文字项修复件）。

为什么（承 DIRECTOR-REVIEW-v730 §三 文字席）：
  v730 石碑与片尾大图上的"楔形文字"是装饰性伪纹样，不是真实字表——本片唯一未过的
  文字项，v731 立卡「真楔文字表贴回」。本工具用 Noto Sans Cuneiform（OFL，
  真 Unicode 楔文块 U+12000-U+123FF）渲染，加阴刻 + 边缘受光，输出石板纹理。

用法：
  python Tools/mv_cuneiform_texture.py --out media/mv0001-handover/v731/cuneiform-tablet.png
  [--w 1024 --h 1536 --seed 7331 --rows 14]

自检：渲染前逐码点探针（notdef/空白剔除），可用码点 <200 直接 abort——
「字体缺字却出图」是这类纹理最隐蔽的假绿。
"""
import argparse
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = os.path.join(r"K:\Fluxgroup\.tools\fonts", "NotoSansCuneiform-Regular.ttf")


def log(*a):
    print(*a, flush=True)


def usable_codepoints(font_path, lo=0x12000, hi=0x123FF, probe=72, probe_size=40):
    """筛出该字体真正有字形的码点。

    首跑判例：探针用成品字号（151px）画进 48×48 画布 → 字形全落在画布外 → 判「0 个
    可用码点」。探针必须独立小字号 + 足够大的画布。
    """
    pfont = ImageFont.truetype(font_path, probe_size)

    def bmp(cp):
        im = Image.new("L", (probe, probe), 0)
        ImageDraw.Draw(im).text((4, 4), chr(cp), font=pfont, fill=255)
        return im.tobytes()

    notdef = bmp(0x10FFFE)
    blank = bytes([0]) * (probe * probe)
    keep = []
    for cp in range(lo, hi + 1):
        try:
            b = bmp(cp)
        except Exception:
            continue
        if b == blank:
            continue
        if notdef is not None and b == notdef:
            continue
        keep.append(cp)
    return keep


def basalt(w, h, rng):
    """玄武岩底：中灰底 + 低频云斑 + 细颗粒（太暗会读不出凿刻）。"""
    base = Image.new("RGB", (w, h), (74, 70, 64))
    px = base.load()
    small = Image.new("L", (max(2, w // 24), max(2, h // 24)))
    sp = small.load()
    for y in range(small.height):
        for x in range(small.width):
            sp[x, y] = rng.randint(70, 190)
    small = small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(8))
    sm = small.load()
    for y in range(h):
        for x in range(w):
            k = 0.62 + sm[x, y] / 255.0 * 0.62
            r, g, b = px[x, y]
            px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)))
    grain = Image.effect_noise((w, h), 14).convert("L")
    return Image.blend(base, Image.merge("RGB", (grain, grain, grain)), 0.05)


def render(w, h, seed, rows):
    rng = random.Random(seed)
    if not os.path.isfile(FONT):
        log("CUNEIFORM ABORT font missing: " + FONT)
        return None
    cps = usable_codepoints(FONT)
    log("usable cuneiform codepoints: %d" % len(cps))
    if len(cps) < 200:
        log("CUNEIFORM ABORT too few glyphs")
        return None

    margin = int(w * 0.06)
    line_h = int((h - margin * 2) / rows)
    size = max(24, int(line_h * 0.60))
    font = ImageFont.truetype(FONT, size)
    log("font size=%d line_h=%d rows=%d" % (size, line_h, rows))

    canvas = basalt(w, h, rng).convert("RGBA")

    # --- 逐行排字（每簇 3-6 字，簇间空格，行内贪心填满） ---
    text_layer = Image.new("L", (w, h), 0)
    td = ImageDraw.Draw(text_layer)
    max_w = w - margin * 2
    y = margin + int(line_h * 0.12)
    used = 0
    while y + size < h - margin and used < rows:
        x = margin
        rng.shuffle(cps)
        i = 0
        while i < len(cps) - 6:
            n = rng.randint(3, 6)
            s = "".join(chr(c) for c in cps[i:i + n])
            i += n
            wd = font.getlength(s)
            if x + wd > margin + max_w:
                break
            td.text((x, y), s, font=font, fill=255)
            x += wd + font.getlength(" ") * 1.6
        y += line_h
        used += 1

    # --- 阴刻：字心压暗 ---
    groove = text_layer.filter(ImageFilter.GaussianBlur(2)).load()
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dp = dark.load()
    for yy in range(h):
        for xx in range(w):
            v = groove[xx, yy]
            if v:
                dp[xx, yy] = (8, 7, 6, int(v * 0.95))
    canvas = Image.alpha_composite(canvas, dark)

    # --- 阳刻边：字缘一圈受光（凿口翻起） ---
    dil = text_layer.filter(ImageFilter.MaxFilter(5))
    rim = dil.filter(ImageFilter.GaussianBlur(2)).load()
    sharp = text_layer.filter(ImageFilter.GaussianBlur(1)).load()
    light = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    lp = light.load()
    for yy in range(h):
        for xx in range(w):
            rv, sv = rim[xx, yy], sharp[xx, yy]
            if rv > sv + 20:
                lp[xx, yy] = (226, 214, 192, int((rv - sv) * 0.72))
    canvas = Image.alpha_composite(canvas, light)

    # --- 分区横线 ---
    d = ImageDraw.Draw(canvas)
    for k in range(1, used):
        yy = margin + k * line_h - int(line_h * 0.10)
        d.line([(margin, yy), (w - margin, yy)], fill=(120, 112, 100, 120), width=2)

    # --- 单侧受光（左上亮、右下暗），保持文字对比 ---
    grad = Image.new("L", (w, h))
    gp = grad.load()
    for yy in range(h):
        for xx in range(w):
            gp[xx, yy] = int(255 * (0.62 + 0.38 * (1.0 - (xx / float(w)) * 0.55 - (yy / float(h)) * 0.45)))
    mask = grad.resize((w, h))
    return Image.composite(canvas.convert("RGB"), Image.new("RGB", (w, h), (0, 0, 0)),
                           mask.point(lambda v: 255)).convert("RGB")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--w", type=int, default=1024)
    ap.add_argument("--h", type=int, default=1536)
    ap.add_argument("--seed", type=int, default=7331)
    ap.add_argument("--rows", type=int, default=14)
    a = ap.parse_args(argv)
    im = render(a.w, a.h, a.seed, a.rows)
    if im is None:
        return 2
    d = os.path.dirname(os.path.abspath(a.out))
    if d:
        os.makedirs(d, exist_ok=True)
    im.save(a.out, "PNG")
    log("CUNEIFORM OK %s %dx%d %dB" % (a.out, im.width, im.height, os.path.getsize(a.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
