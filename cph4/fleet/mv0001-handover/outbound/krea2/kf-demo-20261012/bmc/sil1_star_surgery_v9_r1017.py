# -*- coding: utf-8 -*-
"""SIL1 手术 v9（终迭代）：无痕 LF + 伸长率闸供体 + 收敛星缘"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import cv2

TMP = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\tmp"
SRC = TMP + r"\reburn_SIL1_ref.jpg"
DST = TMP + r"\reburn_SIL1_v53r_r12_surgery.png"

img = cv2.imread(SRC)
H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(float)

BX0, BX1 = 504, 572
AY0, AY1 = 229, 268
BY0, BY1 = 275, 295
F = 6   # 羽化加宽

def runs_max(line):
    best = c = 0
    for v in line:
        c = c + 1 if v else 0
        best = max(best, c)
    return best

def donor_ok(y, x, hh, ww):
    w_ = gray[y:y+hh, x:x+ww]
    if w_.max() > 150 or w_.min() < 55:
        return False
    mu, sd = w_.mean(), w_.std()
    # 伸长率闸：亮/暗细长结构 run>13 即拒（石斑=团块·刻痕=细长）
    bm = w_ > mu + 2.0 * sd
    dm = w_ < mu - 2.0 * sd
    for i in range(hh):
        if runs_max(bm[i, :]) > 13 or runs_max(dm[i, :]) > 13:
            return False
    for j in range(ww):
        if runs_max(bm[:, j]) > 13 or runs_max(dm[:, j]) > 13:
            return False
    return True

def stone_stats(y0, y1, x0, x1):
    reg = img[y0:y1, x0:x1].astype(float)
    rl = gray[y0:y1, x0:x1]
    m = (rl > 90) & (rl < 160)
    px = reg[m]
    return px.mean(axis=0), px.std(axis=0)

tgt_mean, tgt_std = stone_stats(AY0 - 6, BY1 + 6, BX0 - 10, BX0 - 2)

def find_src(hh, ww, tag, ban=None):
    best, best_score = None, 1e18
    for y in range(100, H - hh - 20, 4):
        for x in range(330, W - ww - 30, 6):
            if not (x + ww < 500 or x > 600):
                continue
            if ban and abs(y - ban[0]) < 60 and abs(x - ban[1]) < ww + 20:
                continue
            if not donor_ok(y, x, hh, ww):
                continue
            w_ = gray[y:y+hh, x:x+ww]
            score = abs(w_.mean() - tgt_mean.mean()) * 3 + abs(w_.std() - tgt_std.mean()) * 2
            if score < best_score:
                best_score, best = score, (y, x)
    print(f"{tag}: src={best} score={best_score:.1f}")
    return best

srcA = find_src(AY1 - AY0, BX1 - BX0, "zoneA")
srcB = find_src(BY1 - BY0, BX1 - BX0, "zoneB", ban=srcA)
assert srcA and srcB, "donor search failed"

# ---- 无痕 LF：心形亮像素先替换为行中位石色再模糊 ----
lf_base = img.astype(np.float32).copy()
cell_mask = np.zeros((H, W), dtype=bool)
cell_mask[AY0-2:BY1+2, BX0-2:BX1+2] = True
bright = cell_mask & (gray > 130)
med_color = np.array([np.median(img[AY0:BY1, BX0:BX1][..., c][gray[AY0:BY1, BX0:BX1] < 120]) for c in range(3)])
print("cell stone median BGR:", med_color.round(1))
lf_base[bright] = med_color
LF = cv2.GaussianBlur(lf_base, (0, 0), 8.0)

work = img.astype(np.float64).copy()
for (y0, y1, src) in ((AY0, AY1, srcA), (BY0, BY1, srcB)):
    sy, sx = src
    hh, ww = y1 - y0, BX1 - BX0
    patch = img[sy:sy+hh, sx:sx+ww].astype(np.float64)
    patch_lf = cv2.GaussianBlur(patch.astype(np.float32), (0, 0), 8.0)
    target_lf = LF[y0:y1, BX0:BX1]
    new = np.clip(patch - patch_lf + target_lf, 0, 255)
    reg_l = gray[y0:y1, BX0:BX1]
    mm = (reg_l > 90) & (reg_l < 160)
    for c in range(3):
        cur = new[..., c][mm].mean() if mm.any() else new[..., c].mean()
        new[..., c] += (tgt_mean[c] - cur)
    new = np.clip(new, 0, 255)
    # 羽化 6px（顶/底行遇原亮线硬化）
    alpha = np.ones((hh, ww))
    for i in range(F):
        alpha[i, :] = (i + 1) / (F + 1)
        alpha[hh - 1 - i, :] = np.minimum(alpha[hh - 1 - i, :], (i + 1) / (F + 1))
    alpha[:, :F] = np.minimum(alpha[:, :F], np.array([[(j + 1) / (F + 1) for j in range(F)]]))
    alpha[:, -F:] = np.minimum(alpha[:, -F:], np.array([[(j + 1) / (F + 1) for j in range(F-1, -1, -1)]]))
    ozl = gray[y0:y1, BX0:BX1]
    for i in range(F):
        if ozl[i, :].max() > 138: alpha[i, :] = 1.0
        if ozl[hh - 1 - i, :].max() > 138: alpha[hh - 1 - i, :] = 1.0
    reg = work[y0:y1, BX0:BX1]
    work[y0:y1, BX0:BX1] = reg * (1 - alpha[..., None]) + new * alpha[..., None]
clean = np.clip(work, 0, 255).astype(np.uint8)

# ---- 星体（v8 渲染器·fringe 收敛） ----
bx0, by0, bx1, by1 = 504, 229, 572, 295
cx, cy = 538, 247
wx, wy = bx1 - bx0, by1 - by0
SS = 8
heart = img[230:292, 505:571]
hl = cv2.cvtColor(heart, cv2.COLOR_BGR2GRAY)
p97 = heart[hl > 200].mean(axis=0)
p90 = heart[hl > 163].mean(axis=0)
amber_raw = heart[(hl > 120) & (hl < 150)].mean(axis=0)
core_bgr = p97 * 0.92
fringe_bgr = amber_raw * 0.5 + med_color * 0.5

R_H, R_V, R_D, WM = 21.0, 13.0, 12.5, 5.5
r0 = np.random.default_rng(31)
specs = []
for i, (dx, dy, R) in enumerate([(1, 0, R_H), (-1, 0, R_H), (0, -1, R_V), (0, 1, R_V),
                                 (0.7071, -0.7071, R_D), (-0.7071, -0.7071, R_D),
                                 (0.7071, 0.7071, R_D), (-0.7071, 0.7071, R_D)]):
    rr = np.random.default_rng(400 + i)
    ang = rr.uniform(-0.10, 0.10)
    ca, sa = np.cos(ang), np.sin(ang)
    specs.append(dict(dx=dx*ca - dy*sa, dy=dx*sa + dy*ca, R=R*rr.uniform(0.92, 1.08),
                      ox=r0.uniform(-1.6, 1.6), oy=r0.uniform(-1.6, 1.6),
                      bow=rr.uniform(-0.9, 0.9), wobA=rr.uniform(0.10, 0.18), ph=rr.uniform(0, 6.28)))

def ray_path(spec, steps=96):
    px_, py_ = -spec["dy"], spec["dx"]
    pts = []
    for i in range(steps + 1):
        t = i / steps
        swell = 0.80 + 0.20 * t + 0.30 * max(0.0, (t - 0.82) / 0.18)
        w = WM * swell * (1 + spec["wobA"] * np.sin(t * 7.0 + spec["ph"]))
        off = spec["bow"] * np.sin(t * np.pi)
        X = (cx - bx0 + spec["ox"]) * SS + spec["dx"] * spec["R"] * t * SS + px_ * off * SS
        Y = (cy - by0 + spec["oy"]) * SS + spec["dy"] * spec["R"] * t * SS + py_ * off * SS
        pts.append((X, Y, w))
    return pts

canvas = np.zeros((wy * SS, wx * SS, 3), dtype=np.float32)
for col, mul in ((fringe_bgr, 1.30), (p90, 1.08), (core_bgr, 0.62)):
    for spec in specs:
        for X, Y, w in ray_path(spec):
            cv2.circle(canvas, (int(round(X)), int(round(Y))), max(1, int(round(w * mul * SS / 2))),
                       tuple(float(c) for c in col), -1, cv2.LINE_AA)
for _ in range(3):
    ox, oy = r0.uniform(-2.0, 2.0), r0.uniform(-2.0, 2.0)
    rrb = r0.uniform(2.6, 3.4)
    cv2.circle(canvas, (int((cx - bx0 + ox) * SS), int((cy - by0 + oy) * SS)), int(rrb * SS), tuple(float(c) for c in p90), -1, cv2.LINE_AA)
    cv2.circle(canvas, (int((cx - bx0 + ox) * SS), int((cy - by0 + oy) * SS)), int(rrb * 0.55 * SS), tuple(float(c) for c in core_bgr), -1, cv2.LINE_AA)

star_small = cv2.resize(canvas, (wx, wy), interpolation=cv2.INTER_AREA)
smask01 = np.clip(star_small.sum(axis=2) / 200.0, 0, 1)[..., None]
fp = (star_small.sum(axis=2) > 30).astype(np.uint8)
fpd = cv2.dilate(fp, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
shadow = cv2.GaussianBlur(fpd.astype(np.float32), (0, 0), 1.6)
sh_shift = np.zeros_like(shadow)
sh_shift[1:, 1:] = shadow[:-1, :-1]

base = clean[by0:by1, bx0:bx1].astype(np.float32)
winf = base * (1 - sh_shift[..., None] * 0.06)
winf = winf * (1 - smask01) + star_small * smask01
soft = cv2.GaussianBlur(winf, (0, 0), 0.35)
winf = winf * 0.4 + soft * 0.6

out = clean.copy()
out[by0:by1, bx0:bx1] = np.clip(winf, 0, 255).astype(np.uint8)
cv2.imwrite(DST, out)
print("surgery v9 saved:", DST)

orig = img
diff = np.abs(orig.astype(int) - out.astype(int)).sum(axis=2)
diff[max(0, AY0-F):min(H, BY1+F), max(0, BX0-F):min(W, BX1+F)] = 0
print("outside-box diff>0 px:", int((diff > 0).sum()))
sl = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
sc = sl[AY0:BY1, BX0:BX1].astype(float)
star_fp = cv2.dilate((sc > 150).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))) > 0
sep = np.zeros_like(star_fp); sep[269-AY0:278-AY0, :] = True
print("cell ghost bright px outside star:", int(((sc > 145) & (~star_fp) & (~sep)).sum()))
print("cell lum std now:", round(sc[~sep].std(), 1), " orig:", round(gray[AY0:BY1, BX0:BX1][~sep].std(), 1))
# 格内均亮 vs 邻格均亮（矩形偏亮检测）
nb_l = sl[AY0:AY1, BX0-40:BX0-8].astype(float)
print("cell mean lum:", round(sc[~sep].mean(),1), " left-neighbor stone mean:", round(nb_l.mean(),1))
