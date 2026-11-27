# -*- coding: ascii -*-
# xq_edl_v3_retire_c2150.py - retire PACK-B shot S3-17 from the Xingqing EDL.
#
# Why: S3-17 (95.6-102s, two pairs of feet on the white line) failed three
# burns (r1, r2, r3). r2 and r3 both broke the plate at ~t=3-5s (background
# re-render, MAE >30 in the ground band). The C2149 verdict said: do not spend
# a fourth burn. So the shot leaves the EDL and XQ_S3-18 (PASS take, 9.417s
# clip) moves up to the 95.6s slot.
#
# This script is the arithmetic half of that decision. It does NOT invent
# footage: it moves the PASS clip to the earlier slot, then reports exactly
# how much real picture is left over the retired window and where the hole
# lands. A hole is reported as a hole; it is not papered over with a freeze.
#
# Zero GPU. Reads the C2145 coverage board + the C2133 assembly index.
# Writes:
#   cph4/fleet/mv-album-001-jay/xq-PACKB-EDL-v3-c2150.json
#   cph4/fleet/mv-album-001-jay/xq-PACKB-EDL-v3-c2150.md
#   media/mv-album-001-jay/assembly-packA/XQ-RETIME-PROOF-S3-18-c2150.mp4
# PASS gate: EDL-END retired=1 advanced=1 holes=N proof_ok=1

import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
COVERAGE = os.path.join(OUTDIR, "xq-KF-COVERAGE-c2145.json")
INDEX_V2 = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json")
SHOTLIST = os.path.join(OUTDIR, "\u661f\u6674-SHOTLIST-v3.md")  # Xingqing shotlist v3
SONG = os.path.join(OUTDIR, "audio", "\u5468\u6770\u4f26 - \u661f\u6674.mp3")  # Jay - Xingqing
OUT_JSON = os.path.join(OUTDIR, "xq-PACKB-EDL-v3-c2150.json")
OUT_MD = os.path.join(OUTDIR, "xq-PACKB-EDL-v3-c2150.md")
PROOF_DIR = os.path.join(MEDIA, "assembly-packA")
PROOF_MP4 = os.path.join(PROOF_DIR, "XQ-RETIME-PROOF-S3-18-c2150.mp4")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

BATCH = "C2150"
RETIRED = "S3-17"
ADVANCED = "S3-18"
ADVANCED_T0 = 95.6          # authored window of the retired shot
EVIDENCE = [
    "media/mv-album-001-jay/bmc/qc-768packB-c2149/PACKB-768P-VERDICT-c2149.md",
    "media/mv-album-001-jay/bmc/qc-768packB-c2149-r3/PACKB-768P-VERDICT-c2149r3.md",
]
# r3 numbers quoted in the ledger tail; kept here so the EDL carries its own
# evidence trail instead of pointing at a console scroll.
EVIDENCE_NUMBERS = {
    "r2_mae_t1_t3": 49.09,
    "r2_mae_t3_t5": 55.54,
    "r2_ground_frac_gt25": 0.638,
    "r3_mae": 32.73,
    "r3_frac_gt25": 0.303,
    "pass_reference_s3_21_mae": 9.86,
    "pass_reference_s3_21_frac_gt25": 0.085,
}


def probe(path):
    out = subprocess.check_output([
        FFPROBE, "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
        "-show_entries", "format=duration", "-of", "json", path])
    d = json.loads(out.decode("utf-8", "replace"))
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {
        "res": "%sx%s" % (st["width"], st["height"]),
        "fps": round(float(num) / float(den), 3),
        "frames": int(st["nb_read_frames"]),
        "sec": round(float(d["format"]["duration"]), 3),
    }


def union(intervals):
    iv = sorted((a, b) for a, b in intervals if b > a)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + 1e-9:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def holes_within(covered, t0, t1):
    gaps = []
    cur = t0
    for a, b in covered:
        if b <= cur:
            continue
        if a > cur + 1e-9:
            gaps.append((round(cur, 3), round(min(a, t1), 3)))
        cur = max(cur, b)
        if cur >= t1 - 1e-9:
            break
    if cur < t1 - 1e-9:
        gaps.append((round(cur, 3), round(t1, 3)))
    return gaps


