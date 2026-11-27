# -*- coding: utf-8 -*-
"""beat_grid_fit.py — 二维搜索 (BPM, 相位)，用 onset 峰拟合真实节拍网格。"""
import sys
import wave

import numpy as np

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WAV = r"K:\Fluxgroup\.codely-cli\tmp\edit\a_v11.wav"
with wave.open(WAV, "rb") as w:
    sr = w.getframerate()
    y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
dur = len(y) / float(sr)

n_fft, hop = 1024, 256
win = np.hanning(n_fft).astype(np.float32)
frames = 1 + (len(y) - n_fft) // hop
S = np.empty((n_fft // 2 + 1, frames), dtype=np.float32)
for i in range(frames):
    S[:, i] = np.abs(np.fft.rfft(y[i * hop:i * hop + n_fft] * win))
S = np.log1p(S * 10.0)
flux = np.concatenate([[0.0], np.maximum(0.0, np.diff(S, axis=1)).sum(axis=0)])
flux = (flux - flux.min()) / (flux.max() - flux.min() + 1e-9)

CUTS = [4.4167, 8.4167, 11.9167, 13.6667, 17.2917, 19.5, 22.75, 24.75, 27.75]


def onset(x):
    i = int(round(x * sr / hop))
    if i < 0 or i >= len(flux):
        return 0.0
    return float(flux[max(0, i - 1):min(len(flux), i + 2)].max())


best = None
for bpm in np.arange(118.0, 136.0, 0.02):
    beat = 60.0 / bpm
    for ph in np.arange(0, beat, 0.005):
        g = np.arange(ph, dur, beat)
        if len(g) < 40:
            continue
        sc = sum(onset(x) for x in g) / len(g)
        if best is None or sc > best[0]:
            best = (sc, bpm, ph)
sc, bpm, ph = best
beat = 60.0 / bpm
print("最佳拟合: BPM=%.2f  beat=%.4fs  phase=%.3fs  score=%.4f" % (bpm, beat, ph, sc))

grid = np.arange(ph, dur, beat)
print("\n该网格下各切点残差：")
res = []
for c in CUTS:
    g = min(grid, key=lambda x: abs(x - c))
    d = (c - g) * 1000
    res.append(d)
    print("  %7.3fs → %7.3fs  %+7.1fms  (%.1f 帧@24)" % (c, g, d, d / 1000 * 24))
res = np.array(res)
print("\n平均绝对残差 %.1fms（%.1f 帧）  最大 %.1fms" % (np.abs(res).mean(), np.abs(res).mean() / 1000 * 24, np.abs(res).max()))
print("±21ms 内: %d/%d    ±42ms 内: %d/%d"
      % ((np.abs(res) <= 21).sum(), len(res), (np.abs(res) <= 42).sum(), len(res)))

# 半拍/双拍网格也试（切点常在 8 分音符）
for mult, name in ((0.5, "半拍(8分)"), (2.0, "双拍(2)"), (4.0, "小节")):
    b2 = beat * mult
    g2 = np.arange(ph % b2, dur, b2)
    r2 = [(c - min(g2, key=lambda x: abs(x - c))) * 1000 for c in CUTS]
    print("  %s网格 beat=%.3fs: ±21ms 内 %d/%d, 平均 %.0fms"
          % (name, b2, (np.abs(r2) <= 21).sum(), len(r2), np.abs(r2).mean()))
