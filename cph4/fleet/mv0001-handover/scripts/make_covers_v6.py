# -*- coding: utf-8 -*-
"""make_covers_v6.py — 30s v6 封面帧（16:9 + 9:16）。

选题律（PUBLISH-CHECKLIST §三）：封面禁用 AI 侧脸；本片可选
  A = 28.6s 博物馆剪影（无脸、氛围位）
  B = 23.2s 真楔文石板（记忆点位，本片差异化资产）
排版律：琥珀金衬线 + 字距 + 细金线，禁综艺花字/描边发光。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v6-优化版.mp4"
FRAMES = r"K:\Fluxgroup\.codely-cli\tmp\v6check"
OUT = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\publish-v6"
FONT = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FONT_SANS = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

AMBER = (233, 200, 138)
AMBER_DIM = (196, 168, 122)


def spacing_text(draw, xy, text, font, fill, spacing, anchor_left=True):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + spacing
    return x


def text_width(font, text, spacing):
    return sum(font.getlength(c) for c in text) + spacing * (len(text) - 1)


def shade(im, box, strength=0.62, blur=140):
    """局部压暗，保证字可读（不用硬色块）。"""
    w, h = im.size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=int(255 * strength))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(dark, im, m)


def build(frame_path, out_base, title_xy, title_size, sub_xy, sub_size, layout, strength=0.58):
    im = Image.open(frame_path).convert("RGB")
    if layout == "16x9":
        W, H = 1920, 1097
        im = im.resize((W, H), Image.LANCZOS)
        box = (0, 0, int(W * 0.62), int(H * 0.42)) if title_xy[1] < H // 2 else \
              (0, int(H * 0.58), int(W * 0.62), H)
    else:
        # 9:16 中心裁切
        W, H = 1080, 1920
        sw, sh = im.size
        target = W / float(H)
        cw = int(sh * target)
        x0 = (sw - cw) // 2
        im = im.crop((x0, 0, x0 + cw, sh)).resize((W, H), Image.LANCZOS)
        box = (0, int(H * 0.60), W, H)

    im = shade(im, box, strength, 120 if layout == "16x9" else 90)

    d = ImageDraw.Draw(im)
    f_title = ImageFont.truetype(FONT, title_size)
    f_sub = ImageFont.truetype(FONT_SANS, sub_size)

    # 主标题（字距 8）
    spacing_text(d, title_xy, "爱在西元前", f_title, AMBER, title_size * 0.16)

    # 细金线
    tw = text_width(f_title, "爱在西元前", title_size * 0.16)
    ly = title_xy[1] + title_size * 1.42
    d.line([(title_xy[0], ly), (title_xy[0] + min(tw, 420), ly)], fill=AMBER_DIM, width=2)

    # 副题
    spacing_text(d, sub_xy, "AI 二创 · 30s", f_sub, (206, 186, 156), sub_size * 0.14)

    p = "%s-%s.jpg" % (out_base, layout)
    im.save(p, "JPEG", quality=92)
    print("COVER %s %dx%d %dKB" % (p, im.width, im.height, os.path.getsize(p) // 1024))
    return p


os.makedirs(OUT, exist_ok=True)
a = os.path.join(FRAMES, "cover_museum.png")
b = os.path.join(FRAMES, "cover_tablet.png")
for src, dst in ((a, "cover_museum.png"), (b, "cover_tablet.png")):
    if not os.path.exists(src):
        raise SystemExit("FATAL missing frame: " + src)

build(a, os.path.join(OUT, "cover-A-museum"), (150, 130), 104, (152, 130 + 104 * 1.42 + 26), 30, "16x9", 0.60)
build(b, os.path.join(OUT, "cover-B-tablet"), (150, 130), 104, (152, 130 + 104 * 1.42 + 26), 30, "16x9", 0.78)
build(a, os.path.join(OUT, "cover-A-museum"), (78, 1180), 92, (80, 1180 + 92 * 1.42 + 24), 28, "9x16", 0.62)
build(b, os.path.join(OUT, "cover-B-tablet"), (78, 1180), 92, (80, 1180 + 92 * 1.42 + 24), 28, "9x16", 0.78)
