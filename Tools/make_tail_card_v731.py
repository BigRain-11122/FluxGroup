# -*- coding: utf-8 -*-
"""make_tail_card_v731.py - end card built on REAL cuneiform glyphs.

Replaces the tail shot whose carved marks were pseudo-patterns (the only item the
文字设计 seat kept failing). Composition: basalt ground + a band of genuine Unicode
Cuneiform signs (rendered by Tools/mv_cuneiform.py) + the CEO-ordered credit line.

Output: tail_card_v731.png at 1344x768 (the 24fps master canvas; 4K comes by upscale).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mv_cuneiform import render_band, stone, SEQUENCE, assert_real_cuneiform  # noqa: E402

W, H = 1344, 768
BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
CUN_DIR = r"D:\FluxGroup\cph4\fleet\mv0001-handover\canon\cuneiform"
SUB_GOLD = (199, 177, 131)
TAIL_TEXT = "转载需注明出处 @大喵没鱼吃"
FONTS = [r"C:\Windows\Fonts\NotoSerifCJKsc-Black.otf",
         r"C:\Windows\Fonts\SourceHanSerifSC-Heavy.otf",
         r"C:\Windows\Fonts\SourceHanSerifSC-Bold.otf",
         r"C:\Windows\Fonts\simsun.ttc"]


def cjk(size):
    for p in FONTS:
        if os.path.isfile(p):
            return ImageFont.truetype(p, size)
    raise SystemExit("no CJK font")


def tracked_width(text, size, track):
    return int(size * len(text) + size * track * (len(text) - 1))


def draw_tracked(d, text, x, y, size, track, fill):
    step = size + int(size * track)
    f = cjk(size)
    cx = x
    for ch in text:
        d.text((cx, y), ch, font=f, fill=fill)
        cx += step


def build(out):
    card = stone(W, H)
    # vignette
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.35, -H * 0.45, W * 1.35, H * 1.45], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGB", (W, H), (8, 7, 6))
    card.paste(dark, (0, 0), vig.point(lambda v: int((255 - v) * 0.75)))

    # real cuneiform band, feathered into the stone so it does not read as a pasted panel
    band_path = os.path.join(CUN_DIR, "_band_card.png")
    render_band(band_path, 1000, 240, count=9)
    band = Image.open(band_path).convert("RGB")
    bx, by = (W - 1000) // 2, int(H * 0.30)
    bm = Image.new("L", (1000, 240), 0)
    ImageDraw.Draw(bm).rectangle([0, 0, 999, 239], fill=255)
    bm = bm.filter(ImageFilter.GaussianBlur(46))
    card.paste(band, (bx, by), bm)
    d = ImageDraw.Draw(card, "RGBA")
    d.line([(W // 2 - 470, by + 20), (W // 2 - 470, by + 220)],
           fill=(120, 108, 92, 55), width=2)
    d.line([(W // 2 + 470, by + 20), (W // 2 + 470, by + 220)],
           fill=(120, 108, 92, 55), width=2)

    # hairline rule + credit line
    d.line([(W // 2 - 250, by + 300), (W // 2 + 250, by + 300)],
           fill=(150, 136, 116, 90), width=1)
    size, track = 26, 0.25
    tw = tracked_width(TAIL_TEXT, size, track)
    tx = (W - tw) // 2
    ty = by + 330
    # soft pad so the line stays readable on stone
    pad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(pad).rectangle([tx - 40, ty - 10, tx + tw + 40, ty + size + 14],
                                 fill=(0, 0, 0, 150))
    card.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0),
               pad.filter(ImageFilter.GaussianBlur(14)).getchannel("A"))
    draw_tracked(d, TAIL_TEXT, tx, ty, size, track, SUB_GOLD + (235,))

    card.save(out)
    print("TAILCARD %s %dx%d text=%r signs=%d" % (out, W, H, TAIL_TEXT, 9))
    return out


def self_test():
    assert_real_cuneiform(SEQUENCE[:9])
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "tailcard_selftest.png")
    build(tmp)
    g = Image.open(tmp).convert("L")
    lo, hi = g.getextrema()
    ok = (hi - lo) > 100
    print("PASS  card has content and carve contrast" if ok else "FAIL  flat card")
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CUN_DIR, "tail_card_v731.png")
    build(out)
