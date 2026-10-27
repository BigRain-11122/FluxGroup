# -*- coding: ascii -*-
# build_s107_top3_strip_r1058.py - native-resolution strip of the top-3
# S1-07 T1-1R seeds for the zoom re-check pass (first-choice confirmation).

import os

SRC = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\t1r1"
OUT = os.path.join(SRC, "s107_top3_strip_r1058.png")
TOP = ["s21012", "s21002", "s21000"]


def main():
    from PIL import Image, ImageDraw
    imgs = []
    for s in TOP:
        img = Image.open(os.path.join(SRC, "S1-07_%s.png" % s)).convert("RGB")
        d = ImageDraw.Draw(img)
        w, h = img.size
        d.rectangle((0, 0, w, 18), fill=(0, 0, 0))
        d.text((5, 4), "S1-07_" + s + " (native 672x384)", fill=(255, 255, 255))
        imgs.append(img)
    w, h = imgs[0].size
    strip = Image.new("RGB", (w, h * len(imgs)), (24, 24, 24))
    for i, im in enumerate(imgs):
        strip.paste(im, (0, i * h))
    strip.save(OUT)
    print("STRIP-OK %s %dB" % (OUT, os.path.getsize(OUT)))


if __name__ == "__main__":
    main()
