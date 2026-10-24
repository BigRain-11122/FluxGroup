# -*- coding: utf-8 -*-
"""mv_stability_gate.py - release gate for timeline stability (CEO defect D-20261024-01).

Fails (exit 1) when the cut contains:
  - intra-shot whole-frame jumps (displacement spike, same framing returns, low aligned residual)
  - freezes of 3+ near-identical frames

Passes only when both counts are zero. Cuts and cross-fades are excluded by the return test.

Usage:
  py mv_stability_gate.py <video> [--expect-frames 5623] [--json out.json]
"""
import argparse
import json
import sys

import cv2
import numpy as np

W, H = 336, 188
SCALE = 1344.0 / W
SHIFT_MIN = 6.0        # px at 1344 width
SIM_MIN = 0.78
RESID_MAX = 14.0
FREEZE_MAD = 0.20
FREEZE_RUN = 3


def sim(a, b):
    a = a.astype(np.float32) - a.mean()
    b = b.astype(np.float32) - b.mean()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na < 1e-6 or nb < 1e-6 else float((a * b).sum() / (na * nb))


def static_jump(frames, i, k=12):
    """Corroborate a whole-frame jump on a *static* patch (kills flame/motion false positives).

    A real frame jump moves the static background too; a flickering flame does not.
    """
    if i - k < 0 or i + k >= len(frames):
        return False
    a, b, c = frames[i - k], frames[i + k], frames[i]
    h, w = a.shape
    best = None
    cw, ch = w // 6, h // 3
    for gy in range(3):
        for gx in range(6):
            p = a[gy * ch:(gy + 1) * ch, gx * cw:(gx + 1) * cw]
            q = b[gy * ch:(gy + 1) * ch, gx * cw:(gx + 1) * cw]
            if p.size == 0 or p.std() < 12:
                continue
            s = sim(p, q)
            if s < 0.90:
                continue
            if best is None or p.std() > best[0]:
                best = (float(p.std()), gx * cw, gy * ch, p.copy())
    if best is None:
        return False
    _, x0, y0, tpl = best
    res = cv2.matchTemplate(c, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    if score < 0.40:
        return False
    off = ((loc[0] - x0) ** 2 + (loc[1] - y0) ** 2) ** 0.5 * SCALE
    return off >= SHIFT_MIN


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--expect-frames", type=int, default=0)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    if not cap.isOpened():
        print("FAIL cannot open", a.video)
        sys.exit(2)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    thumbs = []
    small = []
    mad = [0.0]
    shift = [(0.0, 0.0, 0.0)]
    resid = [0.0]
    prev = None
    n = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY)
        thumbs.append(cv2.resize(g, (84, 47), interpolation=cv2.INTER_AREA))
        small.append(g)
        gf = g.astype(np.float32)
        if prev is not None:
            mad.append(float(np.mean(np.abs(gf - prev))))
            (dx, dy), resp = cv2.phaseCorrelate(prev, gf)
            shift.append((dx, dy, resp))
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            w = cv2.warpAffine(prev, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
            resid.append(float(np.mean(np.abs(w - gf))))
        prev = gf
        n += 1
    cap.release()

    shift = np.asarray(shift)
    resid = np.asarray(resid)
    mad = np.asarray(mad)
    mag = np.hypot(shift[:, 0], shift[:, 1]) * SCALE

    seams = []
    cands = []
    for i in range(10, n - 10):
        if mag[i] < SHIFT_MIN or resid[i] > RESID_MAX:
            continue
        s = sim(thumbs[i - 8], thumbs[i + 8])
        if s < SIM_MIN:
            continue          # framing changed -> cut, not a seam
        if not static_jump(small, i):
            continue          # moving content (flame/actor) -> not a frame jump
        cands.append((i, mag[i], s))
    cands.sort(key=lambda x: -x[1])
    for c in cands:
        if all(abs(c[0] - k[0]) > 4 for k in seams):
            seams.append(c)
    seams.sort(key=lambda x: x[0])

    freezes = []
    run = 0
    for i in range(1, n):
        if mad[i] < FREEZE_MAD:
            run += 1
        else:
            if run >= FREEZE_RUN:
                s0 = i - run
                # exempt: closing hold, fade-to-black hold, and a hold that ends on a cut
                pre_cut = any(mad[j] > 15.0 for j in range(i, min(n, i + 3)))
                dark = float(np.mean([f.mean() for f in small[s0:i]])) < 10.0
                if not pre_cut and not dark and s0 < n - 12:
                    freezes.append((s0, run))
            run = 0
    if run >= FREEZE_RUN:
        s0 = n - run
        pre_cut = False
        dark = float(np.mean([f.mean() for f in small[s0:n]])) < 10.0
        if not pre_cut and not dark and s0 < n - 12:
            freezes.append((s0, run))

    print("file   :", a.video)
    print("frames : %d @ %.3f fps" % (n, fps))
    print("seams  : %d" % len(seams))
    for i, m, s in seams:
        print("   t=%.3fs frame=%d shift=%.1fpx sim=%.3f" % (i / fps, i, m, s))
    print("freezes: %d" % len(freezes))
    for f0, r in freezes:
        print("   t=%.3fs frame=%d run=%d" % (f0 / fps, f0, r))

    frame_ok = (a.expect_frames == 0) or (n == a.expect_frames)
    if not frame_ok:
        print("FAIL frame count %d != %d" % (n, a.expect_frames))
    ok = (len(seams) == 0) and (len(freezes) == 0) and frame_ok

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"frames": n, "fps": fps,
                       "seams": [{"t": round(i / fps, 3), "frame": i, "shift_px": round(m, 1),
                                  "sim": round(s, 3)} for i, m, s in seams],
                       "freezes": [{"t": round(f0 / fps, 3), "frame": f0, "run": r} for f0, r in freezes],
                       "pass": ok}, fh, ensure_ascii=False, indent=1)
        print("json ->", a.json)

    print("VERDICT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()