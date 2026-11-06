# -*- coding: utf-8 -*-
"""regression_diff.py - v722g vs v723 per-second SSIM regression map.
Proof-of-value test: would an automated two-version diff have caught the
16-slot source regression instantly? Extracts 1fps thumbnails from both
masters and computes per-second SSIM; windows below threshold are listed.
Usage: py regression_diff.py <a.mp4> <b.mp4> [--out json]
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

THUMB = "480:272"  # same aspect family, fast


def grab_1fps(path, tmpdir):
    out = os.path.join(tmpdir, os.path.basename(path).replace(".mp4", "") + "_%05d.png")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path,
                     "-vf", "fps=1,scale=%s" % THUMB, out], check=True)
    return {int(os.path.basename(p).split("_")[-1].split(".")[0]): p
            for p in [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)
                      if f.startswith(os.path.basename(path).replace(".mp4", "") + "_")]}


def ssim_gray(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    mu_a, mu_b = a.mean(), b.mean()
    va, vb = a.var(), b.var()
    cov = ((a - mu_a) * (b - mu_b)).mean()
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))


def main():
    a_path, b_path = sys.argv[1], sys.argv[2]
    out_json = None
    if "--out" in sys.argv:
        out_json = sys.argv[sys.argv.index("--out") + 1]
    with tempfile.TemporaryDirectory() as td:
        fa = grab_1fps(a_path, td)
        fb = grab_1fps(b_path, td)
        common = sorted(set(fa) & set(fb))
        rows = []
        for i in common:
            ia = Image.open(fa[i]).convert("L")
            ib = Image.open(fb[i]).convert("L")
            if ia.size != ib.size:
                ib = ib.resize(ia.size)
            rows.append((i, ssim_gray(ia, ib)))
    vals = [r[1] for r in rows]
    med = float(np.median(vals))
    thr = med - 0.15
    dips = [(i, round(v, 3)) for (i, v) in rows if v < thr]
    # merge consecutive dip seconds into windows
    windows = []
    for i, v in dips:
        if windows and i - windows[-1][1] <= 2:
            windows[-1][1] = i
            windows[-1][2] = min(windows[-1][2], v)
        else:
            windows.append([i, i, v])
    print("samples=%d median_ssim=%.3f threshold=%.3f" % (len(rows), med, thr))
    print("regression_windows=%d" % len(windows))
    for w in windows:
        print("  %6ds - %6ds  min_ssim=%.3f" % (w[0], w[1], w[2]))
    if out_json:
        json.dump({"median": med, "threshold": thr,
                   "windows": [{"s0": w[0], "s1": w[1], "min_ssim": w[2]} for w in windows]},
                  open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
