#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图标本地合成器（biggame 图标缺口 L1 件，零云端零 token）。

CEO 2026-11-09 令：「尽量本地大模型解决，不行的才走codely」「使用本地大模型和机队的本地模型能力去调度和解决」。
出图不碰云端。分工：本机 4B 模型做美术判断（local_task.art_spec 题型 → kind/bg/fg），
本工具做像素：确定性几何合成，512×512 PNG，落产品目录 icon_512.png，可复现、零成本。

用法：
  python3 Tools/fleet/icon_render_local.py --list
  python3 Tools/fleet/icon_render_local.py --render <dir>
  python3 Tools/fleet/icon_render_local.py --render-all --spec-file cph4/fleet/game-v1/ARTEXT-<date>.json
"""

import argparse
import json
import math
import os
import sys
import time

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SW = os.path.join(ROOT, "软著申请材料")
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "game-v1")
SIZE = 512

ART = {
    "FluxVerse_FluxVerse": {"bg": ("#0B1B3A", "#1E4FD8"), "fg": "#FFD166", "kind": "tower"},
    "G02_TimeRepairShop": {"bg": ("#FFE6C7", "#FFB37A"), "fg": "#8C4A2F", "kind": "watch"},
    "G03_MergeMania": {"bg": ("#2B1055", "#7597DE"), "fg": "#FFE066", "kind": "merge"},
    "G06_ArrowRush": {"bg": ("#0F3D2E", "#2FBF71"), "fg": "#FFFFFF", "kind": "arrow"},
    "G13_我想有个农场": {"bg": ("#7FD1AE", "#2E8B57"), "fg": "#FFF6D8", "kind": "farm"},
    "P04_DemonTamer": {"bg": ("#2A0845", "#B5179E"), "fg": "#FFD6E0", "kind": "mask"},
}
FALLBACK = {"bg": ("#1B1B2F", "#3A3A6A"), "fg": "#FFB86B", "kind": "default"}
KINDS = ["tower", "watch", "merge", "arrow", "farm", "mask", "coin", "shield", "car",
         "pet", "store", "puzzle", "ghost", "crown", "bag", "food", "flower", "card",
         "fish", "gem"]


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


def star(draw, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def emblem(draw, kind, fg, S):
    c, u = S // 2, S / 512.0

    def P(pts):
        return [(c + x * u, c + y * u) for x, y in pts]

    if kind == "tower":
        draw.rounded_rectangle(P([(-58, -10), (58, 150)]), radius=18 * u, fill=fg)
        draw.ellipse(P([(-72, -96), (72, 48)]), fill=fg)
        for dx in (-150, 0, 150):
            draw.ellipse(P([(dx - 26, 132), (dx + 26, 184)]), fill=fg)
        draw.rectangle(P([(-150, 160), (150, 176)]), fill=fg)
    elif kind == "watch":
        draw.ellipse(P([(-140, -140), (140, 140)]), outline=fg, width=int(26 * u))
        draw.ellipse(P([(-18, -18), (18, 18)]), fill=fg)
        draw.line(P([(0, 0), (0, -96)]), fill=fg, width=int(20 * u))
        draw.line(P([(0, 0), (70, 34)]), fill=fg, width=int(20 * u))
        draw.rounded_rectangle(P([(-34, -196), (34, -150)]), radius=10 * u, fill=fg)
    elif kind == "merge":
        draw.ellipse(P([(-150, -40), (-10, 100)]), fill=fg)
        draw.ellipse(P([(10, -40), (150, 100)]), fill=fg)
        star(draw, c, c - 120 * u, 92 * u, fg)
    elif kind == "arrow":
        draw.polygon(P([(-170, -34), (10, -34), (10, -96), (170, 0),
                        (10, 96), (10, 34), (-170, 34)]), fill=fg)
        for y in (-96, 96):
            draw.rounded_rectangle(P([(-210, y - 12), (-120, y + 12)]), radius=10 * u, fill=fg)
    elif kind == "farm":
        draw.polygon(P([(-150, 10), (0, -120), (150, 10)]), fill=fg)
        draw.rectangle(P([(-100, 10), (100, 140)]), fill=fg)
        draw.rounded_rectangle(P([(-30, 60), (30, 140)]), radius=8 * u, fill=(0, 0, 0, 0))
        draw.ellipse(P([(70, -170), (176, -64)]), fill=fg)
    elif kind == "mask":
        draw.ellipse(P([(-120, -60), (120, 170)]), fill=fg)
        draw.polygon(P([(-118, -40), (-180, -170), (-60, -96)]), fill=fg)
        draw.polygon(P([(118, -40), (180, -170), (60, -96)]), fill=fg)
    elif kind == "coin":
        draw.ellipse(P([(-140, -140), (140, 140)]), fill=fg)
        draw.ellipse(P([(-92, -92), (92, 92)]), fill=(0, 0, 0, 0))
        draw.ellipse(P([(-64, -64), (64, 64)]), fill=fg)
    elif kind == "shield":
        draw.polygon(P([(-120, -110), (120, -110), (120, 30), (0, 160), (-120, 30)]), fill=fg)
        draw.polygon(P([(-64, -46), (64, -46), (64, 16), (0, 92), (-64, 16)]), fill=(0, 0, 0, 0))
    elif kind == "car":
        draw.rounded_rectangle(P([(-170, -10), (170, 70)]), radius=26 * u, fill=fg)
        draw.rounded_rectangle(P([(-96, -92), (96, 0)]), radius=30 * u, fill=fg)
        draw.ellipse(P([(-128, 40), (-56, 112)]), fill=fg)
        draw.ellipse(P([(56, 40), (128, 112)]), fill=fg)
        draw.ellipse(P([(-104, 64), (-80, 88)]), fill=(0, 0, 0, 0))
        draw.ellipse(P([(80, 64), (104, 88)]), fill=(0, 0, 0, 0))
    elif kind == "pet":
        draw.polygon(P([(-118, -60), (-150, -170), (-56, -110)]), fill=fg)
        draw.polygon(P([(118, -60), (150, -170), (56, -110)]), fill=fg)
        draw.ellipse(P([(-124, -86), (124, 150)]), fill=fg)
        draw.ellipse(P([(-58, -10), (-22, 26)]), fill=(0, 0, 0, 0))
        draw.ellipse(P([(22, -10), (58, 26)]), fill=(0, 0, 0, 0))
        draw.ellipse(P([(-24, 56), (24, 104)]), fill=(0, 0, 0, 0))
    elif kind == "store":
        draw.rectangle(P([(-140, -20), (140, 120)]), fill=fg)
        draw.rounded_rectangle(P([(-160, -110), (160, -20)]), radius=12 * u, fill=fg)
        for i in range(-160, 161, 80):
            draw.polygon(P([(i, 0), (i + 40, 0), (i + 20, 60), (i - 20, 60)]), fill=(0, 0, 0, 0))
        draw.rectangle(P([(-52, 40), (52, 120)]), fill=(0, 0, 0, 0))
    elif kind == "puzzle":
        draw.rounded_rectangle(P([(-130, -130), (130, 130)]), radius=22 * u, fill=fg)
        draw.ellipse(P([(92, -34), (168, 42)]), fill=fg)
        draw.ellipse(P([(-42, 92), (34, 168)]), fill=(0, 0, 0, 0))
        draw.rounded_rectangle(P([(-56, -56), (56, 56)]), radius=14 * u, fill=(0, 0, 0, 0))
    elif kind == "ghost":
        draw.ellipse(P([(-130, -150), (130, 110)]), fill=fg)
        draw.polygon(P([(-130, -20), (130, -20), (130, 130), (78, 86),
                        (26, 130), (-26, 86), (-78, 130), (-130, 86)]), fill=fg)
        draw.ellipse(P([(-72, -70), (-28, -26)]), fill=(0, 0, 0, 0))
        draw.ellipse(P([(28, -70), (72, -26)]), fill=(0, 0, 0, 0))
    elif kind == "crown":
        draw.polygon(P([(-150, 100), (-150, -60), (-80, 10), (0, -130),
                        (80, 10), (150, -60), (150, 100)]), fill=fg)
        draw.rounded_rectangle(P([(-150, 116), (150, 160)]), radius=12 * u, fill=fg)
    elif kind == "bag":
        draw.arc(P([(-58, -170), (58, -76)]), start=200, end=340, fill=fg, width=int(24 * u))
        draw.rounded_rectangle(P([(-124, -78), (124, 140)]), radius=26 * u, fill=fg)
        draw.rounded_rectangle(P([(-100, -40), (100, 34)]), radius=14 * u, fill=(0, 0, 0, 0))
    elif kind == "food":
        draw.pieslice(P([(-150, -40), (150, 200)]), start=0, end=180, fill=fg)
        draw.rounded_rectangle(P([(-60, 96), (60, 130)]), radius=10 * u, fill=fg)
        for dx in (-56, 0, 56):
            draw.arc(P([(dx - 26, -170), (dx + 26, -70)]), start=200, end=340,
                     fill=fg, width=int(14 * u))
    elif kind == "flower":
        for i in range(5):
            ang = -math.pi / 2 + i * 2 * math.pi / 5
            cx, cy = 92 * math.cos(ang), 92 * math.sin(ang)
            draw.ellipse(P([(cx - 62, cy - 62), (cx + 62, cy + 62)]), fill=fg)
        draw.ellipse(P([(-42, -42), (42, 42)]), fill=(0, 0, 0, 0))
    elif kind == "card":
        for dx, dy in ((-56, 34), (-28, 17), (0, 0)):
            draw.rounded_rectangle(P([(dx - 96, dy - 128), (dx + 96, dy + 128)]),
                                   radius=18 * u, outline=fg, width=int(16 * u))
        draw.ellipse(P([(-34, -34), (34, 34)]), fill=fg)
    elif kind == "fish":
        draw.ellipse(P([(-170, -86), (70, 86)]), fill=fg)
        draw.polygon(P([(50, 0), (176, -96), (176, 96)]), fill=fg)
        draw.ellipse(P([(-124, -22), (-92, 10)]), fill=(0, 0, 0, 0))
    elif kind == "gem":
        draw.polygon(P([(0, -170), (150, -20), (0, 170), (-150, -20)]), fill=fg)
        draw.polygon(P([(0, -80), (74, -20), (0, 74), (-74, -20)]), fill=(0, 0, 0, 0))
    else:
        draw.ellipse(P([(-130, -130), (130, 130)]), fill=fg)
        draw.ellipse(P([(-58, -58), (58, 58)]), fill=(0, 0, 0, 0))


def render(target_dir, override=None):
    specs = dict(ART)
    if override:
        specs.update(override)
    spec = specs.get(target_dir, FALLBACK)
    size = SIZE
    bg = gradient(size, hex2rgb(spec["bg"][0]), hex2rgb(spec["bg"][1]))
    glow = Image.new("L", (size, size), 0)
    ImageDraw.Draw(glow).ellipse([-size * 0.3, -size * 0.6, size * 1.3, size * 0.55], fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(size // 12))
    bg = Image.composite(Image.new("RGB", (size, size), (255, 255, 255)), bg, glow)
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fg = hex2rgb(spec["fg"]) + (255,)
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
    ap.add_argument("--spec-file", help="icon_art_director 产出的 ARTEXT-*.json，逐款覆盖 ART")
    a = ap.parse_args(argv)
    override = {}
    if a.spec_file and os.path.exists(a.spec_file):
        data = json.load(open(a.spec_file, encoding="utf-8"))
        for k, v in (data.get("items") or {}).items():
            if isinstance(v, dict) and v.get("kind") in KINDS:
                override[k] = {"bg": list(v["bg"]), "fg": v["fg"], "kind": v["kind"]}
    if a.list:
        for k, v in ART.items():
            print(" %-28s %s %s" % (k, v["kind"], v["bg"]))
        print(" kinds:", ",".join(KINDS))
        return 0
    if a.render:
        targets = [a.render]
    elif a.render_all:
        targets = sorted(set(ART) | set(override))
    else:
        print(__doc__)
        return 1
    made = []
    for t in targets:
        p = render(t, override)
        made.append({"dir": t, "path": os.path.relpath(p, ROOT),
                     "spec": "override" if t in override else ("registered" if t in ART else "fallback"),
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
