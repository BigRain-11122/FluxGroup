# -*- coding: utf-8 -*-
"""audio_master_v7.py — 两遍 loudnorm 母带处理，视频流直拷（不动水印）。

问题：v6/v7 的音轨沿用原片，全片实测 -13.0 LUFS / **True peak +2.1 dBFS（削波）**。
正法：两遍 loudnorm（测量→应用），目标 I=-14 LUFS / TP=-1.0 dBTP / LRA=11，
视频 -c:v copy 保住暗水印，仅音频重编码 192k。
"""
import json
import os
import re
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
SRC = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v7-wmvs.mp4"
DST = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v7-final.mp4"

# pass 1: 测量
p1 = subprocess.run(
    [FF, "-hide_banner", "-i", SRC, "-af",
     "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "NUL"],
    capture_output=True, text=True, errors="replace")
m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p1.stderr, re.S)
if not m:
    print("PASS1 FAIL"); print(p1.stderr[-800:]); raise SystemExit(1)
meas = json.loads(m.group(0))
print("measured:", {k: meas[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh", "output_i", "target_offset")})

af = ("loudnorm=I=-12.8:TP=-1.0:LRA=11:linear=true"
      ":measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s,"
      "alimiter=level_in=1:level_out=1:limit=0.749:attack=5:release=80:level=false,"
      "volume=-1.2dB"
      % (meas["input_i"], meas["input_tp"], meas["input_lra"],
         meas["input_thresh"], meas["target_offset"]))

# pass 2: 应用（视频直拷）
p2 = subprocess.run(
    [FF, "-y", "-i", SRC, "-map", "0:v", "-map", "0:a",
     "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
     "-t", "30.000", "-movflags", "+faststart", DST],
    capture_output=True, text=True, errors="replace")
print("PASS2 rc=%d" % p2.returncode)
if p2.returncode:
    print(p2.stderr[-1000:]); raise SystemExit(1)

# 复测
p3 = subprocess.run([FF, "-hide_banner", "-i", DST, "-af", "ebur128=peak=true",
                     "-f", "null", "NUL"], capture_output=True, text=True, errors="replace")
tail = p3.stderr[-1200:]
for line in tail.splitlines():
    if any(k in line for k in ("I:", "Peak:", "LRA:")) and "t:" not in line:
        print("  " + line.strip()[:100])
print("OUT %s  %.2f MB" % (DST, os.path.getsize(DST) / 1048576))
