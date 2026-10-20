# -*- coding: ascii -*-
# xq_packb_assembly_v2_c2156.py - PACK-B frame-exact assembly pass.
#
# Why: v1 (C2155) cut the timeline in seconds through the concat demuxer, so
# every outpoint was rounded up to a whole frame and the 41 joins accumulated
# ~5 frames of drift (238.083s container instead of 238.000s). A cut whose
# boundaries move is not reviewable by the director seat: the lyric beats and
# the card timing both shift.
#
# This pass works in frames from end to end:
#   - every slot boundary is snapped with round(t * 24), so it is an integer
#     frame and cannot drift;
#   - every segment is rendered with trim=end_frame=N, so the segment length is
#     N frames exactly, not "N seconds rounded by the encoder";
#   - the 41 segments are joined in one filter graph (concat filter) instead of
#     the demuxer, so no per-input seek rounding can touch the join.
#
# Allocation decisions are the ones v1 proved out and are kept unchanged:
#   1) 172-186s astronomy montage cycles S5-26/27/28 (shotlist sanctions REUSE);
#      in frames each take is 56f, so 336f fills the slot with six whole takes.
#   2) S1-08 is 141f against a 144f slot; S1-07 lends 3f of its 34f surplus.
#   3) S2-11/12/13 share a 120f slot and are cut 40/40/40.
#   4) S3-18 starts at 95.6s but S2-16 runs to 96.0s; the earlier shot is cut at
#      the boundary so the timeline is never double-covered.
#
# Zero GPU. Read-only on the clips. PASS gate: FRAMES-END ok=1 frames=5712/5712.
#
# Outputs:
#   cph4/fleet/mv-album-001-jay/xq-PACKB-ASSEMBLY-INDEX-v2-c2156.json / .md
#   cph4/fleet/mv-album-001-jay/xq-PACKB-ASSEMBLY-RECEIPT-c2156.json
#   media/mv-album-001-jay/assembly-packB/XQ-PACKB-ASSEMBLY-v2-c2156.mp4
#   media/mv-album-001-jay/assembly-packB/XQ-PACKB-ASSEMBLY-c2156-strip.jpg

import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
EDL = os.path.join(OUTDIR, "xq-PACKB-EDL-v5-c2154.json")
INDEX_A = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json")
SONG = os.path.join(OUTDIR, "audio", "\u5468\u6770\u4f26 - \u661f\u6674.mp3")
OUT_JSON = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v2-c2156.json")
OUT_MD = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v2-c2156.md")
OUT_RECEIPT = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-RECEIPT-c2156.json")
OUT_MEDIA = os.path.join(MEDIA, "assembly-packB")
OUT_MP4 = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v2-c2156.mp4")
OUT_NOMUX = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v2-c2156.video-only.mp4")
OUT_STRIP = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-c2156-strip.jpg")
FILTER_SCRIPT = os.path.join(OUT_MEDIA, "filter-c2156.txt")
LOG_RUN = os.path.join(MEDIA, "log-packb-assembly-c2156.run.txt")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

BATCH = "C2156"
FPS = 24
TIMELINE = 238.0
TIMELINE_FRAMES = 5712          # 238.0s * 24
MONTAGE = ("S5-26", "S5-27", "S5-28")
BUMP = "S1-07"                  # lends 3 frames to S1-08
BUMP_FRAMES = 3
B_FILES = {
    "S1-08": "clips-local-768/XQ_B-S1-08.mp4",
    "S3-18cont": "clips-local-768/XQ_B-S3-18cont.mp4",
    "S3-21": "clips-local-768/XQ_B-S3-21.mp4",
    "S5-31": "clips-local-768/XQ_B-S5-31.mp4",
}


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


def fr(sec):
    """Snap a timeline second to the nearest whole frame."""
    return int(round(float(sec) * FPS))


