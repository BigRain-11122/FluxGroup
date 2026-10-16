# -*- coding: utf-8 -*-
# make_text_layers.py — V5 字层生成器（V5-TYPOGRAPHY-SPEC §一/§四 执法件·make_s9_lyric 变体）
# 1) title_card.png   歌名卡「爱在西元前」：76px 思源宋 Heavy·深金 #E9C87A + 暖金光晕 3px@30%
#    + 软暗投影 offset(2,2)@40%（禁硬描边——2001 质感=阴影不是描边）
#    选位律：INT2 窗 4.2-7.4s·最暗琥珀区/避脸 bbox>=60px/避画缘>=120px——默认 (690,160)·17 件到货后
#    按 INT2 s9904 正片帧多模态实定（定后改 --x --y 重生成）
# 2) aigc_badge.png   AIGC 开门帧标识「AI 生成内容」28px·白@40%·右下角整帧层（驻 3s·AIGC 标识办法）
# 3) s9_lyric.png     金句层按 TYPOGRAPHY §二 复核位重生成（默认 x=200 y=340·左侧暗带中央偏下）
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = (233, 200, 122)  # #E9C87A
CANDIDATE_FONTS = [
    r"C:\Windows\Fonts\NotoSerifCJKsc-Black.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Heavy.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Bold.otf",
    r"C:\Windows\Fonts\simsun.ttc",   # 宋体衬线（simsunb.ttf 实测缺字 tofu·勿用）
    r"C:\Windows\Fonts\simhei.ttf",
]


def pick_font(size, prefer_medium=False):
    chain = CANDIDATE_FONTS
    if prefer_medium:
        chain = [r"C:\Windows\Fonts\NotoSerifCJKsc-Medium.otf",
                 r"C:\Windows\Fonts\SourceHanSerifSC-Medium.otf"] + CANDIDATE_FONTS
    for c in chain:
        if os.path.isfile(c):
            return ImageFont.truetype(c, size)
    raise SystemExit("NO CJK FONT FOUND")


def draw_text(draw, xy, text, font, fill):
    draw.text(xy, text, font=font, fill=fill)


def gen_title(x=690, y=160, size=76, tracking=0.2, out=""):
    """歌名卡：深金字 + 软暗投影(2,2)@40% + 暖金光晕 3px@30%"""
    text = "爱在西元前"
    font = pick_font(size)
    step = size + int(size * tracking)
    block_w = step * len(text) - int(size * tracking)
    if x < 120 or y < 120 or x + block_w > W - 120 or y + size > H - 120:
        raise SystemExit("PLACEMENT VIOLATION: title block (%d,%d)+w=%d breaks >=120px edge law (x must be in [120,%d])"
                         % (x, y, block_w, W - 120 - block_w))
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # layer A: text alpha mask
    mask = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(mask)
    cx = x
    for ch in text:
        dm.text((cx, y), ch, font=font, fill=255)
        cx += step
    # soft dark shadow: offset (2,2), blur, 40%
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
    out = out or os.path.join(HERE, "title_card.png")
    canvas.save(out)
    print("SAVED %s title block=(%d,%d) w=%d size=%d shadow(2,2)@40%%+glow3px@30%%" % (out, x, y, block_w, size))
    return out


def gen_aigc(out=""):
    """AIGC 标识：右下角「AI 生成内容」28px 白@40%·整帧透明层（装配 overlay 0:0）"""
    text = "AI 生成内容"
    font = pick_font(28, prefer_medium=True)
    tmp = ImageDraw.Draw(Image.new("L", (W, H), 0))
    bb = tmp.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    x, y = W - 120 - tw, H - 80
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.text((x, y), text, font=font, fill=(255, 255, 255, 102))  # 白 40%
    out = out or os.path.join(HERE, "aigc_badge.png")
    canvas.save(out)
    print("SAVED %s aigc badge (%d,%d) 28px white@40%%" % (out, x, y))
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--title-x", type=int, default=690)
    ap.add_argument("--title-y", type=int, default=160)
    ap.add_argument("--s9-x", type=int, default=200)
    ap.add_argument("--s9-y", type=int, default=340)
    a = ap.parse_args()
    gen_title(a.title_x, a.title_y)
    gen_aigc()
    print("NEXT: python make_s9_lyric.py --x %d --y %d  (S9 golden-line re-gen at V5 reviewed default; "
          "re-check against INT2/S9 actual frames when the 17-batch lands)" % (a.s9_x, a.s9_y))
