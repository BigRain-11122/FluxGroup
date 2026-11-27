# -*- coding: ascii -*-
# xq_packa_assembly_index_c2132.py - build the assembly index for Xingqing PACK-A.
#
# Why: the 32 final clips live in two folders (base lane + redo-r1 lane). Six
# units were re-burned and judged PASS in C2093, so the editor must pick the
# redo file for those six and the base file for the rest. Without an explicit
# index the assembly station can silently cut the rejected takes.
#
# Zero GPU, read-only on media. Writes:
#   cph4/fleet/mv-album-001-jay/xq-PACKA-ASSEMBLY-INDEX-c2132.json
#   cph4/fleet/mv-album-001-jay/xq-PACKA-ASSEMBLY-INDEX-c2132.md
# PASS gate: INDEX-END units=33 redos=6 missing=0 labels_match=1

import hashlib
import json
import os
import re
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
BASE = os.path.join(MEDIA, "clips-packA-768")
REDO = os.path.join(MEDIA, "clips-packA-redo-r1")
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
OUT_JSON = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-c2132.json")
OUT_MD = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-c2132.md")
BOARD_JSON = os.path.join(OUTDIR, "xq-PACKA-33-FULL-BOARD-c2114.json")
BATCH = "C2132"

# Units re-burned and accepted in C2093 (direct3 + i2v3 batches).
REDO_UNITS = {
    "XQ_S2-14": "XQ_S2-14-redo-r1.mp4",
    "XQ_S3-19": "XQ_S3-19-redo-r1.mp4",
    "XQ_S3-20": "XQ_S3-20-redo-r1.mp4",
    "XQ_S4-22": "XQ_S4-22-redo-r1.mp4",
    "XQ_S4-24": "XQ_S4-24-redo-r1.mp4",
    "XQ_F5-33a": "XQ_F5-33a-redo-r1.mp4",
}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,avg_frame_rate,nb_frames",
           "-show_entries", "format=duration", "-of", "json", path]
    raw = subprocess.check_output(cmd)
    d = json.loads(raw.decode("utf-8"))
    st = d["streams"][0]
    num, den = st["avg_frame_rate"].split("/")
    fps = round(float(num) / float(den), 3) if float(den) else 0.0
    frames = st.get("nb_frames")
    if frames in (None, "N/A"):
        frames = None
    else:
        frames = int(frames)
    return {
        "width": int(st["width"]),
        "height": int(st["height"]),
        "fps": fps,
        "frames": frames,
        "duration_s": round(float(d["format"]["duration"]), 3),
    }


def unit_sort_key(name):
    m = re.match(r"XQ_([A-Z])(\d)-(\d+)([a-z]?)$", name)
    if not m:
        return (99, 99, 99, name)
    return (m.group(1), int(m.group(2)), int(m.group(3)), m.group(4))


def main():
    unit_files = {}
    for fn in os.listdir(BASE):
        if fn.lower().endswith(".mp4"):
            unit_files[os.path.splitext(fn)[0]] = fn

    rows = []
    missing = []
    total_sec = 0.0
    total_bytes = 0
    for unit in sorted(unit_files, key=unit_sort_key):
        if unit in REDO_UNITS:
            src_dir = REDO
            fn = REDO_UNITS[unit]
            tier = "redo-r1"
        else:
            src_dir = BASE
            fn = unit_files[unit]
            tier = "base"
        path = os.path.join(src_dir, fn)
        if not os.path.exists(path):
            missing.append({"unit": unit, "path": path})
            continue
        size = os.path.getsize(path)
        if size < 100_000:
            missing.append({"unit": unit, "path": path, "reason": "undersize"})
            continue
        info = probe(path)
        row = {
            "unit": unit,
            "tier": tier,
            "file": os.path.join(os.path.basename(src_dir), fn).replace("\\", "/"),
            "bytes": size,
            "sha256": sha256_of(path),
            "width": info["width"],
            "height": info["height"],
            "fps": info["fps"],
            "frames": info["frames"],
            "duration_s": info["duration_s"],
        }
        rows.append(row)
        total_sec += info["duration_s"]
        total_bytes += size

    redos_used = sum(1 for r in rows if r["tier"] == "redo-r1")

    # Cross-check the unit set and order against the C2114 full board labels.
    with open(BOARD_JSON, encoding="utf-8-sig") as f:
        board = json.load(f)
    labels = board["labels"]
    labels_match = 1 if [r["unit"] for r in rows] == labels else 0
    rec = {
        "batch": BATCH,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "project": "mv0001-xingqing-PACK-A",
        "purpose": "assembly index: one authoritative clip per unit, redo-r1 supersedes rejected takes",
        "law": "C2093 verdict: 25 base PASS + direct3 (S2-14/S3-20/S4-22) + i2v3 (F5-33a/S4-24/S3-19); S5-27 from the r1061 reshake; unit list cross-checked against xq-PACKA-33-FULL-BOARD-c2114.json",
        "units": len(rows),
        "redos_used": redos_used,
        "labels_match": labels_match,
        "missing": missing,
        "total_bytes": total_bytes,
        "total_duration_s": round(total_sec, 3),
        "clips": rows,
        "gate": "INDEX-END units=%d redos=%d missing=%d labels_match=%d" % (len(rows), redos_used, len(missing), labels_match),
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")

    lines = []
    lines.append("# Xingqing PACK-A - assembly index (%s)" % BATCH)
    lines.append("")
    lines.append("> Built %s from disk (ffprobe + sha256). One authoritative clip per unit." % rec["ts"])
    lines.append("> Rule: six units re-burned and accepted in C2093 use `clips-packA-redo-r1`, the rest use `clips-packA-768`.")
    lines.append("> S5-27 comes from the r1061 reshake (bm-a ruling) and is already in the base lane.")
    lines.append("")
    lines.append("- units: **%d** / redo-r1 picks: **%d** / missing: **%d**" % (len(rows), redos_used, len(missing)))
    lines.append("- total bytes: **%d** / total duration: **%.1fs**" % (total_bytes, total_sec))
    lines.append("")
    lines.append("| # | unit | tier | file | bytes | res | fps | frames | sec | sha256(12) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        lines.append("| %d | %s | %s | %s | %d | %dx%d | %s | %s | %.2f | %s |" % (
            i, r["unit"], r["tier"], r["file"], r["bytes"], r["width"], r["height"],
            r["fps"], r["frames"] if r["frames"] is not None else "-",
            r["duration_s"], r["sha256"][:12]))
    lines.append("")
    if missing:
        lines.append("## blockers")
        for m in missing:
            lines.append("- %s -> %s" % (m["unit"], m.get("reason", "missing")))
        lines.append("")
    lines.append("## assembly note")
    lines.append("1. Cut in unit order above; the six redo-r1 files replace the base takes (they are the PASS takes).")
    lines.append("2. Keep original resolution 1344x768; no upscale inside the editor, the 4K master is produced by the shipping pack.")
    lines.append("3. Gate line: `%s`." % rec["gate"])
    lines.append("")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print(rec["gate"])
    print("OUT_JSON %s %dB" % (OUT_JSON, os.path.getsize(OUT_JSON)))
    print("OUT_MD   %s %dB" % (OUT_MD, os.path.getsize(OUT_MD)))
    if missing:
        sys.exit(2)


if __name__ == "__main__":
    main()