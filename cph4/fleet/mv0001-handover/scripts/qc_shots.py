# -*- coding: utf-8 -*-
"""按硬切分段，输出每镜的逐帧统计（亮度/清晰度/运动量/闪烁）。"""
import csv
import os
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = r"K:\Fluxgroup\.codely-cli\tmp\qc_full"
rows = list(csv.DictReader(open(os.path.join(D, "perframe.csv"), encoding="utf-8")))
for r in rows:
    for k in ("yavg", "lap", "diff", "r", "g", "b"):
        r[k] = float(r[k])
    r["i"] = int(r["i"])
    r["ham"] = int(r["ham"])

fps = 24.0
cuts = [0]
for k in range(1, len(rows)):
    if rows[k]["diff"] > 12 or rows[k]["ham"] > 28:
        cuts.append(rows[k]["i"])
cuts.append(len(rows))

print("%-14s %-6s %-5s %-24s %-22s %s" % ("区间(秒)", "帧数", "时长", "亮度 mean/min/max", "清晰度 mean/min", "运动 diff mean/max"))
for a, b in zip(cuts[:-1], cuts[1:]):
    seg = [r for r in rows if a <= r["i"] < b]
    if not seg:
        continue
    ys = [x["yavg"] for x in seg]
    ls = [x["lap"] for x in seg]
    ds = [x["diff"] for x in seg]
    # 闪烁：相邻帧亮度差的平均绝对值（去掉切点首帧）
    osc = sum(abs(seg[k]["yavg"] - seg[k - 1]["yavg"]) for k in range(1, len(seg))) / max(1, len(seg) - 1)
    print("%6.2f-%6.2f %5d %5.2fs %6.1f/%5.1f/%5.1f  %7.1f/%6.1f  %5.2f/%5.2f  osc=%.2f  %s"
          % (a / fps, b / fps, len(seg), len(seg) / fps,
             sum(ys) / len(ys), min(ys), max(ys),
             sum(ls) / len(ls), min(ls),
             sum(ds) / len(ds), max(ds), osc,
             "近静止" if sum(ds) / len(ds) < 2.0 else ""))
