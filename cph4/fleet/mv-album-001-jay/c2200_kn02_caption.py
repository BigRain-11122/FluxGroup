# -*- coding: utf-8 -*-
"""C2200: remove the burnt-in pseudo caption strip from KN02.

C2170/C2171 scanned every landed KN clip for the subtitle-band pseudo-text class
and flagged exactly one hit: KN_A-KN02.mp4 carries a white glyph-like strip at
the bottom of the frame for the whole take. The keyframe is clean, so it is a
generator prior fired by the talking-head framing, not something the source plate
ever had.

Re-burning costs GPU minutes and the prior would likely fire again, while the
strip sits entirely inside the bottom 76px of the 1344x768 frame. Cropping that
band and scaling back to 1344x768 removes it outright: the shot is a medium
portrait, the crop is a 1.11x punch-in that stays inside the film's own framing
language, and nothing else in the frame changes.

Usage:
  python c2200_kn02_caption.py --build
  python c2200_kn02_caption.py --report
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image
import io

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
SRC = os.path.join(MEDIA, "clips-local-768", "KN_A-KN02.mp4")
BAK = os.path.join(MEDIA, "clip-archive-c2200", "KN_A-KN02-pre-c2200.mp4")
TMP = os.path.join(MEDIA, "clip-archive-c2200", "KN_A-KN02-c2200-tmp.mp4")
QC = os.path.join(MEDIA, "qc-frames-c2200")
VERDICT = os.path.join(MEDIA, "logs", "kn02-caption-c2200.json")

W, H = 1344, 768
CROP_H = 692           # everything below this row is the caption band
CAP_TOP = 688          # measurement window for the strip


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit("cmd failed: %s\n%s" % (" ".join(cmd), res.stderr[-1200:]))
    return res


def strip_stats(path, t):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path,
                        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True)
    a = np.asarray(Image.open(io.BytesIO(p.stdout)).convert("RGB")).astype(np.float32)
    y = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    band = y[CAP_TOP:, :]
    bright = int((band > 205).sum())
    return {"bright_px": bright, "max": round(float(band.max()), 1)}


def build():
    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if os.path.isfile(SRC) and not os.path.isfile(BAK):
        shutil.copy2(SRC, BAK)
        print("backed up -> %s" % os.path.basename(BAK))
    if not os.path.isfile(BAK):
        raise SystemExit("no source take to rebuild from")
    run(["ffmpeg", "-y", "-v", "error", "-i", BAK,
         "-vf", "crop=%d:%d:0:0,scale=%d:%d:flags=lanczos,setsar=1" % (W, CROP_H, W, H),
         "-an", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
         "-pix_fmt", "yuv420p", TMP])
    os.replace(TMP, SRC)
    print("rewrote %s bytes=%d" % (os.path.basename(SRC), os.path.getsize(SRC)))


def report():
    os.makedirs(QC, exist_ok=True)
    rows = []
    for t in (0.5, 2.0, 4.0, 6.0):
        before = os.path.join(QC, "kn02_t%s_before.png" % t)
        after = os.path.join(QC, "kn02_t%s_after.png" % t)
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", BAK, "-frames:v", "1", before])
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1", after])
        rows.append({"t": t, "before": strip_stats(BAK, t), "after": strip_stats(SRC, t)})
    payload = {"batch": "C2200", "method": "bottom-band crop + rescale (no generation)",
               "take": SRC, "archived_previous": BAK, "crop_from": [W, CROP_H],
               "strip": rows, "note": ("bright_px counts pixels above 205 in the caption band; "
                                       "the strip is gone when that collapses to the frame's own "
                                       "highlights.")}
    with open(VERDICT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
    for r in rows:
        print("t=%s caption-band bright %d -> %d" % (r["t"], r["before"]["bright_px"], r["after"]["bright_px"]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.build or a.report:
        report()
    return 0


if __name__ == "__main__":
    sys.exit(main())