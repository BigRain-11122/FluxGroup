#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""preview_concat.py - 把竖屏素材拼成一条预览片（装配线的最小可看产物）。

做法：按文件名排序取前 N 段，统一 1080x1920/30fps，用 concat demuxer 拼接，
      超长则截断到 --seconds。产物必须是能直接播放的 mp4。

用法：
  python3 Tools/fleet/preview_concat.py --dir <竖屏素材目录> --out <out.mp4> [--clips 6] [--seconds 30]
Exit: 0 成功；1 编码失败；2 无素材
"""
import argparse
import os
import subprocess
import sys
import tempfile

FFMPEG = "/Users/junsheng.sun/bin/ffmpeg" if os.path.exists("/Users/junsheng.sun/bin/ffmpeg") else "ffmpeg"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--clips", type=int, default=6)
    ap.add_argument("--seconds", type=int, default=30)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        print("[preview] 素材目录不存在（rc=2）")
        return 2
    clips = sorted(f for f in os.listdir(a.dir) if f.lower().endswith((".mp4", ".mov")))[: a.clips]
    if not clips:
        print("[preview] 无素材（rc=2）")
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="fluxprev-")
    norm = []
    for i, n in enumerate(clips):
        p = os.path.join(tmpdir, "n%02d.mp4" % i)
        cmd = [FFMPEG, "-y", "-v", "error", "-i", os.path.join(a.dir, n),
               "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                      "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
               "-t", "6", "-c:v", "h264_videotoolbox", "-b:v", "6M",
               "-c:a", "aac", "-b:a", "128k", p]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(p) and os.path.getsize(p) > 0:
            norm.append(p)
    if not norm:
        print("[preview] 归一化全失败（rc=1）")
        return 1
    lst = os.path.join(tmpdir, "list.txt")
    with open(lst, "w") as f:
        for p in norm:
            f.write("file '%s'\n" % p)
    r = subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-t", str(a.seconds),
                        "-c:v", "h264_videotoolbox", "-b:v", "8M",
                        "-c:a", "aac", "-b:a", "128k", a.out],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(a.out):
        print("[preview] 拼接失败：%s" % (r.stderr or "")[-200:])
        return 1
    size = os.path.getsize(a.out)
    print("[preview] %d 段 -> %s (%d KB)" % (len(norm), a.out, size // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())