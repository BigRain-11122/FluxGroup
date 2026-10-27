# -*- coding: utf-8 -*-
"""mv_transition_audit.py - quantify every cut: motion continuity and "pull-out" transitions.

For each cut time t:
  tail : 0.5s before the cut
  head : 0.5s after the cut
Measures, from dense optical flow on downscaled frames:
  mag_tail / mag_head     mean flow magnitude (how much the frame moves)
  dir_match               cosine between dominant flow directions (1=same, -1=opposite)
  div_tail / div_head     mean flow divergence (positive = zoom-out / pull-back)
  luma_gap                |mean luma last frame - first frame| after the cut

Verdicts:
  MATCH        direction continues, magnitudes comparable       (premium continuity)
  OPPOSE       camera goes in then out (or vice versa)          (reads as "douyin pull-out")
  PULLOUT      tail divergence high (shot ends by moving away)   (suspicious)
  STATIC_JUMP  static -> moving or moving -> static with big luma/motion gap
  HARD         no continuity at all

Usage:
  py mv_transition_audit.py <video> [--json out.json]
"""
import argparse
import json
import sys

import cv2
import numpy as np

W, H = 256, 144
WIN = 12   # 0.5s at 24fps


def flow_stats(flow):
    fx, fy = flow[..., 0], flow[..., 1]
    mag = float(np.mean(np.hypot(fx, fy)))
    # dominant direction = mean vector (robust enough for a short window)
    vx, vy = float(np.mean(fx)), float(np.mean(fy))
    div = float(np.mean(np.gradient(fx, axis=1) + np.gradient(fy, axis=0)))
    return mag, (vx, vy), div


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA),
                                    cv2.COLOR_BGR2GRAY))
    cap.release()
    n = len(frames)

    # cut detection: frame-to-frame MAD spike + return test
    mad = np.zeros(n)
    for i in range(1, n):
        mad[i] = float(np.mean(np.abs(frames[i].astype(np.float32) - frames[i - 1].astype(np.float32))))
    cuts = []
    for i in range(1, n - 1):
        if mad[i] < 18.0:
            continue
        # exclude one-frame flashes: compare i-1 and i+2
        if i + 2 < n:
            back = float(np.mean(np.abs(frames[i - 1].astype(np.float32) - frames[i + 2].astype(np.float32))))
            if back < 8.0:
                continue
        cuts.append(i)

    def window_stats(i0, i1):
        mags, dirs, divs = [], [], []
        for i in range(i0 + 1, i1):
            if i < 1 or i >= n:
                continue
            f = cv2.calcOpticalFlowFarneback(frames[i - 1], frames[i], None,
                                             0.5, 3, 15, 3, 5, 1.2, 0)
            m, d, dv = flow_stats(f)
            mags.append(m)
            dirs.append(d)
            divs.append(dv)
        if not mags:
            return None
        # camera motion (global), not subject motion: phase correlation between window ends
        a, b = frames[max(0, i0)].astype(np.float32), frames[min(n - 1, i1 - 1)].astype(np.float32)
        try:
            (gx, gy), gresp = cv2.phaseCorrelate(a, b)
        except cv2.error:
            (gx, gy), gresp = 0.0, 0.0, 0.0
        return (float(np.mean(mags)), (float(np.mean([d[0] for d in dirs])),
                                       float(np.mean([d[1] for d in dirs]))),
                float(np.mean(divs)), (float(gx), float(gy)), float(gresp))

    rows = []
    for c in cuts:
        tail = window_stats(max(0, c - WIN), c)
        head = window_stats(c, min(n, c + WIN))
        if tail is None or head is None:
            continue
        mt, dt, vt, gt, rt = tail
        mh, dh, vh, gh, rh = head
        nt = np.hypot(*dt)
        nh = np.hypot(*dh)
        cos = float((dt[0] * dh[0] + dt[1] * dh[1]) / (nt * nh)) if nt > 0.05 and nh > 0.05 else 0.0
        # camera-only direction: use global shift, not subject flow
        gnt, gnh = np.hypot(*gt), np.hypot(*gh)
        gcos = float((gt[0] * gh[0] + gt[1] * gh[1]) / (gnt * gnh)) if gnt > 1.5 and gnh > 1.5 else 0.0
        luma_gap = float(abs(frames[c].mean() - frames[c - 1].mean()))

        if vt > 0.04 and gnt * 84 / 336 > 6.0:
            verdict = "PULLOUT"
        elif gnt > 1.5 and gnh > 1.5 and gcos < -0.25:
            verdict = "OPPOSE"
        elif cos > 0.4 and abs(mt - mh) < max(1.5, 0.7 * max(mt, mh)):
            verdict = "MATCH"
        elif max(mt, mh) > 0.8 and min(mt, mh) < 0.2:
            verdict = "STATIC_JUMP"
        else:
            verdict = "HARD"

        rows.append({
            "t": round(c / fps, 3), "frame": int(c), "verdict": verdict,
            "mag_tail": round(mt, 2), "mag_head": round(mh, 2),
            "dir_cos": round(cos, 2), "g_cos": round(gcos, 2),
            "g_tail": round(float(gnt), 1), "g_head": round(float(gnh), 1),
            "div_tail": round(vt, 3), "div_head": round(vh, 3),
            "luma_gap": round(luma_gap, 1),
        })

    from collections import Counter
    cnt = Counter(r["verdict"] for r in rows)
    print("frames=%d cuts=%d" % (n, len(rows)))
    print("summary:", dict(cnt))
    print("")
    print("%-9s %-6s %-12s %7s %7s %7s %8s" % ("time", "frame", "verdict", "magT", "magH", "cos", "divT"))
    for r in rows:
        print("%-9.3f %-6d %-12s %7.2f %7.2f %7.2f %8.3f" % (
            r["t"], r["frame"], r["verdict"], r["mag_tail"], r["mag_head"],
            r["dir_cos"], r["div_tail"]))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
        print("json ->", a.json)


if __name__ == "__main__":
    main()