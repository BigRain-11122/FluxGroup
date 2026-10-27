# -*- coding: utf-8 -*-
"""mv_aigc_label.py - burn the AIGC label onto a finished cut.

Why: the S5 assembly chain carries the AIGC label (AIGC 标识办法 = publish gate), but
`mv_rebuild_from_edl.py` rebuilds picture+subtitle only, so every rebuild silently drops
the label. v717 checked 2026-10-28: head frame at 0.4s is bare picture, no label.

How: burn a one-line ASS (libass) instead of drawtext - this ffmpeg build has no
fontconfig, and drawtext crashes without it (0xC0000005, probed 2026-10-28), while the
repo's lyric subtitles already burn fine through libass.

Scope: label only. Title card / end credits are director-owned typography and are not
invented here.

Usage:
  python Tools/mv_aigc_label.py <video> --out <out.mp4> [--text "AI 生成内容"]
                                 [--corner br|bl|tr|tl] [--fontsize 22] [--crf 16]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

FONT = "Microsoft YaHei"
CORNERS = ("br", "bl", "tr", "tl")

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Aigc,{font},{size},&H00FFFFFF,&H00FFFFFF,&H80000000,&H00000000,0,0,0,0,100,100,0,0,1,0,1,9,20,20,24,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,9:59:59.00,Aigc,,0,0,0,,{{\\an9\\pos({x},{y})\\bord0\\shad1\\alpha&H40&}}{text}
"""


def fern_bin(name):
    cands = [shutil.which(name),
             r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages"
             r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
             r"\ffmpeg-9.0.2-full_build\bin\%s.exe" % name,
             r"C:\Program Files\ffmpeg\bin\%s.exe" % name]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return name


def probe_size(video, ffprobe):
    try:
        r = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0", video],
                           capture_output=True, text=True, timeout=60)
        w, h = r.stdout.strip().splitlines()[0].split(",")[:2]
        return int(w), int(h)
    except Exception:
        return 1344, 768


def ass_path(out_dir, w, h, corner, size, text):
    pad = 28
    x = {"r": w - pad, "l": pad}
    y = {"b": h - pad, "t": pad}
    ax, ay = x[corner[1]], y[corner[0]]
    body = ASS_HEAD.format(w=w, h=h, font=FONT, size=size, x=ax, y=ay, text=text)
    p = os.path.join(out_dir, "aigc_label_%d.ass" % os.getpid())
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="AI 生成内容")
    ap.add_argument("--corner", default="br", choices=CORNERS)
    ap.add_argument("--fontsize", type=int, default=22)
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--preset", default="slow")
    a = ap.parse_args(argv)

    if not os.path.isfile(a.video):
        print("AIGC-LABEL FAIL: input missing:", a.video)
        return 2
    out_dir = os.path.dirname(os.path.abspath(a.out)) or "."
    os.makedirs(out_dir, exist_ok=True)

    ff, fp = fern_bin("ffmpeg"), fern_bin("ffprobe")
    w, h = probe_size(a.video, fp)
    tmp_dir = tempfile.mkdtemp(prefix="aigc_")
    ass = ass_path(tmp_dir, w, h, a.corner, a.fontsize, a.text)

    # argv-level call: inside a filter value a Windows drive colon must be escaped,
    # and the whole filename must be single-quoted or the graph parser eats the colon.
    vf = "ass=filename='%s'" % ass.replace("\\", "/").replace(":", "\\:")
    cmd = [ff, "-v", "error", "-y", "-i", a.video, "-vf", vf,
           "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf),
           "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", a.out]
    rc = subprocess.call(cmd)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    if rc != 0:
        print("AIGC-LABEL FAIL rc=%s" % rc)
        return 1
    print("AIGC-LABEL OK text=%r corner=%s playres=%dx%d bytes=%d out=%s" % (
        a.text, a.corner, w, h, os.path.getsize(a.out), a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())