def main():
    if not os.path.isdir(OUT_MEDIA):
        os.makedirs(OUT_MEDIA)

    with open(EDL, encoding="utf-8-sig") as f:
        edl = json.load(f)
    with open(INDEX_A, encoding="utf-8-sig") as f:
        idx = json.load(f)
    by_unit = {c["unit"]: c for c in idx["clips"]}

    def clip_of(shot):
        if shot in B_FILES:
            rel = B_FILES[shot]
            return os.path.join(MEDIA, rel.replace("/", os.sep)), rel
        row = by_unit.get("XQ_" + shot)
        if not row:
            return None, None
        return os.path.join(MEDIA, row["file"].replace("/", os.sep)), row["file"]

    # 1) group same-slot rows (variants) but keep authored order
    slots = []
    for s in sorted(edl["shots"], key=lambda r: (float(r["t0"]), float(r["t1"]), r["shot"])):
        key = (round(float(s["t0"]), 3), round(float(s["t1"]), 3))
        if slots and slots[-1]["slot"] == key:
            slots[-1]["shots"].append(s["shot"])
        else:
            slots.append({"slot": key, "shots": [s["shot"]]})

    # 2) allocate takes to slots in whole frames
    rows = []
    cursor = 0
    for sl in slots:
        t0, t1 = sl["slot"]
        start = max(fr(t0), cursor)
        end = fr(t1)
        need = end - start
        if need <= 0:
            continue
        shots = sl["shots"]

        if len(shots) > 1 and shots[0] in MONTAGE:
            infos = []
            for shot in shots:
                path, rel = clip_of(shot)
                infos.append((shot, rel, probe(path)["frames"]))
            shortest = min(i[2] for i in infos)
            n = max(1, -(-need // shortest))
            base = need // n
            rem = need - base * n
            for k in range(n):
                shot, rel, src_frames = infos[k % len(infos)]
                take = base + (1 if k < rem else 0)
                rows.append({"shot": shot, "file": rel, "src_frames": src_frames,
                             "in_frame": 0, "frames": take,
                             "slot": [round(t0, 3), round(t1, 3)]})
                start += take
            cursor = start
            continue

        # single take, or a variant chain sharing one slot
        if len(shots) > 1:
            base = need // len(shots)
            rem = need - base * len(shots)
            parts = [(shots[k], base + (1 if k < rem else 0)) for k in range(len(shots))]
        else:
            parts = [(shots[0], need)]

        for shot, want in parts:
            path, rel = clip_of(shot)
            if not path or not os.path.exists(path):
                logline("MISSING %s" % shot)
                sys.exit(3)
            info = probe(path)
            take = min(want, info["frames"])
            if shot == BUMP and len(shots) == 1:
                take = min(want + BUMP_FRAMES, info["frames"])
            if take < want:
                logline("SHORT %s frames=%d want=%d deficit=%d" %
                        (shot, take, want, want - take))
            rows.append({"shot": shot, "file": rel, "src_frames": info["frames"],
                         "in_frame": 0, "frames": take, "want_frames": want,
                         "deficit_frames": max(0, want - take),
                         "slot": [round(t0, 3), round(t1, 3)]})
            start += take
        # the cursor is where the picture actually ends, not where the slot was
        # meant to end: S1-07 lends S1-08 3f, so S1-08's slot is 3f shorter and
        # must not be booked as a shortfall.
        cursor = start

    # 3) timeline in frames, drift measured against the true 238.000s
    cur = 0
    for r in rows:
        r["timeline_frames"] = [cur, cur + r["frames"]]
        r["timeline"] = [round(cur / FPS, 4), round((cur + r["frames"]) / FPS, 4)]
        r["cut_span"] = round(r["frames"] / FPS, 4)
        cur += r["frames"]
    cut_frames = cur
    drift_frames = TIMELINE_FRAMES - cut_frames
    deficits = [r for r in rows if r.get("deficit_frames")]

    # 4) one filter graph: trim every input to its exact frame count, then concat
    lines = []
    for i, r in enumerate(rows):
        lines.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,"
                     "scale=1344:768:flags=lanczos,setsar=1,fps=%d,format=yuv420p[v%d]"
                     % (i, r["in_frame"], r["in_frame"] + r["frames"], FPS, i))
    lines.append("%sconcat=n=%d:v=1:a=0[vout]" %
                 ("".join("[v%d]" % i for i in range(len(rows))), len(rows)))
    with open(FILTER_SCRIPT, "w", encoding="ascii", errors="replace", newline="\n") as f:
        f.write(";\n".join(lines) + "\n")

    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"]
    for r in rows:
        cmd += ["-i", os.path.join(MEDIA, r["file"].replace("/", os.sep))]
    cmd += ["-filter_complex_script", FILTER_SCRIPT, "-map", "[vout]", "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-movflags", "+faststart", OUT_NOMUX]
    logline("ASSEMBLY-START units=%d frames=%d drift=%d" %
            (len(rows), cut_frames, drift_frames))
    subprocess.check_call(cmd)

    if not os.path.exists(SONG):
        logline("SONG-MISSING %s" % SONG)
        sys.exit(5)
    dur = round(min(cut_frames / FPS, TIMELINE), 3)
    fade_out = max(dur - 1.6, 0.1)
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", OUT_NOMUX, "-i", SONG,
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-af", "afade=t=in:st=0:d=0.6,afade=t=out:st=%.3f:d=1.6" % fade_out,
           "-t", "%.3f" % dur, "-movflags", "+faststart", OUT_MP4]
    subprocess.check_call(cmd)

    info = probe(OUT_MP4)
    out_bytes = os.path.getsize(OUT_MP4)
    frames_ok = 1 if info["frames"] == TIMELINE_FRAMES else 0
    drift_ok = 1 if drift_frames == 0 else 0
    dur_ok = 1 if abs(info["sec"] - TIMELINE) <= 0.05 else 0

    # 5) index + md
    v = {
        "schema": "xq-packb-assembly-index/v2",
        "batch": BATCH,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "project": "mv0001-xingqing",
        "edl": "v5",
        "why": ("v1 cut in seconds and the concat demuxer rounded every outpoint up to a "
                "frame, so 41 joins accumulated ~5 frames of drift. This pass snaps every "
                "boundary to the frame grid and trims every segment to an exact frame "
                "count, then joins them in one filter graph."),
        "fps": FPS,
        "timeline_seconds": TIMELINE,
        "timeline_frames": TIMELINE_FRAMES,
        "slots": len(slots),
        "units": len(rows),
        "cut_frames": cut_frames,
        "cut_seconds": round(cut_frames / FPS, 4),
        "drift_frames": drift_frames,
        "deficit_frames": sum(r.get("deficit_frames", 0) for r in rows),
        "montage_fill": {
            "slot": [172.0, 186.0],
            "takes": list(MONTAGE),
            "rule": "cycle the three takes (shotlist sanctions REUSE for this window)",
            "segments": sum(1 for r in rows if r["shot"] in MONTAGE),
            "frames_per_take": 56,
        },
        "borrow": {"from": BUMP, "to": "S1-08", "frames": BUMP_FRAMES,
                   "why": "S1-08 is 141f against a 144f slot; S1-07 has 34f surplus"},
        "clips": rows,
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(v, f, ensure_ascii=False, indent=1)
        f.write("\n")

    md = [
        "# Xingqing PACK-B - assembly index v2 (%s)" % BATCH,
        "",
        "> Built %s. Frame-exact cut of the whole film on EDL v5." % v["ts"],
        "",
        "- slots: **%d** / units: **%d**" % (v["slots"], v["units"]),
        "- cut: **%d frames = %.3fs** of %d frames (238.000s) / drift: **%d frames**" %
        (cut_frames, cut_frames / FPS, TIMELINE_FRAMES, drift_frames),
        "",
        "## What changed from v1",
        "- every slot boundary is snapped with round(t*24); no boundary can drift.",
        "- every segment is rendered with trim=end_frame=N, so its length is N frames, "
        "not a rounded second value.",
        "- the 41 segments are joined with the concat filter in one graph, so the outer "
        "container no longer lands on 238.083s.",
        "",
        "## Cut table (frames are authoritative)",
        "| # | shot | src frames | cut frames | timeline (s) | file |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        md.append("| %d | %s | %d | %d | %.3f-%.3f | %s |" %
                  (i, r["shot"], r["src_frames"], r["frames"],
                   r["timeline"][0], r["timeline"][1], r["file"]))
    md += ["", "## Honest notes",
           "- all picture is real takes; each span is cut from its source clip only.",
           "- one scale pass and one encode for the whole cut; straight cuts only.",
           "- the 172-186s window is six whole 56f takes of the sanctioned montage cycle."]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")

    # 6) QC strip at the same six marks as v1 so the two cuts compare directly
    marks = [0.8, 39.0, 63.0, 106.0, 178.0, 234.0]
    tmp = []
    for i, t in enumerate(marks):
        p = os.path.join(OUT_MEDIA, "_stripf%d.png" % i)
        subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                               "-ss", "%.3f" % t, "-i", OUT_MP4, "-frames:v", "1", p])
        tmp.append(p)
    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-i", tmp[0], "-i", tmp[1], "-i", tmp[2], "-i", tmp[3],
                           "-i", tmp[4], "-i", tmp[5],
                           "-filter_complex",
                           "[0:v]scale=480:-1[a];[1:v]scale=480:-1[b];[2:v]scale=480:-1[c];"
                           "[3:v]scale=480:-1[d];[4:v]scale=480:-1[e];[5:v]scale=480:-1[f];"
                           "[a][b][c]hstack=inputs=3[t];[d][e][f]hstack=inputs=3[u];"
                           "[t][u]vstack=inputs=2",
                           "-q:v", "2", OUT_STRIP])
    for p in tmp:
        if os.path.exists(p):
            os.remove(p)

    receipt = {
        "batch": BATCH,
        "ts": v["ts"],
        "units": len(rows),
        "cut_frames": cut_frames,
        "timeline_frames": TIMELINE_FRAMES,
        "drift_frames": drift_frames,
        "out_frames": info["frames"],
        "out_seconds": info["sec"],
        "out": os.path.relpath(OUT_MP4, REPO).replace("\\", "/"),
        "out_bytes": out_bytes,
        "song": os.path.relpath(SONG, REPO).replace("\\", "/"),
        "index": os.path.relpath(OUT_JSON, REPO).replace("\\", "/"),
        "strip": os.path.relpath(OUT_STRIP, REPO).replace("\\", "/"),
        "strip_marks": marks,
        "previous_cut": "media/mv-album-001-jay/assembly-packB/XQ-PACKB-ASSEMBLY-v1-c2155.mp4",
        "previous_seconds": 238.083,
        "notes": [
            "frame-exact cut; the container now matches the timeline",
            "montage slot filled by sanctioned reuse of the three astronomy takes",
            "no freeze, no slow-mo, no filler inserted",
        ],
    }
    with open(OUT_RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
        f.write("\n")

    ok = 1 if (frames_ok and drift_ok and dur_ok and out_bytes > 3000000) else 0
    logline("FRAMES-END ok=%d frames=%d/%d drift=%d out=%.3fs bytes=%d deficits=%d" %
            (ok, info["frames"], TIMELINE_FRAMES, drift_frames, info["sec"],
             out_bytes, len(deficits)))
    logline("OUT %s %dB %ss" % (receipt["out"], out_bytes, info["sec"]))
    logline("STRIP %s %dB" % (receipt["strip"], os.path.getsize(OUT_STRIP)))
    if not ok:
        sys.exit(4)


if __name__ == "__main__":
    main()