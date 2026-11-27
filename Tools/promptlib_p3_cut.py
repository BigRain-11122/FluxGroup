# -*- coding: utf-8 -*-
"""Concat whatever micro-shots are ready into one performance cut."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "out", "p3_three_shot")
ORDER = ["S1_ecu_eyes.mp4", "S2_ecu_fingertip.mp4", "S3_cu_lips.mp4"]
OUT = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "out", "p3_performance_cut.mp4")

ready = [f for f in ORDER if os.path.exists(os.path.join(D, f))]
if not ready:
    sys.exit("no shots yet")
print("using:", ready)

lst = os.path.join(D, "list.txt")
with open(lst, "w", encoding="utf-8") as fh:
    for f in ready:
        fh.write("file '%s'\n" % os.path.join(D, f).replace("\\", "/"))

r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", OUT], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("concat failed: " + r.stderr[:400])

p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", OUT], capture_output=True, text=True)
print("cut:", OUT)
print("duration:", p.stdout.strip())