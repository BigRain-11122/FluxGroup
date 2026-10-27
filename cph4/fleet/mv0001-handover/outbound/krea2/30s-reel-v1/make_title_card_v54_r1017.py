# -*- coding: utf-8 -*-
# make_title_card_v54_r1017.py — V5.4 歌名卡+片尾声明卡 重设计（CEO 终审令 2026-10-17：
#   「爱在西元前的片头歌曲名好好设计」「大喵没鱼吃也好好设计，在画面里要美观」
#   +「注明欢迎转载，请注明出处」）
# 设计定谳（TITLE-TAIL-AUDIT 多模态判读·2026-10-17 夜）：
#   版式：右侧暗窗格内「碑刻展签」位——主标单行横排（弃 2+3 断行），右缘退足 ≥110px 画边距；
#   层级：主标 56px 鎏金渐变 / 署名 22px 灰金降一档 落款式 / 上方楔形符号带 3 枚 25%；
#   质感：鎏金竖渐变 #F0D9A0→#C89B4E + 笔画内泥板颗粒 8% + 2px 柔影；克制·无全屏叠加；
#   尾声明：「欢迎转载，请注明出处：大喵没鱼吃」19px 灰金 @70% 底部居中 y≈90% + 两侧小楔形。
# 断言律承 make_title_sub_r1017.py：画缘律 ≥120px（尾声明居中行按横向缘核）+ 中轴对齐 ±1px。
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
AXIS = 1068.0            # 主标块中轴（右缘退足 120px 画边距后的几何心）

GOLD_TOP = (240, 217, 160)   # #F0D9A0 鎏金亮
GOLD_BOT = (182, 136, 64)    # #B68840 鎏金沉底（V5.4 验收微调·压深 9%）
SUB_GOLD = (199, 177, 131)   # #C7B183 灰金（署名/尾声明降档色）
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

