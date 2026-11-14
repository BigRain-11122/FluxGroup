# -*- coding: utf-8 -*-
"""mv_cuneiform.py - render REAL cuneiform glyph forms (not decorative squiggles).

Why: the 文字设计 seat failed v729/v730 on one item only - the carved marks on the
stele and the tail tablet are pseudo-patterns, i.e. decorative incisions that only
look like writing. This renders actual signs from the Unicode Cuneiform block
(U+12000-U+1254F) with Segoe UI Historic, which carries genuine sign forms, and
embosses them so they read as cut into stone.

Honesty note: the glyph FORMS are authentic; the sequence is NOT a verified
translation, so no caption here claims a reading.

Usage:
  py Tools/mv_cuneiform.py --band  out_band_1x.png --w 1200 --h 160
  py Tools/mv_cuneiform.py --band  out_band_4x.png --w 3600 --h 480
  py Tools/mv_cuneiform.py --self-test
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = r"C:\Windows\Fonts\seguihis.ttf"
CUNEIFORM_LO, CUNEIFORM_HI = 0x12000, 0x1254F

# A spread of real signs (A, AS, BA, DA, EN, GAL, KU, LUGAL, ME, NIN, SAR, UD ...).
SEQUENCE = [0x12000, 0x12020, 0x12039, 0x12049, 0x12060, 0x1208B,
            0x120F0, 0x12220, 0x1223F, 0x12269, 0x1228B, 0x1230D,
            0x12313, 0x12362, 0x12399, 0x12400]


def assert_real_cuneiform(cps):
    bad = [c for c in cps if not (CUNEIFORM_LO <= c <= CUNEIFORM_HI)]
    if bad:
        raise SystemExit("non-cuneiform codepoint(s): %s" % ["U+%04X" % c for c in bad])
    return True


def stone(w, h):
    """Dark basalt-ish ground so the band drops onto the stele / tablet."""
    img = Image.new("RGB", (w, h), (26, 24, 22))
    px = img.load()
    import random
    rnd = random.Random(20261114)
    for y in range(h):
        band = 0.85 + 0.3 * (y / float(h))
        for x in range(w):
            n = rnd.gauss(0, 4.5)
            v = int(max(0, min(255, (24 + n) * band)))
            px[x, y] = (v, int(v * 0.96), int(v * 0.90))
    return img.filter(ImageFilter.GaussianBlur(0.6))


def render_band(out, w, h, count=None, margin_ratio=0.06):
    cps = SEQUENCE[:count] if count else SEQUENCE
    assert_real_cuneiform(cps)
    img = stone(w, h)
    draw = ImageDraw.Draw(img)

    # fit the signs to the band: pick the largest size that still leaves margins.
    # An inscription line reads at 8-10 signs, not 16 crushed ones (first pass shrank
    # to 25px on a 1200px band and the carve test failed).
    size = int(h * 0.72)
    inner = int(w * (1 - 2 * margin_ratio))
    while size > 8:
        f = ImageFont.truetype(FONT, size)
        widths = [f.getbbox(chr(c))[2] for c in cps]
        total = sum(widths) + int(size * 0.30) * (len(cps) - 1)
        if total <= inner:
            break
        size = int(size * 0.94)
    f = ImageFont.truetype(FONT, size)
    gap = int(size * 0.30)

    widths = [f.getbbox(chr(c))[2] for c in cps]
    total = sum(widths) + gap * (len(cps) - 1)
    x = (w - total) // 2
    y = (h - size) // 2 - int(size * 0.06)

    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    for c, cw in zip(cps, widths):
        md.text((x, y), chr(c), font=f, fill=255)
        x += cw + gap
    # clay-tablet weight: the font draws thin outlines at these sizes; one dilation
    # pass reads as a pressed wedge rather than a hairline drawing
    mask = mask.filter(ImageFilter.MaxFilter(3 if size < 90 else 5))

    # incised look: dark lip below-right, lit lip above-left, then the groove itself
    lit = Image.new("RGB", (w, h), (188, 176, 154))
    img.paste(lit, (-2, -2), mask.filter(ImageFilter.GaussianBlur(1.5)).point(
        lambda v: int(v * 0.70)))
    dark = Image.new("RGB", (w, h), (4, 4, 4))
    shifted = Image.new("L", (w, h), 0)
    shifted.paste(mask.filter(ImageFilter.GaussianBlur(1.3)), (2, 3))
    img.paste(dark, (0, 0), shifted.point(lambda v: int(v * 0.85)))
    groove = Image.new("RGB", (w, h), (86, 77, 64))
    img.paste(groove, (0, 0), mask.point(lambda v: int(v * 0.80)))

    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    img.save(out)
    print("BAND %s %dx%d signs=%d size=%dpx" % (out, w, h, len(cps), size))
    return out


def self_test():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("PASS  " if cond else "FAIL  ") + name)

    check("all sequence codepoints are real cuneiform", assert_real_cuneiform(SEQUENCE))
    try:
        assert_real_cuneiform([0x41, 0x12220])
        check("latin letter is rejected", False)
    except SystemExit:
        check("latin letter is rejected", True)
    # a rendered band must contain real ink, not a flat stone plate
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "cun_selftest.png")
    render_band(tmp, 600, 120, count=6)
    g = Image.open(tmp).convert("L")
    lo, hi = g.getextrema()
    check("band has carved contrast", (hi - lo) > 60)
    check("font carries the glyphs", ImageFont.truetype(FONT, 40).getbbox("\U00012220")[2] > 10)
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", default="")
    ap.add_argument("--w", type=int, default=1200)
    ap.add_argument("--h", type=int, default=160)
    ap.add_argument("--count", type=int, default=9)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.band:
        ap.error("--band <out.png> required")
    render_band(a.band, a.w, a.h, a.count or None)


if __name__ == "__main__":
    sys.exit(main())
