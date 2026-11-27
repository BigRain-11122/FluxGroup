#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contact_sheet.py - 生成带标签的缩略图总览，供人眼验收素材。

为什么：素材质量闸只能判格式，主题对不对、有没有品牌 logo 必须人眼看。
把一整个目录排成一张图，一次看完，比逐张打开快一个数量级。

用法：
  python3 Tools/fleet/contact_sheet.py --dir <dir> --out /tmp/sheet.png [--cols 5] [--thumb 320]
Exit: 0 生成成功；2 目录为空或不存在
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--thumb", type=int, default=320)
    ap.add_argument("--recursive", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        print("[sheet] 目录不存在（rc=2）")
        return 2
    files = []
    if a.recursive:
        for d, _s, fs in os.walk(a.dir):
            for n in sorted(fs):
                if n.lower().endswith(IMG):
                    files.append(os.path.join(d, n))
    else:
        files = [os.path.join(a.dir, n) for n in sorted(os.listdir(a.dir))
                 if n.lower().endswith(IMG)]
    if not files:
        print("[sheet] 无图片（rc=2）")
        return 2
    tw = a.thumb
    label_h = 22
    cols = a.cols
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (tw + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(files):
        try:
            with Image.open(p) as im:
                im = im.convert("RGB")
                im.thumbnail((tw - 8, tw - 8), Image.LANCZOS)
                x = (i % cols) * tw + (tw - im.width) // 2
                y = (i // cols) * (tw + label_h) + (tw - im.height) // 2
                sheet.paste(im, (x, y))
        except Exception as e:
            print("[sheet] 跳过 %s（%s）" % (os.path.basename(p), str(e)[:40]))
        lab = os.path.basename(p)[:34]
        draw.text(((i % cols) * tw + 6, (i // cols) * (tw + label_h) + tw + 4), lab, fill="black")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    sheet.save(a.out)
    print("[sheet] %d 张 -> %s（%dx%d）" % (len(files), a.out, sheet.width, sheet.height))
    return 0


if __name__ == "__main__":
    sys.exit(main())