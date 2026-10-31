# -*- coding: ascii -*-
# kn21_harvest_c2173.py - harvest the KN21 c2173 take when ComfyUI finishes it.
#
# Why: the i2v runner polls for 2400s then gives up, but the server keeps rendering
# (int8 768P under desktop contention runs ~47s/frame, so 362 frames outlives any
# sane poll budget). Rather than re-burn, wait for the finished file in the ComfyUI
# output dir, make sure its size is stable, then move it into the lane.

import json
import os
import shutil
import subprocess
import sys
import time

OUT_DIR = r"D:\ComfyUI\ComfyUI\output"
CLIP = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\clips-local-768\KN_A-KN21.mp4"
RECEIPT = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\KN21-HARVEST-c2173.json"
LOG = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\logs\kn21_harvest_c2173.log"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"
STARTED = time.time()
WAIT_S = 6 * 3600


def log(m):
    line = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), m)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="ascii", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass


def newest_mp4_since(t0):
    best, best_m = None, 0.0
    try:
        for n in os.listdir(OUT_DIR):
            if not n.lower().endswith(".mp4"):
                continue
            p = os.path.join(OUT_DIR, n)
            m = os.path.getmtime(p)
            if m > t0 and m > best_m:
                best, best_m = p, m
    except Exception:
        pass
    return best


def probe(p):
    try:
        out = subprocess.check_output([FFPROBE, "-v", "error", "-count_frames",
                                       "-select_streams", "v:0",
                                       "-show_entries", "stream=width,height,nb_read_frames",
                                       "-show_entries", "format=duration", "-of", "json", p])
        d = json.loads(out.decode("utf-8", "replace"))
        st = d["streams"][0]
        return {"res": "%sx%s" % (st["width"], st["height"]),
                "frames": int(st["nb_read_frames"]),
                "sec": round(float(d["format"]["duration"]), 3)}
    except Exception as e:
        return {"err": str(e)}


def main():
    if os.path.exists(CLIP):
        log("SKIP: clip already in place")
        return 0
    log("START waiting for a new mp4 in %s" % OUT_DIR)
    while time.time() - STARTED < WAIT_S:
        p = newest_mp4_since(STARTED - 5)
        if p:
            s1 = os.path.getsize(p)
            time.sleep(20)
            s2 = os.path.getsize(p)
            if s1 == s2 and s2 > 300000:
                info = probe(p)
                if info.get("frames", 0) > 0:
                    shutil.copy2(p, CLIP)
                    payload = {"batch": "C2173", "shot": "KN21",
                               "source": p, "clip": CLIP,
                               "bytes": os.path.getsize(CLIP), "probe": info,
                               "note": "harvested after the runner poll budget expired; server kept rendering"}
                    with open(RECEIPT, "w", encoding="utf-8", newline="\n") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=1)
                    log("HARVEST-OK %s frames=%s %sB" % (CLIP, info.get("frames"), payload["bytes"]))
                    return 0
        time.sleep(30)
    log("HARVEST-TIMEOUT after %ds" % WAIT_S)
    return 1


if __name__ == "__main__":
    sys.exit(main())