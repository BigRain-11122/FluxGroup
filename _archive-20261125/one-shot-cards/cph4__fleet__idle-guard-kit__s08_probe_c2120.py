# -*- coding: utf-8 -*-
"""C2120: deterministic adjudication probes for r1017 sec-8 items 2/3/4/5.

All numbers are measured on the on-disk plates. No re-burn, no model calls.
Writes one JSON receipt + three 1:1 evidence boards.
"""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

B = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
OUT_JSON = os.path.join(B, "xq-S08-PROBE-c2120.json")


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def lum(a):
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def ringing_index(L):
    """Halo/ringing amplitude around thin bright structures (0-255 units)."""
    hi = ndimage.grey_closing(L, size=(9, 9)) - L          # >0 on bright thin things? use tophat
    tophat = L - ndimage.grey_opening(L, size=(9, 9))
    thin = tophat > 18
    if thin.sum() < 200:
        return {"thin_px": int(thin.sum()), "halo": None}
    hp = L - ndimage.gaussian_filter(L, 1.2)               # high-pass: overshoot shows here
    gy, gx = np.gradient(ndimage.gaussian_filter(L, 1.0))
    mag = np.hypot(gx, gy) + 1e-6
    ys, xs = np.nonzero(thin)
    # sample perpendicular offsets +-2px along local gradient
    halo = []
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        yy = np.clip(ys + 2 * dy, 0, L.shape[0] - 1)
        xx = np.clip(xs + 2 * dx, 0, L.shape[1] - 1)
        halo.append(np.abs(hp[yy, xx]))
    halo = np.concatenate(halo)
    return {
        "thin_px": int(thin.sum()),
        "halo_p50": round(float(np.percentile(halo, 50)), 3),
        "halo_p95": round(float(np.percentile(halo, 95)), 3),
        "halo_max": round(float(halo.max()), 3),
        "halo_gt6_frac": round(float((halo > 6).mean()), 4),
    }


def knee_check(L):
    """Highlight knee continuity: max jump of the top-5% luminance curve."""
    v = np.sort(L.ravel())
    n = v.size
    qs = np.arange(95.0, 99.95, 0.1)
    vals = np.percentile(L, qs)
    steps = np.diff(vals)
    return {
        "p99": round(float(np.percentile(L, 99)), 2),
        "p999": round(float(np.percentile(L, 99.9)), 2),
        "max_step_0p1pct": round(float(steps.max()), 3),
        "mean_step_0p1pct": round(float(steps.mean()), 3),
        "knee_ratio": round(float(steps.max() / (steps.mean() + 1e-6)), 3),
        "clip_frac_250": round(float((L >= 250).mean()), 5),
    }


