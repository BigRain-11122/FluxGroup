# -*- coding: ascii -*-
# xq_edl_v4_gap_c2151.py - EDL v4: close the 52.00-54.00s script gap with footage
# that already exists.
#
# Why: the C2145 coverage board flagged 52.00-54.00s as a shotlist gap between
# S1-09 (44-52s) and S2-10 (54-62s). Both clips were cut short of their own
# length: XQ_S1-09 and XQ_S2-10 are 9.4167s each but the EDL only used 8.0s of
# each. That surplus is real picture, so the gap can be closed without a burn:
#   - S1-09 runs its full clip: 44.000 -> 53.417 (surplus 1.417s)
#   - S2-10 starts 0.583s before its lyric beat and is trimmed at the S2-11 cut
#     (53.417 -> 62.000, 8.583s used of 9.417s)
# Net: the 2.00s hole goes to 0.00s, lyric drift is 0.583s on one shot.
#
# What this script does NOT do: it does not touch the 105.017-110.00s residual
# left by the S3-17 retirement. That one needs footage nobody has shot yet
# (option c: one new burn for the leftover span only), so it stays a hole and is
# recorded as such.
#
# Zero GPU. Reads the C2145 coverage board + the C2133 assembly index.
# Writes:
#   cph4/fleet/mv-album-001-jay/xq-PACKB-EDL-v4-c2151.json
#   cph4/fleet/mv-album-001-jay/xq-PACKB-EDL-v4-c2151.md
#   media/mv-album-001-jay/assembly-packA/XQ-GAP-PROOF-52-54-c2151.mp4
#   media/mv-album-001-jay/assembly-packA/XQ-GAP-PROOF-52-54-c2151-strip.jpg
# PASS gate: EDL-GAP closed=1 covered_delta=+2.0 holes=1 proof_ok=1

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
SONG = os.path.join(OUTDIR, "audio", "\u5468\u6770\u4f26 - \u661f\u6674.mp3")
OUT_JSON = os.path.join(OUTDIR, "xq-PACKB-EDL-v4-c2151.json")
OUT_MD = os.path.join(OUTDIR, "xq-PACKB-EDL-v4-c2151.md")
PROOF_DIR = os.path.join(MEDIA, "assembly-packA")
PROOF_MP4 = os.path.join(PROOF_DIR, "XQ-GAP-PROOF-52-54-c2151.mp4")
PROOF_STRIP = os.path.join(PROOF_DIR, "XQ-GAP-PROOF-52-54-c2151-strip.jpg")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

