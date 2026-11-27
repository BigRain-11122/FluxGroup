# -*- coding: utf-8 -*-
# whisper_album.py - 《Jay》全专词级锚点批（资源库ape已转320k mp3）
#
# 2026-11-06 (CEO-PROXY event round): two fixes that made this unusable off bm-a and
# unusable for the remaining 27 tracks.
#   1. SRC/OUT were hardcoded to C:\Users\sjs20\Desktop\FluxGroup, so on bm-b (root
#      C:/Fluxgroup/FluxGroup) the lane could not run its own words leg at all. Paths
#      now derive from this file, per the fleet portability norm (C-20261016-05).
#   2. No way to cap a run. A 27-track whisper pass is hours on CPU; the caller needs
#      to take a batch and come back. --limit/--songs added, default = all remaining.
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "audio")
OUT = os.path.join(BASE, "anchors")
os.makedirs(OUT, exist_ok=True)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="process at most N songs (0 = all)")
    ap.add_argument("--model", default="small")
    ap.add_argument("songs", nargs="*", help="only these song titles")
    a = ap.parse_args(argv[1:])

    import whisper
    m = whisper.load_model(a.model)

    todo = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".mp3"):
            continue
        # Only album tracks are named "<artist> - <song>". The folder also holds
        # mv001_source_320k.mp3, a whole-album master; transcribing it produced a
        # 496-word junk anchor under the name mv001_source_320k (caught 2026-11-06
        # smoke). Explicit --songs still wins so a rename never hides real work.
        if not f.startswith("周杰伦 - ") and f[:-4] not in a.songs:
            continue
        sid = f.replace("周杰伦 - ", "").replace(".mp3", "")
        if a.songs and sid not in a.songs:
            continue
        if os.path.isfile(os.path.join(OUT, sid + ".json")):
            print("SKIP", sid, flush=True)
            continue
        todo.append((f, sid))
    if a.limit and len(todo) > a.limit:
        todo = todo[:a.limit]
    print("QUEUE %d song(s)" % len(todo), flush=True)

    done = 0
    for f, sid in todo:
        r = m.transcribe(os.path.join(SRC, f), word_timestamps=True, language="zh", verbose=False)
        words, lines = [], []
        for seg in r["segments"]:
            sw = seg.get("words") or []
            if sw:
                t0, t1 = sw[0]["start"], sw[-1]["end"]
                text = "".join(w["word"] for w in sw)
            else:
                t0, t1, text = seg["start"], seg["end"], seg["text"]
            lines.append({"t0": round(t0, 2), "t1": round(t1, 2), "text": text.strip()})
            for w in sw:
                words.append({"t0": round(w["start"], 2), "t1": round(w["end"], 2), "w": w["word"].strip()})
        if not lines:
            print("EMPTY %s" % sid, flush=True)
            continue
        with open(os.path.join(OUT, sid + ".json"), "w", encoding="utf-8") as fo:
            json.dump({"words": words, "lines": lines}, fo, ensure_ascii=False, indent=1)
        with open(os.path.join(OUT, sid + ".txt"), "w", encoding="utf-8") as fo:
            for L in lines:
                fo.write("%7.2f - %7.2f | %s\n" % (L["t0"], L["t1"], L["text"]))
        done += 1
        print("DONE %s words=%d lines=%d last=%.2f" % (sid, len(words), len(lines), lines[-1]["t1"]),
              flush=True)
    # Readiness is deliberately NOT reported as a ratio here: five first-batch anchors
# were named by hand (jiandanan / kaibuliaokou / 安静-words / 晴天-words / ...), so a
# "<song>.json exists" count under-reports (measured 11/41 while 15 songs really had
# words). The authoritative number is anchor_shotgrid.py --matrix, which checks all
# four artifacts per song.
    print("ALBUM ANCHORS DONE built=%d (authoritative readiness: anchor_shotgrid.py --matrix)"
          % done, flush=True)
    # exit 0 only when this run actually produced something (a silent no-op must not
    # look like success to the queue).
    return 0 if done else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))