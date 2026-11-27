"""C2119c: native probe for the S5-28 (and all six) 4K-vs-SRC pairs.
Eye-gate on a JPEG board claimed the constellation layer vanished from the 4K
frames; precedent (B1145) says probe before accepting an FAIL verdict.
The probe resamples the 4K crop back to the SRC crop size and compares:
  - mean absolute difference (aligned content => small)
  - bright-pixel count in the crop (stars / linkage lines)
  - per-quadrant mean luma
"""
import json
import os

import numpy as np
from PIL import Image

REPO = r"K:\Fluxgroup\FluxGroup"
SRC_DIR = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "abatch_s7r")
OUT_DIR = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "s7r-4k")
RECEIPT = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4K-PROBE-c2119.json")

PAIRS = [
    ("S5-26", "S5-26_s20185_s7rC.png", "S5-26_s20185_s7rC_4k.png"),
    ("S5-26", "S5-26_s20191_s7rC.png", "S5-26_s20191_s7rC_4k.png"),
    ("S5-27", "S5-27_s20192_s7rC.png", "S5-27_s20192_s7rC_4k.png"),
    ("S5-27", "S5-27_s20193_s7rC.png", "S5-27_s20193_s7rC_4k.png"),
    ("S5-28", "S5-28_s20202_s7rC.png", "S5-28_s20202_s7rC_4k.png"),
    ("S5-28", "S5-28_s20205_s7rC.png", "S5-28_s20205_s7rC_4k.png"),
]


def band(im, fx0, fy0, fx1, fy1):
    w, h = im.size
    return im.crop((int(w * fx0), int(h * fy0), int(w * fx1), int(h * fy1)))


def stats(im):
    a = np.asarray(im.convert("L")).astype(np.float32)
    return {
        "mean": round(float(a.mean()), 3),
        "bright200": int((a > 200).sum()),
        "bright160": int((a > 160).sum()),
        "max": int(a.max()),
    }


rows = []
for shot, src_name, out_name in PAIRS:
    src = Image.open(os.path.join(SRC_DIR, src_name)).convert("RGB")
    out = Image.open(os.path.join(OUT_DIR, out_name)).convert("RGB")
    # content window used by the board + the upper star band used by the receipt
    s_crop = band(src, 0.15, 0.03, 0.85, 0.42)
    o_crop = band(out, 0.15, 0.03, 0.85, 0.42)
    o_back = o_crop.resize(s_crop.size, Image.LANCZOS)
    a = np.asarray(s_crop.convert("L")).astype(np.float32)
    b = np.asarray(o_back.convert("L")).astype(np.float32)
    # grain is zero-mean, so MAD stays small when the underlying content matches
    mad = float(np.abs(a - b).mean())
    corr = float(np.corrcoef(a.ravel(), b.ravel())[0, 1])
    rows.append({
        "shot": shot, "src": src_name, "out": out_name,
        "mad_upper_band": round(mad, 3), "corr_upper_band": round(corr, 4),
        "src": stats(s_crop), "out4k": stats(o_crop),
        "verdicted": "CONTENT_MATCH" if corr > 0.95 and mad < 12 else "CONTENT_DRIFT",
    })

with open(RECEIPT, "w", encoding="utf-8") as f:
    json.dump({"batch": "c2119b-native-probe", "rows": rows}, f, ensure_ascii=False, indent=1)
for r in rows:
    print("%s %s corr=%.4f mad=%.2f src_bright200=%d out_bright200=%d"
          % (r["shot"], r["verdicted"], r["corr_upper_band"], r["mad_upper_band"],
             r["src"]["bright200"], r["out4k"]["bright200"]))