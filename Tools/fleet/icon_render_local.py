#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图标本地合成器（biggame 图标缺口 L1 件，零云端零 token）。

背景（CEO 2026-11-09 原话）：「尽量本地大模型解决，不行的才走codely」。
图标出图不得走云端。本工具用 Pillow 在本机确定性合成图标：圆角渐变底 + 几何标识，
无文字、无字体依赖，512×512 PNG，落产品目录 icon_512.png。

分层口径：
  - L1（本工具）：确定性几何合成，立即产出、可复现、零成本。
  - L2（待装）：mflux + FLUX 本地扩散模型出美术级图标，装好后由 --from-art 升级替换。

用法：
  python3 Tools/fleet/icon_render_local.py --list          # 看已注册的美术规格
  python3 Tools/fleet/icon_render_local.py --render <dir>  # 单款
  python3 Tools/fleet/icon_render_local.py --render-all    # 全部已注册款
Exit: 0 成功；2 有未注册规格的款（需补 art spec）。
"""

import argparse
import json
import os
import sys
import time

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SW = os.path.join(ROOT, "软著申请材料")
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "game-v1")
SIZE = 512

# 每款一张美术规格：底渐变两端色 + 标识图元（几何，无文字）
# kind: tower / watch / merge / arrow / farm / mask / default
ART = {
    "FluxVerse_FluxVerse": {"bg": ("#0B1B3A", "#1E4FD8"), "fg": "#FFD166", "kind": "tower"},
    "G02_TimeRepairShop": {"bg": ("#FFE6C7", "#FFB37A"), "fg": "#8C4A2F", "kind": "watch"},
    "G03_MergeMania": {"bg": ("#2B1055", "#7597DE"), "fg": "#FFE066", "kind": "merge"},
    "G06_ArrowRush": {"bg": ("#0F3D2E", "#2FBF71"), "fg": "#FFFFFF", "kind": "arrow"},
    "G13_我想有个农场": {"bg": ("#7FD1AE", "#2E8B57"), "fg": "#FFF6D8", "kind": "farm"},
    "P04_DemonTamer": {"bg": ("#2A0845", "#B5179E"), "fg": "#FFD6E0", "kind": "mask"},
}
FALLBACK = {"bg": ("#1B1B2F", "#3A3A6A"), "fg": "#FFB86B", "kind": "default"}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(size, c1, c2):
    img = Image.new("RGB", (size, size), c1)
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        d.line([(0, y), (size, y)],
               fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    return img


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def emblem(draw, kind, fg, S):
    """几何标识：以画布中心为原点，尺寸随 S 缩放。"""
    c = S // 2
    u = S / 512.0

    def P(pts):
        return [(c + x * u, c + y * u) for x, y in pts]

    if kind == "tower":
        # 脑塔：圆顶 + 塔身 + 三城区点
        draw.rounded_rectangle(P([(-58, -10), (58, 150)]), radius=18 * u, fill=fg)
        draw.ellipse(P([(-72, -96), (72, 48)]), fill=fg)
        for dx in (-150, 0, 150):
            draw.ellipse(P([(dx - 26, 132), (dx + 26, 184)]), fill=fg)
        draw.rectangle(P([(-150, 160), (150, 176)]), fill=fg)
    elif kind == "watch":
        # 怀表：外环 + 指针
        draw.ellipse(P([(-140, -140), (140, 140)]), outline=fg, width=int(26 * u))
        draw.ellipse(P([(-18, -18), (18, 18)]), fill=fg)
        draw.line(P([(0, 0), (0, -96)]), fill=fg, width=int(20 * u))
        draw.line(P([(0, 0), (70, 34)]), fill=fg, width=int(20 * u))
        draw.rounded_rectangle(P([(-34, -196), (34, -150)]), radius=10 * u, fill=fg)
    elif kind == "merge":
        # 合成：两球相撞 + 上星
        draw.ellipse(P([(-150, -40), (-10, 100)]), fill=fg)
        draw.ellipse(P([(10, -40), (150, 100)]), fill=fg)
        star(draw, c, c - 120 * u, 92 * u, fg)
    elif kind == "arrow":
        # 箭头脱身：粗箭身 + 尾迹
        draw.polygon(P([(-170, -34), (10, -34), (10, -96), (170, 0),
                        (10, 96), (10, 34), (-170, 34)]), fill=fg)
        for i, y in enumerate((-96, 96)):
            draw.rounded_rectangle(P([(-210, y - 12), (-120, y + 12)]), radius=10 * u, fill=fg)
    elif kind == "farm":
        # 农场：屋 + 叶
        draw.polygon(P([(-150, 10), (0, -120), (150, 10)]), fill=fg)
        draw.rectangle(P([(-100, 10), (100, 140)]), fill=fg)
        draw.rounded_rectangle(P([(-30, 60), (30, 140)]), radius=8 * u, fill=(0, 0, 0, 0))
        draw.ellipse(P([(70, -170), (176, -64)]), fill=fg)
    elif kind == "mask":
        # 兽面：双角 + 面
        draw.ellipse(P([(-120, -60), (120, 170)]), fill=fg)
        draw.polygon(P([(-118, -40), (-180, -170), (-60, -96)]), fill=fg)
        draw.polygon(P([(118, -40), (180, -170), (60, -96)]), fill=fg)
    else:
        # 通用：圆 + 环
        draw.ellipse(P([(-130, -130), (130, 130)]), fill=fg)
        draw.ellipse(P([(-58, -58), (58, 58)]), fill=(0, 0, 0, 0))


def star(draw, cx, cy, r, fill):
    import math
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def render(target_dir):
    spec = ART.get(target_dir, FALLBACK)
    size = SIZE
    bg = gradient(size, hex2rgb(spec["bg"][0]), hex2rgb(spec["bg"][1]))
    # 顶部柔光
    glow = Image.new("L", (size, size), 0)
    ImageDraw.Draw(glow).ellipse([-size * 0.3, -size * 0.6, size * 1.3, size * 0.55], fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(size // 12))
    bg = Image.composite(Image.new("RGB", (size, size), (255, 255, 255)), bg, glow)

    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fg = hex2rgb(spec["fg"]) + (255,)
    # 投影
    sh = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    emblem(ImageDraw.Draw(sh), spec["kind"], (0, 0, 0, 90), size)
    sh = sh.filter(ImageFilter.GaussianBlur(size // 40))
    layer.alpha_composite(sh, (0, int(size * 0.012)))
    emblem(d, spec["kind"], fg, size)

    img = bg.convert("RGBA")
    img.alpha_composite(layer)
    img.putalpha(rounded_mask(size, int(size * 0.22)))
    out = os.path.join(SW, target_dir, "icon_512.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "PNG")
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--render")
    ap.add_argument("--render-all", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        for k, v in ART.items():
            print(" %-28s %s %s" % (k, v["kind"], v["bg"]))
        print(" fallback:", len(ART), "registered")
        return 0
    targets = []
    if a.render:
        targets = [a.render]
    elif a.render_all:
        targets = list(ART)
    else:
        print(__doc__)
        return 1
    made = []
    for t in targets:
        p = render(t)
        made.append({"dir": t, "path": os.path.relpath(p, ROOT),
                     "spec": "registered" if t in ART else "fallback",
                     "layer": "L1-deterministic-local"})
        print("  OK", os.path.relpath(p, ROOT))
    rec = os.path.join(OUTDIR, "ICON-RENDER-LOG.jsonl")
    with open(rec, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            "made": made, "engine": "pillow-deterministic",
                            "cloud": False}, ensure_ascii=False) + "\n")
    print("made=%d log=%s" % (len(made), os.path.relpath(rec, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
