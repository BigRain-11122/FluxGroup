"""C2197: build the KN18 keyframe as a crop of the proven KN17 plate.

Why: the KN18 keyframe is the root of three RED i2v takes. The generated
keyframes could not be aimed between two failure modes - at the "darkness clean
and empty" wording they come back nearly empty (p99 19-22) and the i2v model
tiles the sky with glowing lamps; pushed toward a dense field they come back
milky bright (p99 89, then 145). KN17's plate already holds the right field
(median 18, p99 37) and cleared 768P, so the close-up is taken as a real crop
into that same band: deterministic, continuous with the wide shot, and measured
against the same gate before any burn is spent on it.
"""

import io
import json
import os
import sys

from PIL import Image, ImageFilter
import numpy as np

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
FRAMES = os.path.join(MEDIA, "frames")
SRC = os.path.join(FRAMES, "KN_KN17.png")
DST = os.path.join(FRAMES, "KN_KN18.png")
OUT = os.path.join(MEDIA, "logs", "kn18-kf-crop-c2197.json")

# crop fractions of the KN17 plate: slightly above centre, where the gold band
# sits, keeping a 16:9 window so the resize is a pure zoom
CX, CY, CW, CH = 0.28, 0.12, 0.44, 0.44


def glow(im):
    g = im.convert("L")
    w, h = g.size
    sky = g.crop((0, 0, w, int(h * 0.55)))
    bl = sky.filter(ImageFilter.GaussianBlur(radius=max(6, w // 40)))
    a = np.asarray(bl).astype("float32")
    return {
        "med": round(float(np.median(a)), 1),
        "p95": round(float(np.percentile(a, 95)), 1),
        "p99": round(float(np.percentile(a, 99)), 1),
        "mean": round(float(a.mean()), 1),
    }


def main():
    src = Image.open(SRC).convert("RGB")
    w, h = src.size
    box = (int(w * CX), int(h * CY), int(w * (CX + CW)), int(h * (CY + CH)))
    crop = src.crop(box)
    # keep the film grain honest: resize up, then re-seed a light grain pass
    big = crop.resize((w, h), Image.LANCZOS)
    arr = np.asarray(big).astype("float32")
    rng = np.random.default_rng(102675)
    arr = np.clip(arr + rng.normal(0.0, 2.6, arr.shape), 0, 255).astype("uint8")
    out = Image.fromarray(arr, "RGB")
    out.save(DST, quality=96)
    res = {"src": SRC, "dst": DST, "crop_box": box, "out_size": [w, h],
           "src_stats": glow(src), "dst_stats": glow(out),
           "checked_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S")}
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print("crop box=%s src=%s dst=%s" % (box, res["src_stats"], res["dst_stats"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())