#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_cuneiform_stele_v2.py — 真楔文字「石刻表面」渲染器 v2（v6 用）。

相对 v1（mv_cuneiform_texture.py）修掉 AI 评审查出的三处：
  1. 四角/边框死黑糊成一片 → 改成「左侧斜射火炬光」单向梯度，无矩形暗角框；
  2. 表面太光滑、无泥板/岩石颗粒、无裂纹缺角 → 加多尺度噪斑 + 裂纹网络 + 麻点 + 边缘崩口；
  3. 字形排得像印刷网格、重复率高 → 行高/基线抖动、逐字缩放旋转抖动、8% 磨损字、
     行分隔线改成手刻波浪线且不贯通。

用法：
  python Tools/mv_cuneiform_stele_v2.py --out media/mv0001-handover/v6/stele-v2.png \
      [--w 1344 --h 768 --seed 7031 --rows 11 --light left]
自检：可用码点 < 200 直接 abort（字体缺字却出图是最隐蔽的假绿）。
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_GLYPH = os.path.join(r"K:\Fluxgroup\.tools\fonts", "NotoSansCuneiform-Regular.ttf")


def log(*a):
    print(*a, flush=True)


def usable_codepoints(font_path, lo=0x12000, hi=0x123FF, probe=72, probe_size=40):
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
        if b == blank or b == notdef:
            continue
        keep.append(cp)
    return keep


