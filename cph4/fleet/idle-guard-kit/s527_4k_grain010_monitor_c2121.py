"""C2121 pre-stow: 4K monitor recheck at the adopted grain 0.10 (r1017 sec-8 item-1 tail).

Measures faint-star retention (upper band bright-pixel ratio) and corner-darkness ratio
for the six grain-0.10 plates against their s7rC sources, and builds a 1:1 dark-band
strip so the director can read star retention without opening 15MB PNGs.
"""
import importlib.util
import json
import os
import time

from PIL import Image, ImageDraw

KIT = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit"
spec = importlib.util.spec_from_file_location("c2119", os.path.join(KIT, "s527_4k_esrgan_c2119.py"))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

SHOT_DIR = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
RECEIPT = os.path.join(SHOT_DIR, "xq-S527-4K-GRAIN010-MONITOR-c2121.json")
BOARD = os.path.join(SHOT_DIR, "xq-S527-4K-GRAIN010-MONITOR-c2121.jpg")

PAIRS = [
    ("S5-26", "S5-26_s20185_s7rC.png", "S5-26_S5-26_s20185_s7rC_4k_grain010.png"),
    ("S5-26", "S5-26_s20191_s7rC.png", "S5-26_S5-26_s20191_s7rC_4k_grain010.png"),
    ("S5-27", "S5-27_s20192_s7rC.png", "S5-27_S5-27_s20192_s7rC_4k_grain010.png"),
    ("S5-27", "S5-27_s20193_s7rC.png", "S5-27_S5-27_s20193_s7rC_4k_grain010.png"),
    ("S5-28", "S5-28_s20202_s7rC.png", "S5-28_S5-28_s20202_s7rC_4k_grain010.png"),
    ("S5-28", "S5-28_s20205_s7rC.png", "S5-28_S5-28_s20205_s7rC_4k_grain010.png"),
]

rows = []
tiles = []
for shot, src_name, out_name in PAIRS:
    out_p = os.path.join(base.OUT_DIR, out_name)
    src_p = os.path.join(base.SRC_DIR, src_name)
    if not (os.path.exists(out_p) and os.path.exists(src_p)):
        print("MISSING", out_p, os.path.exists(out_p), src_p, os.path.exists(src_p), flush=True)
        continue
    im = Image.open(out_p).convert("RGB")
    src = Image.open(src_p).convert("RGB")
    w, h = im.size
    band = (int(w * 0.15), int(h * 0.03), int(w * 0.85), int(h * 0.42))
    sw, sh = src.size
    sband = (int(sw * 0.15), int(sh * 0.03), int(sw * 0.85), int(sh * 0.42))
    row = {
        "shot": shot, "plate": out_name, "size": [w, h],
        "star_ratio_4k": round(base.star_metric(im, band), 5),
        "star_ratio_src": round(base.star_metric(src, sband), 5),
        "corner_dark_ratio": round(base.corner_dark(im, (0, 0, int(w * .12), int(h * .18))), 4),
    }
    row["star_retention"] = round(row["star_ratio_4k"] / max(row["star_ratio_src"], 1e-6), 3)
    rows.append(row)
    # 1:1 dark-band tile (upper band, native pixels, downscaled only to fit a 640px tile)
    crop = im.crop(band)
    cw = 640
    tiles.append((shot + " 4K upper band", crop.resize((cw, int(crop.height * cw / crop.width)), Image.LANCZOS)))

if tiles:
    cw = max(t.width for _, t in tiles)
    ch = max(t.height for _, t in tiles)
    cols = 2
    rws = (len(tiles) + cols - 1) // cols
    bd = Image.new("RGB", (cw * cols, (ch + 18) * rws), (10, 10, 10))
    d = ImageDraw.Draw(bd)
    for i, (lab, t) in enumerate(tiles):
        x, y = (i % cols) * cw, (i // cols) * (ch + 18)
        bd.paste(t, (x, y + 16))
        d.text((x + 3, y + 3), lab, fill=(255, 232, 170))
    bd.save(BOARD, "JPEG", quality=92)
    bw = os.path.getsize(BOARD)
else:
    bw = 0

rec = {"batch": "c2121-s527-4k-grain010-monitor",
       "spec": "r1017 sec-8 item-1 tail: 4K monitor recheck, faint star retention + corner darkness",
       "grain": 0.10, "plates": rows,
       "pass_rule": "star_retention >= 0.90 vs source and corner_dark_ratio stable across the six plates",
       "board": os.path.basename(BOARD), "board_bytes": bw,
       "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
with open(RECEIPT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print("GRAIN010-MONITOR-END ok=%d board_bytes=%d" % (len(rows), bw))
for r in rows:
    print(r["shot"], "retention", r["star_retention"], "corner_dark", r["corner_dark_ratio"])