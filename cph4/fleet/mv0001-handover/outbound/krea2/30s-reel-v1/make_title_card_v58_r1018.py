# -*- coding: utf-8 -*-
# make_title_card_v58_r1018.py — V5.8 字卡 credits 四件套版（CEO MV 版权令 2026-10-18 14:32：
# 片名必带=专辑名+作词+作曲+导演·「大喵没鱼吃」=二创·避免侵权——承 V5.7 三行版加导演行）
# vs V57 变更：第三行（专辑/词/曲）后新增第四行「导演：大喵没鱼吃」36px 角标金·衬底随块加高·间距重排过边距律
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
AXIS = W / 2.0

GOLD_TOP = (252, 240, 190)
GOLD_MID = (132, 86, 40)
GOLD_BOT = (228, 184, 112)
SUB_GOLD = (236, 216, 164)   # 二创行亮金
CRED_GOLD = (198, 172, 118)  # 署名行角标金
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
    cx, f = x, pick_font(size)
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

# ---------- 版式（V5.8 credits 四件套版） ----------
MAIN_TEXT, MAIN_SIZE, MAIN_TRACK = "爱在西元前", 140, 0.13
SUB_TEXT,  SUB_SIZE,  SUB_TRACK  = "二创：大喵没鱼吃", 50, 0.22
CRED_TEXT, CRED_SIZE, CRED_TRACK = "专辑《范特西》 · 作词：方文山 · 作曲：周杰伦", 36, 0.10
DIR_TEXT,  DIR_SIZE,  DIR_TRACK  = "导演：大喵没鱼吃", 36, 0.10
MAIN_W = line_width(MAIN_TEXT, MAIN_SIZE, MAIN_TRACK)
MAIN_X, MAIN_Y = int(AXIS - MAIN_W / 2), 318
SUB_W = line_width(SUB_TEXT, SUB_SIZE, SUB_TRACK)
SUB_X, SUB_Y = int(AXIS - SUB_W / 2), 490
CRED_W = line_width(CRED_TEXT, CRED_SIZE, CRED_TRACK)
CRED_X, CRED_Y = int(AXIS - CRED_W / 2), 556
DIR_W = line_width(DIR_TEXT, DIR_SIZE, DIR_TRACK)
DIR_X, DIR_Y = int(AXIS - DIR_W / 2), 604

def edge_law_check(x, y, w, h, margin=120):
    assert x >= margin and y >= margin and x + w <= W - margin and y + h <= H - margin, \
        "PLACEMENT VIOLATION: (%d,%d)+%dx%d vs %dpx edge law" % (x, y, w, h, margin)

edge_law_check(MAIN_X, MAIN_Y, MAIN_W, MAIN_SIZE)
edge_law_check(SUB_X, SUB_Y, SUB_W, SUB_SIZE)
edge_law_check(CRED_X, CRED_Y, CRED_W, CRED_SIZE)
edge_law_check(DIR_X, DIR_Y, DIR_W, DIR_SIZE)

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# ① 双层暗衬底（块加高至导演行）
scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(scrim)
sd.rounded_rectangle([(236, 262), (1108, 696)], radius=52, fill=(10, 7, 4, 255))
scrim = scrim.filter(ImageFilter.GaussianBlur(46))
scrim.putalpha(scrim.getchannel("A").point(lambda v: int(v * 0.30)))
canvas = Image.alpha_composite(canvas, scrim)
core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(core)
cd.rounded_rectangle([(284, 286), (1060, 682)], radius=44, fill=(8, 5, 3, 255))
core = core.filter(ImageFilter.GaussianBlur(28))
core.putalpha(core.getchannel("A").point(lambda v: int(v * 0.24)))
canvas = Image.alpha_composite(canvas, core)

# ② 主标：投影 + 三段金属渐变 + 鎏金颗粒（承 v56/v57 工艺）
black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
draw_text_tracked(dm, MAIN_TEXT, MAIN_X, MAIN_Y, MAIN_SIZE, MAIN_TRACK)
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh.paste(black, (4, 4), mask)
sh = sh.filter(ImageFilter.GaussianBlur(2.6))
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
rng = np.random.default_rng(41018)
noise = rng.integers(0, 255, size=(H, W), dtype=np.uint8)
noise_img = Image.fromarray(noise, "L").filter(ImageFilter.GaussianBlur(1.2))
grain_layer = Image.new("RGBA", (W, H), (30, 22, 12, 255))
grain_layer.putalpha(noise_img.point(lambda v: int(v * 0.08 * 0.5)))
solid = Image.alpha_composite(solid, Image.composite(
    grain_layer, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))
solid.putalpha(Image.composite(
    solid.getchannel("A").point(lambda v: int(v * 0.98)),
    Image.new("L", (W, H), 0), mask))
canvas = Image.alpha_composite(canvas, solid)

# ③ 文本行渲染器（投影+纯色）
def text_line(text, x, y, size, track, color, sh_alpha, sh_off=(2, 2), sh_blur=2.0):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    draw_text_tracked(d, text, x, y, size, track)
    s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s.paste(black, sh_off, m)
    s = s.filter(ImageFilter.GaussianBlur(sh_blur))
    s.putalpha(s.getchannel("A").point(lambda v: int(v * sh_alpha)))
    t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    t.paste(Image.new("RGBA", (W, H), color + (255,)), (0, 0), m)
    return Image.alpha_composite(Image.alpha_composite(canvas, s), t)

canvas = text_line(SUB_TEXT, SUB_X, SUB_Y, SUB_SIZE, SUB_TRACK, SUB_GOLD, 0.52, (2, 2), 2.0)
canvas = text_line(CRED_TEXT, CRED_X, CRED_Y, CRED_SIZE, CRED_TRACK, CRED_GOLD, 0.42, (2, 2), 1.8)
canvas = text_line(DIR_TEXT, DIR_X, DIR_Y, DIR_SIZE, DIR_TRACK, CRED_GOLD, 0.42, (2, 2), 1.8)

out = os.path.join(HERE, "title_card_v58.png")
canvas.save(out)
print("TITLE-V58 -> %s  main=%dpx@(%d,%d) sub=%dpx@(%d,%d) cred=%dpx@(%d,%d) dir=%dpx@(%d,%d)" % (
    out, MAIN_SIZE, MAIN_X, MAIN_Y, SUB_SIZE, SUB_X, SUB_Y,
    CRED_SIZE, CRED_X, CRED_Y, DIR_SIZE, DIR_X, DIR_Y))