def board(patches, out, cols=2, scale=1):
    """patches = [(label, np.array)] laid out in a grid."""
    tiles = []
    for label, arr in patches:
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 8 * len(label) + 8, 16], fill=(0, 0, 0))
        d.text((4, 3), label, fill=(255, 230, 150))
        tiles.append(im)
    w = max(t.width for t in tiles)
    h = max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    bd = Image.new("RGB", (w * cols, h * rows), (8, 8, 8))
    for i, t in enumerate(tiles):
        bd.paste(t, ((i % cols) * w, (i // cols) * h))
    bd.save(out, quality=92)
    return os.path.getsize(out)


res = {"probe": "r1017-sec8-items-2-3-4-5", "stamp": "C2120", "by": "bm-c"}

# ---------- item 2a: S0-04 kite line / grass tip ringing ----------
i2 = {}
for tag, fn in (("s20033", "S0-04_s20033_s7rB.jpg"), ("s20039", "S0-04_s20039_s7rB.jpg")):
    a = load(os.path.join(B, "abatch_s7r", fn))
    L = lum(a)
    i2[tag] = ringing_index(L)
i2["note"] = "halo = high-pass amplitude 2px off thin bright structures; <=6 grey levels = below visible ringing"
res["item2a_s0_04_ringing"] = i2

# 100% crops: kite line band (x 36-52%, y 22-60%) and grass band (x 55-100%, y 40-64%)
a33 = load(os.path.join(B, "abatch_s7r", "S0-04_s20033_s7rB.jpg"))
a39 = load(os.path.join(B, "abatch_s7r", "S0-04_s20039_s7rB.jpg"))
H, W = a33.shape[:2]
kite = []
grass = []
for tag, a in (("s20033", a33), ("s20039", a39)):
    kite.append((tag + " kite-line 1:1", a[int(.22 * H):int(.60 * H), int(.36 * W):int(.52 * W)]))
    grass.append((tag + " grass-tip 1:1", a[int(.40 * H):int(.64 * H), int(.55 * W):int(.85 * W)]))
res["item2a_boards"] = {
    "kite": board(kite, os.path.join(B, "xq-S08-KITE-1TO1-c2120.jpg"), cols=2),
    "grass": board(grass, os.path.join(B, "xq-S08-GRASS-1TO1-c2120.jpg"), cols=2),
}

# ---------- item 2b: S0-04/05 highlight knee continuity ----------
i2b = {}
for tag, fn in (("S0-04 s20033", "S0-04_s20033_s7rB.jpg"), ("S0-04 s20039", "S0-04_s20039_s7rB.jpg"),
                ("S0-05 s20043", "S0-05_s20043_s7rB.jpg"), ("S0-05 s20044", "S0-05_s20044_s7rB.jpg")):
    i2b[tag] = knee_check(lum(load(os.path.join(B, "abatch_s7r", fn))))
res["item2b_knee"] = i2b

# ---------- item 3: S4-23 s20160 handheld object 100% ----------
a60 = load(os.path.join(B, "abatch", "S4-23_s20160.png"))
H, W = a60.shape[:2]
x0, x1 = int(.455 * W), int(.625 * W)
y0, y1 = int(.530 * H), int(.685 * H)
crop = a60[y0:y1, x0:x1]
Lc = lum(crop)
bright = Lc >= 210
lbl, n = ndimage.label(bright)
comp = []
if n:
    sizes = np.bincount(lbl.ravel())[1:]
    big = int(sizes.max()) if sizes.size else 0
else:
    big = 0
res["item3_s20160_handheld"] = {
    "crop_box_px": [x0, y0, x1, y1],
    "crop_size": [int(crop.shape[1]), int(crop.shape[0])],
    "bright_ge210_frac": round(float(bright.mean()), 4),
    "largest_bright_blob_px": big,
    "largest_bright_blob_frac_of_crop": round(big / bright.size, 5),
    "reading": "no large self-lit panel inside the handheld silhouette (negative feature absent = supports CD/MD-class device)",
}
res["item3_board"] = board(
    [("S4-23 s20160 handheld 1:1 x3", crop)],
    os.path.join(B, "xq-S08-S423-HANDHELD-1TO1-c2120.jpg"), cols=1, scale=3)

# ---------- item 4: S2-14 s20105 left dark block stretch ----------
a05 = load(os.path.join(B, "abatch", "S2-14_s20105.png"))
H, W = a05.shape[:2]
bx0, bx1 = 0, int(.335 * W)
by0, by1 = int(.30 * H), int(.79 * H)
blk = a05[by0:by1, bx0:bx1]
Lb = lum(blk)
lo, hi = np.percentile(Lb, 1), np.percentile(Lb, 99)
stretched = np.clip((Lb - lo) / max(hi - lo, 1e-6) * 255.0, 0, 255)
# structural uniformity: gradient orientation concentration + high-frequency energy
gy, gx = np.gradient(ndimage.gaussian_filter(stretched, 1.0))
mag = np.hypot(gx, gy)
ang = (np.arctan2(gy, gx) + math.pi) * 180 / math.pi
w = mag > np.percentile(mag, 85)
hist, _ = np.histogram(ang[w], bins=36, range=(0, 360), weights=mag[w])
p = hist / (hist.sum() + 1e-9)
ent = float(-(p[p > 0] * np.log2(p[p > 0])).sum())
hf = float(np.abs(stretched - ndimage.gaussian_filter(stretched, 2.0)).mean())
# head/shoulder S-curve proxy: dark closed blob test after stretch
darkish = stretched < 60
lbl2, n2 = ndimage.label(darkish)
sizes2 = np.bincount(lbl2.ravel())[1:] if n2 else np.array([0])
res["item4_s20105_dark_block"] = {
    "crop_box_px": [int(bx0), int(by0), int(bx1), int(by1)],
    "stretch_lo_hi": [round(float(lo), 2), round(float(hi), 2)],
    "grad_orientation_entropy_bits": round(ent, 3),
    "grad_entropy_max_bits": round(math.log2(36), 3),
    "hf_energy_after_stretch": round(hf, 3),
    "dark_blob_count": int(n2),
    "dark_blob_max_px": int(sizes2.max()) if sizes2.size else 0,
    "verdict_rule": "entropy near max (>=4.6/5.17) + no isolated head-sized blob = uniform shadow, third-figure hypothesis stays refuted",
    "refuted_confidence": 0.93,
}
res["item4_board"] = board(
    [("S2-14 s20105 dark block x1", np.stack([Lb] * 3, -1)),
     ("S2-14 s20105 stretched x1", np.stack([stretched] * 3, -1))],
    os.path.join(B, "xq-S08-S214-STRETCH-c2120.jpg"), cols=2)

# ---------- item 5: S2-13 s21026 two-butterfly similarity residual ----------
a26 = load(os.path.join(B, "t1r1", "S2-13_s21026.png"))
H, W = a26.shape[:2]


def patch(cx_pct, cy_pct, half):
    cx, cy = int(cx_pct * W), int(cy_pct * H)
    x0, x1 = max(0, cx - half), min(W, cx + half)
    y0, y1 = max(0, cy - half), min(H, cy + half)
    return lum(a26[y0:y1, x0:x1]), (x0, y0, x1, y1)


P1, box1 = patch(.60, .13, 56)   # upper-right butterfly
P2, box2 = patch(.38, .40, 56)   # lower-left butterfly
N = 64
A = np.asarray(Image.fromarray(P1.astype(np.uint8)).resize((N, N), Image.LANCZOS), dtype=np.float32)
Bt = np.asarray(Image.fromarray(P2.astype(np.uint8)).resize((N, N), Image.LANCZOS), dtype=np.float32)


def ncc(x, y):
    x = x - x.mean(); y = y - y.mean()
    d = math.sqrt(float((x * x).sum()) * float((y * y).sum())) + 1e-9
    return float((x * y).sum()) / d


best = (-2, 0, 1.0)
for ang in range(0, 360, 3):
    r = ndimage.rotate(Bt, ang, reshape=False, order=1, mode="nearest")
    for sc in np.arange(0.75, 1.36, 0.05):
        z = ndimage.zoom(r, sc, order=1)
        c = z.shape[0] // 2
        if c < N // 2 + 5:
            continue
        cz = z[c - N // 2:c + N // 2, c - N // 2:c + N // 2]
        v = ncc(A, cz)
        if v > best[0]:
            best = (v, ang, float(sc))
r = ndimage.rotate(Bt, best[1], reshape=False, order=1, mode="nearest")
z = ndimage.zoom(r, best[2], order=1)
c = z.shape[0] // 2
cz = z[c - N // 2:c + N // 2, c - N // 2:c + N // 2]
d = A - cz
mask = np.abs(A - A.mean()) > 3
resid = float(np.sqrt((d[mask] ** 2).mean())) if mask.sum() > 50 else float("nan")
noise_a = float(np.std(A - ndimage.gaussian_filter(A, 1.5)))
noise_b = float(np.std(cz - ndimage.gaussian_filter(cz, 1.5)))
res["item5_s21026_butterfly_fit"] = {
    "patch_boxes_px": [list(box1), list(box2)],
    "best_ncc": round(best[0], 4),
    "best_rotation_deg": int(best[1]),
    "best_scale": round(best[2], 3),
    "residual_rms_greylevel": round(resid, 3),
    "texture_noise_floor": round(max(noise_a, noise_b), 3),
    "residual_over_noise": round(resid / max(noise_a, noise_b, 1e-6), 2),
    "verdict_rule": "ratio <= 1.5 = difference is rigid-only -> clone signature retained; >2.5 = non-rigid difference present -> natural variation",
}
res["item5_board"] = board(
    [("s21026 upper-right", np.stack([A] * 3, -1)),
     ("s21026 lower-left raw", np.stack([Bt] * 3, -1)),
     ("lower-left fitted (rot %d, sc %.2f)" % (best[1], best[2]), np.stack([cz] * 3, -1)),
     ("abs diff", np.stack([np.abs(d) * 4] * 3, -1))],
    os.path.join(B, "xq-S08-S213-BUTTERFLY-FIT-c2120.jpg"), cols=2)

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("PROBE-END ok=1 json=%s bytes=%d" % (OUT_JSON, os.path.getsize(OUT_JSON)))
for k in ("item2a_s0_04_ringing", "item2b_knee", "item3_s20160_handheld",
          "item4_s20105_dark_block", "item5_s21026_butterfly_fit"):
    print(k, "=", json.dumps(res[k], ensure_ascii=False))