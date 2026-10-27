# -*- coding: utf-8 -*-
# make_title_2line.py — 歌名卡双行版（V5 INT2 实帧选位终版·承 make_text_layers.py gen_title 视觉配方）
# 选位律裁定（2026-10-17 导演席·三帧画框多模态实证）：
#   76px 单行在上带几何无解（头/发梢右缘实测 x≈950·右侧净空 354px<440px）
#   → 保字号 76px·单行让位双行：「爱在」(1028,125) /「西元前」(988,215) 中轴对齐锁排
#   皮肤缘净距 ≥73px·发梢最差帧 38px（暗叠暗无害）·右缘 1222≤1224·上缘 125≥120 全合法
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

LINES = [("爱在", 1028, 125), ("西元前", 988, 215)]
SIZE = 76
TRACK = 0.05   # 双行锁排用紧字距（单行时代 0.2 的字距在 440px 放不下——见裁定头注）

def edge_law():
    for text, x, y in LINES:
        step = SIZE + int(SIZE * TRACK)
        w = step * len(text) - int(SIZE * TRACK)
        if x < 120 or y < 120 or x + w > W - 120 or y + SIZE > H - 120:
            raise SystemExit("PLACEMENT VIOLATION: line %r (%d,%d)+w=%d breaks >=120px edge law" % (text, x, y, w))

edge_law()
font = pick_font(SIZE)
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# layer A: text alpha mask（双行）
mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
for text, x, y in LINES:
    step = SIZE + int(SIZE * TRACK)
    cx = x
    for ch in text:
        dm.text((cx, y), ch, font=font, fill=255)
        cx += step

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
print("SAVED %s two-line title: %r@(1028,125) + %r@(988,215) size=%d track=%.2f" % (out, "爱在", "西元前", SIZE, TRACK))
