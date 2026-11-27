# -*- coding: utf-8 -*-
# make_title_sub_r1017.py — 歌名卡副标版（CEO 令 2026-10-17：「可以 尽快出成片，然后歌曲名下面也给我加上 大喵没鱼吃 搭配好看点！」）
# 承 make_title_2line.py 双行主标定谳几何与视觉配方（爱在/西元前 一字未动），仅追加副标行。
# 副标选位（2026-10-17·INT2 5.5s 实帧多模态实测）：
#   人物躯干在 y≈300-360 肩线带右缘伸至 x≈1070-1120（暗外套+暗背景=暗叠暗可读）；
#   → 副标 32px·track 0.25·中轴对齐主标块（1105）·y=320（主标二行底 291 下方 29px）
#   左端「喵」半字压肩线暗区，金+软投影+光晕三件套保可读；画缘律全项合法（1201≤1224·352≤648）。
#   宽字距用 track 0.25 而非全角空格（全角空格版宽 288 越右缘律 1224）。
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = (233, 200, 122)  # #E9C87A
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

# 主标双行（承 make_title_2line.py 定谳几何·一字未动）
LINES = [("爱在", 1028, 125, 76, 0.05), ("西元前", 988, 215, 76, 0.05)]
# 副标（CEO 令）：小一号同金·宽字距·中轴对齐主标块
SUB_TEXT, SUB_SIZE, SUB_TRACK, SUB_X, SUB_Y = "大喵没鱼吃", 32, 0.25, 1009, 320
TITLE_AXIS = 1105.0  # 主标两行中轴（爱在 1105.5 / 西元前 1105 → 取 1105）

def line_width(text, size, track):
    step = size + int(size * track)
    return step * len(text) - int(size * track)

def edge_law():
    for text, x, y, size, track in LINES:
        w = line_width(text, size, track)
        if x < 120 or y < 120 or x + w > W - 120 or y + size > H - 120:
            raise SystemExit("PLACEMENT VIOLATION: line %r (%d,%d)+w=%d breaks >=120px edge law" % (text, x, y, w))
    w = line_width(SUB_TEXT, SUB_SIZE, SUB_TRACK)
    if SUB_X < 120 or SUB_Y < 120 or SUB_X + w > W - 120 or SUB_Y + SUB_SIZE > H - 120:
        raise SystemExit("PLACEMENT VIOLATION: subtitle %r (%d,%d)+w=%d breaks >=120px edge law" % (SUB_TEXT, SUB_X, SUB_Y, w))
    sub_c = SUB_X + w / 2.0
    if abs(sub_c - TITLE_AXIS) > 1.0:
        raise SystemExit("AXIS MISALIGNED: subtitle center %.1f vs title axis %.1f" % (sub_c, TITLE_AXIS))

edge_law()

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# 全部文字共用同一 alpha mask → 主标/副标同一配方一体化渲染（软投影+光晕+主字）
mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)

def draw_line(text, x, y, size, track):
    step = size + int(size * track)
    cx = x
    f = pick_font(size)
    for ch in text:
        dm.text((cx, y), ch, font=f, fill=255)
        cx += step

for text, x, y, size, track in LINES:
    draw_line(text, x, y, size, track)
draw_line(SUB_TEXT, SUB_X, SUB_Y, SUB_SIZE, SUB_TRACK)

# soft dark shadow: offset (2,2), blur 1.5, 40%
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
sh.paste(black, (2, 2), mask)
sh = sh.filter(ImageFilter.GaussianBlur(1.5))
sh.putalpha(sh.getchannel("A").point(lambda v: int(v * 0.40)))
canvas = Image.alpha_composite(canvas, sh)

# warm gold glow 3px @30%
glow_base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gold_full = Image.new("RGBA", (W, H), GOLD + (255,))
glow_base.paste(gold_full, (0, 0), mask)
glow = glow_base.filter(ImageFilter.GaussianBlur(3))
glow.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.30)))
canvas = Image.alpha_composite(canvas, glow)

# main text @95%
txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
txt.paste(gold_full, (0, 0), mask)
txt.putalpha(txt.getchannel("A").point(lambda v: int(v * 0.95)))
canvas = Image.alpha_composite(canvas, txt)

out = os.path.join(HERE, "title_card.png")
canvas.save(out)
print("SAVED %s two-line title + subtitle %r@(%d,%d) size=%d track=%.2f width=%d" % (
    out, SUB_TEXT, SUB_X, SUB_Y, SUB_SIZE, SUB_TRACK, line_width(SUB_TEXT, SUB_SIZE, SUB_TRACK)))
