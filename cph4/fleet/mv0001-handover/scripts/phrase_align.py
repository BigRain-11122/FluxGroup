# -*- coding: utf-8 -*-
"""phrase_align.py — 用色度(chroma)变化找乐句/和声边界，检查切点是否落在乐句上。"""
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

n_fft, hop = 4096, 1024
win = np.hanning(n_fft).astype(np.float32)
frames = 1 + (len(y) - n_fft) // hop
S = np.empty((n_fft // 2 + 1, frames), dtype=np.float32)
for i in range(frames):
    S[:, i] = np.abs(np.fft.rfft(y[i * hop:i * hop + n_fft] * win))
freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)

# 12 音级 chroma（对数频率加权）
chroma = np.zeros((12, frames), dtype=np.float32)
mask = (freqs > 65) & (freqs < 2000)
f = freqs[mask]
pc = np.round(12 * np.log2(f / 440.0)).astype(int) % 12
for k in range(12):
    chroma[k] = S[mask][pc == k].sum(axis=0)
chroma /= (chroma.sum(axis=0, keepdims=True) + 1e-9)

# 归一化 + 平滑
k = np.ones(9) / 9.0
chroma = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, chroma)
novelty = np.linalg.norm(np.diff(chroma, axis=1), axis=0)
novelty = np.concatenate([[0.0], novelty])
novelty = (novelty - novelty.mean()) / (novelty.std() + 1e-9)
t = np.arange(len(novelty)) * hop / float(sr)

peaks, props = find_peaks(novelty, distance=int(0.9 * sr / hop), height=0.6)
print("检测到乐句/和声边界 %d 个（间隔≥0.9s，阈值 0.6σ）" % len(peaks))
print("  " + " ".join("%.2f" % t[p] for p in peaks))

CUTS = [4.4167, 8.4167, 11.9167, 13.6667, 17.2917, 19.5, 22.75, 24.75, 27.75]
print("\n切点 → 最近乐句边界 残差")
res = []
for c in CUTS:
    p = peaks[np.argmin(np.abs(t[peaks] - c))]
    d = (c - t[p]) * 1000
    res.append(d)
    print("  %7.3fs → %7.3fs  %+7.1fms  (%.1f 帧@24)" % (c, t[p], d, d / 1000 * 24))
res = np.array(res)
print("\n平均绝对残差 %.0fms（%.1f 帧）  ±42ms(1帧) 内 %d/%d  ±84ms(2帧) 内 %d/%d"
      % (np.abs(res).mean(), np.abs(res).mean() / 1000 * 24,
         (np.abs(res) <= 42).sum(), len(res), (np.abs(res) <= 84).sum(), len(res)))

# 谱通量边界（音头）也测一版
n2, hop2 = 1024, 256
fr2 = 1 + (len(y) - n2) // hop2
S2 = np.empty((n2 // 2 + 1, fr2), dtype=np.float32)
for i in range(fr2):
    S2[:, i] = np.abs(np.fft.rfft(y[i * hop2:i * hop2 + n2] * np.hanning(n2).astype(np.float32)))
S2 = np.log1p(S2 * 10)
fl = np.concatenate([[0.0], np.maximum(0.0, np.diff(S2, axis=1)).sum(axis=0)])
fl = (fl - fl.mean()) / (fl.std() + 1e-9)
t2 = np.arange(len(fl)) * hop2 / float(sr)
pk2, _ = find_peaks(fl, distance=int(0.45 * sr / hop2), height=1.0)
print("\n强音头 %d 个；切点在 ±42ms 内命中音头 %d/%d"
      % (len(pk2), sum(1 for c in CUTS if np.min(np.abs(t2[pk2] - c)) <= 0.042), len(CUTS)))
print("各切点到最近音头: " + " ".join("%.0fms" % (np.min(np.abs(t2[pk2] - c)) * 1000) for c in CUTS))
