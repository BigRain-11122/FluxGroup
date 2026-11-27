#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_dedupe.py - 素材库感知哈希去重（训练前必做）。

为什么：同一张图重复入训练集会让 LoRA 过拟合；不同分辨率/轻微改色的重复图
用 sha256 抓不到，必须用感知哈希（dHash + aHash）。

做法：PIL 转 9x8 灰度算 dHash(64bit)、8x8 算 aHash(64bit)；
汉明距离 <= threshold 即判近重复（默认 6），并输出可读报告。

用法：
  python3 Tools/fleet/asset_dedupe.py --dir <dir> [--recursive] [--jobs 8] [--threshold 6]
Exit: 0 无重复；1 发现近重复；2 目录不存在
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "asset-dedupe.json")
IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def hashes(path):
    with Image.open(path) as im:
        g = im.convert("L").resize((9, 8), Image.LANCZOS)
        px = list(g.getdata())
        d = 0
        for r in range(8):
            for c in range(8):
                d = (d << 1) | (1 if px[r * 9 + c] > px[r * 9 + c + 1] else 0)
        g2 = im.convert("L").resize((8, 8), Image.LANCZOS)
        p2 = list(g2.getdata())
        avg = sum(p2) / 64.0
        a = 0
        for v in p2:
            a = (a << 1) | (1 if v > avg else 0)
    return d, a


def collect(base, recursive):
    out = []
    if recursive:
        for d, _s, fs in os.walk(base):
            for n in fs:
                if n.lower().endswith(IMG):
                    out.append(os.path.join(d, n))
    else:
        for n in sorted(os.listdir(base)):
            p = os.path.join(base, n)
            if os.path.isfile(p) and n.lower().endswith(IMG):
                out.append(p)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--threshold", type=int, default=6)
    ap.add_argument("--json", default=OUT)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        print("[dedupe] 目录不存在 %s（rc=2）" % a.dir)
        return 2
    files = collect(a.dir, a.recursive)
    if not files:
        print("[dedupe] 没有图片（rc=2）")
        return 2
    t0 = time.time()
    recs, failed = [], []

    def work(p):
        try:
            d, h = hashes(p)
            return {"path": p, "d": d, "a": h, "bytes": os.path.getsize(p)}
        except Exception as e:
            failed.append({"path": p, "why": str(e)[:60]})
            return None

    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for r in ex.map(work, files):
            if r:
                recs.append(r)

    dup = []
    n = len(recs)
    for i in range(n):
        for j in range(i + 1, n):
            dd = bin(recs[i]["d"] ^ recs[j]["d"]).count("1")
            da = bin(recs[i]["a"] ^ recs[j]["a"]).count("1")
            if dd <= a.threshold or da <= a.threshold:
                dup.append({"a": recs[i]["path"], "b": recs[j]["path"],
                            "d_hash_dist": dd, "a_hash_dist": da})
    res = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "dir": a.dir, "images": n,
           "failed": failed[:50], "threshold": a.threshold,
           "duplicate_pairs": dup[:500], "dup_pairs": len(dup),
           "seconds": round(time.time() - t0, 1),
           "verdict": "DUPES" if dup else "CLEAN"}
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("[dedupe] %d 张，用时 %.1fs，近重复对 %d%s"
          % (n, res["seconds"], len(dup), ("（失败 %d）" % len(failed)) if failed else ""))
    for p in dup[:8]:
        print("  ~ %s == %s (d=%d a=%d)" % (os.path.basename(p["a"]),
                                            os.path.basename(p["b"]),
                                            p["d_hash_dist"], p["a_hash_dist"]))
    return 0 if not dup else 1


if __name__ == "__main__":
    sys.exit(main())