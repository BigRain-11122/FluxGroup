# -*- coding: utf-8 -*-
"""edit_audit2.py — 纯 numpy/scipy 的剪辑量化（谱通量 onset + 自相关测速 + 拍点峰选）。"""
import os
import subprocess
import sys

import numpy as np
from scipy.signal import find_peaks

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
SRC = sys.argv[1] if len(sys.argv) > 1 else \
    r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v10-final.mp4"
WAV = r"K:\Fluxgroup\.codely-cli\tmp\edit\audio.wav"
os.makedirs(os.path.dirname(WAV), exist_ok=True)
subprocess.run([FF, "-y", "-i", SRC, "-vn", "-ac", "1", "-ar", "22050", WAV],
               capture_output=True)

import wave  # noqa: E402

with wave.open(WAV, "rb") as w:
    sr = w.getframerate()
    raw = w.readframes(w.getnframes())
y = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
dur = len(y) / float(sr)
print("audio %.3fs sr=%d" % (dur, sr))

# ---- 谱通量 onset envelope ----
n_fft, hop = 1024, 256
win = np.hanning(n_fft).astype(np.float32)
frames = 1 + (len(y) - n_fft) // hop
S = np.empty((n_fft // 2 + 1, frames), dtype=np.float32)
for i in range(frames):
    seg = y[i * hop:i * hop + n_fft] * win
    S[:, i] = np.abs(np.fft.rfft(seg))
S = np.log1p(S * 10.0)
flux = np.maximum(0.0, np.diff(S, axis=1)).sum(axis=0)
flux = np.concatenate([[0.0], flux])
flux = (flux - flux.mean()) / (flux.std() + 1e-9)
t = np.arange(len(flux)) * hop / float(sr)

# ---- 自相关测 BPM ----
env = flux - flux.mean()
ac = np.correlate(env, env, mode="full")[len(env) - 1:]
ac[:int(0.25 * sr / hop)] = 0          # 忽略 <0.25s
lo = int(60.0 / 200 * sr / hop)        # 200 BPM 上限
hi = int(60.0 / 60 * sr / hop)         # 60 BPM 下限
seg = ac[lo:hi]
bpm = 60.0 * sr / hop / (lo + int(np.argmax(seg)))
print("BPM ≈ %.2f   小节 ≈ %.3fs" % (bpm, 4 * 60 / bpm))

# ---- 拍点：按 BPM 网格 + 局部峰对齐 ----
period = 60.0 / bpm
peaks, _ = find_peaks(flux, distance=int(period * 0.5 * sr / hop), height=0.15)
beats = t[peaks]
print("拍点 %d 个，平均间隔 %.3fs" % (len(beats), np.mean(np.diff(beats)) if len(beats) > 1 else 0))

CUTS = [4.4167, 8.4167, 11.9167, 13.6667, 17.2917, 19.5, 22.75, 24.75, 27.75]
print("\n切点 → 最近拍点 / 偏移 / 判定(±60ms)")
onbeat = 0
for c in CUTS:
    if len(beats) == 0:
        break
    i = int(np.argmin(np.abs(beats - c)))
    off = c - beats[i]
    ok = abs(off) <= 0.060
    onbeat += ok
    print("  %7.3fs  beat@%7.3f  Δ=%+6.3fs  %s" % (c, beats[i], off, "ON" if ok else "OFF"))
print("落拍率 = %d/%d = %.0f%%" % (onbeat, len(CUTS), 100.0 * onbeat / len(CUTS)))

bounds = [0.0] + CUTS + [dur]
lens = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
print("\n镜长(秒): " + " ".join("%.2f" % v for v in lens))
print("  均值 %.2f 中位 %.2f 最短 %.2f 最长 %.2f 方差 %.3f"
      % (np.mean(lens), np.median(lens), min(lens), max(lens), np.var(lens)))
print("密度(每5秒切数): " + "  ".join(
    "%d-%ds:%d" % (s, s + 5, sum(1 for c in CUTS if s <= c < s + 5)) for s in range(0, 30, 5)))

vals = []
for c in CUTS:
    i = int(np.argmin(np.abs(t - c)))
    vals.append(float(np.abs(flux[max(0, i - 2):i + 3]).max()))
print("\n切点 onset 强度: " + " ".join("%.2f" % v for v in vals))
print("  mean=%.2f min=%.2f max=%.2f  低于均值一半的切点 %d 个"
      % (np.mean(vals), min(vals), max(vals), sum(1 for v in vals if v < np.mean(vals) * 0.5)))
