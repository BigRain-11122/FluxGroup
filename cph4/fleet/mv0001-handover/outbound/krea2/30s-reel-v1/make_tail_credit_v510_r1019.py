# -*- coding: utf-8 -*-
# make_tail_credit_v510_r1019.py — V5.10 片尾出处字卡（CEO 令 2026-10-19「片尾写好 转载需注明出处 @大喵没鱼吃」）
# 风格=tail_credit_v55 正典复刻（make_title_card_v55_r1018.py ②节配方：24px@88%·SUB_GOLD·软垫带+阴影+两侧单笔楔形·y=678 全宽居中）
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1344, 768
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SUB_GOLD = (199, 177, 131)

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

def wedge_stroke(dr, x, y, direction, head=9, tail=13, color=SUB_GOLD, alpha=66, lw=3):
    c = color + (alpha,)
    if direction == "r":
        dr.polygon([(x, y - 4), (x, y + 4), (x + head, y)], fill=c)
        dr.line([(x + head, y), (x + head + tail, y)], fill=c, width=lw)

# ---- 片尾声明卡（CEO 10-19 新文本·v55 同风格）----
TAIL_TEXT = "转载需注明出处 @大喵没鱼吃"
TAIL_SIZE, TAIL_TRACK = 24, 0.25
TAIL_W = line_width(TAIL_TEXT, TAIL_SIZE, TAIL_TRACK)
TAIL_X, TAIL_Y = int(W / 2 - TAIL_W / 2), 678
assert TAIL_X >= 120 and TAIL_Y >= 120 and TAIL_X + TAIL_W <= W - 120, "edge law"

tail_mask = Image.new("L", (W, H), 0)
dtm = ImageDraw.Draw(tail_mask)
draw_text_tracked(dtm, TAIL_TEXT, TAIL_X, TAIL_Y, TAIL_SIZE, TAIL_TRACK)

tail_canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
# 软垫带（可读性优先·承 v55 C1 v2）
pad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(pad)
half = max(360, TAIL_W // 2 + 120)
pd.rectangle([(W // 2 - half, TAIL_Y - 7), (W // 2 + half, TAIL_Y + TAIL_SIZE + 12)], fill=(0, 0, 0, 255))
pad = pad.filter(ImageFilter.GaussianBlur(12))
pad.putalpha(pad.getchannel("A").point(lambda v: int(v * 0.17)))
tail_canvas = Image.alpha_composite(tail_canvas, pad)
# 软阴影
sh3 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh3.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (1, 1), tail_mask)
sh3 = sh3.filter(ImageFilter.GaussianBlur(1.2))
sh3.putalpha(sh3.getchannel("A").point(lambda v: int(v * 0.30)))
tail_canvas = Image.alpha_composite(tail_canvas, sh3)
# 文字本层（SUB_GOLD@88%）
tail_txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
tail_txt.paste(Image.new("RGBA", (W, H), SUB_GOLD + (255,)), (0, 0), tail_mask)
tail_txt.putalpha(tail_txt.getchannel("A").point(lambda v: int(v * 0.88)))
tail_canvas = Image.alpha_composite(tail_canvas, tail_txt)
# 两侧单笔画小楔形（v55 判读 v2 定款）
ovt = ImageDraw.Draw(tail_canvas, "RGBA")
wedge_stroke(ovt, TAIL_X - 58, TAIL_Y + 10, "r", head=9, tail=13, alpha=66)
wedge_stroke(ovt, TAIL_X + TAIL_W + 36, TAIL_Y + 10, "r", head=9, tail=13, alpha=66)

out2 = os.path.join(HERE, "tail_credit_v510.png")
tail_canvas.save(out2)
print("TAIL -> %s  %dpx@88%% @(%d,%d) width=%d text=%r" % (out2, TAIL_SIZE, TAIL_X, TAIL_Y, TAIL_W, TAIL_TEXT))

# ---- 自验证预览板（叠真实末镜帧 232.6s）----
import subprocess
FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
bg = os.path.join(HERE, "v510_probe")
os.makedirs(bg, exist_ok=True)
bgf = os.path.join(bg, "tail_bg_2326.jpg")
subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "232.60", "-i", os.path.join(HERE, "full_mv_v59.mp4"),
                "-frames:v", "1", "-q:v", "3", bgf], capture_output=True)
if os.path.isfile(bgf):
    f = Image.open(bgf).convert("RGB")
    c = Image.open(out2)
    f.paste(c, (0, 0), c)
    f.resize((960, 549)).save(os.path.join(bg, "V510-TAIL-PREVIEW.jpg"), quality=92)
    print("PREVIEW -> %s" % os.path.join(bg, "V510-TAIL-PREVIEW.jpg"))
