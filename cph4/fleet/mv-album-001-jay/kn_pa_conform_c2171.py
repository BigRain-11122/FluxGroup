# -*- coding: ascii -*-
# kn_pa_conform_c2171.py - KN (Ke Ai Nv Ren) PACK-A station-4 conform preview.
#
# Why: bank job kn-pa-station4-conform-author-c2169 (lane bm-c) was still pending
# with an empty cmd. The 30-unit 768P pack is harvested (KN-PA768-HARVEST-c2169:
# units=30 check=0) but nobody could watch motion across cuts. This builds the
# review proxy in the authored pack order, 960px wide, straight cuts, no
# transitions, song muxed. Zero GPU, read-only on the clips.
#
# Reused from xq_packa_conform_c2133.py (same conform math, different pack).
# PASS gate: CONFORM-END ok=1 units=30.

import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay")
CLIP_SUB = os.path.join(CLIPS, "clips-local-768")
PACK_JSON = os.path.join(OUTDIR, "\u53ef\u7231\u5973\u4eba-i2v-PACK-A-v1.json")
SONG = os.path.join(OUTDIR, "audio", "\u5468\u6770\u4f26 - \u53ef\u7231\u5973\u4eba.mp3")
OUT_MEDIA = os.path.join(CLIPS, "assembly-packA")
OUT_MP4 = os.path.join(OUT_MEDIA, "KN-PACKA-CONFORM-v1-c2171.mp4")
OUT_NOMUX = os.path.join(OUT_MEDIA, "KN-PACKA-CONFORM-v1-c2171.video-only.mp4")
CONCAT_LIST = os.path.join(OUT_MEDIA, "concat-kn-c2171.txt")
OUT_RECEIPT = os.path.join(OUTDIR, "KN-PA-CONFORM-c2171.json")
LOG_RUN = os.path.join(CLIPS, "log-kn-conform-c2171.run.txt")
PROXY_W = 960

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"


def logline(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
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
    if not os.path.exists(SONG):
        logline("SONG-MISSING %s" % SONG)
        sys.exit(3)

    with open(PACK_JSON, encoding="utf-8-sig") as f:
        pack = json.load(f)
    units = pack["units"]

    rows = []
    total = 0.0
    for i, u in enumerate(units, 1):
        unit = u["id"]
        path = os.path.join(CLIP_SUB, unit + ".mp4")
        if not os.path.exists(path):
            logline("CLIP-MISSING %s" % unit)
            sys.exit(2)
        info = probe(path)
        win = float(u["win_s"])
        clamped = win > info["sec"]
        if clamped:
            # a window can never exceed the take; keep the legal part only
            win = info["sec"]
        total += win
        rows.append({
            "n": i,
            "unit": unit,
            "win": round(win, 3),
            "win_authored": round(float(u["win_s"]), 3),
            "clamped": clamped,
            "clip_sec": info["sec"],
            "res": info["res"],
            "fps": info["fps"],
            "frames": info["frames"],
            "bytes": os.path.getsize(path),
        })

    missing = [r for r in rows if r["clamped"]]
    if missing:
        logline("WINDOW-CLAMPED %s" % ",".join(r["unit"] for r in missing))

    with open(CONCAT_LIST, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            abs_path = os.path.join(CLIP_SUB, r["unit"] + ".mp4")
            f.write("file '%s'\n" % abs_path.replace("\\", "/"))
            f.write("inpoint 0\n")
            f.write("outpoint %.3f\n" % r["win"])

    logline("CONFORM-START units=%d cut=%.2fs" % (len(rows), total))
    vf = "scale=%d:-2,fps=24,format=yuv420p" % PROXY_W
    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-f", "concat", "-safe", "0", "-i", CONCAT_LIST,
                           "-an", "-vf", vf,
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                           "-movflags", "+faststart", OUT_NOMUX])

    fade_out = max(total - 1.4, 0.1)
    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-i", OUT_NOMUX, "-i", SONG,
                           "-map", "0:v:0", "-map", "1:a:0",
                           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                           "-af", "afade=t=in:st=0:d=0.6,afade=t=out:st=%.2f:d=1.4" % fade_out,
                           "-t", "%.2f" % total, "-movflags", "+faststart", OUT_MP4])

    info = probe(OUT_MP4)
    bytes_out = os.path.getsize(OUT_MP4)
    receipt = {
        "batch": "C2171",
        "card": "kn-pa-station4-conform-author-c2169",
        "units": len(rows),
        "cut_sec_expected": round(total, 2),
        "out": os.path.relpath(OUT_MP4, REPO).replace("\\", "/"),
        "out_bytes": bytes_out,
        "out_probe": info,
        "proxy_width": PROXY_W,
        "song": os.path.relpath(SONG, REPO).replace("\\", "/"),
        "song_bytes": os.path.getsize(SONG),
        "order_source": "\u53ef\u7231\u5973\u4eba-i2v-PACK-A-v1.json",
        "clamped_units": [r["unit"] for r in rows if r["clamped"]],
        "note": ("Conform preview only: authored windows, straight cuts, no transitions, "
                 "no grade, no titles. Review proxy - not a delivery master."),
        "rows": rows,
    }
    with open(OUT_RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
        f.write("\n")

    ok = 1 if abs(info["sec"] - total) <= 1.5 and bytes_out > 1000000 else 0
    logline("CONFORM-END ok=%d units=%d cut=%.2fs out=%.2fs bytes=%d" %
            (ok, len(rows), total, info["sec"], bytes_out))
    if not ok:
        sys.exit(4)


if __name__ == "__main__":
    main()