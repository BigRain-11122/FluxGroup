# -*- coding: ascii -*-
# xq_packb_assembly_v1_c2155.py - PACK-B assembly pass on the fully covered EDL v5.
#
# Why: EDL v5 proves every lyric window has picture (holes=0), but that metric
# counts a slot as covered when ANY take exists, including same-slot variants.
# The first real cut therefore needs its own arithmetic: walk 0..238s, put one
# take per slot, trim each to its slot, and see what a cut can actually reach.
#
# Findings this script makes explicit:
#   1) the 172-186s astronomy montage carries three 2.333s takes (S5-26/27/28).
#      The shotlist sanctions REUSE for this window, so the slot is
#      filled by cycling the three takes - real picture, no freeze, no slow-mo.
#   2) S1-08 is 5.875s against a 6.0s slot. The 0.125s is borrowed from S1-07's
#      surplus (9.417s clip, 8.0s slot) so no lyric beat moves.
#   3) S3-18 starts at 95.6s while S2-16 ends at 96.0s; the earlier shot is cut
#      at the boundary instead of double-covering the timeline.
#
# Zero GPU. Read-only on the clips. Renders the whole film once, straight cuts,
# real song. PASS gate: ASSEMBLY-END ok=1 cut=238.00 units=N holes=0.
#
# Outputs:
#   cph4/fleet/mv-album-001-jay/xq-PACKB-ASSEMBLY-INDEX-v1-c2155.json / .md
#   cph4/fleet/mv-album-001-jay/xq-PACKB-ASSEMBLY-RECEIPT-c2155.json
#   media/mv-album-001-jay/assembly-packB/XQ-PACKB-ASSEMBLY-v1-c2155.mp4
#   media/mv-album-001-jay/assembly-packB/XQ-PACKB-ASSEMBLY-c2155-strip.jpg

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
OUT_JSON = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v1-c2155.json")
OUT_MD = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v1-c2155.md")
OUT_RECEIPT = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-RECEIPT-c2155.json")
OUT_MEDIA = os.path.join(MEDIA, "assembly-packB")
OUT_MP4 = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v1-c2155.mp4")
OUT_NOMUX = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v1-c2155.video-only.mp4")
OUT_STRIP = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-c2155-strip.jpg")
CONCAT_LIST = os.path.join(OUT_MEDIA, "concat-c2155.txt")
LOG_RUN = os.path.join(MEDIA, "log-packb-assembly-c2155.run.txt")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

