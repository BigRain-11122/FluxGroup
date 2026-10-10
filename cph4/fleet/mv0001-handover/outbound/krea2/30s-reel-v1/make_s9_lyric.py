# -*- coding: utf-8 -*-
# make_s9_lyric.py - S9 金字层渲染（文字席 spec·受众席「叠字不叠脸」定谳落地件）
# 「我却在旁静静欣赏你」单行 9 字·深金 #E9C87A @ alpha 0.85·3px 暖金外晕 @30%·字距 0.2em
# 用法: python make_s9_lyric.py --x 560 --y 150 [--size 68] [--tracking 0.2] [--font <path>] [--out <png>]
# 选位律(拿到 KF9 实帧后多模态检后定 --x/--y):
#   最暗琥珀区·文字框与人脸 bbox 间隔 >=60px·距画缘 >=120px·避开玻璃高光带
#   侧脸朝左→字上右侧·朝右→字上左侧（文字块宽 = 9*size*(1+tracking)·先算后选避出缘）
# 字体链: 思源宋体 Heavy/Noto Serif CJK SC Black(碑刻衬线骨架·OFL) → 兜底 simhei
import argparse, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CANDIDATE_FONTS = [
    r"C:\Windows\Fonts\NotoSerifCJKsc-Black.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Heavy.otf",
    r"C:\Windows\Fonts\SourceHanSerifSC-Bold.otf",
    r"C:\Windows\Fonts\simhei.ttf",
]
TEXT = "我却在旁静静欣赏你"
GOLD = (233, 200, 122)  # #E9C87A 深金(「字=光」同族·零冷色律内)
W, H = 1344, 768


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", type=int, required=True, help="text block top-left x px")
    ap.add_argument("--y", type=int, required=True, help="text block top-left y px")
    ap.add_argument("--size", type=int, default=68)
    ap.add_argument("--tracking", type=float, default=0.2, help="tracking in em (0.18-0.22 spec)")
    ap.add_argument("--alpha", type=float, default=0.85)
    ap.add_argument("--glow", type=int, default=3)
    ap.add_argument("--font", default="")
    ap.add_argument("--out", default=r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\s9_lyric.png")
    args = ap.parse_args()

    font_path = args.font
    if not font_path:
        for c in CANDIDATE_FONTS:
            if os.path.isfile(c):
                font_path = c
                break
    if not font_path:
        raise SystemExit("NO FONT FOUND - pass --font <path to CJK serif ttf/otf>")
    font = ImageFont.truetype(font_path, args.size)

    step = args.size + int(args.size * args.tracking)
    block_w = step * len(TEXT) - int(args.size * args.tracking)
    if args.x < 120 or args.y < 40 or args.x + block_w > W - 120 or args.y + args.size > H - 40:
        raise SystemExit("PLACEMENT VIOLATION: block (%d,%d)+w=%d exceeds >=120px edge margin law" % (args.x, args.y, block_w))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = args.x
    for ch in TEXT:
        d.text((x, args.y), ch, font=font, fill=GOLD + (255,))
        x += step

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = layer.filter(ImageFilter.GaussianBlur(args.glow))
    ga = glow.getchannel("A").point(lambda v: int(v * 0.30))
    glow.putalpha(ga)
    canvas = Image.alpha_composite(canvas, glow)
    ta = layer.getchannel("A").point(lambda v: int(v * args.alpha))
    layer.putalpha(ta)
    canvas = Image.alpha_composite(canvas, layer)
    canvas.save(args.out)
    print("SAVED %s  text-block=(%d,%d) w=%d h~%d  font=%s  alpha=%.2f glow=%dpx@30%%"
          % (args.out, args.x, args.y, block_w, args.size, os.path.basename(font_path), args.alpha, args.glow))


if __name__ == "__main__":
    main()
