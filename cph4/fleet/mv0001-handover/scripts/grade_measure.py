# -*- coding: utf-8 -*-
"""grade_measure.py — 按调色席判据量测成片（每镜取一帧）。"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
SRC = sys.argv[1] if len(sys.argv) > 1 else \
    r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v7-final.mp4"
OUT = r"K:\Fluxgroup\.codely-cli\tmp\v8\measure"
os.makedirs(OUT, exist_ok=True)

# 每镜取中段一帧
SHOTS = [(2.0, "1_fire"), (6.0, "2_wall"), (10.0, "3_stele"), (12.8, "4_relief"),
         (15.5, "5_darkwall"), (18.3, "6_carve"), (20.8, "7_temple"),
         (22.0, "8_glow"), (23.7, "9_tablet"), (26.0, "10_museum"), (28.8, "11_wide")]


def grab(t, name):
    p = os.path.join(OUT, name + ".png")
    subprocess.run([FF, "-y", "-ss", str(t), "-i", SRC, "-frames:v", "1", p],
                   capture_output=True)
    return p


def lum_stats(a):
    y = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    p1 = np.percentile(y, 1)
    p99 = np.percentile(y, 99)
    clip = float((y >= 254.5).mean() * 100)
    return p1, p99, clip, float(y.mean())


def band_rb(a):
    y = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    m_sh = y < 64
    m_mid = (y >= 64) & (y < 160)
    m_hi = y >= 160
    out = []
    for m in (m_sh, m_mid, m_hi):
        if m.sum() < 100:
            out.append(None)
            continue
        out.append(float(a[:, :, 0][m].mean() - a[:, :, 2][m].mean()))
    return out


def grain_sigma(a):
    """用 3x3 高频残差的稳健标准差估颗粒。"""
    y = (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]).astype(np.float32)
    k = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], dtype=np.float32) / 4.0
    h = y[1:-1, 1:-1] * 4 - y[:-2, 1:-1] - y[2:, 1:-1] - y[1:-1, :-2] - y[1:-1, 2:]
    mid = (y[1:-1, 1:-1] > 40) & (y[1:-1, 1:-1] < 200)
    dark = y[1:-1, 1:-1] < 25
    s_mid = float(np.median(np.abs(h[mid]))) * 1.4826 if mid.sum() > 500 else None
    s_dark = float(np.median(np.abs(h[dark]))) * 1.4826 if dark.sum() > 500 else None
    return s_mid, s_dark


print("%-12s %6s %6s %6s  %-22s %-16s" % ("镜", "p1", "p99", "clip%", "三带R-B(暗/中/亮)", "颗粒σ(中/暗)"))
rows = []
for t, name in SHOTS:
    p = grab(t, name)
    a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)
    p1, p99, clip, ym = lum_stats(a)
    rb = band_rb(a)
    sm, sd = grain_sigma(a)
    print("%-12s %6.1f %6.1f %6.2f  %-22s %s" % (
        name, p1, p99, clip,
        " / ".join("%+.0f" % v if v is not None else "-" for v in rb),
        "%.2f / %s" % (sm, "%.2f" % sd if sd is not None else "-")))
    rows.append((name, p1, p99, clip, rb, sm, sd))

print("\n--- 目标（调色席判据）---")
print("黑位 p1=10-14 | 高光 p99=247-251 & clip=0 | 三带 R-B: 暗 +24~32 / 中 +110~130 / 亮 +20~35")
print("颗粒 σ: 中调 1.5-3.0 / 黑位 <1.0 | 肤色颊部 R-B +55~85")
