#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_cuneiform_shot.py — 用真楔文纹理合成「石碑特写」关键帧（v731 替换镜）。

为什么纯合成而不走文生图：v730 的病根正是模型把字画成伪纹样。把真字表渲染成纹理后
**直接贴在石板几何上**，才能保证字形不被重新"创作"。光影/颗粒/边缘由程序加，
与全片 tw90s_noir grade 对齐（暖橙侧光 +  crushed black + 胶片颗粒）。

用法：
  python Tools/mv_cuneiform_shot.py --tex media/mv0001-handover/v731/cuneiform-tablet.png \
      --out media/mv0001-handover/v731/KF-E05-stele.png [--w 1344 --h 768] [--seed 7331]
输出：KF PNG（1344×768），并写同名 .meta.json 记录参数。
"""
import argparse
import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def warp_slab(tex, w, h, rng):
    """从纹理里**原生分辨率**裁一块贴成石板面。

    首跑判例：用逐列缩放做伪透视 → 笔画被重采样糊成一片，凿刻结构全丢。
    宁可少一点"透视感"，也不能动字形——字形真实是本镜存在的唯一理由。
    """
    # 目标块（留边给暗部与光衰）
    slab_w, slab_h = int(w * 0.86), int(h * 0.90)
    if tex.width >= slab_w and tex.height >= slab_h:
        left = (tex.width - slab_w) // 2
        top = int((tex.height - slab_h) * 0.30)
        t = tex.crop((left, top, left + slab_w, top + slab_h))
    else:  # 纹理不够大才放大（并保持锐度）
        t = tex.resize((slab_w, slab_h), Image.LANCZOS)
    # 局部对比拉满：阴刻才读得出
    t = ImageEnhance.Contrast(t).enhance(1.55).convert("RGB")
    return t


def perspective(img, quad, size):
    """四点透视变换（纯 PIL：用逐列/逐行线性插值的近似，够用且无 numpy 依赖风险）。"""
    # 简化：用仿射近似（左右各向内收一点），比真透视稳定且不会撕裂
    w, h = size
    out = Image.new("RGB", (w, h), (18, 16, 14))
    ox, oy = (img.width - w) // 2, (img.height - h) // 2
    for x in range(w):
        # 竖直方向按 x 做细微缩放，制造"面朝右"的错觉
        k = 1.0 - 0.035 * (x / float(w))
        col = img.crop((max(0, ox + x), max(0, oy), max(0, ox + x + 1), img.height))
        col = col.resize((1, max(1, int(h * k))), Image.BILINEAR)
        out.paste(col, (x, (h - col.height) // 2))
    return out


def torch_light(img, w, h):
    """暖橙侧光（左上强）+ 右侧压暗 + crushed black。"""
    light = Image.new("L", (w, h))
    lp = light.load()
    for y in range(h):
        for x in range(w):
            dx = x / float(w)
            dy = y / float(h)
            d = ((dx - 0.18) ** 2 + (dy - 0.30) ** 2) ** 0.5
            v = max(0.0, 1.0 - d * 1.55)
            lp[x, y] = int(255 * (0.16 + 0.84 * v ** 1.35))
    light = light.filter(ImageFilter.GaussianBlur(w // 60))
    rgb = img.convert("RGB")
    # 光色：暖橙只做轻微染色（首跑判例：40/255 的暖色混合把对比洗平，字就看不清了）
    r, g, b = rgb.split()
    rgb = Image.merge("RGB", (
        r.point(lambda v: min(255, int(v * 1.06))),
        g.point(lambda v: int(v * 0.97)),
        b.point(lambda v: int(v * 0.86)),
    ))
    lit = Image.composite(rgb, Image.new("RGB", (w, h), (9, 8, 7)), light)
    lit = ImageEnhance.Contrast(lit).enhance(1.22)
    lit = ImageEnhance.Color(lit).enhance(0.92)
    return lit


def grain_and_vignette(img, w, h, rng):
    noise = Image.effect_noise((w, h), 20).convert("L")
    img = Image.blend(img, Image.merge("RGB", (noise, noise, noise)), 0.055)
    vig = Image.new("L", (w, h))
    vp = vig.load()
    for y in range(h):
        for x in range(w):
            dx = (x / float(w) - 0.5) * 2.0
            dy = (y / float(h) - 0.5) * 2.0
            r = (dx * dx + dy * dy) ** 0.5
            vp[x, y] = max(0, int(255 * (1.0 - max(0.0, r - 0.62) * 1.5)))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, dark, vig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--w", type=int, default=1344)
    ap.add_argument("--h", type=int, default=768)
    ap.add_argument("--seed", type=int, default=7331)
    a = ap.parse_args(argv)
    if not os.path.isfile(a.tex):
        print("SHOT ABORT tex missing")
        return 2
    rng = random.Random(a.seed)
    tex = Image.open(a.tex).convert("RGB")
    slab = warp_slab(tex, a.w, a.h, rng)
    canvas = Image.new("RGB", (a.w, a.h), (10, 9, 8))
    canvas.paste(slab, ((a.w - slab.width) // 2, (a.h - slab.height) // 2))
    canvas = torch_light(canvas, a.w, a.h)
    canvas = grain_and_vignette(canvas, a.w, a.h, rng)
    canvas = canvas.filter(ImageFilter.UnsharpMask(radius=1.6, percent=45, threshold=3))
    d = os.path.dirname(os.path.abspath(a.out))
    if d:
        os.makedirs(d, exist_ok=True)
    canvas.save(a.out, "PNG")
    meta = {"tex": os.path.relpath(a.tex, ROOT).replace("\\", "/"), "w": a.w, "h": a.h,
            "seed": a.seed, "grade": "tw90s_noir / torch-left", "tool": "mv_cuneiform_shot"}
    json.dump(meta, open(os.path.splitext(a.out)[0] + ".meta.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("SHOT OK %s %dx%d %dB" % (a.out, canvas.width, canvas.height, os.path.getsize(a.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
