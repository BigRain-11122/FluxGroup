# -*- coding: utf-8 -*-
"""mv_shot_audit.py - per-shot temporal-stability audit for a finished cut.

Scores every shot on four human-visible failure modes:
  FLICKER   high-frequency luma change with little structural change
  JERK      second difference of global camera motion (judder / snap)
  FLOW      frame-to-frame instability of local optical flow (i2v warp jitter)
  FREEZE    ratio of near-identical consecutive frames (frozen i2v tail)

Shot windows come from mv_full_shots.py (NEW + REUSE), which is the edit's source of truth,
so planned cuts are never counted as defects. Title cards / glyph bridges are tagged and
excluded from ranking (their motion is authored).

Usage:
  py mv_shot_audit.py <video> [--json out.json] [--top 20]
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REEL = os.path.join(HERE, "..", "cph4", "fleet", "mv0001-handover", "outbound", "krea2", "30s-reel-v1")

AW, AH = 256, 144
FW, FH = 160, 90
FREEZE_MAD = 0.20
TITLE_IDS = {"T_glyphs", "S9_profile", "Z01_words_alone", "Z03_lights_out", "Z04_glyph_remains"}


def robust(x):
    x = np.asarray(x, float)
    if x.size == 0:
        return 0.0, 0.0
    med = float(np.median(x))
    return med, float(np.median(np.abs(x - med)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default=None)
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()

    sys.path.insert(0, REEL)
    import mv_full_shots as M

    shots = []
    for r in M.NEW:
        shots.append((r[0], float(r[1]), float(r[2]), float(r[3])))
    for r in M.REUSE:
        shots.append((r[0] + "@reuse", float(r[1]), float(r[2]), float(r[3])))
    shots.sort(key=lambda x: x[1])

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    gray = []
    prev = None
    flow_prev = None
    luma = []
    shift = []
    flow_mag = []
    dflow = []
    mad = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(fr, (AW, AH), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY)
        gray.append(g)
        luma.append(float(g.mean()))
        if prev is None:
            shift.append((0.0, 0.0, 0.0)); mad.append(0.0)
            flow_mag.append(0.0); dflow.append(0.0); flow_prev = None
        else:
            mad.append(float(np.mean(np.abs(g.astype(np.float32) - prev.astype(np.float32)))))
            try:
                (dx, dy), resp = cv2.phaseCorrelate(prev.astype(np.float32), g.astype(np.float32))
            except cv2.error:
                (dx, dy), resp = 0.0, 0.0, 0.0
            shift.append((float(dx), float(dy), float(resp)))
            fg = cv2.resize(g, (FW, FH), interpolation=cv2.INTER_AREA)
            fp = cv2.resize(prev, (FW, FH), interpolation=cv2.INTER_AREA)
            flow = cv2.calcOpticalFlowFarneback(fp, fg, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            fm = float(np.mean(np.hypot(flow[..., 0], flow[..., 1])))
            flow_mag.append(fm)
            if flow_prev is not None:
                dflow.append(float(np.mean(np.abs(flow - flow_prev))))
            else:
                dflow.append(0.0)
            flow_prev = flow
        prev = g
    cap.release()

    luma = np.asarray(luma); mad = np.asarray(mad); dflow = np.asarray(dflow)
    shift = np.asarray(shift); mag = np.hypot(shift[:, 0], shift[:, 1])
    n = len(luma)

    rows = []
    for sid, t0, t1, speed in shots:
        ia, ib = max(0, int(round(t0 * fps))), min(n, int(round(t1 * fps)))
        if ib - ia < 6:
            continue
        L = luma[ia:ib]
        d1 = np.diff(L)
        flick = float(np.median(np.abs(np.diff(d1)))) if d1.size > 3 else 0.0
        S = mag[ia + 1:ib]
        jerk = float(np.median(np.abs(np.diff(S, n=2)))) if S.size > 3 else 0.0
        flow_j = float(np.median(dflow[ia + 1:ib])) if ib - ia > 3 else 0.0
        m = mad[ia + 1:ib]
        freeze = float(np.mean(m < FREEZE_MAD)) if m.size else 0.0
        rows.append({"shot": sid, "t0": round(t0, 2), "t1": round(t1, 2),
                     "dur": round(t1 - t0, 2), "speed": speed,
                     "flicker": round(flick, 3), "jerk": round(jerk, 3),
                     "flow": round(flow_j, 3), "freeze": round(freeze, 3),
                     "title": sid in TITLE_IDS})

    # z-score ranking on non-title shots
    def z(key, base):
        vals = np.array([r[key] for r in base], float)
        med, madv = robust(vals)
        scale = max(1e-6, 1.4826 * madv)
        return lambda v: (v - med) / scale

    base = [r for r in rows if not r["title"]]
    zf = z("flicker", base); zj = z("jerk", base); zo = z("flow", base); zr = z("freeze", base)
    for r in rows:
        r["score"] = round(zf(r["flicker"]) * 1.0 + zj(r["jerk"]) * 1.0 +
                            zo(r["flow"]) * 1.0 + zr(r["freeze"]) * 0.5, 2)
    rows.sort(key=lambda r: (-r["score"], r["t0"]))

    print("frames=%d fps=%.3f shots=%d" % (n, fps, len(rows)))
    print("")
    print("%-24s %7s %7s %6s %8s %8s %8s %7s %6s" % (
        "shot", "start", "end", "speed", "flicker", "jerk", "flow", "freeze", "score"))
    for r in rows[:a.top]:
        print("%-24s %7.2f %7.2f %6.2f %8.3f %8.3f %8.3f %7.2f %6.2f%s" % (
            r["shot"], r["t0"], r["t1"], r["speed"], r["flicker"], r["jerk"],
            r["flow"], r["freeze"], r["score"], " T" if r["title"] else ""))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
        print("json ->", a.json)


if __name__ == "__main__":
    main()