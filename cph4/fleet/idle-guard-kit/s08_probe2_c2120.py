# -*- coding: utf-8 -*-
"""C2120b: butterfly silhouette similarity fit (mask IoU) + ROI-scoped ringing index."""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

B = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
OUT = os.path.join(B, "xq-S08-PROBE2-c2120.json")


def load(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)


def lum(a):
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


res = {}

# ---- ROI-scoped ringing index (spec points: kite line band, grass tip band) ----
for tag, fn in (("s20033", "S0-04_s20033_s7rB.jpg"), ("s20039", "S0-04_s20039_s7rB.jpg")):
    a = load(os.path.join(B, "abatch_s7r", fn)); L = lum(a); H, W = L.shape
    rois = {"kite_line": (int(.30 * H), int(.62 * H), int(.34 * W), int(.54 * W)),
            "grass_tip": (int(.40 * H), int(.66 * H), int(.55 * W), int(.88 * W))}
    per = {}
    for name, (y0, y1, x0, x1) in rois.items():
        R = L[y0:y1, x0:x1]
        hp = R - ndimage.gaussian_filter(R, 1.2)
        tophat = R - ndimage.grey_opening(R, size=(9, 9))
        thin = tophat > 20
        if thin.sum() < 50:
            per[name] = {"thin_px": int(thin.sum()), "halo_p50": None}
            continue
        halo = []
        for dy, dx in ((0, 2), (0, -2), (2, 0), (-2, 0)):
            yy = np.clip(np.nonzero(thin)[0] + dy, 0, R.shape[0] - 1)
            xx = np.clip(np.nonzero(thin)[1] + dx, 0, R.shape[1] - 1)
            halo.append(np.abs(hp[yy, xx]))
        halo = np.concatenate(halo)
        per[name] = {"thin_px": int(thin.sum()),
                     "halo_p50": round(float(np.percentile(halo, 50)), 2),
                     "halo_p90": round(float(np.percentile(halo, 90)), 2),
                     "frac_gt8": round(float((halo > 8).mean()), 4)}
    res[tag] = per

# ---- butterfly silhouette fit ----
a26 = load(os.path.join(B, "t1r1", "S2-13_s21026.png"))
H, W = a26.shape[:2]


def mask_at(cx, cy, half):
    x0, x1 = max(0, cx - half), min(W, cx + half)
    y0, y1 = max(0, cy - half), min(H, cy + half)
    p = a26[y0:y1, x0:x1]
    r, g, b = p[..., 0], p[..., 1], p[..., 2]
    mx = p.max(2); mn = p.min(2); sat = (mx - mn) / (mx + 1e-6)
    # orange/black monarch: strong warm chroma (R>G>B) with decent saturation
    m = (r > g + 12) & (g >= b - 6) & (sat > 0.28) & (mx > 70)
    m = ndimage.binary_closing(m, np.ones((3, 3)))
    m = ndimage.binary_opening(m, np.ones((2, 2)))
    return m.astype(np.float32), (x0, y0, x1, y1), p


M1, box1, P1 = mask_at(int(.60 * W), int(.13 * H), 62)
M2, box2, P2 = mask_at(int(.38 * W), int(.40 * H), 62)
N = 96


def prep(m):
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)
    return (np.asarray(im, dtype=np.float32) > 127).astype(np.float32)


A_ = prep(M1)
Bm = prep(M2)
best = (0.0, 0, 1.0)
for ang in range(0, 360, 2):
    r = ndimage.rotate(Bm, ang, reshape=False, order=0, mode="constant")
    for sc in np.arange(0.8, 1.31, 0.05):
        z = ndimage.zoom(r, sc, order=0)
        c = z.shape[0] // 2
        if c < N // 2 + 4:
            continue
        cz = z[c - N // 2:c + N // 2, c - N // 2:c + N // 2]
        cz = (cz > .5)
        inter = float((A_ * cz).sum()); uni = float(((A_ + cz) > .5).sum())
        iou = inter / max(uni, 1)
        if iou > best[0]:
            best = (iou, ang, float(sc))
r = ndimage.rotate(Bm, best[1], reshape=False, order=0, mode="constant")
z = ndimage.zoom(r, best[2], order=0)
c = z.shape[0] // 2
CZ = (z[c - N // 2:c + N // 2, c - N // 2:c + N // 2] > .5)

oned = ndimage.binary_fill_holes(A_ > .5)
twod = ndimage.binary_fill_holes(CZ)
res["butterfly_silhouette"] = {
    "boxes_px": [list(box1), list(box2)],
    "mask_area_px": [int(M1.sum()), int(M2.sum())],
    "best_iou": round(best[0], 4),
    "best_rotation_deg": int(best[1]),
    "best_scale": round(best[2], 3),
    "shape_area_ratio": round(float(M2.sum()) / max(float(M1.sum()), 1), 3),
    "verdict_rule": "IoU>=0.90 after similarity fit = rigid-only clone signature; IoU<0.75 = non-rigid/wing-shape difference = natural variation",
}
# evidence board: both masks + overlap
def m2img(m):
    return np.stack([(m * 255).astype(np.float32)] * 3, -1)
ov = np.zeros((N, N, 3), np.float32)
ov[..., 0] = A_ * 255
ov[..., 1] = CZ * 255
tiles = [("upper-right mask", m2img(oned)), ("lower-left fitted mask", m2img(twod)), ("overlap R=A G=fitted", ov)]
bd = Image.new("RGB", (N * 3 + 24, N + 20), (10, 10, 10))
d = ImageDraw.Draw(bd)
for i, (lab, arr) in enumerate(tiles):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    bd.paste(im, (i * (N + 12), 18))
    d.text((i * (N + 12) + 2, 4), lab[:34], fill=(255, 230, 150))
p = os.path.join(B, "xq-S08-S213-MASKFIT-c2120.jpg")
bd.save(p, quality=92)
res["mask_board_bytes"] = os.path.getsize(p)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("PROBE2-END ok=1 bytes=%d" % os.path.getsize(OUT))
print(json.dumps(res, ensure_ascii=False))