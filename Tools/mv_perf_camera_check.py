"""表演-运镜闸（AI-ACTOR-PERFORMANCE-v2 的机器可判部分）。

只做能在成片上量出来的三件事，其余交人眼（意图可读/微手势/情绪渐变）。

判据来源 = cph4/fleet/mv-album-001-jay/AI-ACTOR-PERFORMANCE-v2.md §五：
  1. 运镜匀速（速度标准差≈0）= AI 签名，判负
  2. 无缓入缓出（硬起硬停）= 判负
  3. 镜内推近冒充（径向散度大 + 平移小）= 禁用（CEO 2026-10-24 红线：禁推近裁切冒充修复）
  4. 整镜几乎不动 = 交静场白名单（不在本闸判负，只报）

用法：
  python Tools/mv_perf_camera_check.py <video> [--json out.json]
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

W, H = 336, 188
CUT_MAD = 12.0

# 阈值（改动须带实测证据，见 spec §G）
RADIAL_W = 8.0           # 径向散度换算成等效像素/帧的权重（由 synth uniform_push 标定）
MIN_MOTION = 0.10        # 运动强度低于此视为静止（交静场白名单），不谈匀速
UNIFORM_CV = 0.35        # 强度序列 cv：synth 匀速 0.294 / 缓动 0.475，取中间
EASE_RATIO = 0.90        # 首末段强度/中段：synth 匀速 ~1.04 / 缓动 0.44。>=0.90 = 全程同速
PUSH_SHARE = 0.60        # 径向分量占运动强度比例 >= 此值 = 该镜是推/拉而非横移
MIN_DUR_FOR_EASE = 3.0   # 只有 >=3s 的镜才谈缓入缓出（正典：<3s 只给动作，脸来不及演弧）


def scan(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    gray, mad = [], []
    prev = None
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY)
        gray.append(g)
        gf = g.astype(np.float32)
        mad.append(0.0 if prev is None else float(np.mean(np.abs(gf - prev))))
        prev = gf
    cap.release()
    return fps, gray, np.asarray(mad)


def shot_motion(grays):
    """返回每帧运动强度序列。

    推近时平移均值≈0（径向向量互相抵消），只测平移会漏掉推近。
    故运动强度 = 平移量 + k*|径向散度|：平移和推近都进入同一序列，
    再用序列的变异系数判「匀速」（AI 默认等速的核心签名）。
    """
    speeds, divs, motion = [], [], []
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2.0, H / 2.0
    rx, ry = xx - cx, yy - cy
    norm = np.sqrt(rx * rx + ry * ry) + 1e-6
    for i in range(1, len(grays)):
        p0, p1 = grays[i - 1], grays[i]
        flow = cv2.calcOpticalFlowFarneback(p0, p1, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        u, v = flow[..., 0], flow[..., 1]
        tx, ty = float(u.mean()), float(v.mean())
        rad = (u * rx + v * ry) / norm
        div = float(rad.mean())
        speed = float((tx * tx + ty * ty) ** 0.5)
        speeds.append(speed)
        divs.append(div)
        motion.append(speed + RADIAL_W * abs(div))
    return np.asarray(speeds), np.asarray(divs), np.asarray(motion)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    if not os.path.isfile(a.video):
        sys.exit("no such video: " + a.video)

    fps, grays, mad = scan(a.video)
    n = len(grays)
    cuts = [i for i in range(1, n) if mad[i] >= CUT_MAD]
    bounds = [0] + cuts + [n]
    shots = [(bounds[k], bounds[k + 1]) for k in range(len(bounds) - 1)
             if bounds[k + 1] - bounds[k] >= 6]

    rows, fails = [], []
    for s0, s1 in shots:
        seg = grays[s0:s1]
        speeds, divs, motion = shot_motion(seg)
        if motion.size < 4:
            continue
        m_mean = float(motion.mean())
        m_std = float(motion.std())
        m_cv = m_std / m_mean if m_mean > 1e-6 else 0.0
        k = max(1, len(motion) // 5)
        head, tail = motion[:k].mean(), motion[-k:].mean()
        mid = motion[k:-k].mean() if len(motion) > 2 * k else motion.mean()
        ease = (head + tail) / 2.0 / (mid + 1e-6)
        div = float(divs.mean())
        push_share = RADIAL_W * abs(div) / (m_mean + 1e-6)
        t0, t1 = round(s0 / fps, 2), round(s1 / fps, 2)
        flags = []
        dur = (s1 - s0) / fps
        if m_mean >= MIN_MOTION and dur >= MIN_DUR_FOR_EASE:
            kind = "推近" if push_share >= PUSH_SHARE else "运镜"
            if m_cv < UNIFORM_CV:
                flags.append("匀速%s(无加速度, cv=%.2f)" % (kind, m_cv))
            if ease >= EASE_RATIO:
                flags.append("无缓入缓出(硬起硬停, ease=%.2f)" % ease)
        rows.append({"t0": t0, "t1": t1, "dur": round((s1 - s0) / fps, 2),
                     "motion": round(m_mean, 3), "m_cv": round(m_cv, 3),
                     "ease_ratio": round(float(ease), 3), "divergence": round(div, 3),
                     "push_share": round(float(push_share), 3),
                     "mean_speed": round(float(speeds.mean()), 3),
                     "flags": flags})
        if flags:
            fails.append({"t0": t0, "t1": t1, "flags": flags})

    out = {"file": a.video, "frames": n, "fps": fps, "shots": len(shots),
           "hits": len(fails), "rows": rows,
           "human_required": [
               {"item": "意图可读", "how": "静音片段盲看，'他在做什么/想要什么' ≥4/5 一致"},
               {"item": "微手势", "how": "一镜 ≤2 个"},
               {"item": "情绪渐变", "how": "禁一步到位：说前状态→触发→动作→落点"},
               {"item": "反应延迟", "how": "双人镜先看/先听，身体后动（3-8 帧）"},
           ]}
    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("file  :", a.video)
    print("shots : %d  hits=%d" % (len(shots), len(fails)))
    for f in fails[:16]:
        print("  %.2f-%.2fs  %s" % (f["t0"], f["t1"], " / ".join(f["flags"])))
    print("人眼必查:", ", ".join(x["item"] for x in out["human_required"]))


if __name__ == "__main__":
    main()