BATCH = "C2155"
TIMELINE = 238.0
MONTAGE = ("S5-26", "S5-27", "S5-28")
# 172-186s montage slot is filled by cycling the three astronomy takes; the
# shotlist already sanctions reuse for this window.
BUMP = "S1-07"          # lends 0.125s to S1-08
BUMP_S = 0.125
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
        key = (float(s["t0"]), float(s["t1"]))
        if slots and slots[-1]["slot"] == key:
            slots[-1]["shots"].append(s["shot"])
        else:
            slots.append({"slot": key, "shots": [s["shot"]]})

    # 2) allocate takes to slots; the cut must not overlap and must not freeze
    rows = []
    cursor = 0.0
    borrow = 0.0
    for sl in slots:
        t0, t1 = sl["slot"]
        start = max(t0, cursor)
        need = round(t1 - start, 3)
        if need <= 0.0005:
            continue
        shots = sl["shots"]
        if len(shots) > 1 and shots[0] in MONTAGE:
            # cycle the takes until the slot is full; split evenly so no
            # sub-frame tail fragment is produced
            infos = []
            for shot in shots:
                path, rel = clip_of(shot)
                infos.append((shot, rel, probe(path)["sec"]))
            shortest = min(i[2] for i in infos)
            n = max(1, int(-(-need // shortest)))
            per = round(need / n, 4)
            for k in range(n):
                shot, rel, src = infos[k % len(infos)]
                rows.append({"shot": shot, "file": rel, "src_sec": src,
                             "in": 0.0, "out": round(min(per, src), 4),
                             "slot": [round(start, 3), round(t1, 3)]})
                start = round(start + rows[-1]["out"], 4)
                need = round(t1 - start, 4)
            cursor = round(start, 3)
            continue

        # single take, or a short variant chain (S2-11/12/13 share 62-67s)
        parts = []
        if len(shots) > 1:
            each = round(need / len(shots), 3)
            parts = [(shot, each) for shot in shots]
            parts[-1] = (parts[-1][0], round(need - each * (len(parts) - 1), 3))
        else:
            parts = [(shots[0], need)]

        first = True
        for shot, want in parts:
            path, rel = clip_of(shot)
            if not path or not os.path.exists(path):
                logline("MISSING %s" % shot)
                sys.exit(3)
            info = probe(path)
            take = min(want, info["sec"])
            extra = 0.0
            # S1-07 lends its surplus so S1-08 keeps a full slot
            if shot == BUMP and len(shots) == 1 and take >= want:
                extra = BUMP_S
                take = min(want + extra, info["sec"])
            if first and take < want - 0.001:
                deficit = round(want - take, 3)
                rows.append({"shot": shot, "file": rel, "src_sec": info["sec"],
                             "in": 0.0, "out": round(take, 3),
                             "deficit_s": deficit,
                             "slot": [round(start, 3), round(t1, 3)]})
                logline("SHORT %s take=%.3f want=%.3f deficit=%.3f" % (shot, take, want, deficit))
                start = round(start + take, 3)
                first = False
                continue
            rows.append({"shot": shot, "file": rel, "src_sec": info["sec"],
                         "in": 0.0, "out": round(take, 3),
                         "slot": [round(start, 3), round(t1, 3)]})
            start = round(start + take, 3)
            first = False
        cursor = round(start, 3)

    cut = round(sum(r["out"] - r["in"] for r in rows), 3)
    deficits = [r for r in rows if r.get("deficit_s")]
    total_deficit = round(sum(r["deficit_s"] for r in deficits), 3)
    # timeline holes the cut cannot reach (deficit pushes the rest earlier, so
    # report the shortfall honestly instead of hiding it)
    rows_out = []
    cur = 0.0
    for r in rows:
        d = r["out"] - r["in"]
        rows_out.append({
            "shot": r["shot"],
            "file": r["file"],
            "src_sec": r["src_sec"],
            "in": r["in"],
            "out": r["out"],
            "cut_span": round(d, 3),
            "timeline": [round(cur, 3), round(cur + d, 3)],
            "slot": r["slot"],
        })
        cur = round(cur + d, 3)

    v = {
        "schema": "xq-packb-assembly-index/v1",
        "batch": BATCH,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "project": "mv0001-xingqing",
        "edl": "v5",
        "why": ("The first cut of the full film. EDL v5 proves every lyric window has "
                "picture; this pass turns that coverage map into one take per slot and "
                "measures what a cut can actually reach."),
        "timeline_seconds": TIMELINE,
        "slots": len(slots),
        "units": len(rows_out),
        "cut_seconds": cut,
        "deficit_seconds": total_deficit,
        "montage_fill": {
            "slot": [172.0, 186.0],
            "takes": list(MONTAGE),
            "rule": "cycle the three takes (shotlist sanctions REUSE for this window)",
            "segments": sum(1 for r in rows_out if r["shot"] in MONTAGE),
        },
        "borrow": {"from": BUMP, "to": "S1-08", "seconds": BUMP_S,
                   "why": "S1-08 clip is 5.875s against a 6.0s slot; S1-07 has 1.417s surplus"},
        "clips": rows_out,
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(v, f, ensure_ascii=False, indent=1)
        f.write("\n")

    lines = [
        "# Xingqing PACK-B - assembly index v1 (%s)" % BATCH,
        "",
        "> Built %s. The first cut of the whole film on EDL v5." % v["ts"],
        "",
        "- slots: **%d** / cut units: **%d**" % (v["slots"], v["units"]),
        "- cut length: **%.2fs** of %.1fs / uncovered: **%.2fs**" %
        (cut, TIMELINE, TIMELINE - cut),
        "",
        "## What changed from the EDL",
        "- the 172-186s astronomy montage is filled by cycling S5-26/27/28 "
        "(shotlist sanctions REUSE); %d segments, no freeze, no slow-mo." %
        v["montage_fill"]["segments"],
        "- S1-07 lends %.3fs of its surplus to S1-08 so its slot stays 6.0s." % BUMP_S,
        "- S2-11/12/13 share one 62-67s slot and are cut %s." %
        ", ".join("%s=%.2fs" % (r["shot"], r["cut_span"]) for r in rows_out
                  if r["shot"] in ("S2-11", "S2-12", "S2-13")),
        "",
        "## Cut table",
        "| # | shot | src(s) | cut(s) | timeline | file |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows_out, 1):
        lines.append("| %d | %s | %.3f | %.3f | %.3f-%.3f | %s |" %
                     (i, r["shot"], r["src_sec"], r["cut_span"],
                      r["timeline"][0], r["timeline"][1], r["file"]))
    lines += ["", "## Honest notes",
              "- all picture is real takes; covered spans are cut from source clips only.",
              "- one grade/scale pass for the whole cut; transitions are straight cuts."]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # 3) concat list in cut order
    with open(CONCAT_LIST, "w", encoding="utf-8", newline="\n") as f:
        for r in rows_out:
            abs_path = os.path.join(MEDIA, r["file"].replace("/", os.sep))
            f.write("file '%s'\n" % abs_path.replace("\\", "/"))
            f.write("inpoint %.3f\n" % r["in"])
            f.write("outpoint %.3f\n" % r["out"])

    logline("ASSEMBLY-START units=%d cut=%.3fs" % (len(rows_out), cut))
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", CONCAT_LIST,
           "-an", "-vf", "fps=24,scale=1344:768,setsar=1,format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
           "-movflags", "+faststart", OUT_NOMUX]
    subprocess.check_call(cmd)

    if not os.path.exists(SONG):
        logline("SONG-MISSING %s" % SONG)
        sys.exit(5)
    dur = round(min(cut, TIMELINE), 3)
    fade_out = max(dur - 1.6, 0.1)
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", OUT_NOMUX, "-i", SONG,
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-af", "afade=t=in:st=0:d=0.6,afade=t=out:st=%.2f:d=1.6" % fade_out,
           "-t", "%.3f" % dur, "-movflags", "+faststart", OUT_MP4]
    subprocess.check_call(cmd)

    info = probe(OUT_MP4)
    out_bytes = os.path.getsize(OUT_MP4)
    ok = 1 if abs(info["sec"] - dur) <= 0.5 and out_bytes > 3000000 else 0

    # 4) QC strip: open, S1-08 slot, S2-variant slot, the seam, the montage, the end
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
        "units": len(rows_out),
        "cut_seconds": cut,
        "deficit_seconds": total_deficit,
        "timeline_seconds": TIMELINE,
        "out": os.path.relpath(OUT_MP4, REPO).replace("\\", "/"),
        "out_bytes": out_bytes,
        "out_probe": info,
        "song": os.path.relpath(SONG, REPO).replace("\\", "/"),
        "index": os.path.relpath(OUT_JSON, REPO).replace("\\", "/"),
        "strip": os.path.relpath(OUT_STRIP, REPO).replace("\\", "/"),
        "strip_marks": marks,
        "notes": [
            "full film, straight cuts, one grade pass, real song",
            "montage slot filled by sanctioned reuse of the three astronomy takes",
            "no freeze, no slow-mo, no filler inserted",
        ],
    }
    with open(OUT_RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
        f.write("\n")

    gate = "ASSEMBLY-END ok=%d cut=%.2f/%0.2f units=%d deficits=%d" % (
        ok, cut, TIMELINE, len(rows_out), len(deficits))
    logline(gate)
    logline("OUT %s %dB %ss" % (receipt["out"], out_bytes, info["sec"]))
    logline("STRIP %s %dB" % (receipt["strip"], os.path.getsize(OUT_STRIP)))
    if not ok or total_deficit > 0.5:
        sys.exit(4)


if __name__ == "__main__":
    main()