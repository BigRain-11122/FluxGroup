# -*- coding: utf-8 -*-
# judge_bare_cuts_r1017.py — 47 bare cuts quantitative jump audit (luma/pixel/color deltas)
# Purpose: rank bare hard cuts by measurable light-state / content jump before multimodal review.
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FR = os.path.join(HERE, "v54_probe", "bare_cuts")

# 71 cuts (build_rows_v51 measured, probe_v54_r1017.py)
CUTS = [3.50,7.50,11.50,14.60,17.50,21.90,25.90,29.00,31.14,34.74,36.92,38.82,40.22,42.22,44.00,
45.22,47.50,50.52,54.22,58.44,61.98,68.86,74.60,77.34,78.00,80.18,83.56,87.74,91.06,92.62,95.22,
100.14,102.88,108.22,110.52,114.70,118.46,122.82,126.32,131.72,138.56,141.76,144.56,147.84,150.54,
152.00,153.60,155.40,159.66,163.04,167.22,172.50,177.00,180.00,182.00,184.08,187.26,190.00,191.60,
193.12,197.00,199.00,200.80,205.10,207.00,208.80,212.66,219.84,224.00,227.50,230.50]
XF = {21.90,38.82,40.22,47.50,80.18,102.88,110.52,131.72,187.26,219.84}
FX = [17.42,28.76,38.62,40.02,47.30,58.20,68.62,77.30,80.05,91.02,92.56,102.80,110.42,110.62,
131.62,141.72,150.34,159.42,168.30,176.76,187.24,193.04,199.30,212.62,219.80,231.90]

def covered(t):
    if t in XF:
        return "xf"
    for f in FX:
        if abs(f - t) <= 0.60:
            return "fx"
    return "bare"

bare = [t for t in CUTS if covered(t) == "bare"]
print("BARE=%d (expect 47)" % len(bare))

from PIL import Image
rows = []
for i, t in enumerate(bare):
    pre_p = os.path.join(FR, "b%02d_pre.jpg" % i)
    post_p = os.path.join(FR, "b%02d_post.jpg" % i)
    if not (os.path.isfile(pre_p) and os.path.isfile(post_p)):
        print("MISS b%02d @%.2f" % (i, t))
        continue
    a = Image.open(pre_p).convert("L").resize((160, 90))
    b = Image.open(post_p).convert("L").resize((160, 90))
    pa, pb = list(a.getdata()), list(b.getdata())
    ma = sum(pa) / len(pa); mb = sum(pb) / len(pb)
    dmean = abs(mb - ma)                       # light-state jump (flash/darkness pop)
    pdiff = sum(abs(x - y) for x, y in zip(pa, pb)) / len(pa)  # content jump under similar light
    ca = Image.open(pre_p).convert("RGB").resize((80, 45))
    cb = Image.open(post_p).convert("RGB").resize((80, 45))
    qa, qb = list(ca.getdata()), list(cb.getdata())
    ra = sum(p[0] for p in qa) / len(qa); ga = sum(p[1] for p in qa) / len(qa); ba_ = sum(p[2] for p in qa) / len(qa)
    rb = sum(p[0] for p in qb) / len(qb); gb = sum(p[1] for p in qb) / len(qb); bb = sum(p[2] for p in qb) / len(qb)
    colshift = abs(ra - rb) + abs(ga - gb) + abs(ba_ - bb)     # color-temp jump
    score = dmean * 1.0 + min(pdiff, 60) * 0.55 + min(colshift, 120) * 0.35
    rows.append((i, t, dmean, pdiff, colshift, score, ma, mb))

rows.sort(key=lambda r: -r[5])
print("\n%-5s %-7s %-6s %-7s %-8s %-6s  %s" % ("id", "cut@s", "dLuma", "pixDiff", "colShift", "score", "pre->post luma"))
for i, t, dmean, pdiff, colshift, score, ma, mb in rows:
    print("b%02d  @%6.2f  %5.1f  %6.1f  %6.1f  %6.1f   %.0f->%.0f" % (i, t, dmean, pdiff, colshift, score, ma, mb))

# also dump the bNN -> timestamp table in bare order (for board mapping)
print("\n-- bare order --")
for i, t in enumerate(bare):
    print("b%02d=%.2f" % (i, t), end="  ")
print()
