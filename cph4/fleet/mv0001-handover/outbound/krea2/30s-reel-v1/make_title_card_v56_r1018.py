# -*- coding: utf-8 -*-
# make_title_card_v56_r1018.py — V5.6 字卡大字版 v2（CEO V5.5 终审反馈①整改·2026-10-18）
# CEO 原话：「歌曲名和大喵没鱼吃」位置/字体不好看、要大一点、构图/字体/颜色好好设计
# v1 判读 7.5/8.5 → v2 微调（判读 P0/P1 全落）：
#   主标 120→140px（画宽 49%→57%·「要大一点」再加档）｜投影加深 0.58+扩径
#   楔形带 44→62px 级·改中鎏金（弃偏白 GOLD_TOP）·中轴 +8px 修正·gap 52
#   衬底双层（宽 0.30 + 字区核心 0.24 → 中心 ~45% 压暗·亮纸底可读）
#   落款 44→50px｜鎏金颗粒层回归（v55 grain 0.08 工艺·判读 P2 banding 预防）
# 承工艺正典：三段金属反光渐变/复合楔形字符/画缘律 ≥120px/中轴对齐 ±1px
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
BAND_GOLD = (238, 204, 128)   # 楔形带真鎏金（v2 判读「暗铜·亮纸底隐形」判改·#EECC80）
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

def wedge_stroke(dr, x, y, direction, head=19, tail=27, color=BAND_GOLD, alpha=225, lw=6):
    c = color + (alpha,)
    if direction == "r":
        dr.polygon([(x, y - 8), (x, y + 8), (x + head, y)], fill=c)
        dr.line([(x + head, y), (x + head + tail, y)], fill=c, width=lw)
    elif direction == "d":
        dr.polygon([(x - 8, y), (x + 8, y), (x, y + head)], fill=c)
        dr.line([(x, y + head), (x, y + head + tail)], fill=c, width=lw)
    else:
        dr.polygon([(x + 8, y - 8), (x + 16, y), (x, y)], fill=c)
        dr.line([(x - 1, y + 1), (x - 1 - tail, y + 1 + tail)], fill=c, width=lw)

def cuneiform_glyph(dr, cx, cy, variant, color, alpha):
    if variant == 0:
        wedge_stroke(dr, cx - 31, cy - 16, "r", color=color, alpha=alpha)
        wedge_stroke(dr, cx + 17, cy - 8, "d", head=17, tail=20, color=color, alpha=alpha)
    elif variant == 1:
        wedge_stroke(dr, cx - 24, cy - 25, "d", head=17, tail=24, color=color, alpha=alpha)
        wedge_stroke(dr, cx + 17, cy - 12, "ld", color=color, alpha=alpha)
    else:
        wedge_stroke(dr, cx - 31, cy - 23, "r", head=17, tail=24, color=color, alpha=alpha)
        wedge_stroke(dr, cx - 7, cy + 7, "r", head=17, tail=25, color=color, alpha=alpha)

def wedge_glyph_band(dr, cx, y, n=3, gap=56, color=BAND_GOLD, alpha=225):
    total = n * 68 + (n - 1) * gap
    x0 = cx - total // 2 + 8          # v1 判读「略偏左」→ +8px 中轴修正
    for i in range(n):
        cuneiform_glyph(dr, x0 + i * (68 + gap) + 34, y, i, color, alpha)

# ---------- 版式（V5.6 v2 大字版） ----------
MAIN_TEXT, MAIN_SIZE, MAIN_TRACK = "爱在西元前", 140, 0.13   # 772px 宽 = 画宽 57%
SUB_TEXT,  SUB_SIZE,  SUB_TRACK  = "大喵没鱼吃", 50, 0.30    # 310px 宽
MAIN_W = line_width(MAIN_TEXT, MAIN_SIZE, MAIN_TRACK)
MAIN_X, MAIN_Y = int(AXIS - MAIN_W / 2), 348                # 主标带 348-488
SUB_W = line_width(SUB_TEXT, SUB_SIZE, SUB_TRACK)
SUB_X, SUB_Y = int(AXIS - SUB_W / 2), 518                   # 落款带 518-568
BAND_Y = 310                                                # 楔形铭带（62px 级）

def edge_law_check(x, y, w, h, margin=120):
    assert x >= margin and y >= margin and x + w <= W - margin and y + h <= H - margin, \
        "PLACEMENT VIOLATION: (%d,%d)+%dx%d vs %dpx edge law" % (x, y, w, h, margin)

