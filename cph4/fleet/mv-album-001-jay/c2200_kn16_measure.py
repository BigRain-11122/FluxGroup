# -*- coding: utf-8 -*-
"""C2200: measure the re-burned KN16 take against the take it replaces.

C2199 removed the rainbow chroma from the moon halo of KN_A-KN16.mp4 by
de-saturating an annulus, but at native size the take still carries two
concentric glow arcs across the open sky (the additive glow survived the
chroma fix). C2200 fired a 768P re-burn whose prompt holds the glow close
to the moon and keeps the sky open.

This script answers one question with numbers: does the new take drop the
ring energy, and does it keep the grade / luma / motion of the old one.
No generation, no rewriting - measurement only.

Usage:
  python c2200_kn16_measure.py
"""
import io
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
OLD = os.path.join(MEDIA, "clips-local-768", "KN_A-KN16.mp4")
NEW = os.path.join(MEDIA, "clips-local-768", "KN_A-KN16-c2200.mp4")
BOARD = os.path.join(MEDIA, "qc-boards", "KN16-C2200-COMPARE.jpg")
QC = os.path.join(MEDIA, "qc-frames-c2200")
OUT = os.path.join(MEDIA, "logs", "kn16-compare-c2200.json")

W, H = 1344, 768
CX, CY = 681.0, 213.0
BINS = 40
R_MIN, R_MAX = 40.0, 900.0
SAMPLES = (2.0, 6.0, 9.0, 12.0)


def frame(path, t):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path,
                        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True)
    if p.returncode != 0 or not p.stdout:
        raise SystemExit("frame extract failed: %s @%s" % (path, t))
    return np.asarray(Image.open(io.BytesIO(p.stdout)).convert("RGB")).astype(np.float32)


def radial_profile(y, r):
    edges = np.linspace(R_MIN, R_MAX, BINS + 1)
    prof = np.full(BINS, np.nan)
    for i in range(BINS):
        m = (r >= edges[i]) & (r < edges[i + 1]) & (y < 200.0)
        if m.sum() > 200:
            prof[i] = np.median(y[m])
    last = np.nanmin(prof[-6:])
    return np.where(np.isnan(prof), last, prof)


def smooth(p, width):
    k = np.ones(width) / float(width)
    pad = width // 2
    q = np.concatenate([np.full(pad, p[0]), p, np.full(pad, p[-1])])
    return np.convolve(q, k, mode="valid")


def stats(a):
    y = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2)
    prof = radial_profile(y, r)
    base = smooth(prof, 11)
    bump = smooth(np.maximum(prof - base, 0.0), 5)
    band = np.linspace(R_MIN, R_MAX, BINS) > 200
    # chroma of the halo band, measured only where the annulus actually glows
    ring = band & (bump > 3.0)
    if ring.sum() >= 3:
        sel = (r >= np.linspace(R_MIN, R_MAX, BINS + 1)[:-1][ring].min()) & \
              (r <= np.linspace(R_MIN, R_MAX, BINS + 1)[1:][ring].max()) & (y < 200.0)
    else:
        sel = np.zeros_like(y > 1e9)
    if sel.sum() > 200:
        px = a[sel]
        mx = px.max(axis=1)
        mn = px.min(axis=1)
        sats = np.where(mx > 1.0, (mx - mn) / np.maximum(mx, 1.0), 0.0)
        sat = float(np.median(sats))
        green = float(np.median(px[:, 1] - np.maximum(px[:, 0], px[:, 2])))
    else:
        sat, green = 0.0, 0.0
    return {
        "bump_mean": round(float(bump[band].mean()), 3),
        "bump_max": round(float(bump[band].max()), 3),
        "sky_yavg": round(float(np.median(y[y < 200.0])), 2),
        "full_yavg": round(float(y.mean()), 2),
        "halo_sat": round(sat, 3),
        "green_excess": round(green, 2),
        "ring_frac": round(float(ring.sum()) / float(band.sum()), 3),
    }


def main():
    os.makedirs(QC, exist_ok=True)
    os.makedirs(os.path.dirname(BOARD), exist_ok=True)
    rows, thumbs = [], []
    for t in SAMPLES:
        for tag, path in (("old", OLD), ("new", NEW)):
            a = frame(path, t)
            rows.append(dict(shot=tag, t=t, **stats(a)))
            p = os.path.join(QC, "kn16cmp_%s_t%s.png" % (tag, t))
            Image.fromarray(a.astype(np.uint8)).save(p)
            thumbs.append(p)
    cw = 336
    sized = [Image.open(p).resize((cw, int(cw * H / float(W)))) for p in thumbs]
    rh = sized[0].size[1]
    sheet = Image.new("RGB", (cw * 4, rh * 2), (10, 10, 12))
    # row 0 = old, row 1 = new, columns = the four sample times
    for i, im in enumerate(sized):
        sheet.paste(im, ((i // 2) * cw, (i % 2) * rh))
    sheet.save(BOARD, quality=93)

    old_t = [r for r in rows if r["shot"] == "old"]
    new_t = [r for r in rows if r["shot"] == "new"]
    o_bump = float(np.mean([r["bump_mean"] for r in old_t]))
    n_bump = float(np.mean([r["bump_mean"] for r in new_t]))
    o_sat = float(np.mean([r["halo_sat"] for r in old_t]))
    n_sat = float(np.mean([r["halo_sat"] for r in new_t]))
    payload = {
        "batch": "C2200",
        "old": OLD,
        "new": NEW,
        "rows": rows,
        "summary": {
            "bump_mean_old": round(o_bump, 3),
            "bump_mean_new": round(n_bump, 3),
            "bump_drop_pct": round(100.0 * (o_bump - n_bump) / max(o_bump, 1e-6), 1),
            "halo_sat_old": round(o_sat, 3),
            "halo_sat_new": round(n_sat, 3),
            "sky_yavg_old": round(float(np.mean([r["sky_yavg"] for r in old_t])), 2),
            "sky_yavg_new": round(float(np.mean([r["sky_yavg"] for r in new_t])), 2),
        },
        "board": BOARD,
        "note": ("Top row = the take the film currently uses (post-C2199 chroma fix), "
                 "bottom row = the C2200 re-burn. bump_* is the radial excess of the sky "
                 "above its own wide baseline: concentric glow arcs read as a large bump. "
                 "halo_sat is the chroma of the glowing annulus."),
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
    for r in rows:
        print("%s t=%-4s bump %.2f/%.2f sat %.3f sky %.1f ring_frac %.2f green %.1f"
              % (r["shot"], r["t"], r["bump_mean"], r["bump_max"], r["halo_sat"],
                 r["sky_yavg"], r["ring_frac"], r["green_excess"]))
    print("SUMMARY %s" % json.dumps(payload["summary"], ensure_ascii=False))
    print("board=%s" % os.path.basename(BOARD))
    return 0


if __name__ == "__main__":
    sys.exit(main())