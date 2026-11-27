# -*- coding: utf-8 -*-
"""qc_full_film.py — 全片机检：逐帧亮度（找黑帧/欠曝）+ 近重复帧 + 帧数。"""
import os
import subprocess
import sys

import numpy as np

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-全片-v1-未审.mp4"
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FP = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

o = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-count_frames",
                    "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", SRC],
                   capture_output=True, text=True).stdout.strip()
print("frames =", o)

r = subprocess.run([FF, "-hide_banner", "-i", SRC, "-vf",
                    "signalstats,metadata=print:file=-", "-f", "null", "NUL"],
                   capture_output=True, text=True, errors="replace")
y = []
for line in r.stdout.splitlines():
    if "YAVG=" in line:
        try:
            y.append(float(line.split("YAVG=")[1].split()[0]))
        except Exception:
            pass
if not y:
    for line in r.stderr.splitlines():
        if "YAVG=" in line:
            try:
                y.append(float(line.split("YAVG=")[1].split()[0]))
            except Exception:
                pass

y = np.array(y)
print("YAVG frames=%d min=%.1f max=%.1f mean=%.1f" % (len(y), y.min(), y.max(), y.mean()))
dark = np.where(y < 12)[0]
print("欠曝帧(<12): %d 个" % len(dark))
if len(dark):
    groups = []
    s = dark[0]
    p = dark[0]
    for d in dark[1:]:
        if d - p > 12:
            groups.append((s, p))
            s = d
        p = d
    groups.append((s, p))
    for a, b in groups[:20]:
        print("   %6.2f-%6.2f s  (%d 帧, minY=%.1f)"
              % (a / 24, b / 24, b - a + 1, y[a:b + 1].min()))
