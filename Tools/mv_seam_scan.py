# -*- coding: utf-8 -*-
"""mv_seam_scan.py - list *intra-shot* camera/seam jumps (not cuts).

Cut test: aligned residual high AND the shot does not return.
Seam test: global shift spike AND the shot returns (same framing) AND aligned residual low.

This is deliberately separate from mv_jitter_analyze.py: the question here is only
"which frames inside a shot move the whole frame abruptly", which is what reads as a jump.
"""
import sys

import cv2
import numpy as np

p = sys.argv[1] if len(sys.argv) > 1 else None
if not p:
    sys.exit("usage: mv_seam_scan.py <video>")

cap = cv2.VideoCapture(p)
fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
AW, AH = 336, 188
thumbs = []
mad = [0.0]
shift = [(0.0, 0.0, 0.0)]
resid = [0.0]
prev = None
n = 0
while True:
    ok, fr = cap.read()
    if not ok:
        break
    g = cv2.cvtColor(cv2.resize(fr, (AW, AH), interpolation=cv2.INTER_AREA),
                     cv2.COLOR_BGR2GRAY)
    thumbs.append(cv2.resize(g, (84, 47), interpolation=cv2.INTER_AREA))
    gf = g.astype(np.float32)
    if prev is not None:
        mad.append(float(np.mean(np.abs(gf - prev))))
        (dx, dy), resp = cv2.phaseCorrelate(prev, gf)
        shift.append((dx, dy, resp))
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        w = cv2.warpAffine(prev, M, (AW, AH), borderMode=cv2.BORDER_REPLICATE)
        resid.append(float(np.mean(np.abs(w - gf))))
    prev = gf
    n += 1
cap.release()

shift = np.asarray(shift); resid = np.asarray(resid); mad = np.asarray(mad)
mag = np.hypot(shift[:, 0], shift[:, 1]) * (1344.0 / AW)


def sim(a, b):
    a = a.astype(np.float32) - a.mean()
    b = b.astype(np.float32) - b.mean()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na < 1e-6 or nb < 1e-6 else float((a * b).sum() / (na * nb))


cands = []
for i in range(8, n - 8):
    if mag[i] < 6.0:
        continue
    s = sim(thumbs[i - 8], thumbs[i + 8])
    if s < 0.78:
        continue          # shot did not return -> cut, not seam
    if resid[i] > 14.0:
        continue          # structural change even after alignment
    cands.append((i, mag[i], s, resid[i], mad[i]))

# cluster within 4 frames, keep the strongest
cands.sort(key=lambda x: -x[1])
kept = []
for c in cands:
    if all(abs(c[0] - k[0]) > 4 for k in kept):
        kept.append(c)
kept.sort(key=lambda x: x[0])

print("frames=%d  seam candidates=%d" % (n, len(kept)))
print("%-9s %-7s %8s %7s %7s %7s" % ("time", "frame", "shift_px", "sim", "resid", "mad"))
for i, m, s, r, d in kept[:40]:
    print("%-9.3f %-7d %8.1f %7.3f %7.2f %7.2f" % (i / fps, i, m, s, r, d))