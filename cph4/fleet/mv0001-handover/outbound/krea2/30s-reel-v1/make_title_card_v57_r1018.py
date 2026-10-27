# -*- coding: utf-8 -*-
# make_title_card_v57_r1018.py — V5.7 字卡署名版（CEO 三连令·2026-10-18 13:4x）
# CEO 令：①片名卡加专辑名+作词作曲署名（所有曲）②「大喵没鱼吃」=二创定位·署名避免侵权
#        ③爱在西元前上方看不懂的楔形符号——去掉
# vs V56 变更：撤楔形铭带（CEO 判负）·增两行署名（二创行+专辑/作词/作曲行）·衬底随块加高
# 版式：主标 140px 鎏金 → 二创：大喵没鱼吃 50px 亮金 → 专辑/作词/作曲 36px 角标金
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
CRED_GOLD = (198, 172, 118)  # 署名行角标金（次级）
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

# ---------- 版式（V5.7 署名版·撤楔形带） ----------
MAIN_TEXT, MAIN_SIZE, MAIN_TRACK = "爱在西元前", 140, 0.13      # 772px = 画宽 57%
SUB_TEXT,  SUB_SIZE,  SUB_TRACK  = "二创：大喵没鱼吃", 50, 0.22  # 477px
CRED_TEXT, CRED_SIZE, CRED_TRACK = "专辑《范特西》 · 作词：方文山 · 作曲：周杰伦", 36, 0.10
MAIN_W = line_width(MAIN_TEXT, MAIN_SIZE, MAIN_TRACK)
MAIN_X, MAIN_Y = int(AXIS - MAIN_W / 2), 318                  # 主标带 318-458
SUB_W = line_width(SUB_TEXT, SUB_SIZE, SUB_TRACK)
SUB_X, SUB_Y = int(AXIS - SUB_W / 2), 490                     # 二创带 490-540
CRED_W = line_width(CRED_TEXT, CRED_SIZE, CRED_TRACK)
CRED_X, CRED_Y = int(AXIS - CRED_W / 2), 566                  # 署名带 566-602

def edge_law_check(x, y, w, h, margin=120):
    assert x >= margin and y >= margin and x + w <= W - margin and y + h <= H - margin, \
        "PLACEMENT VIOLATION: (%d,%d)+%dx%d vs %dpx edge law" % (x, y, w, h, margin)

edge_law_check(MAIN_X, MAIN_Y, MAIN_W, MAIN_SIZE)
edge_law_check(SUB_X, SUB_Y, SUB_W, SUB_SIZE)
edge_law_check(CRED_X, CRED_Y, CRED_W, CRED_SIZE)

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# ① 双层暗衬底（块加高至署名行）
scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(scrim)
sd.rounded_rectangle([(236, 262), (1108, 648)], radius=52, fill=(10, 7, 4, 255))
scrim = scrim.filter(ImageFilter.GaussianBlur(46))
scrim.putalpha(scrim.getchannel("A").point(lambda v: int(v * 0.30)))
canvas = Image.alpha_composite(canvas, scrim)
core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(core)
cd.rounded_rectangle([(284, 286), (1060, 634)], radius=44, fill=(8, 5, 3, 255))
core = core.filter(ImageFilter.GaussianBlur(28))
core.putalpha(core.getchannel("A").point(lambda v: int(v * 0.24)))
canvas = Image.alpha_composite(canvas, core)

# ② 主标：投影 + 三段金属渐变 + 鎏金颗粒（承 v56 工艺）
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

out = os.path.join(HERE, "title_card_v57.png")
canvas.save(out)
print("TITLE-V57 -> %s  main=%dpx@(%d,%d) sub=%dpx@(%d,%d) cred=%dpx@(%d,%d) band=REMOVED" % (
    out, MAIN_SIZE, MAIN_X, MAIN_Y, SUB_SIZE, SUB_X, SUB_Y, CRED_SIZE, CRED_X, CRED_Y))

# ---------- ④ 自验证预览板 ----------
import subprocess
PROBE = os.path.join(HERE, "v56_probe")
os.makedirs(PROBE, exist_ok=True)
bg1 = os.path.join(PROBE, "bg_r_macro.jpg")
bg2 = os.path.join(PROBE, "bg_b_pause.jpg")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.70", "-i", os.path.join(HERE, "v56src", "V56_R_rubbing_macro.mp4"),
                "-frames:v", "1", "-q:v", "3", bg1], capture_output=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.75",
                "-i", r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo\INT2_paper_v5.mp4",
                "-frames:v", "1", "-q:v", "3", bg2], capture_output=True)
cw, ch = 672, 384
board = Image.new("RGB", (2 * (cw + 6), ch + 34), (12, 12, 14))
db = ImageDraw.Draw(board)
fb = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
db.text((8, 6), "V57 card preview: L=over R rubbing macro @6.2s | R=over INT2 pause @4.9s", fill=(255, 220, 120), font=fb)
for i, (bg) in enumerate((bg1, bg2)):
    if os.path.isfile(bg):
        f = Image.open(bg).convert("RGB").resize((cw, ch))
        c = Image.open(out).resize((cw, ch))
        f.paste(c, (0, 0), c)
        board.paste(f, (i * (cw + 6), 30))
bp = os.path.join(PROBE, "V57-CARDS-PREVIEW.jpg")
board.save(bp, quality=92)
print("PREVIEW ->", bp)
