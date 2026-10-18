# -*- coding: utf-8 -*-
# make_kft_cover_v57_r1018.py — KFT 封面帧终版（PUBLISH-CHECKLIST §三：KFT 金字 bloom 峰值帧
# +顶部 y0-25% 暗带叠曲名标题字·琥珀金衬线·禁综艺花字；封面禁 AI 脸=KFT 无人物天然合规）
# 基帧=39.60s（四候选判读唯一首选：金字满峰值+顶部暗带干净）
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
PA = os.path.join(HERE, "publish_assets")
BASE = os.path.join(PA, "kft_cover_39_60.jpg")
AXIS = W / 2.0

GOLD_TOP = (252, 240, 190)
GOLD_MID = (132, 86, 40)
GOLD_BOT = (228, 184, 112)
SUB_GOLD = (236, 216, 164)
SHADOW = 0.58

CANDIDATE_FONTS = [
    r"C:\Windows\Fonts\NotoSerifCJKsc-Black.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Heavy.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Bold.otf",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]

def pick_font(size):
    for c in CANDIDATE_FONTS:
        if os.path.isfile(c):
            return ImageFont.truetype(c, size)
    raise SystemExit("NO CJK FONT FOUND")

def line_width(text, size, track):
    step = size + int(size * track)
    return step * len(text) - int(size * track)

def draw_text_tracked(dm, text, x, y, size, track, fill=255):
    step = size + int(size * track)
    cx, f = x, y and pick_font(size)
    for ch in text:
        dm.text((cx, y), ch, font=f, fill=fill)
        cx += step

def lerp3(a, b, u):
    return tuple(int(a[k] * (1 - u) + b[k] * u) for k in range(3))

def gold_band_color(t):
    if t < 0.18:
        return GOLD_TOP
    if t < 0.55:
        return lerp3(GOLD_TOP, GOLD_MID, (t - 0.18) / 0.37)
    return lerp3(GOLD_MID, GOLD_BOT, (t - 0.55) / 0.45)

MAIN_TEXT, MAIN_SIZE, MAIN_TRACK = "爱在西元前", 104, 0.13
SUB_TEXT, SUB_SIZE, SUB_TRACK = "二创：大喵没鱼吃", 38, 0.22
MAIN_W = line_width(MAIN_TEXT, MAIN_SIZE, MAIN_TRACK)
MAIN_X, MAIN_Y = int(AXIS - MAIN_W / 2), 34
SUB_W = line_width(SUB_TEXT, SUB_SIZE, SUB_TRACK)
SUB_X, SUB_Y = int(AXIS - SUB_W / 2), 158
assert MAIN_X >= 120 and SUB_X >= 120, "edge law violation"

base = Image.open(BASE).convert("RGBA")

# 顶部暗带微衬底（KFT-2 顶部本净·轻衬稳字即可）
scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(scrim)
sd.rounded_rectangle([(180, 14), (1164, 216)], radius=40, fill=(6, 4, 2, 255))
scrim = scrim.filter(ImageFilter.GaussianBlur(34))
scrim.putalpha(scrim.getchannel("A").point(lambda v: int(v * 0.34)))
canvas = Image.alpha_composite(base, scrim)

black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
draw_text_tracked(dm, MAIN_TEXT, MAIN_X, MAIN_Y, MAIN_SIZE, MAIN_TRACK)
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh.paste(black, (3, 3), mask)
sh = sh.filter(ImageFilter.GaussianBlur(2.2))
sh.putalpha(sh.getchannel("A").point(lambda v: int(v * SHADOW)))
canvas = Image.alpha_composite(canvas, sh)
ys, xs = np.where(np.asarray(mask) > 0)
grad = Image.new("RGBA", (W, H), (0, 0, 0, 255))
g = np.asarray(grad).copy()
if len(ys):
    y0, y1 = ys.min(), ys.max()
    for yy in range(y0, y1 + 1):
        col = list(gold_band_color((yy - y0) / max(1, (y1 - y0)))) + [255]
        g[yy, :, :] = col
grad = Image.fromarray(g)
solid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
solid.paste(grad, (0, 0), mask)
canvas = Image.alpha_composite(canvas, solid)

m2 = Image.new("L", (W, H), 0)
d2 = ImageDraw.Draw(m2)
draw_text_tracked(d2, SUB_TEXT, SUB_X, SUB_Y, SUB_SIZE, SUB_TRACK)
sh2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh2.paste(black, (2, 2), m2)
sh2 = sh2.filter(ImageFilter.GaussianBlur(1.8))
sh2.putalpha(sh2.getchannel("A").point(lambda v: int(v * 0.50)))
t2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
t2.paste(Image.new("RGBA", (W, H), SUB_GOLD + (255,)), (0, 0), m2)
canvas = Image.alpha_composite(Image.alpha_composite(canvas, sh2), t2)

out = os.path.join(PA, "kft_cover_final_v57.jpg")
canvas.convert("RGB").save(out, quality=93)
print("KFT-COVER -> %s  main=%dpx@(%d,%d) sub=%dpx@(%d,%d) base=39.60s" % (
    out, MAIN_SIZE, MAIN_X, MAIN_Y, SUB_SIZE, SUB_X, SUB_Y))
