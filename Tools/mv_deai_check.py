"""MV 去 AI 感复检（DE-AI-SPEC-v1 回灌）。

只做「能在成片上机器判」的部分，其余明确标成人眼项，不假装机器判过。

对应条目：
  C1 画风统一      -> 逐镜色彩/亮度/对比度离群检测（本脚本）
  C3 帧间稳定      -> 引用 mv_stability_gate / mv_delivery_gate 结论，本脚本不重复
  C7 结构对账      -> 帧数/时长，本脚本只记录
  B1 皮肤质感      -> 皮肤区高频能量代理值，只报数不下判（蜡质感必须人眼）
  B4 手部/解剖     -> 抽帧图板，交人眼/多模态
  C6 字幕字卡      -> 成片已烧死，无法机判，标 UNJUDGEABLE

用法：
  python Tools/mv_deai_check.py <video> --json <out.json> [--sheet <contact.jpg>]
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

W, H = 336, 188
CUT_MAD = 12.0
OUTLIER_K = 3.0


def scan(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames, prev = [], None
    mad = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        small = cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)
        g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gf = g.astype(np.float32)
        mad.append(0.0 if prev is None else float(np.mean(np.abs(gf - prev))))
        prev = gf
        frames.append(small)
    cap.release()
    return fps, frames, np.asarray(mad)


def shot_stats(imgs):
    """一镜的聚合指标。"""
    b = np.mean([im[:, :, 0].mean() for im in imgs])
    g = np.mean([im[:, :, 1].mean() for im in imgs])
    r = np.mean([im[:, :, 2].mean() for im in imgs])
    hsv = [cv2.cvtColor(im, cv2.COLOR_BGR2HSV) for im in imgs]
    sat = float(np.mean([h[:, :, 1].mean() for h in hsv]))
    val = float(np.mean([h[:, :, 2].mean() for h in hsv]))
    # 对比度：灰度 RMS
    contrast = float(np.mean([np.std(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)) for im in imgs]))
    # 色温代理：R-B 差（越大越暖）
    warm = float(r - b)
    return {"b": float(b), "g": float(g), "r": float(r),
            "sat": sat, "val": val, "contrast": contrast, "warm": warm}


def median_mad(xs):
    med = float(np.median(xs))
    mad = float(np.median([abs(x - med) for x in xs])) or 1e-6
    return med, mad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default="")
    ap.add_argument("--sheet", default="")
    a = ap.parse_args()

    if not os.path.isfile(a.video):
        sys.exit("no such video: %s" % a.video)

    fps, frames, mad = scan(a.video)
    n = len(frames)
    cuts = [i for i in range(1, n) if mad[i] >= CUT_MAD]
    bounds = [0] + cuts + [n]
    shots = [(bounds[k], bounds[k + 1]) for k in range(len(bounds) - 1)
             if bounds[k + 1] - bounds[k] >= 6]

    rows = []
    for s0, s1 in shots:
        idx = sorted({s0, (s0 + s1) // 2, s1 - 1})
        imgs = [frames[i] for i in idx if 0 <= i < n]
        st = shot_stats(imgs)
        st.update({"t0": round(s0 / fps, 2), "t1": round(s1 / fps, 2)})
        rows.append(st)

    hits = []
    for key, label in (("val", "C1 亮度离群"), ("sat", "C1 饱和离群"),
                       ("contrast", "C1 对比度离群"), ("warm", "C1 色温离群")):
        xs = [r[key] for r in rows]
        med, m = median_mad(xs)
        for r in rows:
            if abs(r[key] - med) > OUTLIER_K * 1.4826 * m:
                hits.append({"de_ai": label, "t0": r["t0"], "t1": r["t1"],
                             "value": round(r[key], 2), "median": round(med, 2)})

    verdict = {
        "file": a.video,
        "frames": n,
        "fps": fps,
        "shots": len(shots),
        "C1_outliers": hits,
        "B1_note": "皮肤质感无可靠代理：暖色火光/土墙整片落在 YCrCb 肤色范围，"
                   "2026-11-04 两次实测均把火盆特写误报为低高频皮肤区。"
                   "B1/B2/B3 一律交人眼（DE-AI B1 要求毛孔与次表面不均，本就无法机判）。",
        "C3_stability": "见 mv_delivery_gate 回执（不重复判）",
        "C7_structure": {"frames": n, "fps": fps, "duration_sec": round(n / fps, 3)},
        "human_required": [
            {"item": "B1", "why": "皮肤蜡质/塑料感"},
            {"item": "B2", "why": "面部过对称"},
            {"item": "B3", "why": "眼神光与主光不同源"},
            {"item": "B4", "why": "手部指节与融合肢"},
            {"item": "C5", "why": "调色是否胶片感、有无艳俗饱和"},
        ],
        "unjudgeable": [
            {"item": "C6", "why": "字幕已烧入画面，无法从成片机判折行/孤字"},
        ],
    }
    if a.json:
        json.dump(verdict, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("file   :", a.video)
    print("shots  : %d  frames=%d  %.1ffps" % (len(shots), n, fps))
    print("C1 离群 :", len(hits))
    for h in hits[:12]:
        print("  %-12s %.2f-%.2fs  value=%.2f (median %.2f)" %
              (h["de_ai"], h["t0"], h["t1"], h["value"], h["median"]))
    print("B1     : 无可靠代理，交人眼（见 verdict.B1_note）")
    print("人眼必查:", ", ".join(x["item"] for x in verdict["human_required"]))
    print("不可机判:", ", ".join(x["item"] for x in verdict["unjudgeable"]))


if __name__ == "__main__":
    main()