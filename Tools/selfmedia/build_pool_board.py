#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_pool_board.py — 把剪辑表里的「不同素材镜」全部抽帧拼板，供逐镜过审。

为什么：CEO 2026-11-25「一个镜头一个镜头的过，不好就重烧」。
按片段时间轴看会重复看同一素材；按**唯一素材**看才是一次过完。

产物：BOARD-POOL-01..NN.jpg（每板 3x3，每格带 id/时长/素材名）
       POOL-INDEX.json（唯一素材清单 + 在原片出现次数 + 时间点）
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = "ffmpeg"
CELL_W = 426

ROOTS = [
    r"K:\Fluxgroup\FluxGroup\media\MV\mv0001",
    r"K:\Fluxgroup\FluxGroup\media\mv0001-handover",
    r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover",
    r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay",
]


def find(src):
    if not src:
        return None
    s = src.replace("\\", "/")
    if os.path.isabs(s) and os.path.exists(s):
        return s
    for r in ROOTS:
        p = os.path.join(r, s)
        if os.path.exists(p):
            return p
    # 尾部重锚
    parts = [x for x in s.split("/") if x]
    if len(parts) >= 2:
        tail = os.path.join(*parts[-2:])
        for r in ROOTS:
            cand = os.path.join(r, tail)
            if os.path.exists(cand):
                return cand
        name = parts[-1]
        for r in ROOTS:
            for dp, _dn, fs in os.walk(r):
                if name in fs:
                    return os.path.join(dp, name)
    return None


def probe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    try:
        return float((r.stdout or "0").strip().split(",")[0])
    except Exception:
        return 0.0


def grab(p, t, out, w=CELL_W):
    subprocess.run([FF, "-y", "-v", "error", "-ss", "%.3f" % max(0, t), "-i", p,
                    "-frames:v", "1", "-vf", "scale=%d:-2" % w, out], capture_output=True)
    return os.path.exists(out) and os.path.getsize(out) > 0


def label(im, lines):
    d = ImageDraw.Draw(im)
    h = 14 * len(lines) + 4
    d.rectangle([0, 0, im.width, h], fill=(0, 0, 0))
    for i, s in enumerate(lines):
        d.text((4, 2 + i * 14), s, fill=(255, 255, 255))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edl", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-board", type=int, default=9)
    a = ap.parse_args()

    plan = json.load(open(a.edl, encoding="utf-8"))
    shots = plan.get("plan") or plan.get("blocks") or []
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp()

    # 按 src 聚合（唯一素材）
    uniq = {}
    for s in shots:
        src = s.get("src") or ""
        if not src:
            continue
        key = os.path.basename(src.replace("\\", "/"))
        uniq.setdefault(key, {"src": src, "ids": [], "times": [], "durs": []})
        uniq[key]["ids"].append(s.get("id") or s.get("desc") or "?")
        uniq[key]["times"].append(float(s.get("t0") or 0))
        uniq[key]["durs"].append(float(s.get("dur") or (float(s.get("t1", 0)) - float(s.get("t0", 0)))))

    cells, index = [], []
    for key, v in uniq.items():
        path = find(v["src"])
        item = {"file": key, "src": v["src"], "found": bool(path),
                "appearances": len(v["times"]),
                "times": [round(t, 2) for t in v["times"]],
                "ids": v["ids"][:6], "total_dur": round(sum(v["durs"]), 2)}
        index.append(item)
        if not path:
            continue
        dur = probe_dur(path)
        mid = dur * 0.5
        png = os.path.join(tmp, key.replace(".mp4", "") + ".png")
        if grab(path, mid, png):
            im = Image.open(png).convert("RGB")
            lines = [key[:34], "%s x%d  %.2fs" % (item["ids"][0][:20], item["appearances"], dur)]
            cells.append(label(im, lines))

    json.dump(index, open(os.path.join(a.out, "POOL-INDEX.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # 拼板
    n = a.per_board
    boards = [cells[i:i + n] for i in range(0, len(cells), n)]
    for bi, group in enumerate(boards, 1):
        cols = 3
        rows = (len(group) + cols - 1) // cols
        cw, ch = group[0].size
        board = Image.new("RGB", (cw * cols, ch * rows), (12, 12, 12))
        for i, im in enumerate(group):
            board.paste(im, ((i % cols) * cw, (i // cols) * ch))
        p = os.path.join(a.out, "BOARD-POOL-%02d.jpg" % bi)
        board.save(p, quality=90)
        print("BOARD-POOL-%02d -> %s  %s  (%d cells)" % (bi, p, board.size, len(group)))

    print("unique assets: %d / found %d / total shots %d"
          % (len(uniq), sum(1 for x in index if x["found"]), len(shots)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
