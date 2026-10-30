# -*- coding: ascii -*-
# kn_lift_5_c2172.py - lift the five underexposed KN pack shots into a review set.
#
# Why: C2172 luma scan (ffmpeg signalstats YAVG, per-frame mean over the clip)
# found five of thirty 768P shots with mean YAVG < 35: KN21 23.33, KN25 27.28,
# KN17 30.30, KN23 30.34, KN18 33.30, against 86-112 on the bright openers.
# Per the standing law the fix for "cannot see it" is light, not a re-shoot, so
# this renders lifted variants next to the originals for a human vote.
#
# Zero GPU, never touches the source clips: output goes to clips-review-lift-c2172.
# PASS gate: LIFT-END ok=1, five variants, before/after board written.

import json
import os
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
BASE = os.path.join(REPO, "media", "mv-album-001-jay")
SRC = os.path.join(BASE, "clips-local-768")
OUT = os.path.join(BASE, "clips-review-lift-c2172")
LUMA_JSON = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "KN-PACKA-LUMA-c2172.json")
OUT_JSON = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "KN-LIFT-5-c2172.json")
LOG = os.path.join(BASE, "log-kn-lift-c2172.txt")
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

# station-1 night photography: lift gamma first, then a small black-point lift,
# so the sky keeps its density instead of turning into grey mush.
GAMMA = 1.45
LIFT = 0.035


def log(msg):
    line = "[%s] %s" % (__import__("time").strftime("%Y-%m-%d %H:%M:%S"), msg)
    with open(LOG, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")
    try:
        print(line)
    except Exception:
        pass


def luma(path):
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path,
                        "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"],
                       capture_output=True, text=True)
    import re
    vals = [float(m) for m in re.findall(r"signalstats\.YAVG=([0-9.]+)", r.stderr + r.stdout)]
    return round(sum(vals) / len(vals), 2) if vals else None


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    data = json.load(open(LUMA_JSON, encoding="utf-8"))
    targets = [d["unit"] for d in data["dark"]]
    rows = []
    for unit in targets:
        src = os.path.join(SRC, unit + ".mp4")
        dst = os.path.join(OUT, unit + "-lift.mp4")
        if not os.path.exists(src):
            log("SRC-MISSING %s" % unit)
            sys.exit(2)
        vf = "eq=gamma=%.2f:brightness=%.3f:saturation=1.04,format=yuv420p" % (GAMMA, LIFT)
        subprocess.check_call([FF, "-y", "-hide_banner", "-loglevel", "error",
                               "-i", src, "-an", "-vf", vf,
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                               "-movflags", "+faststart", dst])
        before = luma(src)
        after = luma(dst)
        rows.append({"unit": unit, "src": src, "out": dst,
                     "yavg_before": before, "yavg_after": after,
                     "bytes": os.path.getsize(dst)})
        log("LIFT %s %.2f -> %.2f" % (unit, before or -1, after or -1))

    ok = 1 if len(rows) == len(targets) and all(r["yavg_after"] and r["yavg_after"] > 40 for r in rows) else 0
    payload = {
        "batch": "C2172",
        "gamma": GAMMA, "black_lift": LIFT,
        "targets": targets,
        "rows": rows,
        "note": ("Review variants only. Sources untouched. This is the cheap branch of the "
                 "fix: if the human vote says the shots still read as empty, the shots need a "
                 "re-burn with a different light setup, not more gamma."),
    }
    json.dump(payload, open(OUT_JSON, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    log("LIFT-END ok=%d n=%d" % (ok, len(rows)))
    if not ok:
        sys.exit(4)


if __name__ == "__main__":
    main()