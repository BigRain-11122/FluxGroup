"""C2123: star-excluded artifact triage on the six SHIPPING grain-0.10 4K plates.

Context: C2121/C2122 locate runs returned 130-357 candidates per plate on BOTH the
grained and the zero-grain substrates, so grain was not the source. The 1:1 locate
board shows every top hit is an undersampled star PSF (compact bright blob on a dark
sky), i.e. the scorer is measuring the highest-frequency LEGITIMATE content.

This leg keeps the same scorer, then classifies each candidate by local background and
peak contrast: dark sky + bright compact core = star; everything else = candidate
artifact that needs an eye/repair decision. No pixels are modified.
"""
import glob
import json
import os
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = r"K:\Fluxgroup\FluxGroup"
OUT_DIR = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "s7r-4k")
BOARD = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-STARFILTER-GRAIN-BOARD-c2123.jpg")
RECEIPT = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-STARFILTER-GRAIN-c2123.json")

# scorer parameters, identical to the C2122 locator so counts stay comparable
SCORE_MIN = 6.0
MAG_MIN = 8.0
# star classifier
SKY_BG_MAX = 70.0      # local mean luminance below this = dark sky
STAR_CONTRAST = 25.0   # peak minus local mean above this = bright point source
EDGE_MARGIN = 24


def classify(plate):
    im = Image.open(plate).convert("RGB")
    L = np.asarray(im.convert("L"), dtype=np.float32)
    hp = L - ndimage.median_filter(L, size=5)
    mag = np.abs(hp)
    wide = ndimage.uniform_filter(mag, size=25) + 1e-3
    score = mag / wide
    mask = (score > SCORE_MIN) & (mag > MAG_MIN)
    lbl, n = ndimage.label(mask)

    bg = ndimage.uniform_filter(L, size=41)
    rows = []
    stars = 0
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
            px = int(sizes[i])
            cx = int((sl[1].start + sl[1].stop) // 2)
            cy = int((sl[0].start + sl[0].stop) // 2)
            peak = float(L[sl].max())
            local_bg = float(bg[cy, cx])
            contrast = peak - local_bg
            edge = cx < EDGE_MARGIN or cy < EDGE_MARGIN or cx > im.width - EDGE_MARGIN or cy > im.height - EDGE_MARGIN
            is_star = (local_bg < SKY_BG_MAX) and (contrast >= STAR_CONTRAST) and not edge
            if is_star:
                stars += 1
            rows.append({"x": cx, "y": cy, "w": int(w), "h": int(h), "px": px,
                         "score": round(float(score[sl].max()), 2),
                         "peak": round(peak, 1), "bg": round(local_bg, 1),
                         "contrast": round(contrast, 1), "edge": bool(edge),
                         "star": bool(is_star)})
    rows.sort(key=lambda c: -c["score"])
    anomalies = [r for r in rows if not r["star"]]
    return im, rows, stars, anomalies


def main():
    plates = sorted(glob.glob(os.path.join(OUT_DIR, "*_4k_grain010.png")))
    summary = []
    tiles = []
    total_stars = 0
    total_anom = 0
    for p in plates:
        im, rows, stars, anomalies = classify(p)
        total_stars += stars
        total_anom += len(anomalies)
        summary.append({"plate": os.path.basename(p), "size": list(im.size),
                        "candidates": len(rows), "stars": stars,
                        "anomalies": len(anomalies), "top_anomalies": anomalies[:6]})
        # board tiles: up to 2 anomalies per plate plus one control star, so the
        # classifier can be judged against its own positive baseline on the same sheet
        picks = anomalies[:2]
        ctrl = [r for r in rows if r["star"]][:1]
        picks = picks + ctrl if picks else (ctrl or rows[:2])
        for c in picks:
            pad = 160
            x0, y0 = max(0, c["x"] - pad), max(0, c["y"] - pad)
            x1, y1 = min(im.width, c["x"] + pad), min(im.height, c["y"] + pad)
            crop = im.crop((x0, y0, x1, y1))
            crop = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
            d = ImageDraw.Draw(crop)
            cx, cy = (c["x"] - x0) * 2, (c["y"] - y0) * 2
            col = (255, 60, 60) if not c["star"] else (80, 220, 120)
            d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], outline=col, width=3)
            tag = "ANOM" if not c["star"] else "star-ctl"
            d.text((6, 6), "%s %s sc%.1f" % (os.path.basename(p).split("_s")[1][:8], tag, c["score"]),
                   fill=(255, 230, 150))
            tiles.append(crop)

    bw = 0
    if tiles:
        cw = max(t.width for t in tiles)
        ch = max(t.height for t in tiles)
        cols = 3
        rws = (len(tiles) + cols - 1) // cols
        bd = Image.new("RGB", (cw * cols, ch * rws), (10, 10, 10))
        for i, t in enumerate(tiles):
            bd.paste(t, ((i % cols) * cw, (i // cols) * ch))
        bd.save(BOARD, "JPEG", quality=92)
        bw = os.path.getsize(BOARD)

    rec = {"batch": "c2123-s527-starfilter-grain",
           "spec": "r1017 sec-8 item-1: decide whether dot-matrix/fine-line artifacts exist, "
                   "on the adopted grain-0.10 plates, so the sec-8 item-1 closure is verified where it matters",
           "classifier": {"score_min": SCORE_MIN, "mag_min": MAG_MIN,
                          "sky_bg_max": SKY_BG_MAX, "star_contrast": STAR_CONTRAST,
                          "edge_margin": EDGE_MARGIN},
           "plates": summary, "total_candidates": total_stars + total_anom,
           "total_stars": total_stars, "total_anomalies": total_anom,
           "board": os.path.basename(BOARD), "board_bytes": bw,
           "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(RECEIPT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("S527-STARFILTER-GRAIN-END ok=%d candidates=%d stars=%d anomalies=%d board_bytes=%d"
          % (len(summary), total_stars + total_anom, total_stars, total_anom, bw), flush=True)
    for s in summary:
        print("  %s cand=%d stars=%d anom=%d" % (s["plate"][:34], s["candidates"], s["stars"], s["anomalies"]),
              flush=True)
    return len(summary)


if __name__ == "__main__":
    main()