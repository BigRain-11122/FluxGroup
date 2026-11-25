"""C2120b: six-grid 4K re-run at adopted grain 0.10 (r1017 sec-5 row-1 endpoint pick).

Re-burns the ESRGAN x4 pass (upstream source, not the grained plate) so the grain
level is a single clean pass instead of stacking on 0.07. Deterministic seeds.
Outputs *_4k_grain010.png next to the 0.07 plates; originals untouched.
"""
import importlib.util
import json
import os
import time

import numpy as np
from PIL import Image, ImageDraw

KIT = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit"
spec = importlib.util.spec_from_file_location("c2119", os.path.join(KIT, "s527_4k_esrgan_c2119.py"))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

GRAIN = 0.10
OUT_DIR = base.OUT_DIR
BOARD = os.path.join(base.REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4K-GRAIN010-BOARD-c2120.jpg")
RECEIPT = os.path.join(base.REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4K-GRAIN010-RECEIPT-c2120.json")

os.makedirs(OUT_DIR, exist_ok=True)
rows, frames = [], []
for shot, fname in base.GRIDS:
    print("BURN %s %s" % (shot, fname), flush=True)
    files, secs = base.run_one(shot, fname)
    tmp = base.fetch_out(files)
    im = Image.open(tmp).convert("RGB")
    w, h = im.size
    if w > base.TARGET_W:
        im = im.resize((base.TARGET_W, int(round(h * base.TARGET_W / float(w)))), Image.LANCZOS)
    arr = np.asarray(im).astype(np.int16)
    rng = np.random.default_rng(20210228)
    noise = rng.normal(0.0, 255 * GRAIN / 3.0, size=(arr.shape[0], arr.shape[1], 1))
    im = Image.fromarray(np.clip(arr + noise, 0, 255).astype("uint8"), "RGB")
    out = os.path.join(OUT_DIR, "%s_%s_4k_grain010.png" % (shot, os.path.basename(fname).replace(".png", "")))
    im.save(out, "PNG", optimize=True)
    os.remove(tmp)
    rows.append({"shot": shot, "src": fname, "out": os.path.basename(out),
                 "out_size": [im.size[0], im.size[1]], "bytes": os.path.getsize(out),
                 "burn_secs": round(secs, 1), "grain": GRAIN})
    frames.append((shot, im))
    print("DONE %s %dx%d %dB %.1fs" % (os.path.basename(out), im.size[0], im.size[1],
                                       os.path.getsize(out), secs), flush=True)

cw, ch, pad = 640, 360, 10
bw = 3 * cw + 4 * pad
bh = 2 * (ch + 24) + 3 * pad
board = Image.new("RGB", (bw, bh), (14, 14, 16))
d = ImageDraw.Draw(board)
for i, (shot, im) in enumerate(frames):
    x = pad + (i % 3) * (cw + pad)
    y = pad + (i // 3) * (ch + 24 + pad)
    w, h = im.size
    board.paste(im.crop((int(w * .5 - cw / 2), int(h * .42 - ch / 2),
                         int(w * .5 + cw / 2), int(h * .42 + ch / 2))), (x, y))
    d.text((x + 4, y + 4), "%s grain %.2f" % (shot, GRAIN), fill=(255, 232, 170))
board.save(BOARD, "JPEG", quality=90)
rec = {"batch": "c2120-s527-4k-grain010", "spec": "r1017 sec-5 row-1 pre-condition 2 endpoint",
       "grain": GRAIN, "endpoint_evidence": "xq-S527-GRAIN-AB-BOARD-c2120.jpg (0.05 vs 0.10)",
       "frames": rows, "board": os.path.basename(BOARD), "board_bytes": os.path.getsize(BOARD),
       "revert": "deterministic: re-run with GRAIN=0.07 restores the C2119 plates",
       "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
with open(RECEIPT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print("S527-4K-GRAIN010-END ok=%d board_bytes=%d" % (len(rows), rec["board_bytes"]))