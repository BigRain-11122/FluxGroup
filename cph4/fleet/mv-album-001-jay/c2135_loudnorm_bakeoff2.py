# -*- coding: ascii -*-
"""C2135 bake-off round 2: loudnorm + true-peak limiter (level=false) variants."""
import json
import os
import re
import subprocess

REPO = r"K:\Fluxgroup\FluxGroup"
FLEET = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
SONG = os.path.join(FLEET, "audio", "\u5468\u6770\u4f26 - \u661f\u6674.mp3")
TMP = os.path.join(REPO, "media", "mv-album-001-jay", "tmp_c2135_bakeoff2.m4a")
DUR = 196.25
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"

p = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", SONG, "-t", "%.3f" % DUR,
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True, errors="replace")
st = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stdout + p.stderr, re.S).group(0))
base = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:"
        "measured_thresh=%s:offset=%s:linear=true" %
        (st["input_i"], st["input_tp"], st["input_lra"], st["input_thresh"], st["target_offset"]))


def measure(path):
    q = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0",
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    out = q.stdout + q.stderr
    tail = out[out.rfind("Summary:"):]
    m_i = re.search(r"I:\s*(-?[\d.]+)", tail)
    m_tp = re.search(r"Peak:\s*(-?[\d.]+)", tail[tail.rfind("True peak:"):])
    return (float(m_i.group(1)) if m_i else None,
            float(m_tp.group(1)) if m_tp else None)


for lim in ("0.841", "0.75", "0.70"):
    af = base + ",alimiter=limit=%s:attack=0.1:release=40:level=false" % lim
    r = subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", SONG,
                        "-t", "%.3f" % DUR, "-af", af, "-c:a", "aac", "-b:a", "192k", TMP],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("lim", lim, "FAIL", r.stderr[-200:])
        continue
    print("lim=%s I=%s TP=%s" % ((lim,) + measure(TMP)))
    os.remove(TMP)