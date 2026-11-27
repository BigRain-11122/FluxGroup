# -*- coding: utf-8 -*-
"""master_full_mv.py — 全片音轨两遍 loudnorm 母带（目标 -14 LUFS / <=-1 dBTP）。"""
import json
import os
import re
import subprocess

FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
ROOT = r"K:\Fluxgroup\FluxGroup"
SRC = os.path.join(ROOT, "media", "mv0001-handover", "deliverable", "爱在西元前-全片-v1-未审.mp4")
DST = os.path.join(ROOT, "media", "mv0001-handover", "deliverable", "爱在西元前-全片-v1-master.mp4")

p1 = subprocess.run([FF, "-hide_banner", "-i", SRC, "-af",
                     "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "NUL"],
                    capture_output=True, text=True, errors="replace")
m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p1.stderr, re.S)
meas = json.loads(m.group(0))
print("measured:", {k: meas[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")})

af = ("loudnorm=I=-12.8:TP=-1.0:LRA=11:linear=true"
      ":measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s,"
      "alimiter=level_in=1:level_out=1:limit=0.749:attack=5:release=80:level=false,"
      "volume=-1.2dB" % (meas["input_i"], meas["input_tp"], meas["input_lra"],
                         meas["input_thresh"], meas["target_offset"]))

p2 = subprocess.run([FF, "-y", "-i", SRC, "-map", "0:v", "-map", "0:a",
                     "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                     "-t", "234.253", "-movflags", "+faststart", DST],
                    capture_output=True, text=True, errors="replace")
print("rc", p2.returncode)
if p2.returncode:
    print((p2.stderr or "")[-1000:])
else:
    p3 = subprocess.run([FF, "-hide_banner", "-i", DST, "-af", "ebur128=peak=true",
                         "-f", "null", "NUL"], capture_output=True, text=True, errors="replace")
    for line in p3.stderr.splitlines()[-8:]:
        if "I:" in line or "Peak:" in line:
            print("  " + line.strip()[:90])
    print("OUT %.1f MB" % (os.path.getsize(DST) / 1048576))
