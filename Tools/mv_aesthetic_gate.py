# -*- coding: utf-8 -*-
"""mv_aesthetic_gate.py - turn "looks bad" into numbers the director can act on.

Per shot it measures:
  luma_mean / luma_p10        exposure and whether shadows carry detail
  sat_mean                    saturation
  hue_top / hue_top_share     dominant hue family (the "one amber palette" detector)
  edge_density                how much structure is in frame (empty / busy)
  color_temp_k                rough warm/cool estimate

Then it compares adjacent shots and flags:
  DARK        luma_mean < 35           (subject unreadable)
  BLOWN       luma_mean > 190
  FLAT        edge_density < 0.02      (empty frame with nothing to look at)
  SAME_PALETTE adjacent shots with |ΔK| < 150 and |Δsat| < 10 for >= 6 consecutive shots

Usage:
  py mv_aesthetic_gate.py <video> [--json out.json]
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_gate as RG

W, H, FPS = 320, 183, 24
FS = W * H * 3


def stats_for_frame(rgb):
    f = rgb.astype(np.float32) / 255.0
    luma = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
    mx = f.max(axis=2)
    mn = f.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # hue in degrees
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    d = mx - mn
    hue = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r)
    gm = m & (mx == g) & ~rm
    bm = m & ~rm & ~gm
    hue[rm] = ((g[rm] - b[rm]) / d[rm]) % 6
    hue[gm] = ((b[gm] - r[gm]) / d[gm]) + 2
    hue[bm] = ((r[bm] - g[bm]) / d[bm]) + 4
    hue = (hue * 60.0) % 360.0
    gray = luma
    gx = np.abs(np.diff(gray, axis=1)).mean()
    gy = np.abs(np.diff(gray, axis=0)).mean()
    edges = float((gx + gy) / 2.0)
    # dominant hue among saturated pixels
    sel = (sat > 0.18) & (luma > 0.08)
    if sel.sum() > 50:
        hh = hue[sel]
        bins = np.histogram(hh, bins=12, range=(0, 360))[0]
        top = int(bins.argmax())
        share = float(bins.max() / bins.sum())
        hue_top = top * 30 + 15
    else:
        hue_top, share = -1, 0.0
    return {
        "luma": float(luma.mean()) * 255.0,
        "luma_p10": float(np.percentile(luma, 10)) * 255.0,
        "sat": float(sat.mean()),
        "edge": edges,
        "hue": hue_top,
        "hue_share": share,
    }


def temp_k(hue):
    """rough: blue 200-260K-equivalent scale -> map to Kelvin-ish number for comparison only"""
    if hue < 0:
        return 4000
    # warm hues 0-60 / 300-360 -> 3000K ; cool 180-260 -> 8000K
    if hue < 90 or hue > 270:
        return 3000 + (abs(((hue + 180) % 360) - 180) / 90.0) * 1000
    return 5000 + (abs(hue - 200) / 60.0) * 3000


ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--json", default=r"D:\FleetWorker\review\aesthetic.json")
a = ap.parse_args()

cuts, err = RG.detect_cuts(a.video)
if err:
    sys.exit("scene detect failed: " + err)
ts = [0.0] + cuts + [5623 / FPS]
shots = [(i + 1, ts[i], ts[i + 1]) for i in range(len(ts) - 1) if ts[i + 1] - ts[i] >= 0.25]

want = {}
for n, t0, t1 in shots:
    for frac in (0.2, 0.5, 0.8):
        want[int(round((t0 + (t1 - t0) * frac) * FPS))] = (n, frac)

p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.video, "-vf", "scale=%d:%d" % (W, H),
                      "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     stdout=subprocess.PIPE, bufsize=10**8)
acc = {}
k = 0
while True:
    b = p.stdout.read(FS)
    if len(b) < FS:
        break
    if k in want:
        n, frac = want[k]
        s = stats_for_frame(np.frombuffer(b, np.uint8).reshape(H, W, 3))
        acc.setdefault(n, []).append(s)
    k += 1
p.stdout.close()
p.wait()

rows = []
for n, t0, t1 in shots:
    ss = acc.get(n, [])
    if not ss:
        continue
    m = {key: float(np.mean([x[key] for x in ss])) for key in ("luma", "luma_p10", "sat", "edge")}
    hue = int(np.median([x["hue"] for x in ss]))
    share = float(np.mean([x["hue_share"] for x in ss]))
    m.update({"shot": n, "t0": round(t0, 2), "t1": round(t1, 2),
              "hue": hue, "hue_share": round(share, 2), "K": int(temp_k(hue))})
    flags = []
    if m["luma"] < 35:
        flags.append("DARK")
    if m["luma"] > 190:
        flags.append("BLOWN")
    if m["edge"] < 0.02:
        flags.append("FLAT")
    m["flags"] = flags
    rows.append(m)

# same-palette runs
run = 1
for i in range(1, len(rows)):
    if abs(rows[i]["K"] - rows[i - 1]["K"]) < 150 and abs(rows[i]["sat"] - rows[i - 1]["sat"]) < 0.10:
        run += 1
        rows[i]["palette_run"] = run
    else:
        run = 1
        rows[i]["palette_run"] = 1

print("shots=%d" % len(rows))
for r in rows:
    if r["flags"] or r.get("palette_run", 1) >= 6:
        print("  #%03d %6.2f-%6.2f luma=%5.1f sat=%.2f edge=%.3f K=%d %s"
              % (r["shot"], r["t0"], r["t1"], r["luma"], r["sat"], r["edge"], r["K"],
                 ",".join(r["flags"])))

dark = [r for r in rows if "DARK" in r["flags"]]
flat = [r for r in rows if "FLAT" in r["flags"]]
worst_run = max((r.get("palette_run", 1) for r in rows), default=1)
print("SUMMARY dark=%d flat=%d longest_same_palette_run=%d" % (len(dark), len(flat), worst_run))
json.dump(rows, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", a.json)