def _noise(size, scale, rng):
    """低频值噪声：小图随机 + 双三次放大。"""
    small = Image.new("L", (max(2, size[0] // scale), max(2, size[1] // scale)))
    px = small.load()
    for y in range(small.height):
        for x in range(small.width):
            px[x, y] = rng.randint(0, 255)
    return small.resize(size, Image.BICUBIC)


def basalt(w, h, rng):
    """玄武岩底：粗砂 + 麻点 + 云斑。"""
    # 三层噪声叠加
    n1 = _noise((w, h), 40, rng)
    n2 = _noise((w, h), 9, rng)
    n3 = _noise((w, h), 3, rng)
    a1, a2, a3 = n1.load(), n2.load(), n3.load()
    im = Image.new("RGB", (w, h), (0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            v = 0.46 * a1[x, y] + 0.34 * a2[x, y] + 0.20 * a3[x, y]
            k = 0.28 + v / 255.0 * 0.62          # 0.28 - 0.90（压暗，给火光留余量）
            px[x, y] = (min(255, int(96 * k)), min(255, int(84 * k)), min(255, int(66 * k)))
    return im


def add_pits(im, rng, count):
    """麻点/气孔：小暗斑 + 微弱高光边。"""
    d = ImageDraw.Draw(im, "RGBA")
    w, h = im.size
    for _ in range(count):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(0.8, 3.4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(18, 16, 14, rng.randint(90, 170)))
        if rng.random() < 0.35:
            d.arc([x - r - 1, y - r - 1, x + r + 1, y + r + 1], 150, 330,
                  fill=(150, 138, 118, 70), width=1)


def add_cracks(im, rng, count, base=(26, 23, 20)):
    """裂纹网络：折线主裂 + 分叉细裂，边缘带受光。"""
    d = ImageDraw.Draw(im, "RGBA")
    w, h = im.size
    for _ in range(count):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ang = rng.uniform(0, math.tau)
        pts = [(x, y)]
        for _ in range(rng.randint(8, 22)):
            ang += rng.uniform(-0.55, 0.55)
            step = rng.uniform(10, 34)
            x += math.cos(ang) * step
            y += math.sin(ang) * step
            pts.append((x, y))
            if not (-40 < x < w + 40 and -40 < y < h + 40):
                break
        if len(pts) < 3:
            continue
        wd = rng.randint(1, 3)
        d.line(pts, fill=base + (rng.randint(150, 220),), width=wd, joint="curve")
        # 裂纹一侧的受光唇边
        off = [(px + rng.uniform(1.0, 2.2), py + rng.uniform(-1.2, 1.2)) for px, py in pts]
        d.line(off, fill=(176, 160, 132, rng.randint(40, 90)), width=1, joint="curve")
        # 分叉
        if rng.random() < 0.6 and len(pts) > 5:
            i0 = rng.randint(2, len(pts) - 2)
            bx, by = pts[i0]
            bang = ang + rng.choice([-1, 1]) * rng.uniform(0.5, 1.2)
            bpts = [(bx, by)]
            for _ in range(rng.randint(3, 8)):
                bang += rng.uniform(-0.4, 0.4)
                bx += math.cos(bang) * rng.uniform(8, 22)
                by += math.sin(bang) * rng.uniform(8, 22)
                bpts.append((bx, by))
            d.line(bpts, fill=base + (rng.randint(110, 180),), width=1)


def chip_edges(im, rng):
    """边缘崩口：只在局部啃出小缺口（不做满幅波浪边，避免「撕纸」观感）。"""
    w, h = im.size
    mask = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(mask)
    for side in range(4):
        pos = rng.randint(0, 40)
        while pos < (w if side % 2 == 0 else h):
            seg = rng.randint(20, 70)
            if rng.random() < 0.45:
                depth = rng.randint(1, 5)
                if side == 0:
                    d.polygon([(pos, 0), (pos + seg, 0), (pos + seg // 2, depth)], fill=0)
                elif side == 2:
                    d.polygon([(pos, h), (pos + seg, h), (pos + seg // 2, h - depth)], fill=0)
                elif side == 1:
                    d.polygon([(w, pos), (w, pos + seg), (w - depth, pos + seg // 2)], fill=0)
                else:
                    d.polygon([(0, pos), (0, pos + seg), (depth, pos + seg // 2)], fill=0)
            pos += seg + rng.randint(30, 120)
    out = Image.new("RGB", (w, h), (8, 7, 6))
    out.paste(im, (0, 0), mask)
    return out


def draw_glyph_rows(canvas, cps, rng, rows, margin_frac=0.055):
    """手刻感排字：行高/基线抖动 + 逐字缩放旋转 + 8% 磨损字 + 波浪分隔线。"""
    w, h = canvas.size
    margin = int(w * margin_frac)
    avail_h = h - margin * 2
    row_h = avail_h / float(rows)
    usable_w = w - margin * 2

    text_layer = Image.new("L", (w, h), 0)
    y = margin
    seps = []
    for r in range(rows):
        this_h = row_h * rng.uniform(0.86, 1.16)
        baseline = y + this_h * rng.uniform(0.52, 0.62)
        size = max(18, int(this_h * rng.uniform(0.46, 0.60)))
        font = ImageFont.truetype(FONT_GLYPH, size)
        x = margin + rng.uniform(-4, 10)
        rng.shuffle(cps)
        i = 0
        while i < len(cps) - 8:
            n = rng.randint(2, 5)
            chunk = cps[i:i + n]
            i += n
            s = "".join(chr(c) for c in chunk)
            gw = font.getlength(s)
            if x + gw > margin + usable_w:
                break
            # 逐字渲染：各自缩放/旋转/透明度
            cx = x
            for ch in s:
                cw = font.getlength(ch)
                gsz = int(size * rng.uniform(0.80, 1.18))
                gfont = ImageFont.truetype(FONT_GLYPH, max(12, gsz))
                box = int(gsz * 1.6) + 8
                tile = Image.new("L", (box, box), 0)
                td = ImageDraw.Draw(tile)
                td.text((box // 2, box // 2), ch, font=gfont, fill=255, anchor="mm")
                ang = rng.uniform(-4.5, 4.5)
                tile = tile.rotate(ang, resample=Image.BICUBIC, expand=False)
                alpha = int(255 * (0.42 if rng.random() < 0.08 else rng.uniform(0.86, 1.0)))
                if alpha < 255:
                    tile = tile.point(lambda v, a=alpha: int(v * a / 255.0))
                gy = int(baseline - box // 2 + rng.uniform(-2.5, 2.5))
                text_layer.paste(tile, (int(cx - (box - cw) / 2), gy),
                                 tile.point(lambda v: v))
                cx += cw * rng.uniform(0.86, 1.06)
            x = cx + font.getlength(" ") * rng.uniform(1.1, 2.4)
        y += this_h
        # 分隔线：手刻波浪，不贯通全宽
        if r < rows - 1:
            yy = y - 1
            x0 = margin + rng.uniform(-6, 16)
            x1 = margin + usable_w - rng.uniform(-10, 40)
            pts = [(x, yy + math.sin((x - x0) / rng.uniform(90, 240)) * rng.uniform(0.6, 2.2))
                   for x in range(int(x0), int(x1), 3)]
            seps.append(pts)
    return text_layer, seps


def carve(canvas, text_layer):
    """阴刻 + 翻唇受光。"""
    w, h = canvas.size
    groove = text_layer.filter(ImageFilter.GaussianBlur(1.6))
    g = groove.load()

    dark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dp = dark.load()
    for y in range(h):
        for x in range(w):
            v = g[x, y]
            if v > 6:
                dp[x, y] = (10, 9, 8, min(255, int(v * 1.02)))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), dark)

    dil = text_layer.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.8)).load()
    sharp = text_layer.filter(ImageFilter.GaussianBlur(1.0)).load()
    light = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    lp = light.load()
    for y in range(h):
        for x in range(w):
            rv, sv = dil[x, y], sharp[x, y]
            if rv > sv + 18:
                lp[x, y] = (232, 220, 196, min(200, int((rv - sv) * 0.80)))
    return Image.alpha_composite(canvas, light)


def raking_light(im, mode="left"):
    """单向斜射火炬光：左侧暖亮、右下入黑；光带偏琥珀色，无矩形暗角。"""
    w, h = im.size
    grad = Image.new("L", (w, h))
    gp = grad.load()
    for y in range(h):
        fy = y / float(h)
        for x in range(w):
            fx = x / float(w)
            if mode == "left":
                v = 1.00 - 1.02 * (fx ** 0.62) - 0.42 * (fy ** 1.35)
            else:
                v = 1.00 - 1.02 * ((1 - fx) ** 0.62) - 0.42 * (fy ** 1.35)
            gp[x, y] = max(0, min(255, int(255 * (0.06 + 0.94 * max(0.0, v)))))
    mask = grad.filter(ImageFilter.GaussianBlur(2.5))
    masked = Image.composite(im, Image.new("RGB", (w, h), (0, 0, 0)), mask)
    # 暖色化：越亮越偏琥珀（2000K 火炬）
    warm = Image.new("RGB", (w, h))
    wp = warm.load()
    mp = masked.load()
    for y in range(h):
        for x in range(w):
            r, g, b = mp[x, y]
            lum = (r * 299 + g * 587 + b * 114) // 1000
            k = lum / 255.0
            wp[x, y] = (min(255, int(r * (0.92 + 0.30 * k))),
                        min(255, int(g * (0.86 + 0.20 * k))),
                        min(255, int(b * (0.74 + 0.06 * k))))
    return warm


def render(w, h, seed, rows, mode):
    rng = random.Random(seed)
    if not os.path.isfile(FONT_GLYPH):
        log("STELE ABORT font missing: " + FONT_GLYPH)
        return None
    cps = usable_codepoints(FONT_GLYPH)
    log("usable codepoints=%d" % len(cps))
    if len(cps) < 200:
        log("STELE ABORT too few glyphs")
        return None

    base = basalt(w, h, rng)
    add_pits(base, rng, count=int(w * h / 900))
    add_cracks(base, rng, count=max(5, int(w * h / 130000)))
    text_layer, seps = draw_glyph_rows(base, cps, rng, rows)
    canvas = carve(base.convert("RGBA"), text_layer)

    d = ImageDraw.Draw(canvas, "RGBA")
    for pts in seps:
        if len(pts) < 2:
            continue
        d.line(pts, fill=(118, 108, 94, 130), width=2, joint="curve")
        d.line([(px, py + 1.4) for px, py in pts], fill=(196, 182, 156, 55), width=1, joint="curve")

    canvas = canvas.convert("RGB")
    canvas = chip_edges(canvas, rng)
    canvas = raking_light(canvas, mode)

    # 细颗粒（胶片感）+ 极轻暖调
    grain = Image.effect_noise((w, h), 12).convert("L")
    canvas = Image.blend(canvas, Image.merge("RGB", (grain, grain, grain)), 0.045)
    return canvas


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--w", type=int, default=1344)
    ap.add_argument("--h", type=int, default=768)
    ap.add_argument("--seed", type=int, default=7031)
    ap.add_argument("--rows", type=int, default=11)
    ap.add_argument("--light", default="left", choices=["left", "right"])
    a = ap.parse_args(argv)
    im = render(a.w, a.h, a.seed, a.rows, a.light)
    if im is None:
        return 2
    d = os.path.dirname(os.path.abspath(a.out))
    if d:
        os.makedirs(d, exist_ok=True)
    im.save(a.out, "PNG")
    log("STELE OK %s %dx%d %dB" % (a.out, im.width, im.height, os.path.getsize(a.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
