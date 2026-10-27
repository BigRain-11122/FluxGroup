"""C2121 pre-stow: localize line-hallucination / dot-matrix residue in the six 4K plates.

r1017 sec-5 row-1 pre-condition 1 requires "clean 2-3 fine-line hallucination artifacts
+ dot-matrix residue" but the locations were never pinned. This leg only LOCATES them:
per plate it scores isolated high-frequency blobs (candidate dots / phantom strokes),
emits a JSON with coordinates + builds one 1:1 zoom board of the top candidates so a
local repair pass has exact addresses. No pixel of the plates is modified.
"""
import json
import os
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OUT_DIR = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\s7r-4k"
SHOT_DIR = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
BOARD = os.path.join(SHOT_DIR, "xq-S527-ARTIFACT-LOCATE-c2121.jpg")
RECEIPT = os.path.join(SHOT_DIR, "xq-S527-ARTIFACT-LOCATE-c2121.json")

PLATES = [
    "S5-26_S5-26_s20185_s7rC_4k_grain010.png",
    "S5-26_S5-26_s20191_s7rC_4k_grain010.png",
    "S5-27_S5-27_s20192_s7rC_4k_grain010.png",
    "S5-27_S5-27_s20193_s7rC_4k_grain010.png",
    "S5-28_S5-28_s20202_s7rC_4k_grain010.png",
    "S5-28_S5-28_s20205_s7rC_4k_grain010.png",
]


def score_plate(path):
    im = Image.open(path).convert("RGB")
    L = np.asarray(im.convert("L"), dtype=np.float32)
    # high-pass: isolate small bright/dark specks that are not part of a large edge
    hp = L - ndimage.median_filter(L, size=5)
    mag = np.abs(hp)
    # local contrast normaliser: big structures produce wide responses, specks are compact
    wide = ndimage.uniform_filter(mag, size=25) + 1e-3
    score = mag / wide
    mask = (score > 6.0) & (mag > 8.0)
    lbl, n = ndimage.label(mask)
    cands = []
    if n:
        objs = ndimage.find_objects(lbl)
        sizes = np.bincount(lbl.ravel())[1:]
        for i, sl in enumerate(objs):
            if sl is None:
                continue
            h = sl[0].stop - sl[0].start
            w = sl[1].stop - sl[1].start
            if not (3 <= h <= 40 and 3 <= w <= 40):
                continue
            if sizes[i] > 400:
                continue
            cands.append({
                "x": int((sl[1].start + sl[1].stop) // 2),
                "y": int((sl[0].start + sl[0].stop) // 2),
                "w": int(w), "h": int(h), "px": int(sizes[i]),
                "score": round(float(score[sl].max()), 2),
            })
    cands.sort(key=lambda c: -c["score"])
    return cands[:6], len(cands), im.size


rows = []
tiles = []
for name in PLATES:
    p = os.path.join(OUT_DIR, name)
    if not os.path.exists(p):
        print("MISSING", p, flush=True)
        continue
    top, total, size = score_plate(p)
    rows.append({"plate": name, "size": list(size), "candidates": total, "top": top})
    im = Image.open(p).convert("RGB")
    for c in top[:3]:
        pad = 80
        x0, y0 = max(0, c["x"] - pad), max(0, c["y"] - pad)
        x1, y1 = min(im.width, c["x"] + pad), min(im.height, c["y"] + pad)
        crop = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.NEAREST)
        d = ImageDraw.Draw(crop)
        cx, cy = (c["x"] - x0) * 2, (c["y"] - y0) * 2
        d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], outline=(255, 60, 60), width=3)
        d.text((4, 4), "%s score %.1f" % (name.split("_s")[1][:8], c["score"]), fill=(255, 230, 150))
        tiles.append(crop)

if tiles:
    cw = max(t.width for t in tiles)
    chh = max(t.height for t in tiles)
    cols = 3
    rws = (len(tiles) + cols - 1) // cols
    bd = Image.new("RGB", (cw * cols, chh * rws), (10, 10, 10))
    for i, t in enumerate(tiles):
        bd.paste(t, ((i % cols) * cw, (i // cols) * chh))
    bd.save(BOARD, "JPEG", quality=91)
    bw = os.path.getsize(BOARD)
else:
    bw = 0

rec = {"batch": "c2121-s527-artifact-locate",
       "spec": "r1017 sec-5 row-1 pre-condition 1 (locate only, zero pixel change)",
       "plates": rows, "board": os.path.basename(BOARD), "board_bytes": bw,
       "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
with open(RECEIPT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print("ARTIFACT-LOCATE-END ok=%d board_bytes=%d" % (len(rows), bw))