BATCH = "C2151"
# v3 retirements/advances that v4 must inherit
RETIRED_V3 = "S3-17"
ADVANCED_V3 = "S3-18"
ADVANCED_V3_T0 = 95.6
# this round
GAP_SHOT_BEFORE = "S1-09"
GAP_SHOT_AFTER = "S2-10"
GAP_WINDOW = (52.0, 54.0)
PROOF_T0 = 48.0
PROOF_SEC = 12.0


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
    old_covered = float(cov["covered_seconds"])  # C2145 baseline (236.0)
    clip = {c["unit"]: c for c in idx["clips"]}

    # 1) shot table: inherit v3, then apply the gap closure
    kept = []
    edits = []
    for s in cov["shots"]:
        if s["shot"] == RETIRED_V3:
            continue
        row = dict(s)
        if s["shot"] == ADVANCED_V3:
            adv_sec = float(clip["XQ_" + ADVANCED_V3]["clip_sec"])
            row["t0"] = ADVANCED_V3_T0
            row["t1"] = round(ADVANCED_V3_T0 + adv_sec, 3)
            row["retime"] = "v3: advanced to the retired slot, full PASS clip"
        if s["shot"] == GAP_SHOT_BEFORE:
            sec = float(clip["XQ_" + GAP_SHOT_BEFORE]["clip_sec"])
            row["t0_orig"], row["t1_orig"] = row["t0"], row["t1"]
            row["t1"] = round(row["t0"] + sec, 3)
            row["retime"] = "v4: full clip used, surplus absorbs the script gap"
            edits.append({
                "shot": GAP_SHOT_BEFORE,
                "from": [row["t0_orig"], row["t1_orig"]],
                "to": [row["t0"], row["t1"]],
                "why": "clip is %.3fs, the EDL used 8.0s; the %+.3fs surplus reaches into the gap" %
                       (sec, row["t1"] - row["t1_orig"]),
            })
        if s["shot"] == GAP_SHOT_AFTER:
            sec = float(clip["XQ_" + GAP_SHOT_AFTER]["clip_sec"])
            row["t0_orig"] = row["t0"]
            row["t0"] = round(float(kept[-1]["t1"]), 3) if kept else row["t0"]
            # t1 stays: the next shot's cut is the fixed anchor
            used = round(row["t1"] - row["t0"], 3)
            row["retime"] = "v4: starts %.3fs early to seal the gap, trimmed at the S2-11 cut" % \
                            (row["t0_orig"] - row["t0"])
            edits.append({
                "shot": GAP_SHOT_AFTER,
                "from": [row["t0_orig"], row["t1"]],
                "to": [row["t0"], row["t1"]],
                "why": "starts %.3fs before its lyric beat; %.3fs used of %.3fs, %.3fs trimmed" %
                       (row["t0_orig"] - row["t0"], used, sec, sec - used),
            })
        kept.append(row)

    # 2) coverage over the same 0..timeline window
    merged = union([(float(r["t0"]), float(r["t1"])) for r in kept])
    covered = round(sum(b - a for a, b in merged), 3)
    gaps = holes_within(merged, 0.0, timeline)

    # 3) integrity: no shot may use more than its clip. Alternate takes share one
    # window (S2-11/12/13, S5-26/27/28), so those rows are not single-clip windows
    # and are skipped - the check only applies to a window that maps 1:1 to a clip.
    win_count = {}
    for r in kept:
        k = (round(float(r["t0"]), 3), round(float(r["t1"]), 3))
        win_count[k] = win_count.get(k, 0) + 1
    over = []
    for r in kept:
        name = "XQ_" + r["shot"]
        k = (round(float(r["t0"]), 3), round(float(r["t1"]), 3))
        if name in clip and win_count[k] == 1:
            used = float(r["t1"]) - float(r["t0"])
            if used > float(clip[name]["clip_sec"]) + 1e-6:
                over.append({"shot": r["shot"], "used": round(used, 3),
                             "clip": clip[name]["clip_sec"]})

    rec = {
        "batch": BATCH,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "project": "mv0001-xingqing",
        "edl": "v4",
        "why": ("EDL v3 left 7.0s uncovered: the 52.00-54.00s script gap plus the "
                "105.017-110.00s residual from the S3-17 retirement. The script gap "
                "can be paid for with clip surplus both neighbours already carry."),
        "inherited_v3": {
            "retired": RETIRED_V3,
            "advanced": ADVANCED_V3,
            "advanced_t0": ADVANCED_V3_T0,
            "source": "cph4/fleet/mv-album-001-jay/xq-PACKB-EDL-v3-c2150.json",
        },
        "edits": edits,
        "shots": [{"shot": r["shot"], "pack": r.get("pack"), "t0": r["t0"], "t1": r["t1"]}
                  for r in kept],
        "timeline_seconds": timeline,
        "covered_before_s": round(float(cov["covered_seconds"]) - 6.4 +
                                  (float(clip["XQ_" + ADVANCED_V3]["clip_sec"]) - 8.0), 3),
        "covered_after_s": covered,
        "uncovered_after_s": round(timeline - covered, 3),
        "holes_after": [{"t0": a, "t1": b, "span_s": round(b - a, 3)} for a, b in gaps],
        "residual": {
            "window": [105.017, 110.0],
            "span_s": 4.983,
            "status": "open - needs footage that does not exist yet",
            "decision": ("option c) one new burn for the leftover span only: an S3-18 "
                         "continuation (couple silhouette on the white line, dusk), "
                         "5.0s, first_frame from the S3-18 keyframe. Not fired this round."),
            "why_not_a_or_b": ("(a) pulls the star reveal 5s before its lyric beat and only "
                               "moves the hole downstream; (b) 0.65x reads as slow motion."),
            "why_not_d": "a 5s black hole in the middle of the second verse is not a cut-away.",
        },
        "clip_budget_overruns": over,
        "gate": "pending",
    }

    # 4) proof clip: the join at 53.417s over the real song (48.0-60.0s)
    if not os.path.isdir(PROOF_DIR):
        os.makedirs(PROOF_DIR)
    s1 = os.path.join(MEDIA, clip["XQ_" + GAP_SHOT_BEFORE]["file"].replace("/", os.sep))
    s2 = os.path.join(MEDIA, clip["XQ_" + GAP_SHOT_AFTER]["file"].replace("/", os.sep))
    if not os.path.exists(SONG):
        print("SONG-MISSING %s" % SONG)
        sys.exit(3)
    row1 = next(r for r in kept if r["shot"] == GAP_SHOT_BEFORE)
    row2 = next(r for r in kept if r["shot"] == GAP_SHOT_AFTER)
    off1 = PROOF_T0 - float(row1["t0"])            # into S1-09
    tail1 = float(row1["t1"]) - PROOF_T0           # seconds of S1-09 in the proof
    head2 = round(PROOF_SEC - tail1, 3)            # seconds of S2-10 in the proof
    head2 = min(head2, float(row2["t1"]) - float(row2["t0"]))
    fc = ("[0:v]trim=start=%.3f,setpts=PTS-STARTPTS[v0];"
          "[1:v]trim=start=0:end=%.3f,setpts=PTS-STARTPTS[v1];"
          "[v0][v1]concat=n=2:v=1:a=0[v]" % (off1, head2))
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", s1, "-i", s2, "-ss", "%.3f" % PROOF_T0, "-i", SONG,
           "-filter_complex", fc, "-map", "[v]", "-map", "2:a:0",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-t", "%.3f" % PROOF_SEC, "-movflags", "+faststart", PROOF_MP4]
    subprocess.check_call(cmd)
    pinfo = probe(PROOF_MP4)
    pbytes = os.path.getsize(PROOF_MP4)
    proof_ok = 1 if abs(pinfo["sec"] - PROOF_SEC) <= 0.25 and pbytes > 300000 else 0

    # 5) QC strip: three native frames across the join (both sides of 5.417s)
    cuts = [1.0, 5.4167, 7.0]
    tmp = []
    for i, t in enumerate(cuts):
        p = os.path.join(PROOF_DIR, "_gapf%d.png" % i)
        subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                               "-ss", "%.4f" % t, "-i", PROOF_MP4, "-frames:v", "1", p])
        tmp.append(p)
    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-i", tmp[0], "-i", tmp[1], "-i", tmp[2],
                           "-filter_complex", "[0:v]scale=640:-1[a];[1:v]scale=640:-1[b];"
                                              "[2:v]scale=640:-1[c];[a][b][c]hstack=inputs=3",
                           "-q:v", "2", PROOF_STRIP])
    for p in tmp:
        os.remove(p)

    rec["gate"] = "EDL-GAP closed=%d covered_delta=%+.3f holes=%d proof_ok=%d" % (
        1 if not any(a == GAP_WINDOW[0] and b == GAP_WINDOW[1] for a, b in gaps) else 0,
        covered - rec["covered_before_s"], len(gaps), proof_ok)
    rec["proof"] = {
        "out": os.path.relpath(PROOF_MP4, REPO).replace("\\", "/"),
        "bytes": pbytes,
        "probe": pinfo,
        "strip": os.path.relpath(PROOF_STRIP, REPO).replace("\\", "/"),
        "what": ("48.0-60.0s of the timeline with the real song: S1-09 tail, the seam at "
                 "%.3fs, S2-10 head. Looking for a jump in framing or a grade step." % (tail1 + PROOF_T0)),
        "join_at_s": round(PROOF_T0 + tail1, 3),
        "not_included": "the 105.017-110.0s residual is untouched",
    }

    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")

    lines = [
        "# Xingqing EDL v4 - 52.00-54.00s script gap closed (%s)" % BATCH,
        "",
        "> Built %s. Arithmetic only: no new footage is invented here." % rec["ts"],
        "",
        "## Edits",
    ]
    for e in edits:
        lines.append("- `%s` %.3f-%.3fs -> %.3f-%.3fs - %s" %
                     (e["shot"], e["from"][0], e["from"][1], e["to"][0], e["to"][1], e["why"]))
    lines += [
        "",
        "## Coverage",
        "| metric | C2145 | v3 | v4 |",
        "|---|---|---|---|",
        "| covered | 236.00s | 231.02s | %.3fs |" % covered,
        "| uncovered | 2.00s | 6.98s | %.3fs |" % (timeline - covered),
        "",
        "## Holes after v4",
    ]
    if gaps:
        for a, b in gaps:
            lines.append("- %.3f-%.3fs (%.3fs)" % (a, b, b - a))
    else:
        lines.append("- none")
    lines += [
        "",
        "## Residual 105.017-110.00s (still open)",
        "- %.3fs, decision: %s" % (rec["residual"]["span_s"], rec["residual"]["decision"]),
        "- why not (a)/(b): %s" % rec["residual"]["why_not_a_or_b"],
        "",
        "## Proof clip",
        "- `%s` (%.2fs, %d B) - seam at %.3fs over the real song." %
        (rec["proof"]["out"], pinfo["sec"], pbytes, rec["proof"]["join_at_s"]),
        "- strip `%s`" % rec["proof"]["strip"],
        "",
        "Gate: `%s`" % rec["gate"],
        "",
    ]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print(rec["gate"])
    print("COVERED before=%.3f after=%.3f delta=%+.3f" % (rec["covered_before_s"], covered, covered - rec["covered_before_s"]))
    for a, b in gaps:
        print("HOLE %.3f-%.3f (%.3f)" % (a, b, b - a))
    if over:
        print("CLIP-OVERRUN %s" % over)
    print("PROOF %s %dB %ss" % (rec["proof"]["out"], pbytes, pinfo["sec"]))
    print("STRIP %s %dB" % (rec["proof"]["strip"], os.path.getsize(PROOF_STRIP)))
    if not proof_ok or over:
        sys.exit(4)


if __name__ == "__main__":
    main()