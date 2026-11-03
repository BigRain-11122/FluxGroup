#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_proxy.py - 用本机硬件编码批量出"给人看"的 720p 审片副本。

为什么（2026-11-03 CEO「好好利用本地的算力支持各公司业务，尤其 MacBook」）：
  成片 1080×1920 一条十几 MB，CEO 在手机上点开要等；审片只需要 720p。
  硬件编码实测 12 秒片 1.16 秒出（h264_videotoolbox），CPU 占用极低，
  属于 Mac 该干的活：不产出画面，只把画面变成能快速看的东西。

判据：
  - 幂等：目标已存在且比源新则跳过
  - 只处理最近 N 天改过的源（默认 7 天）
  - 只用硬件编码；如无 videotoolbox 直接 BLOCKED（不用软件编码顶替，免得占满 CPU 拖累主控）

用法：
  python3 review_proxy.py --src media/drama-out --out media/review-720p [--days 7] [--height 1280]
Exit: 0 完成；3 缺 ffmpeg/无硬件编码（BLOCKED 回执）
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time


def ff():
    for c in (os.environ.get("FFMPEG"), "ffmpeg",
              "/Users/%s/bin/ffmpeg" % os.environ.get("USER", "")):
        if c and shutil.which(c):
            return c
    return None


def has_vt(F):
    try:
        r = subprocess.run([F, "-hide_banner", "-encoders"], capture_output=True,
                           text=True, timeout=30)
        return "h264_videotoolbox" in (r.stdout or "")
    except Exception:
        return False


def blocked(out, why):
    d = os.path.dirname(os.path.abspath(out)) or "."
    os.makedirs(d, exist_ok=True)
    p = os.path.splitext(out)[0] + "-blocked.json"
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "BLOCKED",
               "error_class": "E-BLOCKED-INPUT", "why": why, "tool": "review_proxy"},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[proxy] BLOCKED %s（回执 %s）" % (why, p))
    return 3


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="media/drama-out")
    ap.add_argument("--out", default="media/review-720p")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--height", type=int, default=1280)
    ap.add_argument("--max", type=int, default=6, help="一轮最多出几条（防长时间占机）")
    a = ap.parse_args(argv)
    F = ff()
    if not F:
        return blocked(os.path.join(a.out, "review"), "没有 ffmpeg")
    if not has_vt(F):
        return blocked(os.path.join(a.out, "review"), "本机 ffmpeg 不支持 h264_videotoolbox")
    if not os.path.isdir(a.src):
        return blocked(os.path.join(a.out, "review"), "源目录不存在：%s" % a.src)
    os.makedirs(a.out, exist_ok=True)
    cutoff = time.time() - a.days * 86400
    made, skipped = [], 0
    for f in sorted(os.listdir(a.src)):
        if not f.lower().endswith(".mp4") or f.startswith("."):
            continue
        s = os.path.join(a.src, f)
        if os.path.getmtime(s) < cutoff:
            continue
        o = os.path.join(a.out, os.path.splitext(f)[0] + "-720p.mp4")
        if os.path.exists(o) and os.path.getmtime(o) >= os.path.getmtime(s):
            skipped += 1
            continue
        if len(made) >= a.max:
            break
        t0 = time.time()
        rc = subprocess.run([F, "-hide_banner", "-loglevel", "error", "-y", "-i", s,
                             "-vf", "scale=-2:%d" % a.height,
                             "-c:v", "h264_videotoolbox", "-b:v", "3M",
                             "-c:a", "aac", "-ar", "48000", "-b:a", "128k",
                             "-movflags", "+faststart", o]).returncode
        if rc == 0 and os.path.exists(o):
            made.append({"src": s, "out": o, "seconds": round(time.time() - t0, 2),
                         "mb": round(os.path.getsize(o) / 1048576, 1)})
        else:
            print("[proxy] 失败：%s" % s)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "src": a.src, "out": a.out,
           "made": made, "skipped_uptodate": skipped, "verdict": "PASS"}
    json.dump(rec, open(os.path.join(a.out, "_last.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("[proxy] 出 %d 条审片副本，跳过 %d 条（已是最新）" % (len(made), skipped))
    for m in made:
        print("  - %s  %.2fs  %.1fMB" % (os.path.basename(m["out"]), m["seconds"], m["mb"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))