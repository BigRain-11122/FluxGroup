# -*- coding: utf-8 -*-
"""Title card v2 for mv0001「愛在西元前」(2026-11-05).

Composition facts from the real opening frames: the man sits left-centre, the desk lamp
owns the upper right, and the right third is dark wall — so the type lives there, right
aligned, with wide tracking. Warm paper white (not pure white) so it belongs to the
tungsten scene; two offset shadows fake a soft film drop; a hairline rule ties the block.

v2 changes after reviewing the composite: title 104 -> 118 with tracking 14 -> 20, the block
lifted 32px to balance the lamp, and the credit list gained 演唱 周杰倫 (a full opening
credit block: 作詞 / 作曲 / 演唱).
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
OUT = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "canon", "title-design")
W, H = 1920, 1096

TITLE = "愛在西元前"
CREDITS = [("作詞", "方文山"), ("作曲", "周杰倫"), ("演唱", "周杰倫")]

FONT_SERIF = r"C:\Windows\Fonts\simsun.ttc"
FONT_SANS = r"C:\Windows\Fonts\msyh.ttc"

INK = (242, 237, 228, 255)
SHADOW = (12, 8, 4, 150)
DIM = (232, 226, 214, 205)
ROLE = (219, 211, 197, 165)

RIGHT_MARGIN = 132
TITLE_SIZE = 118
TITLE_TRACK = 20
TITLE_Y = 372
RULE_OFFSET = 168
CREDITS_Y = 214
CREDIT_GAP = 54


def spaced(draw, xy, text, font, fill, tracking=0):
    x, y = xy
    widths = []
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        widths.append(bbox[2] - bbox[0])
    total = sum(widths) + tracking * (len(text) - 1)
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def build(out_name="title-v2.png"):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(FONT_SERIF, TITLE_SIZE)
    f_role = ImageFont.truetype(FONT_SANS, 27)
    f_name = ImageFont.truetype(FONT_SANS, 32)

    right = W - RIGHT_MARGIN
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = spaced(tmp, (0, 0), TITLE, f_title, INK, TITLE_TRACK)
    tx = right - tw

    for dx, dy in ((2, 3), (1, 1)):
        spaced(d, (tx + dx, TITLE_Y + dy), TITLE, f_title, SHADOW, TITLE_TRACK)
    spaced(d, (tx, TITLE_Y), TITLE, f_title, INK, TITLE_TRACK)

    d.rectangle([right - tw, TITLE_Y + RULE_OFFSET,
                 right, TITLE_Y + RULE_OFFSET + 1], fill=(240, 234, 222, 90))

    y = TITLE_Y + CREDITS_Y
    for role, name in CREDITS:
        nw = spaced(tmp, (0, 0), name, f_name, DIM, 6)
        rw = spaced(tmp, (0, 0), role, f_role, ROLE, 8)
        spaced(d, (right - nw, y), name, f_name, DIM, 6)
        spaced(d, (right - nw - rw - 26, y + 7), role, f_role, ROLE, 8)
        y += CREDIT_GAP

    p = os.path.join(OUT, out_name)
    img.save(p)
    print("saved %s  title_w=%d" % (p, tw))
    return p


if __name__ == "__main__":
    build()