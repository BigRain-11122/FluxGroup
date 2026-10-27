# -*- coding: utf-8 -*-
"""mv_fidelity.py - how much a re-encode cost, measured instead of guessed.

Why: rebuilding a master through a filter (label burn, subtitle burn, grade) always
re-encodes. On 2026-10-28 the AIGC-label pass took v717 from 22.17 Mbps to 6.17 Mbps;
whether that is "x264 simply packs better" or "grain got smoothed away" cannot be argued
from bitrate - SSIM/PSNR answers it.

Usage:
  python Tools/mv_fidelity.py <reference.mp4> <candidate.mp4> [--json out.json]
Exit 0 always (this is a measurement, not a gate).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys


def fern(name):
    for c in (shutil.which(name),
              r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages"
              r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
              r"\ffmpeg-9.0.2-full_build\bin\%s.exe" % name,
              r"C:\Program Files\ffmpeg\bin\%s.exe" % name):
        if c and os.path.exists(c):
            return c
    return name


def measure(ff, ref, cand, flt):
    """Return the filter's own summary line, e.g. 'SSIM ... All:0.9812'."""
    cmd = [ff, "-v", "info", "-i", ref, "-i", cand,
           "-lavfi", "[0:v][1:v]%s" % flt, "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    for line in reversed((r.stderr or "").splitlines()):
        if flt.upper() in line.upper():
            return line.strip()
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("candidate")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    for p in (a.reference, a.candidate):
        if not os.path.isfile(p):
            print("FIDELITY FAIL: missing", p)
            return 2
    ff = fern("ffmpeg")
    out = {"reference": a.reference, "candidate": a.candidate}
    for name, flt in (("ssim", "ssim"), ("psnr", "psnr")):
        line = measure(ff, a.reference, a.candidate, flt)
        out[name] = line
        print("%-5s %s" % (name, line or "(no summary)"))
    m = re.search(r"All:\s*([0-9.]+)", out.get("ssim") or "")
    out["ssim_all"] = float(m.group(1)) if m else None
    verdict = "unknown"
    if out["ssim_all"] is not None:
        verdict = "PASS(>=0.97)" if out["ssim_all"] >= 0.97 else (
            "WARN(0.95-0.97)" if out["ssim_all"] >= 0.95 else "FAIL(<0.95)")
    out["verdict"] = verdict
    print("VERDICT:", verdict)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".", exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())