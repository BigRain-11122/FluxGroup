#!/usr/bin/env python3
"""mv_edl.py - 帧精确的时间线渲染器（EDL 驱动，可复现）

解决的问题：手写 ffmpeg 拼接会因 fps/round 掉帧（v726 比 v724 少 5 帧），
且每次改一处要重算全部。这里用 EDL(JSON) 描述"哪一段、从哪进、到哪出、什么速度"，
按帧号裁切+渲染，同一份 EDL 反复跑结果一致。

EDL 格式：
{
  "fps": 24, "size": [1344, 768],
  "audio_from": "<原片路径，可选；提供则重挂其音轨>",
  "segments": [
    {"src": "a.mp4", "in": 0.0, "out": 3.5, "speed": 1.0, "note": "开场"},
    ...
  ]
}

用法：
  python Tools/mv_edl.py render <edl.json> <out.mp4>
  python Tools/mv_edl.py duration <edl.json>       # 只算总时长与帧数，不渲染
  python Tools/mv_edl.py sheet <edl.json> 0 40 out.jpg   # 出联系表
"""
import json
import os
import subprocess
import sys


def sh(a):
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("FFMPEG FAIL:", (r.stderr or "")[-400:])
        sys.exit(1)


def total(edl):
    fps = edl.get("fps", 24)
    dur = sum((s["out"] - s["in"]) if s.get("speed", 1.0) == 1.0
              else (s["out"] - s["in"]) / s["speed"] for s in edl["segments"])
    return dur, int(round(dur * fps))


def render(edl_path, out):
    edl = json.load(open(edl_path, encoding="utf-8"))
    fps = edl.get("fps", 24)
    w, h = edl.get("size", [1344, 768])
    work = os.path.join(os.path.dirname(os.path.abspath(out)), "_edlwork")
    os.makedirs(work, exist_ok=True)

    parts = []
    for i, s in enumerate(edl["segments"]):
        dur = s["out"] - s["in"]
        sp = s.get("speed", 1.0)
        # 按帧对齐：先算目标帧数，再反推裁切时长，避免累积漂移
        frames = int(round(dur * fps))
        take = frames / fps if sp == 1.0 else frames / fps * sp
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
              f"fps={fps},setsar=1")
        if sp != 1.0:
            vf += f",setpts={sp:.4f}*PTS"
        p = os.path.join(work, f"seg{i:03d}.mp4")
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{s['in']:.3f}", "-t", f"{take:.3f}", "-i", s["src"],
            "-an", "-vf", vf, "-frames:v", str(frames),
            "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", p])
        parts.append(p)

    lst = os.path.join(work, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write("file '%s'\n" % os.path.abspath(p).replace("\\", "/"))
    silent = os.path.join(work, "video.mp4")
    sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])

    audio = edl.get("audio_from")
    if audio:
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", silent, "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "copy", "-shortest", out])
    else:
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", silent, "-c", "copy", out])
    d, fr = total(edl)
    print(f"OUT {out}\nEDL segments={len(edl['segments'])} expect={d:.3f}s / {fr}f")


def sheet(edl_path, a, b, out):
    """渲染前先出联系表需要成片；这里直接对 edl 的源按段抽样，快且省时"""
    edl = json.load(open(edl_path, encoding="utf-8"))
    print("提示：sheet 建议在 render 后对成片跑 ffmpeg tile；此处只列段：")
    t = 0.0
    for i, s in enumerate(edl["segments"]):
        d = (s["out"] - s["in"]) / s.get("speed", 1.0)
        print(f"  {i:02d} {t:7.2f}-{t + d:7.2f} ({d:5.2f}s) {s.get('note', '')}")
        t += d


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "render" and len(sys.argv) >= 4:
        render(sys.argv[2], sys.argv[3]); return 0
    if cmd == "duration":
        edl = json.load(open(sys.argv[2], encoding="utf-8"))
        d, f = total(edl); print(f"{d:.3f}s / {f}f"); return 0
    if cmd == "sheet" and len(sys.argv) >= 6:
        sheet(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]); return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())