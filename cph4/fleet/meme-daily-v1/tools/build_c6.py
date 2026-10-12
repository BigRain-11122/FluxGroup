#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_c6.py - V1 拍6 下架按钮合成帧（generic UI·零平台签名）
产出: media/c6.png (720x1280)
构成: 暗底 + 居中视频卡片(去饱和 S3 封面灰罩+ⓧ角标+进度条时间码=仍在播放锚)
      + 「该内容已因权利方投诉下架」(退居语境) + 高对比首读用户评论「还好我踩得慢」
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

MEDIA = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\meme-daily-v1\outbound\v1-zunjie-brake\media"
W, H = 720, 1280
BG = (14, 14, 18)
CARD = (32, 32, 38)

def font(size, bold=True):
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    for p in (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.truetype("C:\Windows\Fonts\msyh.ttc", size)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# —— 视频卡片（居中偏上）——
cw, ch = 640, 400
cx0, cy0 = (W - cw) // 2, 300
d.rounded_rectangle([cx0 - 4, cy0 - 4, cx0 + cw + 4, cy0 + ch + 4], radius=18, fill=(44, 44, 52))
d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=14, fill=(20, 20, 26))

# 灰掉的本片封面 = S3 去饱和裁切
try:
    s3 = Image.open(MEDIA + r"\S3.png").convert("RGB")
    s3 = s3.crop((0, 0, s3.width, int(s3.width * ch / cw)))
    s3 = s3.resize((cw, ch))
    s3 = ImageEnhance.Color(s3).enhance(0.0)          # 去饱和
    s3 = ImageEnhance.Brightness(s3).enhance(0.55)   # 压暗
    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw, ch], radius=14, fill=255)
    img.paste(s3, (cx0, cy0), mask)
except FileNotFoundError:
    d.rectangle([cx0, cy0, cx0 + cw, cy0 + ch], fill=(30, 30, 36))

# 灰罩 + ⓧ（叉角标）
ov = Image.new("RGBA", (cw, ch), (120, 120, 128, 90))
img.paste(Image.alpha_composite(Image.new("RGBA", (cw, ch), (0, 0, 0, 0)), ov).convert("RGB"),
          (cx0, cy0), mask)
xx, yy = cx0 + cw // 2, cy0 + ch // 2
d.ellipse([xx - 54, yy - 54, xx + 54, yy + 54], fill=(148, 148, 156))
d.line([xx - 26, yy - 26, xx + 26, yy + 26], fill=(60, 60, 66), width=9)
d.line([xx - 26, yy + 26, xx + 26, yy - 26], fill=(60, 60, 66), width=9)

# 进度条+时间码（仍在播放锚）
pw = cw - 40
d.rounded_rectangle([cx0 + 20, cy0 + ch - 26, cx0 + 20 + pw, cy0 + ch - 14], radius=6, fill=(70, 70, 78))
d.rounded_rectangle([cx0 + 20, cy0 + ch - 26, cx0 + 20 + int(pw * 0.93), cy0 + ch - 14], radius=6, fill=(188, 188, 198))
tf = font(22)
d.text((cx0 + 20, cy0 + ch + 10), "00:14 / 00:15", fill=(170, 170, 178), font=tf)

# —— 下架通知（退居语境·灰）——
nf = font(30, bold=False)
t = "该内容已因权利方投诉下架"
tw = d.textlength(t, font=nf)
d.text(((W - tw) // 2, cy0 + ch + 72), t, fill=(150, 150, 158), font=nf)

# —— 高对比首读：用户评论 ——
av = (W // 2) - 210, cy0 + ch + 170
d.ellipse([av[0], av[1], av[0] + 56, av[1] + 56], fill=(90, 90, 100))
d.rounded_rectangle([av[0] + 76, av[1] + 8, av[0] + 220, av[1] + 22], radius=7, fill=(90, 90, 100))
cf = font(44)
ct = "还好我踩得慢"
d.text((av[0], av[1] + 84), ct, fill=(255, 255, 255), font=cf)

out = MEDIA + r"\c6.png"
img.save(out)
print("OK", out)
