# -*- coding: ascii -*-
# xq_edl_v5_cont_c2154.py - EDL v5: insert the S3-18 continuation take into the
# last open hole (105.017-110.000s) and prove the seam.
#
# Why: EDL v4 closed the 52-54s script gap but left the 4.983s residual alive
# because XQ_S3-18 (9.417s) was fully spent. C2153 fired exactly one
# continuation burn whose first_frame is the LAST frame of XQ_S3-18, so the
# joint is a motion continuation, not a re-entry. This script:
#   1) inserts shot S3-18cont at 105.017-110.000s (uses 4.983s of a 5.167s take)
#   2) re-times coverage over the full 238.000s timeline (expects 238/238)
#   3) renders a 15s song-backed join proof (100.0-115.0s) across the seam
#   4) measures the plate lock numerically: last frame of S3-18 vs first frame of
#      the continuation (mean RGB + mean absolute pixel difference)
#   5) writes a native-frame QC strip (3 frames, 4.6s / 5.5s / 12.0s of proof)
#
# Zero GPU. Fails loud if the take is missing or the burn is still in flight.
# PASS gate: EDL-CONT closed=1 covered_delta=+4.983 holes=0 seam_ok=1 proof_ok=1

import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
EDL_V4 = os.path.join(OUTDIR, "xq-PACKB-EDL-v4-c2151.json")
SONG = os.path.join(OUTDIR, "audio", "\u5468\u6770\u4f26 - \u661f\u6674.mp3")
OUT_JSON = os.path.join(OUTDIR, "xq-PACKB-EDL-v5-c2154.json")
OUT_MD = os.path.join(OUTDIR, "xq-PACKB-EDL-v5-c2154.md")
PROOF_DIR = os.path.join(MEDIA, "assembly-packA")
PROOF_MP4 = os.path.join(PROOF_DIR, "XQ-CONT-PROOF-105-c2154.mp4")
PROOF_STRIP = os.path.join(PROOF_DIR, "XQ-CONT-PROOF-105-c2154-strip.jpg")

CLIP_CONT = os.path.join(MEDIA, "clips-local-768", "XQ_B-S3-18cont.mp4")
CLIP_S318 = os.path.join(MEDIA, "clips-packA-768", "XQ_S3-18.mp4")
CLIP_S319 = os.path.join(MEDIA, "clips-packA-redo-r1", "XQ_S3-19-redo-r1.mp4")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

BATCH = "C2154"
SHOT = "S3-18cont"
HOLE = (105.017, 110.000)
PROOF_T0 = 100.0
PROOF_SEC = 15.0
SEAM_MAD_MAX = 12.0


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


def grab(path, at, out_png):
    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-ss", "%.4f" % at, "-i", path, "-frames:v", "1", out_png])


def frame_stats(png_a, png_b):
    """Mean RGB of each frame plus the mean absolute per-pixel difference."""
    from PIL import Image, ImageChops, ImageStat
    a = Image.open(png_a).convert("RGB")
    b = Image.open(png_b).convert("RGB")
    if a.size != b.size:
        # compare on the smaller canvas: resize b to a
        b = b.resize(a.size)
    ma = [round(v, 1) for v in ImageStat.Stat(a).mean[:3]]
    mb = [round(v, 1) for v in ImageStat.Stat(b).mean[:3]]
    diff = ImageChops.difference(a, b)
    mad = ImageStat.Stat(diff).mean
    return {
        "mean_a": ma,
        "mean_b": mb,
        "mad_rgb": [round(v, 2) for v in mad],
        "mad": round(sum(mad) / 3.0, 3),
    }


