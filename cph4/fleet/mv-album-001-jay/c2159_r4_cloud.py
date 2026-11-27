# -*- coding: utf-8 -*-
# c2159_r4_cloud.py -- R4 fix for Xingqing PACK-B shot S1-07 (30.0-38.125s).
#
# Problem (DIRECTOR-REVIEW-PACKB-V2-20261020.md R4): the white cloud on the left
# third is a pasted walking-woman silhouette -- hard contour, no sun-side rim, no
# aerial haze, grain smoothed flat. Luma/saturation thresholds cannot separate it
# from the sky (measured: cloud luma 159.7 mean vs sky 157.3), so the mask is a
# plate-locked soft ellipse (the cloud layer sits in the same screen box for all
# 226 frames, which is itself part of why it reads pasted).
#
# Treatment, purely photographic, no GPU and no re-render:
#   1) long-tailed wind smear of the plate inside the mask (three stacked
#      horizontal box passes = motion-blur profile) so the head / waist / legs
#      fuse into one wind-eroded mass instead of a body contour;
#   2) near the horizon the mass is blended towards the background estimated by
#      normalized convolution of the unmasked plate (aerial perspective, this is
#      what kills the "walking legs" read);
#   3) warm rim on the sun side;
#   4) film grain restored over the smoothed area.
import os
import sys

import numpy as np
from PIL import Image

SRC = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\qc-r4-c2159\srcframes"
DST = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\qc-r4-c2159\outframes"

SEED = 2159
CX, CY, RX, RY = 0.300, 0.480, 0.185, 0.520


def box_h(a, r):
    if r < 1:
        return a
    pad = np.pad(a, ((0, 0), (r + 1, r), (0, 0)), mode="edge")
    c = np.cumsum(pad, axis=1, dtype=np.float64)
    out = (c[:, 2 * r + 1:, :] - c[:, :-2 * r - 1, :]) / (2 * r + 1)
    return out.astype(np.float32)


def box(a, r):
    return np.transpose(box_h(np.transpose(box_h(a, r), (1, 0, 2)), r), (1, 0, 2))


def smoothstep(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def make_noise(h, w, seed, cell):
    rng = np.random.RandomState(seed)
    gh, gw = h // cell + 3, w // cell + 3
    g = (rng.rand(gh, gw) * 255).astype(np.uint8)
    img = Image.fromarray(g).resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32)[:h, :w] / 255.0


def main():
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".png"))
    if not files:
        print("NO-FRAMES")
        return 3
    os.makedirs(DST, exist_ok=True)
    n = len(files)

    first = np.asarray(Image.open(os.path.join(SRC, files[0])).convert("RGB"), dtype=np.float32)
    h, w, _ = first.shape
    yy = np.arange(h, dtype=np.float32)[:, None] / h
    xx = np.arange(w, dtype=np.float32)[None, :] / w
    rr = np.sqrt(((xx - CX) / RX) ** 2 + ((yy - CY) / RY) ** 2)
    base = 1.0 - smoothstep(rr, 0.30, 1.06)
    base = base * (yy > 0.02)
    base = box(base[:, :, None], 6)[:, :, 0]
    print("frames=%d mask_px=%d" % (n, int((base > 0.5).sum())))

    rng = np.random.RandomState(SEED)
    for i, fn in enumerate(files):
        img = np.asarray(Image.open(os.path.join(SRC, fn)).convert("RGB"), dtype=np.float32)

        # long-tailed horizontal smear: 40 + 80 + 120 box passes
        sm = box_h(box_h(box_h(img, 40), 80), 120)
        sm = box(sm, 9)
        # the head-shaped knob survives the plain smear: give the top band an
        # even longer profile so it becomes a wind streak
        sm_top = box_h(box_h(sm, 70), 70)
        toplink = np.clip((0.32 - yy) / 0.32, 0.0, 1.0)
        sm = sm * (1.0 - toplink[:, :, None] * 0.9) + sm_top * (toplink[:, :, None] * 0.9)

        # per-row wind shear: ragged rows instead of a symmetrical column
        rngrow = np.random.RandomState(SEED + i)
        raw = box(np.repeat(rngrow.rand(h, 4, 1).astype(np.float32), w // 4 + 1, axis=1)[:, :w, :], 24)
        shift = ((raw[:, :, 0] - 0.5) * 68.0 / max(0.5, (raw[:, :, 0].max() - raw[:, :, 0].min()) * 0.5 or 1.0))
        shift = np.clip((raw[:, :, 0] - 0.5) * 150.0, -34.0, 34.0)
        xsrc = np.clip(np.arange(w)[None, :] + shift.astype(np.int32), 0, w - 1)
        sm = np.take_along_axis(sm, np.repeat(xsrc[:, :, None], 3, axis=2), axis=1)

        # background under the mask: normalized convolution of the unmasked plate
        wmask = (1.0 - base)[:, :, None]
        bg = box(img * wmask, 90) / np.maximum(box(wmask, 90), 1e-3)

        nse = make_noise(h, w, SEED + (i // 8), 60)
        nse2 = make_noise(h, w, SEED + 500 + (i // 10), 20)

        # full replacement inside the mask -- the original contour must not leak
        base2 = base
        a = base2 * (0.90 + 0.06 * nse + 0.03 * nse2)
        a = np.clip(a, 0.0, 0.97)
        cloud = sm * (0.98 + 0.05 * nse2[:, :, None])

        out = img * (1.0 - a[:, :, None]) + cloud * a[:, :, None]

        # aerial perspective: fog dissolves into the background near the horizon
        lowfog = np.clip((yy - 0.42) / 0.46, 0.0, 1.0) ** 1.3 * base2 * 0.90
        out = out * (1.0 - lowfog[:, :, None]) + bg * lowfog[:, :, None]

        # sun-side warm rim on the right edge of the mass
        rim = np.clip(base - np.roll(base, 12, axis=1), 0.0, 1.0)
        rim = box(rim[:, :, None], 4)[:, :, 0]
        out[:, :, 0] += rim * 16.0
        out[:, :, 1] += rim * 11.0
        out[:, :, 2] += rim * 2.0

        grain = rng.normal(0.0, 1.0, (h, w, 1)).astype(np.float32)
        out += grain * (1.1 + 2.2 * a[:, :, None])

        np.clip(out, 0.0, 255.0, out=out)
        Image.fromarray(out.astype(np.uint8)).save(os.path.join(DST, fn))
        if i % 40 == 0:
            print("  %d/%d" % (i + 1, n))
    print("R4-CLOUD-DONE frames=%d" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
