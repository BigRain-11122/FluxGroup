# -*- coding: ascii -*-
# build_s7r_strips_r1058.py - two full-resolution before/after comparison
# strips for the S7 remediation evidence pack (bm-c r1058):
#   strip1: S5-26_s20185 sky-banding case: orig | A grain | C esrgan+down
#   strip2: S0-03_s20027 oily-highlight case: orig | A grain | B shoulder+grain
# Full 1344x768 cells so banding / specular differences stay visible.

import os

SRC = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch"
S7R = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch_s7r"
OUT1 = os.path.join(S7R, "xq-AB-S7R-COMPARE-S5-26-r1058.jpg")
OUT2 = os.path.join(S7R, "xq-AB-S7R-COMPARE-S0-03-r1058.jpg")


def strip(paths, labels, out):
    from PIL import Image, ImageDraw
    imgs = []
    for p in paths:
        img = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(img)
        w, h = img.size
        d.rectangle((0, 0, w, 20), fill=(0, 0, 0))
        d.text((6, 4), labels[len(imgs)], fill=(255, 255, 255))
        imgs.append(img)
    w, h = imgs[0].size
    s = Image.new("RGB", (w, h * len(imgs)), (24, 24, 24))
    for i, im in enumerate(imgs):
        s.paste(im, (0, i * h))
    s.save(out, quality=88)
    print("STRIP %s %dB" % (os.path.basename(out), os.path.getsize(out)))


def main():
    name = "S5-26_s20185"
    strip([os.path.join(SRC, name + ".png"),
           os.path.join(S7R, name + "_s7rA.png"),
           os.path.join(S7R, name + "_s7rC.png")],
          ["S5-26_s20185 ORIGINAL (sky banding)", "A grain-only (0.14)",
           "C esrgan-x4 + LANCZOS down"], OUT1)
    name = "S0-03_s20027"
    strip([os.path.join(SRC, name + ".png"),
           os.path.join(S7R, name + "_s7rA.png"),
           os.path.join(S7R, name + "_s7rB.jpg")],
          ["S0-03_s20027 ORIGINAL (oily speculars)",
           "A grain-only (0.14)", "B highlight-shoulder + grain"], OUT2)


if __name__ == "__main__":
    main()
