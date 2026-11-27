# -*- coding: utf-8 -*-
"""vertical_hook.py — cut a 9:16 short hook (抖音/视频号) from a finished 16:9 film.

Usage:
    python Tools/selfmedia/vertical_hook.py --video <film.mp4> --out <hook.mp4> \
        --segments 12,58,150 --dur 5 --title "爱在西元前"

Behaviour: takes N equal slices starting at the given timecodes, centre-crops 9:16,
scales to 1080x1920, concatenates, keeps the original audio (already loudness-normalised).
"""
import argparse, json, os, subprocess, sys, tempfile


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--segments", default="12,58,150", help="comma separated start times (s)")
    ap.add_argument("--dur", type=float, default=5.0, help="seconds per slice")
    ap.add_argument("--title", default="")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    a = ap.parse_args()

    if not os.path.isfile(a.video):
        print("MISSING", a.video); return 2
    starts = [float(x) for x in a.segments.split(",") if x.strip()]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="vhook_")
    parts = []
    for i, st in enumerate(starts):
        p = os.path.join(tmp, "p%02d.mp4" % i)
        vf = ("crop=ih*9/16:ih,scale=%d:%d:flags=lanczos,setsar=1" % (a.width, a.height))
        r = run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % st, "-t", "%.3f" % a.dur,
                 "-i", a.video, "-vf", vf, "-r", "24",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", p])
        if r.returncode != 0:
            print("SLICE FAIL", st, r.stderr[-200:]); return 3
        parts.append(p)

    lst = os.path.join(tmp, "list.txt")
    open(lst, "w", encoding="utf-8").write("".join("file '%s'\n" % p.replace("\\", "/") for p in parts))
    r = run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
             "-c", "copy", "-movflags", "+faststart", a.out])
    if r.returncode != 0:
        print("CONCAT FAIL", r.stderr[-200:]); return 4

    probe = run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
                 "-show_entries", "stream=width,height,r_frame_rate", "-of", "json", a.out])
    info = json.loads(probe.stdout or "{}")
    print(json.dumps({"out": a.out, "segments": starts, "dur_each": a.dur,
                      "spec": info.get("streams", [{}])[0], "format": info.get("format", {})},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
