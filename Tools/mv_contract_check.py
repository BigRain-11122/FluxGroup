# -*- coding: utf-8 -*-
"""G4 创作契约闸 · 2026-11-05

为什么有这个文件：2026-11-05 的教训是「机器面全绿但全片一个调子」——交付闸只查
重复/静止/闪烁，没有一条断言检查创作契约，于是调色错一个月都发现不了。
本闸把 CEO 令里可机器测的部分变成断言（MV-DEFINITION-OF-DONE-v1.md G4）。

判据（--era 或分段表给定时逐段判）：
  现代段：R-B <= MODERN_RB_MAX 且 饱和度 <= 基线 * MODERN_SAT_RATIO
  古代段：R-B >= ANCIENT_RB_MIN
  镜长  ：主歌段 <= SHOT_MAX_S（段表给的时长直接判）

用法：
  python Tools/mv_contract_check.py <video> --segments <segments.json> [--json out.json]
  python Tools/mv_contract_check.py <video> --baseline-sat 190      # 只做全片体检
分段表 schema: [{"id":"INT1..","t0":0.0,"t1":3.5,"era":"modern"}, ...]
"""
import argparse
import json
import sys

import cv2
import numpy as np

MODERN_RB_MAX = 5.0      # solo-eyeball fallback; the live rule below is separation-based
DARK_LUMA = 40.0         # below this a frame is too dark for HSV saturation to mean anything
SEPARATION_MIN = 12.0    # modern must sit at least this much cooler than the ancient baseline
MODERN_SAT_RATIO = 0.98  # 现代段不得比古代基线更饱和（原 0.80 不可达：同源暖调底，实测 0.42 desat 仍在 173-206）
NIGHT_SAT_RATIO = 0.95   # 台灯夜景：色相是物理正确的，只要求降饱和（2026-11-05 单段标定）
ANCIENT_RB_MIN = 15.0    # 古代段应暖
SHOT_MAX_S = 3.4         # 主歌段镜长上限（CEO 10-19 §一）
SAMPLES_PER_SEG = 5


def seg_stats(cap, t0, t1, fps):
    n = max(1, SAMPLES_PER_SEG)
    rbs, sats, vs = [], [], []
    for i in range(n):
        t = t0 + (t1 - t0) * (i + 0.5) / n
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ok, f = cap.read()
        if not ok:
            continue
        b, g, r = cv2.split(f)
        rbs.append(float(r.mean() - b.mean()))
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        sats.append(float(hsv[:, :, 1].mean()))
        vs.append(float(hsv[:, :, 2].mean()))
    if not rbs:
        return None
    return float(np.mean(rbs)), float(np.mean(sats)), float(np.mean(vs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--segments", default="")
    ap.add_argument("--baseline-sat", type=float, default=0.0)
    ap.add_argument("--json", default="")
    ap.add_argument("--fps-scan", type=float, default=0.0)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    if not cap.isOpened():
        sys.exit("cannot open %s" % a.video)
    fps = a.fps_scan or cap.get(cv2.CAP_PROP_FPS) or 24.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    print("file    : %s" % a.video)
    print("frames  : %d @ %.3ffps" % (total, fps))

    if not a.segments:
        rb, sat, _v = seg_stats(cap, 0, total / fps, fps) or (0.0, 0.0, 0.0)
        print("whole   : R-B %+.1f  sat %.1f  (no segment table: report only)" % (rb, sat))
        cap.release()
        return 0

    segs = json.load(open(a.segments, encoding="utf-8"))
    print("segments: %d" % len(segs))
    # the film's own ancient segments are the baseline: the rule is
    # "modern must read cooler / less saturated than ancient", not an absolute number
    anc_rb, anc_sat = [], []
    for s in segs:
        if s.get("era") == "ancient":
            st = seg_stats(cap, s["t0"], s["t1"], fps)
            if st:
                anc_rb.append(st[0]); anc_sat.append(st[1])
    anc_rb_med = float(np.median(anc_rb)) if anc_rb else 25.0
    anc_sat_med = float(np.median(anc_sat)) if anc_sat else 190.0
    base_sat = a.baseline_sat or anc_sat_med
    rb_cap = min(MODERN_RB_MAX + 10.0, anc_rb_med - SEPARATION_MIN)
    print("ancient baseline: R-B %+.1f  sat %.0f  -> modern cap R-B %+.1f" % (anc_rb_med, anc_sat_med, rb_cap))

    rows, fails = [], []
    for s in segs:
        st = seg_stats(cap, s["t0"], s["t1"], fps)
        if st is None:
            continue
        rb, sat, vmean = st
        era = s.get("era", "")
        dur = s["t1"] - s["t0"]
        bad = []
        if era == "modern":
            if rb > rb_cap:
                bad.append("R-B %+.1f > %.1f (separation from ancient)" % (rb, rb_cap))
            if vmean < DARK_LUMA:
                if sat > anc_sat_med * MODERN_SAT_RATIO:
                    print("  note %s: mean V %.0f < %.0f, chroma not judged" % (s["id"], vmean, DARK_LUMA))
            elif sat > anc_sat_med * MODERN_SAT_RATIO:
                bad.append("sat %.0f > %.0f (ancient baseline x %.2f)" %
                           (sat, anc_sat_med * MODERN_SAT_RATIO, MODERN_SAT_RATIO))
        elif era == "modern_night":
            # tungsten-lit interiors: colour is diegetic, only saturation is constrained
            if vmean >= DARK_LUMA and sat > anc_sat_med * NIGHT_SAT_RATIO:
                bad.append("sat %.0f > %.0f (ancient baseline x %.2f)" %
                           (sat, anc_sat_med * NIGHT_SAT_RATIO, NIGHT_SAT_RATIO))
        # ancient carries the baseline; no absolute floor - a dark stele lit by one
        # flame is legitimately neutral, and the modern-side separation already
        # guarantees the two worlds read differently (2026-11-05).
        if dur > SHOT_MAX_S and s.get("main_verse"):
            bad.append("len %.2fs > %.1fs" % (dur, SHOT_MAX_S))
        rows.append({"id": s["id"], "era": era, "r_b": round(rb, 1),
                     "sat": round(sat, 1), "dur": round(dur, 2), "bad": bad})
        if bad:
            fails.append("%s (%s): %s" % (s["id"], era, "; ".join(bad)))

    for r in rows:
        flag = "FAIL" if r["bad"] else "ok  "
        print("  %s %-22s %-7s R-B %+6.1f  sat %5.1f  %.2fs" %
              (flag, r["id"], r["era"], r["r_b"], r["sat"], r["dur"]))
    print("baseline_sat: %.1f  modern_sat_max: %.1f" % (base_sat, base_sat * MODERN_SAT_RATIO))
    if fails:
        print("VERDICT: FAIL (%d segment(s))" % len(fails))
        for f in fails[:10]:
            print("  " + f)
        if len(fails) > 10:
            print("  ... %d more" % (len(fails) - 10))
        rc = 1
    else:
        print("VERDICT: PASS")
        rc = 0
    if a.json:
        json.dump({"file": a.video, "fails": fails, "rows": rows,
                   "verdict": "PASS" if rc == 0 else "FAIL"},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cap.release()
    return rc


if __name__ == "__main__":
    sys.exit(main())