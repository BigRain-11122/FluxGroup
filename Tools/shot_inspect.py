# -*- coding: utf-8 -*-
"""shot_inspect.py —— 抽指定时间段的帧做带时间戳拼板（定位用，不定罪）

用法：
    python shot_inspect.py <video> <start_s> <end_s> <out.jpg> [--fps N] [--cols N] [--width N]

单次 ffmpeg 调用完成抽帧+缩放+打时间戳+拼板，不依赖 PIL。
默认每秒取 6 帧（约每 4 帧一帧），8 列。
"""
import argparse, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("start", type=float)
ap.add_argument("end", type=float)
ap.add_argument("out")
ap.add_argument("--fps", type=float, default=6.0, help="取样帧率")
ap.add_argument("--cols", type=int, default=8)
ap.add_argument("--width", type=int, default=420)
a = ap.parse_args()

dur = a.end - a.start
count = max(1, int(round(dur * a.fps)))
rows = (count + a.cols - 1) // a.cols
font = "C\\:/Windows/Fonts/arial.ttf"

vf = (
    "fps=%(fps)s,scale=%(w)s:-2,"
    "drawtext=fontfile='%(font)s':text='%%{pts\\:hms}':x=6:y=6:fontsize=17:"
    "fontcolor=yellow:box=1:boxcolor=black@0.55:boxborderw=3,"
    "tile=%(cols)sx%(rows)s:padding=2:margin=2"
) % {"fps": a.fps, "w": a.width, "font": font, "cols": a.cols, "rows": rows}

os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
cmd = ["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % a.start, "-t", "%.3f" % dur,
       "-i", a.video, "-vf", vf, "-frames:v", "1", "-q:v", "3", a.out]
r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
if r.returncode != 0 or not os.path.exists(a.out):
    sys.exit("抽板失败: %s" % (r.stderr.strip()[:400]))
print("已出板 %s  %d 帧 %dx%d  %s" % (a.out, count, a.cols, rows,
                                     "%.1f KB" % (os.path.getsize(a.out) / 1024)))