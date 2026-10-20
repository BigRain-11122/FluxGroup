# -*- coding: utf-8 -*-
# detect_d08_wireframe_r1017.py — green wireframe / CG artifacts detector for D08 sources
# Evidence chain:
#   1) Self-calibrate on convicted in-film frames (v54_probe/style_audit/D08_world_flip_{0,1}.jpg)
#      — extracted from full_mv_v53.mp4 whose D08 base = media segments version
#   2) Run identical detector on media segments 5 frames + cloudv2 archived 5 frames
#      -> verdict: archived same-defect or clean
import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
PROBE = os.path.join(HERE, "v54_probe")
MEDIA = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\D08_world_flip.mp4"
ARCH  = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\cloudv2\_w2_archived\D08_world_flip.mp4"

import json
def dur(f):
    r = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",f], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

def grab(f, t, path):
    subprocess.run(["ffmpeg","-y","-ss","%.2f"%t,"-i",f,"-frames:v","1","-q:v","3",path], capture_output=True)
    return os.path.isfile(path)

import numpy as np
from PIL import Image

def metrics(path):
    im = np.asarray(Image.open(path).convert("RGB"), dtype=np.int32)
    R, G, B = im[...,0], im[...,1], im[...,2]
    # saturated green pixels (wireframe / green-screen family)
    green = (G - R > 25) & (G - B > 25) & (G > 85)
    frac_green = float(green.mean())
    # bright thin-line pixels (wireframe edges often bright cyan/green)
    luma = (R*299 + G*587 + B*114) // 1000
    gx = np.abs(np.diff(luma, axis=1)).mean()
    gy = np.abs(np.diff(luma, axis=0)).mean()
    # magenta/violet CG overlay tints (some renders use magenta wireframe)
    mag = ((R - G > 30) & (B - G > 30))
    frac_mag = float(mag.mean())
    # per-region green share to locate the artifact (3x3 grid)
    h, w = green.shape
    grid = []
    for r in range(3):
        for c in range(3):
            sub = green[r*h//3:(r+1)*h//3, c*w//3:(c+1)*w//3]
            grid.append(round(float(sub.mean()), 4))
    return frac_green, frac_mag, gx+gy, grid

print("== self-calibration on convicted in-film frames ==")
for i in (0, 1):
    p = os.path.join(PROBE, "style_audit", "D08_world_flip_%d.jpg" % i)
    if os.path.isfile(p):
        fg, fm, ed, grid = metrics(p)
        print("film_%d: green=%.4f magenta=%.4f edge=%.2f grid9=%s" % (i, fg, fm, ed, grid))

# extract 5 frames per source (0.6/25/50/75/93%)
dm, da = dur(MEDIA), dur(ARCH)
for tag, f, d in (("media", MEDIA, dm), ("arch", ARCH, da)):
    for r, frac in enumerate((0.6/d, 0.25, 0.5, 0.75, 0.93)):
        grab(f, d*frac, os.path.join(PROBE, "d08_%s_%d.jpg" % (tag, r)))

print("\n== source frames ==")
res = {}
for tag in ("media", "arch"):
    rows = []
    for r in range(5):
        p = os.path.join(PROBE, "d08_%s_%d.jpg" % (tag, r))
        if os.path.isfile(p):
            fg, fm, ed, grid = metrics(p)
            rows.append((r, fg, fm, ed, grid))
            print("%s_%d: green=%.4f magenta=%.4f edge=%.2f grid9=%s" % (tag, r, fg, fm, ed, grid))
    res[tag] = rows

def agg(rows):
    return (sum(x[1] for x in rows)/len(rows), sum(x[2] for x in rows)/len(rows), sum(x[3] for x in rows)/len(rows))

mg_, ma_, me_ = agg(res["media"])
ag_, aa_, ae_ = agg(res["arch"])
print("\nMEAN  media: green=%.4f magenta=%.4f edge=%.2f" % (mg_, ma_, me_))
print("MEAN  arch : green=%.4f magenta=%.4f edge=%.2f" % (ag_, aa_, ae_))
