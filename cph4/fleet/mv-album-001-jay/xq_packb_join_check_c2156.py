# -*- coding: ascii -*-
# xq_packb_join_check_c2156.py - prove no join is a duplicate frame.
#
# Freeze detection alone cannot answer this: the take material is slow-moving
# generated footage, so two-frame near-identical pairs occur everywhere and the
# montage cycle deliberately revisits the same astronomy scene. The question
# that matters is narrower - at each of the 39 joins, is the outgoing frame
# literally identical to the incoming frame?
#
# Method: pull the last frame of shot A and the first frame of shot B for every
# join as raw 32x18 grey pixels in one decode pass, then report the mean
# absolute difference per join. Zero difference = duplicate seam.

import json
import os
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
INDEX = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v2-c2156.json")
VIDEO = os.path.join(REPO, "media", "mv-album-001-jay", "assembly-packB",
                     "XQ-PACKB-ASSEMBLY-v2-c2156.video-only.mp4")
OUT = os.path.join(OUTDIR, "xq-PACKB-JOINCHECK-c2156.json")
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"

W, H = 32, 18


def main():
    with open(INDEX, encoding="utf-8-sig") as f:
        idx = json.load(f)
    clips = idx["clips"]
    joins = []
    for a, b in zip(clips, clips[1:]):
        f_a = a["timeline_frames"][1]
        joins.append({
            "at": round(f_a / 24.0, 4),
            "frame": f_a,
            "from": a["shot"],
            "to": b["shot"],
            "same_shot": a["shot"].split("cont")[0] == b["shot"].split("cont")[0],
        })

    frames = []
    for j in joins:
        frames.append(j["frame"] - 1)
        frames.append(j["frame"])
    expr = "+".join("eq(n\\,%d)" % n for n in frames)
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-i", VIDEO,
           "-vf", "select='%s',scale=%d:%d,format=gray" % (expr, W, H),
           "-vsync", "0", "-f", "rawvideo", "-"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr.decode("utf-8", "replace"))
        sys.exit(2)
    buf = proc.stdout
    size = W * H
    got = len(buf) // size
    if got != len(frames):
        sys.stderr.write("expected %d frames, got %d\n" % (len(frames), got))
        sys.exit(3)

    rows = []
    worst = None
    for i, j in enumerate(joins):
        a = buf[i * 2 * size:(i * 2 + 1) * size]
        b = buf[(i * 2 + 1) * size:(i * 2 + 2) * size]
        diff = sum(abs(x - y) for x, y in zip(a, b)) / float(size)
        row = {"at": j["at"], "from": j["from"], "to": j["to"],
               "same_shot": j["same_shot"], "mean_abs_diff": round(diff, 3),
               "duplicate": diff < 0.5}
        rows.append(row)
        if worst is None or diff < worst["mean_abs_diff"]:
            worst = row

    dups = [r for r in rows if r["duplicate"]]
    out = {
        "schema": "xq-packb-joincheck/v1",
        "batch": "C2156",
        "joins": len(rows),
        "duplicates": len(dups),
        "min_mean_abs_diff": worst,
        "note": ("mean abs diff on a 32x18 grey thumbnail; <0.5 counts as a "
                 "duplicate seam. Slow takes and the montage cycle can be close "
                 "on purpose, so values near zero are listed, not silently passed."),
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("JOINCHECK joins=%d duplicates=%d min_diff=%.3f at %ss %s->%s" %
          (len(rows), len(dups), worst["mean_abs_diff"], worst["at"],
           worst["from"], worst["to"]))
    low = sorted(rows, key=lambda r: r["mean_abs_diff"])[:6]
    for r in low:
        print("  low %.3f @%ss %s -> %s%s" %
              (r["mean_abs_diff"], r["at"], r["from"], r["to"],
               " (same shot)" if r["same_shot"] else ""))
    if len(dups) > 3:
        sys.exit(4)


if __name__ == "__main__":
    main()