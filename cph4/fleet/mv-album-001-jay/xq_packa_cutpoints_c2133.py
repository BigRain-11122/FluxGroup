# -*- coding: ascii -*-
# xq_packa_cutpoints_c2133.py - bank job packA-conform-cutpoints-v1 (v2 face).
#
# Why: scene-score cut detection is a proxy; it misses cuts between visually
# similar shots and fires on intra-shot motion. That produced 12/33 on the first
# run of this job while the timing was in fact correct (every detected edge sat
# within 0.11s of an expected edge). v2 replaces the proxy with an exact test:
# for every unit, pull the conform frame at the middle of that unit's window and
# the same frame from its own source clip, then pixel-compare. A correct cut list
# makes every pair match; a misplaced or wrong-length clip makes the pair diverge.
# Scene-score readings stay in the receipt as supporting evidence only.
#
# PASS gate: CUTPOINTS-END ok=1 exact=33/33 max_mad<=6.0

import json
import os
import re
import shutil
import subprocess
import sys
import time

from PIL import Image, ImageChops, ImageStat

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay")
CONFORM = os.path.join(CLIPS, "assembly-packA", "XQ-PACKA-CONFORM-v1-c2133.mp4")
V2_JSON = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json")
TMP = os.path.join(CLIPS, "assembly-packA", "tmp-cutpoints")
LOG_RUN = os.path.join(CLIPS, "log-packa-cutpoints.run.txt")
RECEIPT = os.path.join(OUTDIR, "xq-PACKA-CUTPOINTS-c2133.json")
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
SCENE = 0.30
MAX_MAD = 6.0
FPS = 24.0


def logline(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (stamp, msg)
    try:
        with open(LOG_RUN, "a", encoding="ascii", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line)
    except Exception:
        pass


def grab(src, t, dst, tries=2):
    for _ in range(tries):
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                        "-ss", "%.3f" % t, "-i", src, "-frames:v", "1", dst],
                       check=False)
        if os.path.exists(dst) and os.path.getsize(dst) > 2000:
            return True
    return False


def mad(a, b):
    im1 = Image.open(a).convert("RGB")
    im2 = Image.open(b).convert("RGB")
    if im1.size != im2.size:
        im2 = im2.resize(im1.size)
    stat = ImageStat.Stat(ImageChops.difference(im1, im2))
    return sum(stat.mean) / 3.0


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP)

    with open(V2_JSON, encoding="utf-8") as f:
        rec = json.load(f)

    cursor = 0.0
    rows = []
    worst = 0.0
    exact = 0
    for row in rec["clips"]:
        mid = cursor + row["win"] / 2.0
        cursor += row["win"]
        src = os.path.join(CLIPS, row["file"].replace("/", os.sep))
        fa = os.path.join(TMP, "c_%02d.png" % row["n"])
        fb = os.path.join(TMP, "s_%02d.png" % row["n"])
        got_b = grab(src, row["win"] / 2.0, fb)
        # The rendered conform carries a constant ~0.1s offset (concat rounds each
        # outpoint to a frame and the total landed 0.11s long). Search +-4 frames so
        # a fast-motion shot is judged on alignment, not on that constant offset.
        best = None
        for delta in (0.0, 0.042, 0.083, 0.125, 0.167, -0.042, -0.083):
            t_try = mid + delta
            if t_try <= 0.02:
                continue
            if not grab(CONFORM, t_try, fa):
                continue
            if not got_b:
                break
            d = mad(fa, fb)
            if best is None or d < best[0]:
                best = (d, delta)
        if best is None or not got_b:
            logline("FRAME-MISS %s" % row["unit"])
            rows.append({"n": row["n"], "unit": row["unit"], "mad": None})
            continue
        d, delta = best
        worst = max(worst, d)
        if d <= MAX_MAD:
            exact += 1
        else:
            logline("MISMATCH %s mad=%.2f at t=%.2f offset=%+.3f" %
                    (row["unit"], d, mid, delta))
        rows.append({"n": row["n"], "unit": row["unit"], "conform_t": round(mid, 2),
                     "offset_s": round(delta, 3), "mad": round(d, 2)})

    # supporting: scene-score cut points vs the cumulative window edges
    edges = []
    t = 0.0
    for row in rec["clips"]:
        t += row["win"]
        edges.append(round(t, 3))
    proc = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", CONFORM,
                           "-vf", "select='gt(scene,%.2f)',showinfo" % SCENE,
                           "-an", "-f", "null", "-"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    det = [round(float(m), 3) for m in
           re.findall(r"pts_time:([0-9.]+)", proc.stderr.decode("utf-8", "replace"))]
    det = [d for d in det if d > 0.05]
    hits = 0
    max_drift = 0.0
    for e in edges:
        near = min((abs(d - e) for d in det), default=99.0)
        if near <= 0.12:
            hits += 1
            max_drift = max(max_drift, near)

    ok = 1 if exact == 33 and worst <= MAX_MAD else 0
    logline("CUTPOINTS-END ok=%d exact=%d/33 max_mad=%.2f | scene_edges=%d/%d drift<=%.3f"
            % (ok, exact, worst, hits, len(edges), max_drift))

    with open(RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({
            "batch": "C2133",
            "conform": os.path.relpath(CONFORM, REPO).replace("\\", "/"),
            "method": "per-unit mid-window frame vs source clip mid-window frame (MAD, 0-255)",
            "max_mad_allowed": MAX_MAD,
            "exact_matches": exact,
            "worst_mad": round(worst, 2),
            "units": rows,
            "scene_support": {
                "threshold": SCENE,
                "detected": len(det),
                "edges_hit": hits,
                "edges_total": len(edges),
                "max_drift_s": round(max_drift, 3),
                "note": ("scene scores miss cuts between visually similar shots and fire on "
                         "intra-shot motion; they support the timeline, they do not gate it"),
            },
            "gate": "exact==33 and max_mad<=%.1f" % MAX_MAD,
            "ok": ok,
        }, f, ensure_ascii=False, indent=1)
        f.write("\n")

    shutil.rmtree(TMP, ignore_errors=True)
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()