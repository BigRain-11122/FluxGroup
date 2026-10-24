# -*- coding: ascii -*-
# kn_packa_assembly_c2180.py - rough-cut station for the KN (Ke Ai Nv Ren) 768P
# wave, built while the last four units are still on the card.
#
# Why this exists: KN24 landed at 12:45 and 26 of 30 units now sit on disk, but
# the only way anyone could look at them was one clip at a time. This script
# turns the landed units into a single ordered rough cut at the exact manifest
# windows, so the sequence (matching, wardrobe, prop continuity across cuts) can
# be judged before the wave even finishes. It is deliberately a rough cut:
# no grade, no transitions, no titles, no audio - those belong to the assembly
# station that runs once 30/30 is on disk.
#
# Contract:
#   * shot order and window lengths come from the i2v manifest (single source);
#   * each clip is trimmed to its source length, speed-shifted by its declared
#     factor, then hard-trimmed to its window so the timeline cannot drift;
#   * a missing unit is skipped and reported, never filled with a placeholder
#     (no synthetic frames pretend to be a shot).
#
# Usage:
#   python kn_packa_assembly_c2180.py --dry-run      # index only, no encode
#   python kn_packa_assembly_c2180.py --encode       # write the rough cut mp4
import argparse
import json
import os
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
MANIFEST = os.path.join(
    REPO, "cph4", "fleet", "mv-album-001-jay", "local-i2v", "run-bmc-kn-i2v.json"
)
CLIPDIR = os.path.join(REPO, "media", "mv-album-001-jay", "clips-local-768")
OUTDIR = os.path.join(REPO, "media", "mv-album-001-jay", "assembly-packA-KN")
W, H, FPS = 1344, 768, 24
BATCH = "C2180"
MIN_SPEED = 0.85


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def build_index():
    units = json.load(open(MANIFEST, encoding="utf-8"))["units"]
    rows, t = [], 0.0
    for u in units:
        clip = os.path.join(CLIPDIR, u["id"] + ".mp4")
        present = os.path.isfile(clip) and os.path.getsize(clip) > 100 * 1024
        src = probe_duration(clip) if present else 0.0
        row = {
            "id": u["id"], "shot": u["shot"], "win_s": u["win_s"],
            "speed": u["speed"], "src_s": u.get("src_s"), "src_measured_s": round(src, 3),
            "present": present, "start_s": round(t, 3) if present else None,
        }
        if present:
            # Fit the source to its window. When the render is shorter than the
            # window wants at its declared speed, slow it down instead of leaving
            # a hole - but never below MIN_SPEED, because past that the motion
            # reads as a freeze. A real gap is reported, not papered over.
            need = src / u["win_s"] if u["win_s"] else u["speed"]
            if need >= u["speed"]:
                eff, fit = u["speed"], "trim"
            elif need >= MIN_SPEED:
                eff, fit = need, "slowed"
            else:
                eff, fit = MIN_SPEED, "GAP"
            row["eff_speed"] = round(eff, 4)
            row["fit"] = fit
            row["achieved_s"] = round(min(src / eff, u["win_s"]), 3)
            row["deficit_s"] = round(max(0.0, u["win_s"] - src / eff), 3)
            row["end_s"] = round(t + row["achieved_s"], 3)
            t += row["achieved_s"]
        else:
            row["end_s"] = None
        rows.append(row)
    return rows, round(t, 3)


def encode(rows):
    os.makedirs(OUTDIR, exist_ok=True)
    live = [r for r in rows if r["present"]]
    inputs, chains, labels = [], [], []
    for i, r in enumerate(live):
        clip = os.path.join(CLIPDIR, r["id"] + ".mp4")
        inputs += ["-i", clip]
        src = r["src_measured_s"] or r["src_s"] or r["win_s"] * r["speed"]
        chains.append(
            "[{i}:v]trim=0:{src:.3f},setpts=(PTS-STARTPTS)/{sp},"
            "trim=duration={win:.3f},setpts=PTS-STARTPTS,fps={fps},"
            "scale={w}:{h}:force_original_aspect_ratio=increase,"
            "crop={w}:{h},setsar=1,format=yuv420p[v{i}]".format(
                i=i, src=src, sp=r.get("eff_speed", r["speed"]), win=r["win_s"], fps=FPS, w=W, h=H
            )
        )
        labels.append("[v%d]" % i)
    graph = ";".join(chains) + ";%sconcat=n=%d:v=1:a=0[out]" % (
        "".join(labels), len(live)
    )
    mp4 = os.path.join(OUTDIR, "KN-ROUGH-CUT-%dof%d-%s.mp4" % (len(live), len(rows), BATCH))
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + inputs + [
        "-filter_complex", graph, "-map", "[out]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", mp4,
    ]
    print("ENCODING %d units -> %s" % (len(live), os.path.basename(mp4)))
    subprocess.run(cmd, check=True)
    return mp4


def main():
    global BATCH
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--encode", action="store_true")
    ap.add_argument("--batch", default=BATCH,
                    help="batch tag used for the output mp4 and index names")
    a = ap.parse_args()
    BATCH = a.batch
    rows, total = build_index()
    missing = [r["shot"] for r in rows if not r["present"]]
    os.makedirs(OUTDIR, exist_ok=True)
    idx = {
        "batch": BATCH, "manifest": MANIFEST, "units": len(rows),
        "landed": len(rows) - len(missing), "missing": missing,
        "rough_cut_s": total, "full_timeline_s": round(sum(r["win_s"] for r in rows), 3),
        "timeline": rows,
    }
    mp4 = None
    if a.encode:
        mp4 = encode(rows)
        idx["rough_cut"] = mp4
    jp = os.path.join(OUTDIR, "KN-ROUGH-CUT-INDEX-%s.json" % BATCH)
    for r in rows:
        if r["present"]:
            print("%-14s %6.2fs -> %7.3f-%7.3f" % (r["id"], r["win_s"], r["start_s"], r["end_s"]))
        else:
            print("%-14s MISSING" % r["id"])
    short = [r for r in rows if r.get("deficit_s", 0) >= 0.1]
    idx["coverage_short"] = [
        {"id": r["id"], "window_s": r["win_s"], "achieved_s": r["achieved_s"],
         "deficit_s": r["deficit_s"], "src_measured_s": r["src_measured_s"]}
        for r in short]
    for r in short:
        print("COVERAGE-SHORT %-14s window=%.2fs achieved=%.2fs deficit=%.2fs" % (
            r["id"], r["win_s"], r["achieved_s"], r["deficit_s"]))
    json.dump(idx, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ROUGH-END landed=%d/%d rough_cut=%.2fs missing=%s index=%s" % (
        idx["landed"], idx["units"], total, ",".join(missing) or "-", jp))
    if mp4:
        print("ROUGH-MP4 %s" % mp4)


if __name__ == "__main__":
    main()