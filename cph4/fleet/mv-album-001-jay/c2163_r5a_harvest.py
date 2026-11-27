# c2163_r5a_harvest.py - PACK-B S1-07 R5 take harvest (batch C2163).
# Waits for the burning clip, then probes it and pulls native frames for the
# cloud-contour body read. Pure picture, no audio expectations (CEO audio ban).
import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
CLIP = os.path.join(REPO, "media", "mv-album-001-jay", "clips-local-768", "XQ_B-S1-07-r5a.mp4")
EVID = os.path.join(REPO, "media", "mv-album-001-jay", "evidence-c2163")
STAMPS = (0.5, 1.0, 2.0, 4.0, 6.0, 7.5)
WAIT_MAX = 1500


def logline(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (stamp, msg)
    print(line)
    sys.stdout.flush()


def probe(path):
    cmd = ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
           "-show_entries", "format=duration,size", "-of", "json", path]
    d = json.loads(subprocess.check_output(cmd).decode("utf-8", "replace"))
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {
        "res": "%sx%s" % (st["width"], st["height"]),
        "fps": round(float(num) / float(den), 3),
        "frames": int(st.get("nb_read_frames") or 0),
        "duration": round(float(d["format"]["duration"]), 3),
        "bytes": int(d["format"]["size"]),
    }


def main():
    os.makedirs(EVID, exist_ok=True)
    t0 = time.time()
    last = 0
    while time.time() - t0 < WAIT_MAX:
        if os.path.exists(CLIP):
            size = os.path.getsize(CLIP)
            if size > 800000 and size == last:
                break
            last = size
        time.sleep(20)
    if not os.path.exists(CLIP):
        logline("CLIP MISSING after %ds wait" % WAIT_MAX)
        return 2

    info = probe(CLIP)
    logline("PROBE %s" % json.dumps(info))
    frames = []
    for ts in STAMPS:
        out = os.path.join(EVID, "r5a-%04.2fs.png" % ts)
        cmd = ["ffmpeg", "-v", "error", "-ss", "%.2f" % ts, "-i", CLIP,
               "-frames:v", "1", "-y", out]
        subprocess.check_call(cmd)
        frames.append({"t": ts, "path": out, "bytes": os.path.getsize(out)})
        logline("FRAME t=%.2f %dB" % (ts, os.path.getsize(out)))

    meta = {"clip": CLIP, "probe": info, "frames": frames, "stamps": list(STAMPS)}
    with open(os.path.join(EVID, "r5a-harvest.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    logline("HARVEST_OK frames=%d" % len(frames))
    return 0


if __name__ == "__main__":
    sys.exit(main())