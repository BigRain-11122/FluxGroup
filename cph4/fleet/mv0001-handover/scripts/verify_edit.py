# -*- coding: utf-8 -*-
"""verify_edit.py — 从成片里反测切点，验证落拍率。"""
import os
import subprocess
import sys
import wave

import numpy as np

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
SRC = sys.argv[1] if len(sys.argv) > 1 else \
    r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v11-优化版.mp4"
TMP = r"K:\Fluxgroup\.codely-cli\tmp\edit"
os.makedirs(TMP, exist_ok=True)
WAV = os.path.join(TMP, "a_v11.wav")
FRM = os.path.join(TMP, "f_v11")
os.makedirs(FRM, exist_ok=True)
subprocess.run([FF, "-y", "-i", SRC, "-vn", "-ac", "1", "-ar", "22050", WAV], capture_output=True)
subprocess.run([FF, "-y", "-i", SRC, "-vsync", "0", os.path.join(FRM, "f_%03d.png")],
               capture_output=True)

from PIL import Image  # noqa: E402

fs = sorted(f for f in os.listdir(FRM) if f.startswith("f_"))
prev, diffs = None, []
for f in fs:
    a = np.asarray(Image.open(os.path.join(FRM, f)).convert("L"), dtype=np.float32)
    diffs.append(0.0 if prev is None else float(np.abs(a - prev).mean()))
    prev = a

fps = 24.0
cuts = [i / fps for i in range(1, len(diffs)) if diffs[i] > 12]
print("检测到切点 %d 个：" % len(cuts))
print("  " + " ".join("%.3f" % c for c in cuts))

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


def onset_at(x):
    i = int(round(x * sr / hop))
    if i < 0 or i >= len(flux):
        return 0.0
    seg = flux[max(0, i - 1):min(len(flux), i + 2)]
    return float(np.abs(seg).max()) if seg.size else 0.0


BPM, beat = 126.05, 60.0 / 126.05
best = max(((np.mean([onset_at(x) for x in np.arange(ph, dur, beat)]), ph)
            for ph in np.arange(0, beat, 0.005)), key=lambda z: z[0])
phase = best[1]
grid = np.arange(phase, dur, beat)
print("\nbeat=%.4fs phase=%.3fs" % (beat, phase))

on = off = 0
print("\n切点 → 最近拍 残差")
for c in cuts:
    g = min(grid, key=lambda x: abs(x - c))
    d = c - g
    ok = abs(d) <= 0.021
    on += ok
    off += (not ok)
    print("  %7.3fs  %7.3f  %+6.1fms  %s" % (c, g, d * 1000, "ON" if ok else "OFF"))
print("\n落拍率 = %d/%d = %.0f%%（±21ms≈半帧）" % (on, len(cuts), 100.0 * on / max(1, len(cuts))))
