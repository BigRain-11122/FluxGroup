# -*- coding: utf-8 -*-
"""fix_tail.py — 把成片尾补齐到歌长 234.253s（末帧定格 1s 由 -t 截断），并重封音轨。"""
import io
import os
import subprocess

TMP = r"K:\Fluxgroup\.codely-cli\tmp\fullmv"
ROOT = r"K:\Fluxgroup\FluxGroup"
RAW = os.path.join(TMP, "raw.mp4")
SONG = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "audio", "mv001_source_320k.mp3")
OUT = os.path.join(ROOT, "media", "mv0001-handover", "deliverable", "爱在西元前-全片-v1-未审.mp4")
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"

fc = io.open(os.path.join(TMP, "grade.filter"), encoding="ascii").read()
if "tpad" not in fc:
    fc = fc.replace("[v0];", "[v0];\n[v0]tpad=stop_mode=clone:stop_duration=1.2[vp];", 1)
    fc = fc.replace("[v0]drawtext", "[vp]drawtext", 1)
    io.open(os.path.join(TMP, "grade_tail.filter"), "w", encoding="ascii").write(fc)
    print("filter + tpad ok")
else:
    io.open(os.path.join(TMP, "grade_tail.filter"), "w", encoding="ascii").write(fc)
    print("filter already has tpad")

r = subprocess.run([FF, "-y", "-i", RAW, "-i", SONG,
                    "-filter_complex_script", "grade_tail.filter",
                    "-map", "[vout]", "-map", "1:a",
                    "-c:v", "libx264", "-crf", "17", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-r", "24",
                    "-c:a", "aac", "-b:a", "192k",
                    "-t", "234.253", "-movflags", "+faststart", OUT],
                   cwd=TMP, capture_output=True, text=True, errors="replace")
print("rc", r.returncode)
if r.returncode:
    print((r.stderr or "")[-1200:])
else:
    print("OUT %.1f MB" % (os.path.getsize(OUT) / 1048576))