def main():
    with open(COVERAGE, encoding="utf-8") as f:
        cov = json.load(f)
    with open(INDEX_V2, encoding="utf-8") as f:
        idx = json.load(f)

    timeline = float(cov["timeline_seconds"])
    old_covered = float(cov["covered_seconds"])

    clip = {c["unit"]: c for c in idx["clips"]}
    adv = clip["XQ_" + ADVANCED]
    adv_clip_sec = float(adv["clip_sec"])
    adv_win = float(adv["win"])

    # 1) shot table with the retirement applied
    kept = []
    retired_row = None
    for s in cov["shots"]:
        if s["shot"] == RETIRED:
            retired_row = s
            continue
        row = dict(s)
        if s["shot"] == ADVANCED:
            row["t0_orig"] = s["t0"]
            row["t1_orig"] = s["t1"]
            row["t0"] = ADVANCED_T0
            row["t1"] = round(ADVANCED_T0 + min(adv_clip_sec, max(s["t1"] - ADVANCED_T0, adv_win)), 3)
            row["retime"] = "advanced to the retired slot, cut to the full PASS clip"
        kept.append(row)

    # 2) coverage over the same 0..timeline window
    intervals = [(float(r["t0"]), float(r["t1"])) for r in kept]
    merged = union(intervals)
    covered = sum(b - a for a, b in merged)
    gaps = holes_within(merged, 0.0, timeline)
    uncovered = round(timeline - covered, 3)

    # 3) what the retired window actually needs vs what the survivor can give
    retired_span = round(float(retired_row["t1"]) - float(retired_row["t0"]), 3) if retired_row else 0.0
    needed_from_advanced = round(float(retired_row["t1"]) - ADVANCED_T0, 3) if retired_row else 0.0
    short_by = round(max(needed_from_advanced - adv_clip_sec, 0.0), 3)

    rec = {
        "batch": BATCH,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "project": "mv0001-xingqing",
        "edl": "v3",
        "why": ("PACK-B S3-17 failed three burns on plate drift; the C2149 ruling "
                "forbids a fourth burn. Retire it and let the PASS take XQ_S3-18 "
                "cover the earlier slot."),
        "retired": {
            "shot": RETIRED,
            "window": [float(retired_row["t0"]), float(retired_row["t1"])] if retired_row else None,
            "span_s": retired_span,
            "burns": 3,
            "evidence": EVIDENCE,
            "numbers": EVIDENCE_NUMBERS,
            "rule": "no fourth burn on the same recipe (C2149 verdict)",
        },
        "advanced": {
            "shot": ADVANCED,
            "file": adv["file"],
            "clip_sec": adv_clip_sec,
            "window_orig": [float(clip["XQ_" + ADVANCED].get("t0", 0.0)), 0.0],
            "window_new": [ADVANCED_T0, round(ADVANCED_T0 + adv_clip_sec, 3)],
            "source_of_truth": "cph4/fleet/mv-album-001-jay/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json",
        },
        "timeline_seconds": timeline,
        "covered_before_s": old_covered,
        "covered_after_s": round(covered, 3),
        "delta_s": round(covered - old_covered, 3),
        "uncovered_after_s": uncovered,
        "holes_after": [{"t0": a, "t1": b, "span_s": round(b - a, 3)} for a, b in gaps],
        "residual": {
            "needed_over_retired_window_s": needed_from_advanced,
            "survivor_clip_s": adv_clip_sec,
            "short_by_s": short_by,
            "reading": ("the survivor is shorter than the retired slot, so the EDL "
                        "does not pretend the window is filled"),
            "close_options": [
                "a) cut S3-19 in early over the residual tail (star shot arrives before its lyric beat)",
                "b) slow the survivor below 0.83x to stretch 9.42s over 14.4s (motion reads as slow-motion)",
                "c) one new A-pack frame/burn for the leftover span only (not a re-burn of S3-17)",
                "d) accept the residual as a deliberate cut-away and let the audio station decide",
            ],
        },
        "gate": "pending",
    }

    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")

    # 4) proof clip: the PASS take at its new slot, under the real song audio
    if not os.path.isdir(PROOF_DIR):
        os.makedirs(PROOF_DIR)
    src = os.path.join(MEDIA, clip["XQ_" + ADVANCED]["file"].replace("/", os.sep))
    if not os.path.exists(SONG):
        print("SONG-MISSING %s" % SONG)
        sys.exit(3)
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", src, "-ss", "%.3f" % ADVANCED_T0, "-i", SONG,
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-t", "%.3f" % adv_clip_sec, "-movflags", "+faststart", PROOF_MP4]
    subprocess.check_call(cmd)
    pinfo = probe(PROOF_MP4)
    pbytes = os.path.getsize(PROOF_MP4)
    proof_ok = 1 if abs(pinfo["sec"] - adv_clip_sec) <= 0.2 and pbytes > 200000 else 0

    rec["proof"] = {
        "out": os.path.relpath(PROOF_MP4, REPO).replace("\\", "/"),
        "bytes": pbytes,
        "probe": pinfo,
        "what": ("S3-18 PASS take laid into the 95.6s slot with the real song under "
                 "it, so the director can judge the retime without re-cutting"),
        "not_included": "the residual span after the clip ends is NOT padded here",
    }
    rec["gate"] = "EDL-END retired=1 advanced=1 holes=%d proof_ok=%d" % (len(gaps), proof_ok)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")

    lines = [
        "# Xingqing EDL v3 - PACK-B S3-17 retired (%s)" % BATCH,
        "",
        "> Built %s. Arithmetic only: no new footage is invented here." % rec["ts"],
        "",
        "## Decision",
        "- **retire** `%s` (%.1f-%.1fs, %.2fs): three burns, plate re-rendered at t~3-5s on r2 and r3." %
        (RETIRED, rec["retired"]["window"][0], rec["retired"]["window"][1], retired_span),
        "- **advance** `%s` to %.1fs and cut it to the full PASS clip (%.3fs)." % (ADVANCED, ADVANCED_T0, adv_clip_sec),
        "",
        "## Coverage",
        "| metric | before | after |",
        "|---|---|---|",
        "| covered | %.1fs | %.1fs |" % (old_covered, covered),
        "| uncovered | %.1fs | %.1fs |" % (timeline - old_covered, uncovered),
        "",
        "## Holes after the retirement",
    ]
    if gaps:
        for a, b in gaps:
            lines.append("- %.2f-%.2fs (%.2fs)" % (a, b, b - a))
    else:
        lines.append("- none")
    lines += [
        "",
        "## Residual (the honest part)",
        "- the retired slot needs %.2fs from the survivor; the survivor clip is %.3fs, short by **%.2fs**." %
        (needed_from_advanced, adv_clip_sec, short_by),
        "- close options:",
    ]
    for o in rec["residual"]["close_options"]:
        lines.append("  - %s" % o)
    lines += [
        "",
        "## Proof clip",
        "- `%s` (%.2fs, %d B) - the PASS take at the new slot over the real song." %
        (rec["proof"]["out"], pinfo["sec"], pbytes),
        "",
        "Gate: `%s`" % rec["gate"],
        "",
    ]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print(rec["gate"])
    print("COVERED before=%.2f after=%.2f delta=%+.2f" % (old_covered, covered, covered - old_covered))
    for a, b in gaps:
        print("HOLE %.2f-%.2f (%.2f)" % (a, b, b - a))
    print("PROOF %s %dB %ss" % (rec["proof"]["out"], pbytes, pinfo["sec"]))
    if not proof_ok:
        sys.exit(4)


if __name__ == "__main__":
    main()