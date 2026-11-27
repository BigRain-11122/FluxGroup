# -*- coding: utf-8 -*-
"""plan_edit_v12.py — 以「音乐事件」为锚重排 10 镜：切点落在强音头/乐句边界上，
每镜用 ±10% 内的变速吸收时长差（源素材已用满，只能靠变速重排）。"""
import sys
import wave

import numpy as np
from scipy.signal import find_peaks

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WAV = r"K:\Fluxgroup\.codely-cli\tmp\edit\a_v11.wav"
with wave.open(WAV, "rb") as w:
    sr = w.getframerate()
    y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
dur = len(y) / float(sr)

# 谱通量（音头）
n, hop = 1024, 256
S = np.empty((n // 2 + 1, 1 + (len(y) - n) // hop), dtype=np.float32)
for i in range(S.shape[1]):
    S[:, i] = np.abs(np.fft.rfft(y[i * hop:i * hop + n] * np.hanning(n).astype(np.float32)))
S = np.log1p(S * 10)
fl = np.concatenate([[0.0], np.maximum(0.0, np.diff(S, axis=1)).sum(axis=0)])
fl_z = (fl - fl.mean()) / (fl.std() + 1e-9)
t = np.arange(len(fl)) * hop / float(sr)

pk, _ = find_peaks(fl_z, distance=int(0.20 * sr / hop), height=0.5)
events = t[pk]
strength = fl_z[pk]
print("音乐事件 %d 个（音头，间隔≥0.2s）" % len(events))

# 每镜源时长（满长）
SRC_MAX = [4.4167, 4.0, 3.5, 1.75, 3.625, 2.2083, 3.25, 2.0, 3.0, 2.25]
assert abs(sum(SRC_MAX) - 30.0) < 1e-6
LO, HI = 0.90, 1.10          # 变速范围 ±10%

# 贪心+回看：从 0 起，每段选一个≥LO*max 且≤HI*max 的事件点，优先强度高
plan = []
cur = 0.0
for i, mx in enumerate(SRC_MAX):
    remain_after = sum(SRC_MAX[i + 1:])
    lo_t = cur + LO * mx
    hi_t = cur + HI * mx
    # 末段必须落在 30.0
    if i == len(SRC_MAX) - 1:
        plan.append(30.0)
        break
    # 还剩下的镜数需要的最小/最大时间
    need_min = remain_after * LO
    need_max = remain_after * HI
    lo_t = max(lo_t, 30.0 - need_max)
    hi_t = min(hi_t, 30.0 - need_min)
    cand = [(strength[j], events[j]) for j in range(len(events))
            if lo_t <= events[j] <= hi_t]
    if not cand:
        # 退化：取窗口内任意点（不吸附）
        plan.append(round((lo_t + hi_t) / 2, 4))
        cur = plan[-1]
        print("  shot%2d 无事件 → 取中点 %.3f" % (i, cur))
        continue
    cand.sort(reverse=True)
    plan.append(round(cand[0][1], 4))
    cur = plan[-1]
    print("  shot%2d 切点 %.3fs  事件强度 %.2f" % (i, cur, cand[0][0]))

bounds = [0.0] + plan
lens = [round(bounds[i + 1] - bounds[i], 4) for i in range(len(SRC_MAX))]
speed = [round(SRC_MAX[i] / lens[i], 4) for i in range(len(SRC_MAX))]
print("\n切点:", " ".join("%.3f" % v for v in plan))
print("镜长:", " ".join("%.2f" % v for v in lens), " 合计 %.3f" % sum(lens))
print("速度因子(源/新):", " ".join("%.3f" % v for v in speed))
print("最大偏差: %.1f%%" % (max(abs(s - 1) for s in speed) * 100))

# 校验：每刀到最近音乐事件的距离
print("\n切点 → 最近事件 残差")
bad = 0
for c in plan:
    d = np.min(np.abs(events - c)) * 1000
    ok = d <= 21
    bad += (not ok)
    print("  %7.3f  %+6.1fms  %s" % (c, (c - events[np.argmin(np.abs(events - c))]) * 1000, "ON" if ok else "off"))
print("1帧内命中: %d/%d" % (len(plan) - bad, len(plan)))
print("\nPLAN=%s" % ",".join("%.4f" % v for v in plan))
print("SPEED=%s" % ",".join("%.4f" % v for v in speed))
