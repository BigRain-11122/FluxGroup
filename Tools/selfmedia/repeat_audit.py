# -*- coding: utf-8 -*-
"""repeat_audit.py — find pixel-identical repeat windows in a finished film.

A "repeat" = a run of consecutive frames whose framemd5 hashes appear more than once
(i.e. the same footage played twice), which reads on screen as a stutter/copy.
Also reports per-2s darkness (YAVG) so freeze vs under-exposure can be told apart.

Usage:
    python Tools/selfmedia/repeat_audit.py --video <film.mp4> [--json out.json] [--min-run 3]
"""
import argparse, collections, io, json, os, re, subprocess, sys


def framemd5(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-an", "-f", "framemd5", "-"],
                       capture_output=True, text=True, errors="replace")
    rows, t = [], 0.0
    for line in r.stdout.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = [x.strip() for x in line.split(",")]
        if len(p) < 6:
            continue
        try:
            t = float(p[0].split()[-1]) if " " not in p[0] else float(p[0].split()[-1])
        except Exception:
            pass
        rows.append({"t": t, "md5": p[-1]})
    return rows


def ystats(path, win=2.0):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-an",
                        "-vf", "fps=1/%s,signalstats,metadata=print" % win, "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    vals = [float(m) for m in re.findall(r"YAVG=([\d.]+)", r.stderr)]
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--json", default="")
    ap.add_argument("--min-run", type=int, default=3)
    a = ap.parse_args()
    if not os.path.isfile(a.video):
        print("MISSING", a.video); return 2

    frames = framemd5(a.video)
    if not frames:
        print("NO FRAMES"); return 3

    seen = collections.defaultdict(list)
    for i, f in enumerate(frames):
        seen[f["md5"]].append(i)

    # group consecutive frames that are duplicates of an EARLIER frame
    runs, cur = [], []
    for i, f in enumerate(frames):
        idxs = seen[f["md5"]]
        dup = len(idxs) > 1 and idxs[0] < i
        if dup:
            cur.append(i)
        else:
            if len(cur) >= a.min_run:
                runs.append((cur[0], cur[-1]))
            cur = []
    if len(cur) >= a.min_run:
        runs.append((cur[0], cur[-1]))

    fps = 24.0
    r0 = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                         "-show_entries", "stream=r_frame_rate,width,height",
                         "-show_entries", "format=duration", "-of", "json", a.video],
                        capture_output=True, text=True, errors="replace")
    info = json.loads(r0.stdout or "{}")
    try:
        num, den = info["streams"][0]["r_frame_rate"].split("/")
        fps = float(num) / float(den)
    except Exception:
        pass

    dup_frames = sum(b - a1 + 1 for a1, b in runs)
    ys = ystats(a.video)
    dark = [i for i, v in enumerate(ys) if v < 26]

    out = {
        "video": a.video,
        "frames": len(frames),
        "fps": round(fps, 3),
        "duplicate_frames": dup_frames,
        "duplicate_ratio": round(dup_frames / max(1, len(frames)), 4),
        "repeat_windows": [{"start": round(a1 / fps, 2), "end": round((b + 1) / fps, 2),
                            "seconds": round((b - a1 + 1) / fps, 3)} for a1, b in runs],
        "longest_repeat_s": round(max([(b - a1 + 1) / fps for a1, b in runs], default=0.0), 3),
        "dark_windows_2s": [{"t": i * 2, "yavg": ys[i]} for i in dark[:20]],
        "verdict": "PASS" if dup_frames == 0 else ("WARN" if dup_frames / len(frames) < 0.02 else "FAIL"),
    }
    print(json.dumps({k: out[k] for k in ("video", "frames", "duplicate_frames", "duplicate_ratio",
                                          "longest_repeat_s", "verdict")}, ensure_ascii=False, indent=1))
    for w in out["repeat_windows"][:8]:
        print("  repeat %6.2f-%6.2fs (%.3fs)" % (w["start"], w["end"], w["seconds"]))
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".", exist_ok=True)
        io.open(a.json, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
        print("json ->", a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
