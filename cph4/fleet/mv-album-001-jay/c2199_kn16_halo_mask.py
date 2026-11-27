"""C2199: build the static alpha map over KN16's rainbow corona (geometric).

The corona is a clean annulus around the moon, so the mask is that annulus,
feathered and faded out above the cloud line where the take itself drops the ring.

Two alternatives were built and rejected while fixing this:
  * a colour key - the night sky inside the corona is itself cool blue, so the
    key selects the whole sky rather than the ring;
  * saturation weighting (max over sampled frames) - it keeps the mask honest
    where the ring is, but the same pixels are plain sky in the first seconds of
    the take, which printed a phantom ring there.
The phantom-ring problem is solved in the recolour pass instead, by fading the
masked layer in over the seconds where the ring actually forms.

Usage:
  python c2199_kn16_halo_mask.py --build
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageFilter

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
W, H = 1344, 768

CX, CY = 681.1, 212.7        # moon centre, measured on the take
R_IN, R_OUT = 205.0, 495.0   # corona band
FEATHER = 44.0
CLOUD_TOP, CLOUD_FADE = 505.0, 110.0


def smoothstep(x, e0, e1):
    t = np.clip((x - e0) / max(e1 - e0, 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def build():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2)
    ann = smoothstep(r, R_IN - FEATHER, R_IN + FEATHER) * (
        1.0 - smoothstep(r, R_OUT - FEATHER, R_OUT + FEATHER))
    vert = 1.0 - smoothstep(yy.astype("float32"), CLOUD_TOP, CLOUD_TOP + CLOUD_FADE)
    alpha = ann * vert
    img = Image.fromarray(np.clip(alpha * 255.0, 0, 255).astype("uint8"))
    img = img.filter(ImageFilter.GaussianBlur(12))
    path = os.path.join(MEDIA, "c2199-kn16-halo-mask.png")
    img.save(path)
    arr = np.asarray(img)
    print("mask=%s coverage=%.3f mean=%.1f" % (path, float((arr > 24).mean()), float(arr.mean())))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())