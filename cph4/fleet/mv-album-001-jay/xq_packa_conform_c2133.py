# -*- coding: ascii -*-
# xq_packa_conform_c2133.py - PACK-A assembly: ordering fix + cut conform preview.
#
# Why: the C2132 index was built by walking the clip folder, so its unit order is
# filename order (F0,F5,S0..S5). The authored cut order puts the finale block
# (F5-33a/b/c, F5-34) AFTER S5, i.e. at the end of the film. Cutting in filename
# order would open the film with the finale. This script re-derives the order from
# the authored pack manifest, rewrites the index as v2, and renders a conform
# preview trimmed to the authored windows so the whole A pack can be watched.
#
# Zero GPU, read-only on the clips. PASS gate: CONFORM-END ok=1 units=33.

import hashlib
import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay")
IDX_JSON = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-c2132.json")
PACK_JSON = os.path.join(OUTDIR, "\u661f\u6674-i2v-PACK-A-v1.json")  # Xingqing i2v pack v1
F533C_MANIFEST = os.path.join(OUTDIR, "local-i2v", "run-bmc-f533c-i2v.json")
SONG = os.path.join(OUTDIR, "audio", "\u5468\u6770\u4f26 - \u661f\u6674.mp3")  # Jay - Xingqing
OUT_V2_JSON = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json")
OUT_V2_MD = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-v2-c2133.md")
OUT_RECEIPT = os.path.join(OUTDIR, "xq-PACKA-CONFORM-c2133.json")
OUTDIR_MEDIA = os.path.join(CLIPS, "assembly-packA")
OUT_MP4 = os.path.join(OUTDIR_MEDIA, "XQ-PACKA-CONFORM-v1-c2133.mp4")
OUT_MP4_NOMUX = os.path.join(OUTDIR_MEDIA, "XQ-PACKA-CONFORM-v1-c2133.video-only.mp4")
CONCAT_LIST = os.path.join(OUTDIR_MEDIA, "concat-c2133.txt")
LOG_RUN = os.path.join(CLIPS, "log-packa-conform-c2133.run.txt")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"


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


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    if not os.path.isdir(OUTDIR_MEDIA):
        os.makedirs(OUTDIR_MEDIA)

    with open(IDX_JSON, encoding="utf-8") as f:
        base = json.load(f)
    by_unit = {row["unit"]: row for row in base["clips"]}

    with open(PACK_JSON, encoding="utf-8-sig") as f:
        pack = json.load(f)
    order = [u["id"] for u in pack["units"]]
    win = {u["id"]: float(u["win_s"]) for u in pack["units"]}

    # F5-33c was burned after the pack manifest was frozen; take its window from
    # the i2v run manifest and place it between F5-33b and F5-34 (finale block).
    with open(F533C_MANIFEST, encoding="utf-8-sig") as f:
        f533c = json.load(f)
    win["XQ_F5-33c"] = float(f533c["units"][0]["win_s"])
    idx = order.index("XQ_F5-34")
    order.insert(idx, "XQ_F5-33c")

    missing = [u for u in order if u not in by_unit]
    if missing:
        logline("ORDER-MISSING %s" % ",".join(missing))
        sys.exit(2)
    if len(order) != 33:
        logline("ORDER-COUNT %d != 33" % len(order))
        sys.exit(2)

    rows = []
    total = 0.0
    for i, unit in enumerate(order, 1):
        src = by_unit[unit]
        path = os.path.join(CLIPS, src["file"].replace("/", os.sep))
        info = probe(path)
        w = win[unit]
        total += w
        rows.append({
            "n": i,
            "unit": unit,
            "tier": src["tier"],
            "file": src["file"],
            "bytes": src["bytes"],
            "sha256": src["sha256"],
            "res": info["res"],
            "fps": info["fps"],
            "frames": info["frames"],
            "clip_sec": info["sec"],
            "win": round(w, 2),
        })

    v2 = {
        "schema": "xq-packa-assembly-index/v2",
        "built": "2026-10-20",
        "batch": "C2133",
        "why": ("C2132 ordered units by filename; the authored cut opens on F0 and "
                "closes on the F5-33/F5-34 finale block. v2 restores authored order."),
        "units": 33,
        "redo_picks": sum(1 for r in rows if r["tier"] == "redo-r1"),
        "missing": 0,
        "total_clip_bytes": sum(r["bytes"] for r in rows),
        "total_clip_sec": round(sum(r["clip_sec"] for r in rows), 2),
        "cut_sec": round(total, 2),
        "order_source": "cph4/fleet/mv-album-001-jay/Xingqing-i2v-PACK-A-v1.json",
        "clips": rows,
    }
    with open(OUT_V2_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(v2, f, ensure_ascii=False, indent=1)
        f.write("\n")

    lines = [
        "# Xingqing PACK-A - assembly index v2 (C2133)",
        "",
        "> Order fix: the C2132 index listed units by filename, which placed the",
        "> finale block (F5-33a/b/c, F5-34) at the head of the film. v2 follows the",
        "> authored pack order and appends F5-33c before F5-34.",
        "",
        "- units: **33** / redo-r1 picks: **%d** / missing: **0**" % v2["redo_picks"],
        "- cut length at authored windows: **%.2fs** / source clips total: %.2fs" % (total, v2["total_clip_sec"]),
        "",
        "| # | unit | tier | win(s) | clip(s) | file |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| %d | %s | %s | %.2f | %.2f | %s |" %
                     (r["n"], r["unit"], r["tier"], r["win"], r["clip_sec"], r["file"]))
    lines += [
        "",
        "## assembly note",
        "1. Cut in the order above; each row is trimmed to its authored `win` seconds.",
        "2. Keep 1344x768; the 4K master comes from the shipping pack, not the editor.",
        "3. Conform preview: `media/mv-album-001-jay/assembly-packA/XQ-PACKA-CONFORM-v1-c2133.mp4`.",
        "4. Audio offset: the pack opens at song t=0 (F0-01a is the 0-2s opening);",
        "   the audio station owns any later re-offset, this preview is 0-based.",
    ]
    with open(OUT_V2_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # concat list: inpoint/outpoint per file, trimmed to the authored window
    with open(CONCAT_LIST, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            abs_path = os.path.join(CLIPS, r["file"].replace("/", os.sep))
            f.write("file '%s'\n" % abs_path.replace("\\", "/"))
            f.write("inpoint 0\n")
            f.write("outpoint %.3f\n" % r["win"])

    logline("CONFORM-START units=%d cut=%.2fs" % (len(rows), total))
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", CONCAT_LIST,
           "-an", "-vf", "fps=24,format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
           "-movflags", "+faststart", OUT_MP4_NOMUX]
    subprocess.check_call(cmd)

    dur = total
    fade_out = max(dur - 1.4, 0.1)
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", OUT_MP4_NOMUX, "-i", SONG,
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-af", "afade=t=in:st=0:d=0.6,afade=t=out:st=%.2f:d=1.4" % fade_out,
           "-t", "%.2f" % dur, "-movflags", "+faststart", OUT_MP4]
    subprocess.check_call(cmd)

    info = probe(OUT_MP4)
    bytes_out = os.path.getsize(OUT_MP4)
    if not os.path.exists(SONG):
        logline("SONG-MISSING %s" % SONG)
        sys.exit(3)
    receipt = {
        "batch": "C2133",
        "units": len(rows),
        "cut_sec_expected": round(total, 2),
        "out": os.path.relpath(OUT_MP4, REPO).replace("\\", "/"),
        "out_bytes": bytes_out,
        "out_probe": info,
        "song": os.path.relpath(SONG, REPO).replace("\\", "/"),
        "song_bytes": os.path.getsize(SONG),
        "index_v2": os.path.relpath(OUT_V2_JSON, REPO).replace("\\", "/"),
        "order_source": v2["order_source"],
        "audio_offset": 0.0,
        "note": "Conform preview only: full-length windows, straight cuts, no transitions.",
    }
    with open(OUT_RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
        f.write("\n")

    ok = 1 if abs(info["sec"] - total) <= 1.0 and bytes_out > 1000000 else 0
    logline("CONFORM-END ok=%d units=%d cut=%.2fs out=%.2fs bytes=%d" %
            (ok, len(rows), total, info["sec"], bytes_out))
    if not ok:
        sys.exit(4)


if __name__ == "__main__":
    main()