def wedge_glyph_band(draw, cx, y, n=3, w=11, h=9, gap=16, color=GOLD_TOP, alpha=64):
    """row of small cuneiform-wedge triangles, centered on cx"""
    total = n * w + (n - 1) * gap
    x0 = cx - total // 2
    for i in range(n):
        bx = x0 + i * (w + gap)
        # downward-pointing stylus wedge (cuneiform sign head)
        draw.polygon([(bx, y), (bx + w, y), (bx + w // 2, y + h)],
                     fill=color + (alpha,))

# ---------- shared render: mask -> shadow + gold gradient + grain ----------
def render_block(mask, grad_span=None, grain=0.08, alpha_main=0.97):
    """mask: L image. returns RGBA block composited per V5.4 typography recipe."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # soft dark shadow (2,2) blur 1.5 @42%
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    sh.paste(black, (2, 2), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(1.5))
    sh.putalpha(sh.getchannel("A").point(lambda v: int(v * SHADOW)))
    canvas = Image.alpha_composite(canvas, sh)
    # gold vertical gradient clipped to mask
    ys, xs = np.where(np.asarray(mask) > 0)
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    g = np.asarray(grad).copy()
    if len(ys):
        y0, y1 = ys.min(), ys.max()
        for yy in range(y0, y1 + 1):
            t = (yy - y0) / max(1, (y1 - y0))
            col = [int(GOLD_TOP[k] * (1 - t) + GOLD_BOT[k] * t) for k in range(3)] + [255]
            g[yy, :, :] = col
    grad = Image.fromarray(g)
    solid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    solid.paste(grad, (0, 0), mask)
    # clay-tablet grain inside strokes (8% speckle)
    rng = np.random.default_rng(41017)
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

# ---------- ① 歌名卡 title_card_v54.png ----------
MAIN_TEXT, MAIN_SIZE, MAIN_TRACK = "爱在西元前", 56, 0.15
SUB_TEXT,  SUB_SIZE,  SUB_TRACK  = "大喵没鱼吃", 22, 0.30
MAIN_W = line_width(MAIN_TEXT, MAIN_SIZE, MAIN_TRACK)     # 312
MAIN_X, MAIN_Y = int(AXIS - MAIN_W / 2), 214              # 主标 y 214-270
SUB_W = line_width(SUB_TEXT, SUB_SIZE, SUB_TRACK)         # 134
SUB_X, SUB_Y = int(AXIS - SUB_W / 2), 292                 # 落款距 22px 主标底
BAND_Y = 188                                              # 楔形符号带

def edge_law_check(x, y, w, h, margin=120):
    assert x >= margin and y >= margin and x + w <= W - margin and y + h <= H - margin, \
        "PLACEMENT VIOLATION: (%d,%d)+%dx%d vs %dpx edge law" % (x, y, w, h, margin)

edge_law_check(MAIN_X, MAIN_Y, MAIN_W, MAIN_SIZE)
edge_law_check(SUB_X, SUB_Y, SUB_W, SUB_SIZE)

mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
draw_text_tracked(dm, MAIN_TEXT, MAIN_X, MAIN_Y, MAIN_SIZE, MAIN_TRACK)
title_canvas = render_block(mask, grain=0.08, alpha_main=0.97)

# 署名：灰金降档·落款（不做鎏金渐变·扁平一级+柔影更稳）
sub_mask = Image.new("L", (W, H), 0)
dsm = ImageDraw.Draw(sub_mask)
draw_text_tracked(dsm, SUB_TEXT, SUB_X, SUB_Y, SUB_SIZE, SUB_TRACK)
sh2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh2.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (1, 1), sub_mask)
sh2 = sh2.filter(ImageFilter.GaussianBlur(1.2))
sh2.putalpha(sh2.getchannel("A").point(lambda v: int(v * 0.38)))
sub_txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sub_txt.paste(Image.new("RGBA", (W, H), SUB_GOLD + (255,)), (0, 0), sub_mask)
sub_txt.putalpha(sub_txt.getchannel("A").point(lambda v: int(v * 0.97)))
title_canvas = Image.alpha_composite(title_canvas, sh2)
title_canvas = Image.alpha_composite(title_canvas, sub_txt)

# 楔形符号带（主标上方·3 枚 25% 金）
ov = ImageDraw.Draw(title_canvas, "RGBA")
wedge_glyph_band(ov, int(AXIS), BAND_Y, n=3, w=11, h=9, gap=16, color=GOLD_TOP, alpha=140)

out1 = os.path.join(HERE, "title_card_v54.png")
title_canvas.save(out1)
print("TITLE  -> %s  main=%dpx@(%d,%d) axis=%d sub=%dpx@(%d,%d)" % (
    out1, MAIN_SIZE, MAIN_X, MAIN_Y, AXIS, SUB_SIZE, SUB_X, SUB_Y))

# ---------- ② 片尾声明卡 tail_credit_v54.png ----------
TAIL_TEXT = "欢迎转载，请注明出处：大喵没鱼吃"
TAIL_SIZE, TAIL_TRACK = 19, 0.25
TAIL_W = line_width(TAIL_TEXT, TAIL_SIZE, TAIL_TRACK)     # 341
TAIL_X, TAIL_Y = int(W / 2 - TAIL_W / 2), 682             # 基线带 y≈90% 画高
assert TAIL_X >= 120 and TAIL_Y >= 120 and TAIL_X + TAIL_W <= W - 120

tail_mask = Image.new("L", (W, H), 0)
dtm = ImageDraw.Draw(tail_mask)
draw_text_tracked(dtm, TAIL_TEXT, TAIL_X, TAIL_Y, TAIL_SIZE, TAIL_TRACK)
tail_canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
# 横向暗化垫带（720x36 @16% 羽化 12px·V5.4 验收微调：保换底帧可读）
pad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(pad)
pd.rectangle([(W // 2 - 360, TAIL_Y - 6), (W // 2 + 360, TAIL_Y + TAIL_SIZE + 10)], fill=(0, 0, 0, 255))
pad = pad.filter(ImageFilter.GaussianBlur(12))
pad.putalpha(pad.getchannel("A").point(lambda v: int(v * 0.16)))
tail_canvas = Image.alpha_composite(tail_canvas, pad)
sh3 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh3.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (1, 1), tail_mask)
sh3 = sh3.filter(ImageFilter.GaussianBlur(1.2))
sh3.putalpha(sh3.getchannel("A").point(lambda v: int(v * 0.30)))
tail_txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
tail_txt.paste(Image.new("RGBA", (W, H), SUB_GOLD + (255,)), (0, 0), tail_mask)
tail_txt.putalpha(tail_txt.getchannel("A").point(lambda v: int(v * 0.72)))  # 72% 灰金
tail_canvas = Image.alpha_composite(tail_canvas, sh3)
tail_canvas = Image.alpha_composite(tail_canvas, tail_txt)
ovt = ImageDraw.Draw(tail_canvas, "RGBA")
# 两侧小楔形（落款—声明 首尾呼应）
wedge_glyph_band(ovt, TAIL_X - 46, TAIL_Y + 5, n=1, w=10, h=8, gap=0, color=SUB_GOLD, alpha=56)
wedge_glyph_band(ovt, TAIL_X + TAIL_W + 40, TAIL_Y + 5, n=1, w=10, h=8, gap=0, color=SUB_GOLD, alpha=56)

out2 = os.path.join(HERE, "tail_credit_v54.png")
tail_canvas.save(out2)
print("TAIL   -> %s  %dpx@(%d,%d) width=%d" % (out2, TAIL_SIZE, TAIL_X, TAIL_Y, TAIL_W))

# ---------- ③ 自验证预览板（叠净底帧） ----------
# 净底帧需为无字帧：title 用 3.90s（卡窗 4.2 起前·INT2 场景内）、tail 用 232.60s
import subprocess
PROBE = os.path.join(HERE, "v54_probe")
bg_t = os.path.join(PROBE, "bg_int2_39.jpg")
subprocess.run(["ffmpeg", "-y", "-ss", "3.90", "-i", os.path.join(HERE, "full_mv_v53.mp4"),
                "-frames:v", "1", "-q:v", "3", bg_t], capture_output=True)
bg_w = os.path.join(PROKE := PROBE, "tail_now_232.jpg")
cw, ch = 672, 384
board = Image.new("RGB", (2 * (cw + 6), ch + 34), (12, 12, 14))
db = ImageDraw.Draw(board)
fb = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
db.text((8, 6), "V54 cards preview: L=title over INT2@3.9s | R=tail credit over Z04@232.6s", fill=(255, 220, 120), font=fb)
for i, (bg, card) in enumerate(((bg_t, out1), (bg_w, out2))):
    if os.path.isfile(bg):
        f = Image.open(bg).convert("RGB").resize((cw, ch))
        c = Image.open(card).resize((cw, ch))
        f.paste(c, (0, 0), c)
        board.paste(f, (i * (cw + 6), 30))
bp = os.path.join(PROBE, "V54-CARDS-PREVIEW.jpg")
board.save(bp, quality=92)
print("PREVIEW ->", bp)
