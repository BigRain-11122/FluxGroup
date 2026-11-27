#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_shot_pool.py — 把 mv0001 全部片段整理成「按镜头 ID 去重」的镜头池。

去重规则：
  - 同一个镜头 ID（B01/C01/INT3/KF7/...）只留一个版本
  - 优先 768p（1344x768），其次 480p（864x480，需上采样）
  - 同分同辨率时优先更新的目录（v730 > v729 > v728 > v727 > v723 > v5redo > int5/n02）
  - 输出 cph4/fleet/mv0001-handover/pool/SHOT-POOL.json
"""
import json
import os
import re
import subprocess

ROOT = r"K:\Fluxgroup\FluxGroup"
BASE = os.path.join(ROOT, "media", "MV", "mv0001")
OUT = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "pool")
FP = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

VER_RANK = {"v730-clips": 9, "v729-clips": 8, "v728-clips": 7, "v727-clips": 6,
            "v723-clips": 5, "cloud-v4": 4, "v5redo": 3, "int5-reburn-20261103": 2,
            "n02-reburn-20261103": 2, "v718-clips-768": 2, "v719-clips-768": 2}

# 镜头 ID 归并（把各种文件名前缀统一成镜头号）
PATS = [
    (r"^cut_(KF\d+|KFT)", lambda m: m.group(1)),
    (r"^(KF\d+|KFT)", lambda m: m.group(1)),
    (r"^(B0\d|C0\d|D0\d|D03b|E0\dc?|E04|SIL\d|N02|R0\d|SING\d?b?|INT\d|V56_SING\d)", lambda m: m.group(1)),
    (r"^(V718_S\d_\w+|V719_E\d+_\w+)", lambda m: m.group(1)),
]


def shot_id(fname):
    stem = os.path.splitext(fname)[0]
    for pat, fn in PATS:
        m = re.match(pat, stem)
        if m:
            return fn(m)
    return stem


def probe(p):
    try:
        o = subprocess.run([FP, "-v", "error", "-show_entries",
                            "format=duration:stream=width,height", "-of", "json", p],
                           capture_output=True, text=True, timeout=25).stdout
        d = json.loads(o)
        st = d["streams"][0]
        return round(float(d["format"]["duration"]), 3), st["width"], st["height"]
    except Exception:
        return None


def main():
    os.makedirs(OUT, exist_ok=True)
    best = {}
    for dp, dn, fn in os.walk(BASE):
        for f in fn:
            if not f.lower().endswith(".mp4"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, BASE)
            top = rel.split(os.sep)[0]
            pr = probe(p)
            if not pr:
                continue
            dur, w, h = pr
            if dur < 1.0:
                continue
            sid = shot_id(f)
            score = (1 if w >= 1200 else 0, VER_RANK.get(top, 1), dur)
            cur = best.get(sid)
            if cur is None or score > cur["_score"]:
                best[sid] = {"id": sid, "path": rel, "abs": p, "dur": dur,
                             "w": w, "h": h, "dir": top, "_score": score}

    pool = sorted(best.values(), key=lambda x: x["id"])
    for x in pool:
        x.pop("_score", None)

    json.dump({"root": BASE, "count": len(pool), "shots": pool},
              open(os.path.join(OUT, "SHOT-POOL.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    hi = [x for x in pool if x["w"] >= 1200]
    lo = [x for x in pool if x["w"] < 1200]
    print("SHOT POOL: %d 个不同镜头（768p %d / 480p %d），总时长 %.1fs"
          % (len(pool), len(hi), len(lo), sum(x["dur"] for x in pool)))
    print("768p:", ", ".join(x["id"] for x in hi))
    print("480p:", ", ".join(x["id"] for x in lo))


if __name__ == "__main__":
    main()
