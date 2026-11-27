# -*- coding: utf-8 -*-
"""frame_gate.py —— 首尾帧闸（逐镜取帧版，稳）
用法: python Tools/frame_gate.py <video> <plan-cuts.json> <out_dir>
"""
import json, os, subprocess, sys

def ffprobe_meta(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=r_frame_rate,nb_frames",
                        "-of", "default=noprint_wrappers=1", video],
                       capture_output=True, text=True)
    m = dict(l.split("=", 1) for l in r.stdout.strip().splitlines() if "=" in l)
    num, den = m["r_frame_rate"].split("/")
    return float(num) / float(den), int(m["nb_frames"])

def grab(video, t, path):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", "%.4f" % t, "-i", video, "-frames:v", "1",
                    "-vf", "scale=640:-1", path], check=True)

def main():
    video, plan_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    fps, total = ffprobe_meta(video)
    cuts = json.load(open(plan_path, encoding="utf-8"))["cuts"]
    bounds = [0.0] + cuts + [total / fps]
    os.makedirs(os.path.join(out, "first"), exist_ok=True)
    os.makedirs(os.path.join(out, "last"), exist_ok=True)

    n = len(bounds) - 1
    print("shots:", n, "fps:", fps)
    rows = []
    for i in range(n):
        a, b = bounds[i], bounds[i + 1]
        f0 = os.path.join(out, "first", "shot_%03d.png" % (i + 1))
        f1 = os.path.join(out, "last",  "shot_%03d.png" % (i + 1))
        grab(video, a + 0.02, f0)
        grab(video, max(a, b - 1.0 / fps) - 0.02, f1)
        rows.append((i + 1, round(a, 2), round(b, 2)))
        if (i + 1) % 20 == 0:
            print("  ...", i + 1)

    with open(os.path.join(out, "INDEX.tsv"), "w", encoding="utf-8") as f:
        f.write("shot\tstart\tend\n")
        for r in rows:
            f.write("%d\t%.2f\t%.2f\n" % r)
    print("done ->", out)

if __name__ == "__main__":
    main()