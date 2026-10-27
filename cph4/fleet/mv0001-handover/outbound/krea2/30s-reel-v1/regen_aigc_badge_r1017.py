# -*- coding: utf-8 -*-
# regen_aigc_badge_r1017.py - AIGC badge contrast fix (V5 proxy review item #2):
# white@40% too weak -> white@80% + soft dark backing (offset 1,1 blur 1.2 @60%)
# soft-shadow law kept (no hard stroke). Output overwrites aigc_badge.png.
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1344, 768
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
OUT = os.path.join(HERE, "aigc_badge.png")
FONT_CHAIN = [
    r"C:\Windows\Fonts\NotoSerifCJKsc-Medium.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Medium.otf",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]

text = "AI 生成内容"
font = None
for c in FONT_CHAIN:
    if os.path.isfile(c):
        font = ImageFont.truetype(c, 32)
        break
assert font, "no CJK font"

tmp = ImageDraw.Draw(Image.new("L", (W, H), 0))
bb = tmp.textbbox((0, 0), text, font=font)
tw = bb[2] - bb[0]
x, y = W - 120 - tw, H - 80

mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
dm.text((x, y), text, font=font, fill=255)

# dual-layer soft dark backing (r1017 multimodal review: single 1px fringe too thin):
#   A) centered soft pad  blur 2.4 @55%  — visible dark plate under glyphs
#   B) offset (1,1) drop blur 1.2 @60%   — directional shadow (2001 质感·禁硬描边)
black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
shA = Image.new("RGBA", (W, H), (0, 0, 0, 0))
shA.paste(black, (0, 0), mask)
shA = shA.filter(ImageFilter.GaussianBlur(2.4))
# V5.3 strengthen (CEO O-20261017-1330 full-coverage recheck: floor too low, backing too thin):
# white@88%, backing A@70% B@75%, font 32px (+14%). Fade-in timing handled in build (d=0.5).
shA.putalpha(shA.getchannel("A").point(lambda v: int(v * 0.70)))
shB = Image.new("RGBA", (W, H), (0, 0, 0, 0))
shB.paste(black, (1, 1), mask)
shB = shB.filter(ImageFilter.GaussianBlur(1.2))
shB.putalpha(shB.getchannel("A").point(lambda v: int(v * 0.75)))
sh = Image.alpha_composite(shA, shB)

# main text white @80%
txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
white = Image.new("RGBA", (W, H), (255, 255, 255, 255))
txt.paste(white, (0, 0), mask)
txt.putalpha(txt.getchannel("A").point(lambda v: int(v * 0.88)))

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
canvas = Image.alpha_composite(canvas, sh)
canvas = Image.alpha_composite(canvas, txt)
canvas.save(OUT)
print("SAVED %s white@80%% + soft dark backing @60%%" % OUT)
