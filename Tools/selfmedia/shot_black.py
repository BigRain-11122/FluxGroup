# -*- coding: utf-8 -*-
"""shot_black.py — 逐镜测片头/片尾黑帧长度（AI 素材常见 0.2-0.6s 黑起黑收）。"""
import json
import os
import re
import subprocess

ROOT = r"K:\Fluxgroup\FluxGroup"
POOL = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "pool", "SHOT-POOL.json")
OUT = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "pool", "SHOT-BLACK.json")
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"

shots = json.load(open(POOL, encoding="utf-8"))["shots"]
res = {}
for s in shots:
    src = os.path.join(ROOT, "media", "MV", "mv0001", s["path"])
    r = subprocess.run([FF, "-hide_banner", "-i", src, "-vf",
                        "blackdetect=d=0.04:pix_th=0.10", "-f", "null", "NUL"],
                       capture_output=True, text=True, errors="replace", timeout=120)
    spans = [(float(m.group(1)), float(m.group(2))) for m in
             re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    head = 0.0
    tail = 0.0
    for a, b in spans:
        if a <= 0.05:
            head = max(head, b)
        if b >= s["dur"] - 0.06:
            tail = max(tail, s["dur"] - a)
    res[s["id"]] = {"dur": s["dur"], "head_black": round(head, 3), "tail_black": round(tail, 3),
                    "spans": [[round(a, 2), round(b, 2)] for a, b in spans]}

json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("BLACK measured %d" % len(res))
for k, v in sorted(res.items(), key=lambda kv: -kv[1]["head_black"])[:15]:
    if v["head_black"] > 0.05 or v["tail_black"] > 0.05:
        print("  %-22s dur=%.2f 头黑=%.2f 尾黑=%.2f" % (k, v["dur"], v["head_black"], v["tail_black"]))