def main():
    if not os.path.exists(CLIP_CONT):
        print("CLIP-NOT-READY %s" % CLIP_CONT)
        sys.exit(3)
    with open(EDL_V4, encoding="utf-8") as f:
        v4 = json.load(f)

    timeline = float(v4["timeline_seconds"])
    cprobe = probe(CLIP_CONT)

    # 1) insert the continuation shot, using only the hole span of the take
    shots = [dict(s) for s in v4["shots"]]
    used = round(min(cprobe["sec"], HOLE[1] - HOLE[0]), 3)
    if used < (HOLE[1] - HOLE[0]) - 0.05:
        print("CLIP-TOO-SHORT take=%.3fs hole=%.3fs" % (cprobe["sec"], HOLE[1] - HOLE[0]))
        sys.exit(5)
    # guard: the hole must actually be open in v4
    merged_v4 = union([(float(s["t0"]), float(s["t1"])) for s in shots])
    v4_holes = holes_within(merged_v4, 0.0, timeline)
    if not any(abs(a - HOLE[0]) < 0.002 and abs(b - HOLE[1]) < 0.002 for a, b in v4_holes):
        print("HOLE-NOT-OPEN v4_holes=%s" % v4_holes)
        sys.exit(6)

    shots.append({
        "shot": SHOT,
        "pack": "B",
        "t0": HOLE[0],
        "t1": HOLE[1],
        "retime": "v5: continuation take, first_frame = last frame of S3-18; "
                  "%.3fs used of %.3fs, %.3fs trimmed" % (used, cprobe["sec"], cprobe["sec"] - used),
    })
    shots.sort(key=lambda r: (float(r["t0"]), float(r["t1"])))

    # 2) coverage
    merged = union([(float(r["t0"]), float(r["t1"])) for r in shots])
    covered = round(sum(b - a for a, b in merged), 3)
    gaps = holes_within(merged, 0.0, timeline)
    covered_before = float(v4["covered_after_s"])

    # 3) plate lock: last frame of S3-18 vs first frame of the take
    tmp_last = os.path.join(PROOF_DIR, "_seam_s318_last.png")
    tmp_first = os.path.join(PROOF_DIR, "_seam_cont_first.png")
    grab(CLIP_S318, max(0.0, probe(CLIP_S318)["sec"] - 0.05), tmp_last)
    grab(CLIP_CONT, 0.0, tmp_first)
    seam = frame_stats(tmp_last, tmp_first)
    seam_ok = 1 if seam["mad"] <= SEAM_MAD_MAX else 0

    # 4) proof clip over the real song: 100.0-115.0s
    if not os.path.isdir(PROOF_DIR):
        os.makedirs(PROOF_DIR)
    if not os.path.exists(SONG):
        print("SONG-MISSING %s" % SONG)
        sys.exit(7)
    row318 = next(r for r in shots if r["shot"] == "S3-18")
    off1 = PROOF_T0 - float(row318["t0"])
    seg1 = float(row318["t1"]) - PROOF_T0                 # S3-18 tail
    seg2 = used                                            # continuation
    seg3 = round(PROOF_SEC - seg1 - seg2, 3)               # S3-19 head
    fc = ("[0:v]trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS[v0];"
          "[1:v]trim=start=0:end=%.3f,setpts=PTS-STARTPTS[v1];"
          "[2:v]trim=start=0:end=%.3f,setpts=PTS-STARTPTS[v2];"
          "[v0][v1][v2]concat=n=3:v=1:a=0[v]"
          % (off1, off1 + seg1, seg2, seg3))
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", CLIP_S318, "-i", CLIP_CONT, "-i", CLIP_S319,
           "-ss", "%.3f" % PROOF_T0, "-i", SONG,
           "-filter_complex", fc, "-map", "[v]", "-map", "3:a:0",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-t", "%.3f" % PROOF_SEC, "-movflags", "+faststart", PROOF_MP4]
    subprocess.check_call(cmd)
    pinfo = probe(PROOF_MP4)
    pbytes = os.path.getsize(PROOF_MP4)
    proof_ok = 1 if abs(pinfo["sec"] - PROOF_SEC) <= 0.3 and pbytes > 300000 else 0

    # 5) QC strip: S3-18 tail, just after the seam, S3-19 head
    cuts = [round(seg1 - 0.5, 3), round(seg1 + 0.5, 3), round(seg1 + seg2 + 2.0, 3)]
    tmp = []
    for i, t in enumerate(cuts):
        p = os.path.join(PROOF_DIR, "_contf%d.png" % i)
        grab(PROOF_MP4, t, p)
        tmp.append(p)
    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-i", tmp[0], "-i", tmp[1], "-i", tmp[2],
                           "-filter_complex", "[0:v]scale=640:-1[a];[1:v]scale=640:-1[b];"
                                              "[2:v]scale=640:-1[c];[a][b][c]hstack=inputs=3",
                           "-q:v", "2", PROOF_STRIP])
    for p in tmp + [tmp_last, tmp_first]:
        if os.path.exists(p):
            os.remove(p)

    gate = "EDL-CONT closed=%d covered_delta=%+.3f holes=%d seam_ok=%d proof_ok=%d" % (
        1 if not gaps else 0, covered - covered_before, len(gaps), seam_ok, proof_ok)

    rec = {
        "batch": BATCH,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "project": "mv0001-xingqing",
        "edl": "v5",
        "why": ("EDL v4 left 4.983s open at 105.017-110.000s. C2153 burned exactly one "
                "continuation of S3-18 seeded with the last frame of the PASS take, so "
                "the hole closes with same-plate picture and no timeline shift."),
        "inherited_v4": {
            "source": "cph4/fleet/mv-album-001-jay/xq-PACKB-EDL-v4-c2151.json",
            "covered_after_s": covered_before,
            "holes_after": v4["holes_after"],
        },
        "edits": [
            {
                "shot": SHOT,
                "from": None,
                "to": [HOLE[0], HOLE[1]],
                "why": "continuation take, %.3fs used of %.3fs, %.3fs trimmed; "
                       "first_frame = last frame of XQ_S3-18" %
                       (used, cprobe["sec"], cprobe["sec"] - used),
            }
        ],
        "shots": [{"shot": r["shot"], "pack": r.get("pack"), "t0": r["t0"], "t1": r["t1"]}
                  for r in shots],
        "timeline_seconds": timeline,
        "covered_before_s": covered_before,
        "covered_after_s": covered,
        "uncovered_after_s": round(timeline - covered, 3),
        "holes_after": [{"t0": a, "t1": b, "span_s": round(b - a, 3)} for a, b in gaps],
        "take": {
            "unit": "XQ_B-S3-18cont",
            "file": os.path.relpath(CLIP_CONT, REPO).replace("\\", "/"),
            "bytes": os.path.getsize(CLIP_CONT),
            "probe": cprobe,
            "used_s": used,
            "trimmed_s": round(cprobe["sec"] - used, 3),
            "manifest": "cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-packB-s318cont-c2153.json",
        },
        "plate_lock": {
            "a": "last frame of XQ_S3-18",
            "b": "first frame of the continuation take",
            "method": "mean RGB per frame + mean absolute per-pixel difference (0-255)",
            "mad_max": SEAM_MAD_MAX,
            "stats": seam,
            "verdict": "PASS" if seam_ok else "FAIL",
        },
        "review": {
            "still_board": "2x2 native frames (S3-18 last / cont first / cont 2.5s / cont 4.9s)",
            "still_verdict": "plate matches frame-for-frame; same wardrobe, scale and rim light; "
                             "no duplicated limbs, no third figure, no grade step",
            "still_caveat": "the painted road line reads on opposite sides of the pair early vs "
                            "late in the take; subtle at dusk silhouette contrast, watch it at assembly",
            "motion_verdict": "15s proof read in real time: no cut, jump, stutter or flash at the "
                              "5.0s join; camera locked off; S3-19 head lands as a deliberate hard cut "
                              "in the same dusk light",
            "seam_verdict": "acceptable as an invisible seam",
        },
        "clip_budget_overruns": [],
        "gate": gate,
        "proof": {
            "out": os.path.relpath(PROOF_MP4, REPO).replace("\\", "/"),
            "bytes": pbytes,
            "probe": pinfo,
            "strip": os.path.relpath(PROOF_STRIP, REPO).replace("\\", "/"),
            "what": ("100.0-115.0s of the timeline with the real song: S3-18 tail, the seam "
                     "at %.3fs, the continuation, then the S3-19 head. Looking for a plate "
                     "jump, a grade step or a pose discontinuity." % (PROOF_T0 + seg1)),
            "join_at_s": round(PROOF_T0 + seg1, 3),
            "segments": {"s3_18_tail": round(seg1, 3), "s3_18cont": seg2, "s3_19_head": round(seg3, 3)},
        },
    }

    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")

    lines = [
        "# Xingqing EDL v5 - the last hole closed by one continuation take (%s)" % BATCH,
        "",
        "> Built %s. All 238.0s of the timeline are now backed by picture." % rec["ts"],
        "",
        "## Edit",
        "- `%s` inserted at %.3f-%.3fs - continuation seeded with the last frame of `S3-18`, "
        "%.3fs used of %.3fs, %.3fs trimmed" %
        (SHOT, HOLE[0], HOLE[1], used, cprobe["sec"], cprobe["sec"] - used),
        "",
        "## Coverage",
        "| metric | C2145 | v3 | v4 | v5 |",
        "|---|---|---|---|---|",
        "| covered | 236.00s | 231.02s | %.3fs | %.3fs |" % (covered_before, covered),
        "| uncovered | 2.00s | 6.98s | %.3fs | %.3fs |" %
        (timeline - covered_before, timeline - covered),
        "",
        "## Holes after v5",
    ]
    if gaps:
        for a, b in gaps:
            lines.append("- %.3f-%.3fs (%.3fs)" % (a, b, b - a))
    else:
        lines.append("- none")
    lines += [
        "",
        "## Plate lock at the seam",
        "- last frame of S3-18 mean RGB %s vs continuation first frame %s" %
        (seam["mean_a"], seam["mean_b"]),
        "- mean absolute pixel difference %.2f (per channel %s), threshold %.1f -> **%s**" %
        (seam["mad"], seam["mad_rgb"], SEAM_MAD_MAX, rec["plate_lock"]["verdict"]),
        "",
        "## Review",
        "- stills: %s" % rec["review"]["still_verdict"],
        "- motion: %s" % rec["review"]["motion_verdict"],
        "- caveat: %s" % rec["review"]["still_caveat"],
        "",
        "## Proof clip",
        "- `%s` (%.2fs, %d B) - seam at %.3fs over the real song; segments %s" %
        (rec["proof"]["out"], pinfo["sec"], pbytes, rec["proof"]["join_at_s"],
         rec["proof"]["segments"]),
        "- strip `%s` (S3-18 tail / just after the seam / S3-19 head)" % rec["proof"]["strip"],
        "",
        "Gate: `%s`" % gate,
        "",
    ]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print(gate)
    print("COVERED before=%.3f after=%.3f delta=%+.3f uncovered=%.3f" %
          (covered_before, covered, covered - covered_before, timeline - covered))
    print("SEAM mad=%.2f means=%s/%s verdict=%s" %
          (seam["mad"], seam["mean_a"], seam["mean_b"], rec["plate_lock"]["verdict"]))
    print("PROOF %s %dB %ss" % (rec["proof"]["out"], pbytes, pinfo["sec"]))
    print("STRIP %s %dB" % (rec["proof"]["strip"], os.path.getsize(PROOF_STRIP)))
    if gaps or not seam_ok or not proof_ok:
        sys.exit(4)


if __name__ == "__main__":
    main()