# -*- coding: utf-8 -*-
# 一次生产 → 多平台发布包（纯 ffmpeg，本地确定性，无联网）
# 用法: python bili_repurpose.py <母版.mp4> [--out DIR] [--title "标题"]
import argparse, json, os, subprocess, sys

FFMPEG = r"C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffprobe.exe"


def probe(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,duration",
                        "-of", "json", path], capture_output=True)
    s = json.loads(r.stdout.decode())["streams"][0]
    return int(s["width"]), int(s["height"]), float(s.get("duration") or 0)


def run(args):
    p = subprocess.run([FFMPEG, "-y", "-v", "error"] + args, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "replace")[-400:])


def vertical(src, dst, seconds=60):
    """9:16 竖屏：模糊背景 + 原片居中，最长 60 秒"""
    w, h, dur = probe(src)
    run(["-i", src, "-t", str(min(seconds, dur or seconds)),
         "-filter_complex",
         "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:5[bg];"
         "[0:v]scale=1080:-2[fg];"
         "[bg][fg]overlay=(W-w)/2:(H-h)/2",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "128k", dst])


def square_cover(src, dst, t=1.0, size=1080):
    run(["-ss", str(t), "-i", src, "-frames:v", "1",
         "-vf", "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d" % (size, size, size, size),
         "-q:v", "2", dst])


def xhs_frames(src, outdir, n=6):
    _, _, dur = probe(src)
    dur = dur or 60
    os.makedirs(outdir, exist_ok=True)
    files = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        f = os.path.join(outdir, "img%02d.jpg" % (i + 1))
        run(["-ss", "%.2f" % t, "-i", src, "-frames:v", "1",
             "-vf", "scale=1080:1440:force_original_aspect_ratio=increase,crop=1080:1440",
             "-q:v", "2", f])
        files.append(f)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default=r"E:\Fluxgroup\.codely-cli\publish-pack")
    ap.add_argument("--title", default="")
    a = ap.parse_args()

    name = os.path.splitext(os.path.basename(a.src))[0]
    base = os.path.join(a.out, name)
    w, h, dur = probe(a.src)
    print("母版 %dx%d %.1fs" % (w, h, dur), flush=True)

    # 抖音 / 快手：9:16
    for plat in ("douyin", "kuaishou"):
        d = os.path.join(base, plat)
        os.makedirs(d, exist_ok=True)
        vertical(a.src, os.path.join(d, "video.mp4"))
        square_cover(a.src, os.path.join(d, "cover.jpg"), t=min(1.5, max(0.3, (dur or 1) * 0.1)))
        print("OK", d, flush=True)

    # 小红书：九宫格
    d = os.path.join(base, "xiaohongshu")
    xhs_frames(a.src, os.path.join(d, "images"), 6)
    print("OK", d, flush=True)

    # 知乎 / 微博：封面
    for plat in ("zhihu", "weibo"):
        d = os.path.join(base, plat)
        os.makedirs(d, exist_ok=True)
        square_cover(a.src, os.path.join(d, "cover.jpg"), t=min(2.0, max(0.3, (dur or 1) * 0.15)))
        print("OK", d, flush=True)

    json.dump({"src": a.src, "title": a.title, "width": w, "height": h, "duration": dur,
               "pack": base}, open(os.path.join(base, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("PACK ->", base)


if __name__ == "__main__":
    main()