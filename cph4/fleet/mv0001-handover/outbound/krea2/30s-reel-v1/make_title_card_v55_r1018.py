# -*- coding: utf-8 -*-
# make_title_card_v55_r1018.py — V5.5 字卡修订（红队试点1 B4/C1 修复·C-20261018-01 绿队回合 2026-10-18）
# 红队定罪 vs V54 版：
#   B4-符号带：3 枚 11x9 实心小三角读作「省略号/渲染未完成」→ 重画为复合楔形字符
#   （每枚 2 笔画真楔形结构=三角头+拖尾线·22px 级·异质三枚·铭文带观感）
#   B4-鎏金：两段线性渐变 56px 字高内读作平涂 #C4A068 → 三段金属反光渐变
#   （亮金顶→60% 沉金→底部反光回亮·跨度 40% 亮度·渐变可读）
#   C1：尾声明 19px@72% 偏怯弱 → 21px@80% + 垫带同步加宽
# 断言律承 v54：画缘律 ≥120px + 中轴对齐 ±1px。
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
AXIS = 1068.0            # 主标块中轴（右缘退足 120px 画边距后的几何心）

# V5.5 三段金属反光渐变·v2（B4 二轮：预览板缩图实测读作平涂→加大跨度+高光脊线·缩图可读）
GOLD_TOP = (252, 240, 190)   # 亮金脊（顶部窄亮带）
GOLD_MID = (132, 86, 40)     # 沉金（金属暗带·压深 48%）
GOLD_BOT = (225, 180, 108)   # 底部反光回亮
SUB_GOLD = (199, 177, 131)   # #C7B183 灰金（署名/尾声明降档色·承 v54）
SHADOW = 0.42

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
    """V5.5 三段金属渐变 v2：t∈[0,1] 顶→底。窄亮脊(18%)→快速沉入暗带(→55%)→反光回亮。缩图下也读得出鎏金。"""
    if t < 0.18:
        return GOLD_TOP
    if t < 0.55:
        return lerp3(GOLD_TOP, GOLD_MID, (t - 0.18) / 0.37)
    return lerp3(GOLD_MID, GOLD_BOT, (t - 0.55) / 0.45)

def wedge_stroke(dr, x, y, direction, head=10, tail=15, color=SUB_GOLD, alpha=170, lw=3):
    """一笔真楔形：实心三角头（宽=线宽 3.3 倍·判读 v2 要求）+ 细拖尾线。direction: r/d/ld"""
    c = color + (alpha,)
    if direction == "r":
        dr.polygon([(x, y - 4), (x, y + 4), (x + head, y)], fill=c)
        dr.line([(x + head, y), (x + head + tail, y)], fill=c, width=lw)
    elif direction == "d":
        dr.polygon([(x - 4, y), (x + 4, y), (x, y + head)], fill=c)
        dr.line([(x, y + head), (x, y + head + tail)], fill=c, width=lw)
    else:  # ld：头右上、尾左下斜
        dr.polygon([(x + 4, y - 4), (x + 8, y), (x, y)], fill=c)
        dr.line([(x - 1, y + 1), (x - 1 - tail, y + 1 + tail)], fill=c, width=lw)

def cuneiform_glyph(dr, cx, cy, variant, color, alpha):
    """一枚复合楔形字符（2 笔画·34px 级·v2 放大 1.6x）。variant 0/1/2 异质布局。"""
    if variant == 0:      # 横楔在上·竖楔在右下
        wedge_stroke(dr, cx - 15, cy - 8, "r", color=color, alpha=alpha)
        wedge_stroke(dr, cx + 9, cy - 4, "d", head=9, tail=10, color=color, alpha=alpha)
    elif variant == 1:    # 竖楔在左·斜楔在右
        wedge_stroke(dr, cx - 12, cy - 13, "d", head=9, tail=12, color=color, alpha=alpha)
        wedge_stroke(dr, cx + 9, cy - 6, "ld", color=color, alpha=alpha)
    else:                 # 双横楔错位叠
        wedge_stroke(dr, cx - 15, cy - 11, "r", head=9, tail=12, color=color, alpha=alpha)
        wedge_stroke(dr, cx - 3, cy + 3, "r", head=9, tail=13, color=color, alpha=alpha)