edge_law_check(MAIN_X, MAIN_Y, MAIN_W, MAIN_SIZE)
edge_law_check(SUB_X, SUB_Y, SUB_W, SUB_SIZE)

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# ① 双层暗衬底（宽幅 0.30 + 字区核心 0.24 → 中心 ~45%·亮纸底可读·边缘无矩形痕）
scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(scrim)
sd.rounded_rectangle([(236, 272), (1108, 610)], radius=48, fill=(10, 7, 4, 255))
scrim = scrim.filter(ImageFilter.GaussianBlur(46))
scrim.putalpha(scrim.getchannel("A").point(lambda v: int(v * 0.30)))
canvas = Image.alpha_composite(canvas, scrim)
core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(core)
cd.rounded_rectangle([(300, 296), (1044, 592)], radius=40, fill=(8, 5, 3, 255))
core = core.filter(ImageFilter.GaussianBlur(28))
core.putalpha(core.getchannel("A").point(lambda v: int(v * 0.24)))
canvas = Image.alpha_composite(canvas, core)

# ② 主标：投影 + 三段金属渐变 + 鎏金颗粒
mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
draw_text_tracked(dm, MAIN_TEXT, MAIN_X, MAIN_Y, MAIN_SIZE, MAIN_TRACK)
black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
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
    grain_layer, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask.convert("L") if mask.mode == "L" else mask))
solid.putalpha(Image.composite(
    solid.getchannel("A").point(lambda v: int(v * 0.98)),
    Image.new("L", (W, H), 0), mask))
canvas = Image.alpha_composite(canvas, solid)

# ③ 落款：提亮金 + 投影
sub_mask = Image.new("L", (W, H), 0)
dsm = ImageDraw.Draw(sub_mask)
draw_text_tracked(dsm, SUB_TEXT, SUB_X, SUB_Y, SUB_SIZE, SUB_TRACK)
sh2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh2.paste(black, (2, 2), sub_mask)
sh2 = sh2.filter(ImageFilter.GaussianBlur(2.0))
sh2.putalpha(sh2.getchannel("A").point(lambda v: int(v * 0.52)))
sub_txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sub_txt.paste(Image.new("RGBA", (W, H), SUB_GOLD + (255,)), (0, 0), sub_mask)
canvas = Image.alpha_composite(canvas, sh2)
canvas = Image.alpha_composite(canvas, sub_txt)

# ④ 楔形铭带（68px 级·三枚异质·真鎏金+暖光晕+压底投影·v3 判读「亮纸底对比余量不足」保险）
band_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bov = ImageDraw.Draw(band_layer, "RGBA")
wedge_glyph_band(bov, int(AXIS), BAND_Y, n=3, gap=56)
band_mask = band_layer.getchannel("A")
bsh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bsh.paste(black, (2, 2), band_mask)
bsh = bsh.filter(ImageFilter.GaussianBlur(2.5))
bsh.putalpha(bsh.getchannel("A").point(lambda v: int(v * 0.38)))
canvas = Image.alpha_composite(canvas, bsh)
glow = band_layer.filter(ImageFilter.GaussianBlur(7))
glow.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.5)))
canvas = Image.alpha_composite(canvas, glow)
canvas = Image.alpha_composite(canvas, band_layer)

out = os.path.join(HERE, "title_card_v56.png")
canvas.save(out)
print("TITLE-V56v2 -> %s  main=%dpx@(%d,%d) axis=%d sub=%dpx@(%d,%d) band@%d scrim=2layer" % (
    out, MAIN_SIZE, MAIN_X, MAIN_Y, int(AXIS), SUB_SIZE, SUB_X, SUB_Y, BAND_Y))

# ---------- ⑤ 自验证预览板 ----------
import subprocess
PROBE = os.path.join(HERE, "v56_probe")
os.makedirs(PROBE, exist_ok=True)
bg1 = os.path.join(PROBE, "bg_r_macro.jpg")
bg2 = os.path.join(PROBE, "bg_b_pause.jpg")
subprocess.run(["ffmpeg", "-y", "-ss", "0.70", "-i", os.path.join(HERE, "v56src", "V56_R_rubbing_macro.mp4"),
                "-frames:v", "1", "-q:v", "3", bg1], capture_output=True)
subprocess.run(["ffmpeg", "-y", "-ss", "1.75",
                "-i", r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo\INT2_paper_v5.mp4",
                "-frames:v", "1", "-q:v", "3", bg2], capture_output=True)
cw, ch = 672, 384
board = Image.new("RGB", (2 * (cw + 6), ch + 34), (12, 12, 14))
db = ImageDraw.Draw(board)
fb = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
db.text((8, 6), "V56v2 card preview: L=over R rubbing macro @6.2s | R=over INT2 pause @4.9s", fill=(255, 220, 120), font=fb)
for i, (bg) in enumerate((bg1, bg2)):
    if os.path.isfile(bg):
        f = Image.open(bg).convert("RGB").resize((cw, ch))
        c = Image.open(out).resize((cw, ch))
        f.paste(c, (0, 0), c)
        board.paste(f, (i * (cw + 6), 30))
bp = os.path.join(PROBE, "V56-CARDS-PREVIEW.jpg")
board.save(bp, quality=92)
print("PREVIEW ->", bp)
