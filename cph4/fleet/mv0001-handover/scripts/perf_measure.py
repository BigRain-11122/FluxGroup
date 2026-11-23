# -*- coding: utf-8 -*-
"""perf_measure.py — 女主近景 72 帧的表演量化（按 mv-performance 席判据）。"""
import os
import sys

import numpy as np
from PIL import Image

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = r"K:\Fluxgroup\.codely-cli\tmp\perf"
fs = sorted(f for f in os.listdir(D) if f.startswith("f_") and f.endswith(".png"))
if not fs:
    raise SystemExit("no frames")

# 区域（1344x768 中女主面部的大致分区，先按整幅比较再细分）
REGIONS = {
    "eye": (700, 240, 1060, 400),
    "mouth": (760, 470, 1010, 620),
    "face": (620, 120, 1120, 660),
}

prev = {}
series = {k: [] for k in REGIONS}
for i, f in enumerate(fs):
    a = np.asarray(Image.open(os.path.join(D, f)).convert("L"), dtype=np.float32)
    for k, (x0, y0, x1, y1) in REGIONS.items():
        cur = a[y0:y1, x0:x1]
        if k in prev:
            series[k].append(float(np.abs(cur - prev[k]).mean()))
        prev[k] = cur

for k in REGIONS:
    s = np.array(series[k])
    print("%-6s n=%d  mean=%.3f  p50=%.3f  p90=%.3f  max=%.3f  max@frame=%d"
          % (k, len(s), s.mean(), np.percentile(s, 50), np.percentile(s, 90), s.max(),
             int(np.argmax(s)) + 2))

# 眨眼候选：眼区在 2-4 帧内出现明显尖峰后回落
e = np.array(series["eye"])
mu, sd = e.mean(), e.std() + 1e-6
peaks = []
for i in range(2, len(e) - 2):
    if e[i] > mu + 2.2 * sd and e[i] >= e[i - 1] and e[i] >= e[i + 1]:
        peaks.append((i + 2, round(float(e[i]), 2)))
print("\n眼区尖峰(<%d帧宽)→ 眨眼候选:" % 0, peaks[:12], " 共", len(peaks))

# 表情 onset：脸区持续变化段（连续 >=6 帧高于均值 1.3 倍）
f_ = np.array(series["face"])
thr = f_.mean() * 1.3
runs, cur = [], 0
for v in f_:
    if v > thr:
        cur += 1
    else:
        if cur >= 6:
            runs.append(cur)
        cur = 0
if cur >= 6:
    runs.append(cur)
print("脸区持续变化段(>=6帧):", runs if runs else "无（=表演基本静止）")
print("\n判据：眨眼 4-6s 脸镜需 ≥1 次；表情 onset 12-20 帧(0.5-0.8s)；反应延迟 ≥3 帧")