def wedge_glyph_band(dr, cx, y, n=3, gap=34, color=SUB_GOLD, alpha=175):
    """V5.5 楔形铭文带：n 枚异质复合符号（34px 级），以 cx 为带心。"""
    total = n * 34 + (n - 1) * gap
    x0 = cx - total // 2
    for i in range(n):
        cuneiform_glyph(dr, x0 + i * (34 + gap) + 17, y, i, color, alpha)

# ---------- shared render: mask -> shadow + gold gradient + grain ----------
def render_block(mask, grain=0.08, alpha_main=0.97):
    """mask: L image. returns RGBA block composited per V5.4 typography recipe（V5.5 渐变换三段金属带）."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    sh.paste(black, (2, 2), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(1.5))
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
    grain_layer.putalpha(noise_img.point(lambda v: int(v * grain * 0.5)))
    solid = Image.alpha_composite(solid, Image.composite(
        grain_layer, Image.new("RGBA", (W, H), (0, 0, 0, 0)),
        mask.convert("L")))
    solid.putalpha(Image.composite(
        solid.getchannel("A").point(lambda v: int(v * alpha_main)),
        Image.new("L", (W, H), 0), mask))
    canvas = Image.alpha_composite(canvas, solid)
    return canvas

# ---------- ① 歌名卡 title_card_v55.png ----------
MAIN_TEXT, MAIN_SIZE, MAIN_TRACK = "爱在西元前", 56, 0.15
SUB_TEXT,  SUB_SIZE,  SUB_TRACK  = "大喵没鱼吃", 22, 0.30
MAIN_W = line_width(MAIN_TEXT, MAIN_SIZE, MAIN_TRACK)     # 312
MAIN_X, MAIN_Y = int(AXIS - MAIN_W / 2), 214
SUB_W = line_width(SUB_TEXT, SUB_SIZE, SUB_TRACK)         # 134
SUB_X, SUB_Y = int(AXIS - SUB_W / 2), 300                 # 落款距主标底 30px（判读 v2：呼吸感 +35%）
BAND_Y = 178                                              # 楔形铭文带（v2 放大后上移 6px）

def edge_law_check(x, y, w, h, margin=120):
    assert x >= margin and y >= margin and x + w <= W - margin and y + h <= H - margin, \
        "PLACEMENT VIOLATION: (%d,%d)+%dx%d vs %dpx edge law" % (x, y, w, h, margin)

edge_law_check(MAIN_X, MAIN_Y, MAIN_W, MAIN_SIZE)
edge_law_check(SUB_X, SUB_Y, SUB_W, SUB_SIZE)

mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
draw_text_tracked(dm, MAIN_TEXT, MAIN_X, MAIN_Y, MAIN_SIZE, MAIN_TRACK)
title_canvas = render_block(mask, grain=0.08, alpha_main=0.97)

sub_mask = Image.new("L", (W, H), 0)
dsm = ImageDraw.Draw(sub_mask)
draw_text_tracked(dsm, SUB_TEXT, SUB_X, SUB_Y, SUB_SIZE, SUB_TRACK)
sh2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh2.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (1, 1), sub_mask)
sh2 = sh2.filter(ImageFilter.GaussianBlur(1.2))
sh2.putalpha(sh2.getchannel("A").point(lambda v: int(v * 0.38)))
sub_txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sub_txt.paste(Image.new("RGBA", (W, H), SUB_GOLD + (255,)), (0, 0), sub_mask)
sub_txt.putalpha(sub_txt.getchannel("A").point(lambda v: int(v * 1.00)))  # 判读 v2：对比度微升（全黑底上「快看不见」→满 alpha）
title_canvas = Image.alpha_composite(title_canvas, sh2)
title_canvas = Image.alpha_composite(title_canvas, sub_txt)

# 楔形铭文带（V5.5 v2 重画·复合真楔形 3 枚异质·34px 级）
ov = ImageDraw.Draw(title_canvas, "RGBA")
wedge_glyph_band(ov, int(AXIS), BAND_Y, n=3, gap=34, color=GOLD_TOP, alpha=180)

out1 = os.path.join(HERE, "title_card_v55.png")
title_canvas.save(out1)
print("TITLE  -> %s  main=%dpx@(%d,%d) axis=%d sub=%dpx@(%d,%d) band=compound-wedge@%d" % (
    out1, MAIN_SIZE, MAIN_X, MAIN_Y, AXIS, SUB_SIZE, SUB_X, SUB_Y, BAND_Y))

# ---------- ② 片尾声明卡 tail_credit_v55.png（C1 v2：24px@88%·判读「声明可读性优先于含蓄感」）----------
TAIL_TEXT = "欢迎转载，请注明出处：大喵没鱼吃"
TAIL_SIZE, TAIL_TRACK = 24, 0.25
TAIL_W = line_width(TAIL_TEXT, TAIL_SIZE, TAIL_TRACK)
TAIL_X, TAIL_Y = int(W / 2 - TAIL_W / 2), 678
assert TAIL_X >= 120 and TAIL_Y >= 120 and TAIL_X + TAIL_W <= W - 120

tail_mask = Image.new("L", (W, H), 0)
dtm = ImageDraw.Draw(tail_mask)
draw_text_tracked(dtm, TAIL_TEXT, TAIL_X, TAIL_Y, TAIL_SIZE, TAIL_TRACK)
tail_canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(pad)
half = max(360, TAIL_W // 2 + 120)
pd.rectangle([(W // 2 - half, TAIL_Y - 7), (W // 2 + half, TAIL_Y + TAIL_SIZE + 12)], fill=(0, 0, 0, 255))
pad = pad.filter(ImageFilter.GaussianBlur(12))
pad.putalpha(pad.getchannel("A").point(lambda v: int(v * 0.17)))
tail_canvas = Image.alpha_composite(tail_canvas, pad)
sh3 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh3.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (1, 1), tail_mask)
sh3 = sh3.filter(ImageFilter.GaussianBlur(1.2))
sh3.putalpha(sh3.getchannel("A").point(lambda v: int(v * 0.30)))
tail_txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
tail_txt.paste(Image.new("RGBA", (W, H), SUB_GOLD + (255,)), (0, 0), tail_mask)
tail_txt.putalpha(tail_txt.getchannel("A").point(lambda v: int(v * 0.88)))  # C1 v2: 72%→88%（声明可读优先）
tail_canvas = Image.alpha_composite(tail_canvas, sh3)
tail_canvas = Image.alpha_composite(tail_canvas, tail_txt)
ovt = ImageDraw.Draw(tail_canvas, "RGBA")
# 两侧单笔画小楔形（判读 v2：弃双笔复合=去 ⚠ 观感·单右向楔呼应铭文带）
wedge_stroke(ovt, TAIL_X - 58, TAIL_Y + 10, "r", head=9, tail=13, color=SUB_GOLD, alpha=66)
wedge_stroke(ovt, TAIL_X + TAIL_W + 36, TAIL_Y + 10, "r", head=9, tail=13, color=SUB_GOLD, alpha=66)

out2 = os.path.join(HERE, "tail_credit_v55.png")
tail_canvas.save(out2)
print("TAIL   -> %s  %dpx@88%% @(%d,%d) width=%d" % (out2, TAIL_SIZE, TAIL_X, TAIL_Y, TAIL_W))

# ---------- ③ 自验证预览板（叠净底帧·底片取自 full_mv_v54.mp4 最新成片）----------
import subprocess
PROBE = os.path.join(HERE, "v55_probe")
os.makedirs(PROBE, exist_ok=True)
bg_t = os.path.join(PROBE, "bg_int2_39.jpg")
subprocess.run(["ffmpeg", "-y", "-ss", "3.90", "-i", os.path.join(HERE, "full_mv_v54.mp4"),
                "-frames:v", "1", "-q:v", "3", bg_t], capture_output=True)
bg_w = os.path.join(PROBE, "tail_now_232.jpg")
subprocess.run(["ffmpeg", "-y", "-ss", "232.60", "-i", os.path.join(HERE, "full_mv_v54.mp4"),
                "-frames:v", "1", "-q:v", "3", bg_w], capture_output=True)
cw, ch = 672, 384
board = Image.new("RGB", (2 * (cw + 6), ch + 34), (12, 12, 14))
db = ImageDraw.Draw(board)
fb = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
db.text((8, 6), "V55 cards preview: L=title over INT2@3.9s | R=tail credit over Z04@232.6s", fill=(255, 220, 120), font=fb)
for i, (bg, card) in enumerate(((bg_t, out1), (bg_w, out2))):
    if os.path.isfile(bg):
        f = Image.open(bg).convert("RGB").resize((cw, ch))
        c = Image.open(card).resize((cw, ch))
        f.paste(c, (0, 0), c)
        board.paste(f, (i * (cw + 6), 30))
bp = os.path.join(PROBE, "V55-CARDS-PREVIEW.jpg")
board.save(bp, quality=92)
print("PREVIEW ->", bp)
