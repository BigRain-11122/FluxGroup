# -*- coding: utf-8 -*-
"""Title card v3.2 for mv0001「愛在西元前」 (vertical, real credits).

Credits verified 2026-11-05 against two independent sources (Baidu Baike + JayChou wiki):
  作詞 方文山 / 作曲 周杰倫 / 編曲 林邁可 / 演唱 周杰倫   (album《范特西》, 2001-09-14,
  producer 周杰倫). 编曲 was missing in v3.1 and is added here.

Layout: vertical 宋体 title on the only clean column of the opening frame (right edge),
warm paper white, double soft shadow, hairline rule, credits right-aligned against the
rule and vertically centred on the title run.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
OUT = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "canon", "title-design")
W, H = 1920, 1096

TITLE = "愛在西元前"
CREDITS = [("作詞", "方文山"), ("作曲", "周杰倫"), ("編曲", "林邁可"), ("演唱", "周杰倫")]

FONT_SERIF = r"C:\Windows\Fonts\simsun.ttc"
FONT_SANS = r"C:\Windows\Fonts\msyh.ttc"

INK = (243, 238, 229, 255)
SHADOW = (10, 7, 3, 160)
DIM = (233, 227, 215, 210)
ROLE = (220, 212, 198, 170)

RIGHT_MARGIN = 206
TITLE_SIZE = 112
TITLE_GAP = 10
TITLE_TOP = 252
CREDIT_GAP = 46


def draw_v(d, x, y, text, font, fill, gap):
    for ch in text:
        bbox = d.textbbox((0, 0), ch, font=font)
        w = bbox[2] - bbox[0]
        d.text((x - w / 2.0, y), ch, font=font, fill=fill)
        y += (bbox[3] - bbox[1]) + gap
    return y


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


def build(out_name="title-v32.png"):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(FONT_SERIF, TITLE_SIZE)
    f_role = ImageFont.truetype(FONT_SANS, 26)
    f_name = ImageFont.truetype(FONT_SANS, 31)

    col_x = W - RIGHT_MARGIN
    for dx, dy in ((2, 3), (1, 1)):
        draw_v(d, col_x + dx, TITLE_TOP + dy, TITLE, f_title, SHADOW, TITLE_GAP)
    end_y = draw_v(d, col_x, TITLE_TOP, TITLE, f_title, INK, TITLE_GAP)

    d.rectangle([col_x - 74, TITLE_TOP + 6, col_x - 73, end_y - 6],
                fill=(240, 234, 222, 85))

    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    block_h = len(CREDITS) * CREDIT_GAP
    y = TITLE_TOP + max(0, ((end_y - TITLE_TOP) - block_h) // 2)
    right_edge = col_x - 104
    for role, name in CREDITS:
        nw = spaced(tmp, (0, 0), name, f_name, DIM, 5)
        rw = spaced(tmp, (0, 0), role, f_role, ROLE, 7)
        spaced(d, (right_edge - nw, y), name, f_name, DIM, 5)
        spaced(d, (right_edge - nw - rw - 22, y + 8), role, f_role, ROLE, 7)
        y += CREDIT_GAP

    p = os.path.join(OUT, out_name)
    img.save(p)
    print("saved", p)
    return p


if __name__ == "__main__":
    build()