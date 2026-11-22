#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aigc_label.py — 给成片加 AIGC 双标识（显式字卡 + 隐式元数据）

为什么（《人工智能生成合成内容标识办法》·2025-09-01 起）：
  AI 生成内容上线必须同时具备
    ① 显式标识：画面可见、用户能读到
    ② 隐式标识：文件元数据里可被平台/监管读到
  缺任一项 = 不合规。之前我们的成片两项都没有。

本工具做三件事（不改时长、不重编码画面主体）：
  1. 开场前 N 秒叠一行可见标识（默认 2.0s，右下角，不压人脸）
  2. 写入元数据：comment/description 里带 生成信息（ffmpeg -metadata）
  3. 落一份 .aigc.json 侧车（内容编号/生成方/模型/时间），供备案留痕

用法：
  python Tools/aigc_label.py --in cut.mp4 --out cut_labeled.mp4 [--seconds 2.0] [--scene 剧名-EP01]
Exit: 0 成功
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

LABEL_CN = "本剧由 AI 生成"
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]


def font():
    for f in FONT_CANDIDATES:
        if os.path.isfile(f):
            return f
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--seconds", type=float, default=2.0)
    ap.add_argument("--text", default=LABEL_CN)
    ap.add_argument("--scene", default="")
    ap.add_argument("--producer", default="BigStream / bm-c")
    ap.add_argument("--model", default="krea2 + minimax-h3")
    a = ap.parse_args()

    if not os.path.isfile(a.src):
        print("SRC MISSING", a.src)
        return 2
    f = font()
    if not f:
        print("FONT MISSING（需要 msyh/simhei/simsun 任一）")
        return 2

    esc_font = f.replace("\\", "/").replace(":", "\\:")

    # 2026-11-22 实测：drawbox 的 tw/th 别名不可靠（ffmpeg 报 code -22，整条链零输出）。
    # 正法=先 ffprobe 取宽高，字号/边距全用像素算；背景交给 drawtext 的 box（box=1）。
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                         "-show_entries", "stream=width,height", "-of", "csv=p=0", a.src],
                        capture_output=True, text=True)
    try:
        wpx, hpx = [int(x) for x in pr.stdout.strip().split(",")[:2]]
    except Exception:
        wpx, hpx = 1080, 1920
    fs = max(18, int(hpx * 0.028))
    pad = max(10, int(hpx * 0.010))
    vf = ("drawtext=fontfile='%s':text='%s':fontcolor=white@0.88:fontsize=%d:"
          "box=1:boxcolor=black@0.42:boxborderw=%d:"
          "x=w-tw-%d:y=h-th-%d:enable='lt(t,%.2f)'"
          % (esc_font, a.text, fs, pad, pad * 3, pad * 3, a.seconds))

    meta = {
        "comment": "AIGC: generated with %s by %s" % (a.model, a.producer),
        "description": "%s（AI 生成内容·显式标识前 %.1fs）" % (a.text, a.seconds),
        "copyright": a.producer,
        "encoder": "aigc_label.py",
    }
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.src, "-vf", vf]
    for k, v in meta.items():
        cmd += ["-metadata", "%s=%s" % (k, v)]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-movflags", "+faststart", a.dst]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("FAIL", (r.stderr or "")[-400:])
        return 1

    h = hashlib.sha256(open(a.dst, "rb").read()).hexdigest()
    side = os.path.splitext(a.dst)[0] + ".aigc.json"
    json.dump({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scene": a.scene, "producer": a.producer, "model": a.model,
        "explicit_label": "%s（前 %.1fs 可见）" % (a.text, a.seconds),
        "implicit_metadata": meta,
        "output": os.path.basename(a.dst), "sha256": h,
        "size_bytes": os.path.getsize(a.dst),
    }, open(side, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("AIGC LABEL OK %s (sha256=%s…) sidecar=%s" % (a.dst, h[:12], side))
    return 0


if __name__ == "__main__":
    sys.exit(main())
