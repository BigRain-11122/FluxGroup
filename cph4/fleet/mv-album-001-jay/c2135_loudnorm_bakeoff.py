# -*- coding: ascii -*-
"""C2135: chain bake-off for the conform loudness pass (measure only, keeps no file).

Candidates are rendered from the song onto the film's duration and measured with
ebur128 so the winner can be baked into xq_packa_loudnorm_c2135.py.
"""
import json
import os
import re
import subprocess

REPO = r"K:\Fluxgroup\FluxGroup"
FLEET = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
SONG = os.path.join(FLEET, "audio", "\u5468\u6770\u4f26 - \u661f\u6674.mp3")
TMP = os.path.join(REPO, "media", "mv-album-001-jay", "tmp_c2135_bakeoff.m4a")
DUR = 196.25
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


def measure(path):
    p = run([FFMPEG, "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0",
             "-af", "ebur128=peak=true", "-f", "null", "-"])
    out = p.stdout + p.stderr
    tail = out[out.rfind("Summary:"):]
    m_i = re.search(r"I:\s*(-?[\d.]+)", tail)
    m_tp = re.search(r"Peak:\s*(-?[\d.]+)", tail[tail.rfind("True peak:"):])
    return (float(m_i.group(1)) if m_i else None,
            float(m_tp.group(1)) if m_tp else None)


def pass1():
    p = run([FFMPEG, "-hide_banner", "-nostats", "-i", SONG, "-t", "%.3f" % DUR,
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stdout + p.stderr, re.S)
    return json.loads(m.group(0))


st = pass1()
print("PASS1", {k: st[k] for k in ("input_i", "input_tp", "input_lra", "target_offset")})

chains = {
    "loudnorm_dyn": (
        "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:"
        "measured_thresh=%s:offset=%s:linear=false" %
        (st["input_i"], st["input_tp"], st["input_lra"], st["input_thresh"], st["target_offset"])),
    "loudnorm_lin": (
        "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:"
        "measured_thresh=%s:offset=%s:linear=true" %
        (st["input_i"], st["input_tp"], st["input_lra"], st["input_thresh"], st["target_offset"])),
    "gain2_limiter": "volume=-2.20dB,alimiter=limit=0.769:attack=0.1:release=40:level=false",
    "gain3_limiter": "volume=-3.20dB,alimiter=limit=0.769:attack=0.1:release=40:level=false",
}

for name, af in chains.items():
    p = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", SONG,
             "-t", "%.3f" % DUR, "-af", af, "-c:a", "aac", "-b:a", "192k", TMP])
    if p.returncode != 0:
        print(name, "RENDER-FAIL", p.stderr[-300:])
        continue
    i, tp = measure(TMP)
    print("%-14s I=%s TP=%s" % (name, i, tp))
    os.remove(TMP)