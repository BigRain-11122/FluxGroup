# -*- coding: utf-8 -*-
# make_title_card_v59_r1019.py — V5.9 credits 版式重制四件（CEO 令 19:1x 缺陷⑤「作词作曲导演二创者的排版非常丑」
# ·版式设计席 R-20261018-mv-credits-typo-v1.md §三重排案全参数接线）
# vs V58 变更：①删 50px「二创」反层级行（最重缺陷）②署名三行重构 34/34/30px·行距 1.65×③衬底=双层圆角暗块→整幅底部渐变带
# ④错峰淡入（4.85/5.25/5.65 各 0.45s·装配面）⑤片名 140px 鎏金工艺零改动（CEO 判「还行」）
# 产出：title_card_v59_main.png（片名+底部渐变带）+ title_credit_v59_l1/l2/l3.png（三行署名独立层）
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
AXIS = W / 2.0

# ---- 片名工艺（承 v58 零改动面） ----
GOLD_TOP = (252, 240, 190)
GOLD_MID = (132, 86, 40)
GOLD_BOT = (228, 184, 112)
SHADOW = 0.58
MAIN_FONTS = [
    r"C:\Windows\Fonts\NotoSerifCJKsc-Black.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Heavy.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Bold.otf",
    r"C:\Windows\Fonts\simsun.ttc",
]
# 署名行字体：思源宋体 Bold 优先（行标宜规整·R- §二）
LINE_FONTS = [
    r"C:\Windows\Fonts\SourceHanSerifSC-Bold.otf",
    r"C:\Windows\Fonts\NotoSerifCJKsc-Black.otf",
    r"C:\Windows\Fonts\simsun.ttc",
]

def pick_font(cands, size):
    for c in cands:
        if os.path.isfile(c):
            return ImageFont.truetype(c, size)
    raise SystemExit("NO CJK FONT FOUND")

def line_width(font_cands, text, size, track):
    step = size + int(size * track)
    return step * len(text) - int(size * track)

def draw_text_tracked(dm, font_cands, text, x, y, size, track, fill=255):
    step = size + int(size * track)
    cx, f = x, pick_font(font_cands, size)
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

# ---- ① 主卡：片名 140px 鎏金（v58 工艺）+ 底部渐变带（y528→768·透明→黑 α0.55） ----
MAIN_TEXT, MAIN_SIZE, MAIN_TRACK = "愛在西元前", 140, 0.13
MAIN_W = line_width(MAIN_FONTS, MAIN_TEXT, MAIN_SIZE, MAIN_TRACK)
MAIN_X, MAIN_Y = int(AXIS - MAIN_W / 2), 318

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
draw_text_tracked(dm, MAIN_FONTS, MAIN_TEXT, MAIN_X, MAIN_Y, MAIN_SIZE, MAIN_TRACK)
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

# 底部渐变带（R- §三：整幅 y528→768 透明→黑 α0.55·替代双层圆角暗块）
band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bg = np.asarray(band).copy()
BAND_TOP, BAND_A = 528, 0.55
for yy in range(BAND_TOP, H):
    a = int(BAND_A * 255 * (yy - BAND_TOP) / (H - BAND_TOP))
    bg[yy, :, 3] = a
band = Image.fromarray(bg)
canvas = Image.alpha_composite(canvas, band)

out_main = os.path.join(HERE, "title_card_v59_main.png")
canvas.save(out_main)
print("MAIN-V59 -> %s (main=%dpx@(%d,%d) band y%d->768 a%.2f)" % (
    out_main, MAIN_SIZE, MAIN_X, MAIN_Y, BAND_TOP, BAND_A), flush=True)

# ---- ② 署名三行（独立透明层·装配面错峰淡入） ----
CRED_COLOR = (242, 232, 213)   # 暖白 #F2E8D5
LINES = [
    ("title_credit_v59_l1.png", "作词　方文山　·　作曲　周杰伦", 34, 576, 1.00),
    ("title_credit_v59_l2.png", "专辑　《范特西》",             34, 632, 1.00),
    ("title_credit_v59_l3.png", "二创　·　导演　大喵没鱼吃",    30, 692, 0.72),
]

def credit_line(text, size, cy, alpha):
    lw = line_width(LINE_FONTS, text, size, 0.05)
    x, y = int(AXIS - lw / 2), cy - size // 2
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    draw_text_tracked(d, LINE_FONTS, text, x, y, size, 0.05)
    # 软投影 0/2/8px α0.40（R- §三）
    s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s.paste(black, (0, 2), m)
    s = s.filter(ImageFilter.GaussianBlur(8))
    s.putalpha(s.getchannel("A").point(lambda v: int(v * 0.40)))
    t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    t.paste(Image.new("RGBA", (W, H), CRED_COLOR + (255,)), (0, 0), m)
    if alpha < 1.0:
        t.putalpha(t.getchannel("A").point(lambda v: int(v * alpha)))
    return Image.alpha_composite(s, t)

for fn, text, size, cy, alpha in LINES:
    img = credit_line(text, size, cy, alpha)
    p = os.path.join(HERE, fn)
    img.save(p)
    print("CREDIT-V59 -> %s (%dpx cy%d a%.2f)" % (fn, size, cy, alpha), flush=True)
print("TITLE-V59 DONE (1 main + 3 lines)", flush=True)
