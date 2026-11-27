"""C2119b: regenerate the S5-26/27/28 4K compare board with correct height
(previous board cropped the second block's SRC row). Board-only, no re-burn."""
import json
import os

from PIL import Image, ImageDraw

REPO = r"K:\Fluxgroup\FluxGroup"
SRC_DIR = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "abatch_s7r")
OUT_DIR = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "s7r-4k")
BOARD = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4K-BOARD-c2119.jpg")

PAIRS = [
    ("S5-26", "S5-26_s20185_s7rC.png", "S5-26_s20185_s7rC_4k.png"),
    ("S5-26", "S5-26_s20191_s7rC.png", "S5-26_s20191_s7rC_4k.png"),
    ("S5-27", "S5-27_s20192_s7rC.png", "S5-27_s20192_s7rC_4k.png"),
    ("S5-27", "S5-27_s20193_s7rC.png", "S5-27_s20193_s7rC_4k.png"),
    ("S5-28", "S5-28_s20202_s7rC.png", "S5-28_s20202_s7rC_4k.png"),
    ("S5-28", "S5-28_s20205_s7rC.png", "S5-28_s20205_s7rC_4k.png"),
]

cw, ch, pad, lab = 768, 432, 12, 26
rows = [(i % 3, i // 3) for i in range(len(PAIRS))]
bw = 3 * cw + 4 * pad
bh = 2 * (2 * (ch + lab) + pad) + 2 * pad

board = Image.new("RGB", (bw, bh), (14, 14, 16))
d = ImageDraw.Draw(board)
# equal field of view on both sides: a fixed FRACTION window, so a 4K frame and
# its 1344x768 source show the same content (fixed-pixel windows on different
# resolutions was the C2119 board bug that made stars look "missing").
FW, FH = 0.5625, 0.5625


def frac_crop(im):
    w, h = im.size
    cx0 = int(w * 0.5 - w * FW / 2)
    cy0 = int(h * 0.42 - h * FH / 2)
    return im.crop((cx0, cy0, cx0 + int(w * FW), cy0 + int(h * FH))).resize((cw, ch), Image.LANCZOS)


for i, (shot, src_name, out_name) in enumerate(PAIRS):
    col, blk = i % 3, i // 3
    x = pad + col * (cw + pad)
    y4 = pad + blk * (2 * (ch + lab) + pad)
    ys = y4 + ch + lab
    im = Image.open(os.path.join(OUT_DIR, out_name)).convert("RGB")
    w, h = im.size
    board.paste(frac_crop(im), (x, y4))
    src = Image.open(os.path.join(SRC_DIR, src_name)).convert("RGB")
    sw, sh = src.size
    board.paste(frac_crop(src), (x, ys))
    d.text((x + 4, y4 + 4), "%s 4K %dx%d" % (shot, w, h), fill=(255, 232, 170))
    d.text((x + 4, ys + 4), "%s SRC %dx%d" % (shot, sw, sh), fill=(190, 190, 190))

board.save(BOARD, "JPEG", quality=90)
print("BOARD-REBUILD-END %dx%d bytes=%d" % (board.size[0], board.size[1], os.path.getsize(BOARD)))