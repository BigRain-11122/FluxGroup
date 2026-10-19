"""C2121 pre-stow: grain 0.07 vs 0.10 1:1 delta board for the six 4K grids.

The endpoint pick (r1017 sec-5 row-1) needs a same-region side-by-side of the two
grain levels plus a measured grain sigma, so the director reads the delta instead of
guessing from a 2x2 overview. Reads only the plates already on disk; no re-burn.
"""
import json
import os
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OUT_DIR = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\s7r-4k"
SHOT_DIR = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
BOARD = os.path.join(SHOT_DIR, "xq-S527-GRAIN-007-VS-010-c2121.jpg")
RECEIPT = os.path.join(SHOT_DIR, "xq-S527-GRAIN-007-VS-010-c2121.json")

PAIRS = [
    ("S5-26", "S5-26_S5-26_s20185_s7rC_4k.png", "S5-26_S5-26_s20185_s7rC_4k_grain010.png"),
    ("S5-26", "S5-26_S5-26_s20191_s7rC_4k.png", "S5-26_S5-26_s20191_s7rC_4k_grain010.png"),
    ("S5-27", "S5-27_S5-27_s20192_s7rC_4k.png", "S5-27_S5-27_s20192_s7rC_4k_grain010.png"),
    ("S5-27", "S5-27_S5-27_s20193_s7rC_4k.png", "S5-27_S5-27_s20193_s7rC_4k_grain010.png"),
    ("S5-28", "S5-28_S5-28_s20202_s7rC_4k.png", "S5-28_S5-28_s20202_s7rC_4k_grain010.png"),
    ("S5-28", "S5-28_S5-28_s20205_s7rC_4k.png", "S5-28_S5-28_s20205_s7rC_4k_grain010.png"),
]


def grain_sigma(im, box):
    """Residual high-frequency sigma inside a flat-ish dark patch (grain proxy)."""
    crop = np.asarray(im.crop(box).convert("L"), dtype=np.float32)
    hp = crop - ndimage.median_filter(crop, size=3)
    flat = np.abs(hp) < np.percentile(np.abs(hp), 80)
    return float(hp[flat].std())


rows = []
tiles = []
for shot, p007, p010 in PAIRS:
    a_p = os.path.join(OUT_DIR, p007)
    b_p = os.path.join(OUT_DIR, p010)
    if not (os.path.exists(a_p) and os.path.exists(b_p)):
        print("MISSING", a_p, os.path.exists(a_p), b_p, os.path.exists(b_p), flush=True)
        continue
    a = Image.open(a_p).convert("RGB")
    b = Image.open(b_p).convert("RGB")
    w, h = a.size
    # same dark sky region for both sigma measurements
    box = (int(w * .20), int(h * .10), int(w * .40), int(h * .28))
    cw, ch = 660, 372
    cx, cy = int(w * .42), int(h * .34)
    crop_a = a.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2))
    crop_b = b.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2))
    rows.append({"shot": shot, "sigma_007": round(grain_sigma(a, box), 3),
                 "sigma_010": round(grain_sigma(b, box), 3),
                 "delta_sigma": round(grain_sigma(b, box) - grain_sigma(a, box), 3)})
    for lab, cr in ((shot + " grain 0.07 1:1", crop_a), (shot + " grain 0.10 1:1", crop_b)):
        t = cr.copy()
        d = ImageDraw.Draw(t)
        d.rectangle([0, 0, 8 * len(lab) + 8, 16], fill=(0, 0, 0))
        d.text((4, 3), lab, fill=(255, 232, 170))
        tiles.append(t)

if tiles:
    cw = max(t.width for t in tiles)
    chh = max(t.height for t in tiles)
    cols = 2
    rws = (len(tiles) + cols - 1) // cols
    bd = Image.new("RGB", (cw * cols, chh * rws), (8, 8, 8))
    for i, t in enumerate(tiles):
        bd.paste(t, ((i % cols) * cw, (i // cols) * chh))
    bd.save(BOARD, "JPEG", quality=93)
    bw = os.path.getsize(BOARD)
else:
    bw = 0

rec = {"batch": "c2121-grain-007-vs-010",
       "spec": "r1017 sec-5 row-1 endpoint pick support (side-by-side 1:1 + measured sigma)",
       "pairs": rows, "board": os.path.basename(BOARD), "board_bytes": bw,
       "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
with open(RECEIPT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print("GRAIN-DELTA-END ok=%d board_bytes=%d" % (len(rows), bw))