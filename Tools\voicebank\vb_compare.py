# -*- coding: utf-8 -*-
"""vb_compare.py - objective before/after comparison of demos.

Reports, per file: sample rate, HF energy ratio (>8 kHz), pitch spread (expressiveness),
and the level spread (a crude "is it flat" check). Used to prove the 44.1k pipeline is
actually better than the 16k one instead of claiming it.
"""
import glob
import json
import sys
import wave

import numpy as np


def read(p):
    with wave.open(p, "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return x, sr


def hf(x, sr):
    n = 1 << 15
    if len(x) < n:
        return 0.0
    acc = np.zeros(n // 2 + 1)
    for i in range(0, len(x) - n, n):
        acc += np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n))) ** 2
    f = np.fft.rfftfreq(n, 1 / sr)
    return float(acc[f > 8000].sum() / (acc.sum() + 1e-12))


def pitch(x, sr):
    win, hop = int(0.04 * sr), int(0.02 * sr)
    v = []
    for i in range(0, len(x) - win, hop):
        s = x[i:i + win]
        if np.sqrt(np.mean(s * s)) < 0.008:
            continue
        s = s - s.mean()
        ac = np.correlate(s, s, "full")[win - 1:]
        if ac[0] <= 0:
            continue
        ac /= ac[0]
        lo, hi = int(sr / 400), int(sr / 55)
        k = int(np.argmax(ac[lo:hi])) + lo
        if ac[k] < 0.3:
            continue
        v.append(sr / k)
    if not v:
        return 0, 0
    v = np.array(v)
    return float(np.median(v)), float((np.percentile(v, 75) - np.percentile(v, 25)) / np.median(v))


out = []
for p in sys.argv[1:]:
    x, sr = read(p)
    f0, spread = pitch(x, sr)
    out.append({"file": p.split("\\")[-1], "sr": sr, "dur": round(len(x) / sr, 2),
                "hf_ratio": round(hf(x, sr), 4), "f0_med": round(f0, 1),
                "pitch_spread": round(spread, 3)})
print(json.dumps(out, ensure_ascii=False, indent=1))