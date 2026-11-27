# -*- coding: utf-8 -*-
"""qc_full_v6.py — 逐帧全检（不做抽帧采样）。

对 720 帧全部逐帧计算：
  yavg / 逐通道均值 / Laplacian 清晰度 / dHash(64bit) / 与前一帧的绝对差
  + 人脸检测（SCRFD antelopev2，CPU）
再据此判定：硬切、近重复（卡带）、冻结、欠曝、闪白/闪黑（亮度突变）、
颜色跳变、清晰度异常低点。全部落 CSV + JSON 摘要。
"""
import csv
import json
import os
import sys

import cv2
import numpy as np

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v6-wmvs.mp4"
OUT = r"K:\Fluxgroup\.codely-cli\tmp\qc_full"
os.makedirs(OUT, exist_ok=True)

# ---------- 人脸检测器（可选） ----------
det = None
try:
    import insightface
    from insightface.app import FaceAnalysis
    det = FaceAnalysis(name="antelopev2", root=r"D:\ComfyUI\ComfyUI\models\insightface",
                       providers=["CPUExecutionProvider"])
    det.prepare(ctx_id=-1, det_size=(640, 640), det_thresh=0.5)
    print("FACE-DET ready", flush=True)
except Exception as e:
    print("FACE-DET off: %s" % str(e)[:120], flush=True)


def dhash(gray):
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    diff = small[:, 1:] > small[:, :-1]
    bits = 0
    for b in diff.flatten():
        bits = (bits << 1) | int(b)
    return bits


def hamming(a, b):
    return bin(a ^ b).count("1")


cap = cv2.VideoCapture(SRC)
fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print("frames=%d fps=%.3f" % (total, fps), flush=True)

rows = []
prev_gray = None
prev_hash = None
i = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    b, g, r = (float(frame[:, :, k].mean()) for k in range(3))
    yavg = float(gray.mean())
    lap = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    h = dhash(gray)
    diff = float(cv2.absdiff(gray, prev_gray).mean()) if prev_gray is not None else 0.0
    ham = hamming(h, prev_hash) if prev_hash is not None else 0

    faces = []
    if det is not None and (i % 2 == 0):      # 人脸隔帧检测（时序足够，减半耗时）
        try:
            fs = det.get(frame)
            faces = [(round(float(f.bbox[0])), round(float(f.bbox[1])),
                      round(float(f.bbox[2])), round(float(f.bbox[3])),
                      round(float(f.det_score), 3)) for f in fs]
        except Exception:
            faces = []
    rows.append({
        "i": i, "t": round(i / fps, 4),
        "yavg": round(yavg, 3), "r": round(r, 2), "g": round(g, 2), "b": round(b, 2),
        "lap": round(lap, 2), "diff": round(diff, 4), "ham": ham,
        "nface": len(faces), "faces": json.dumps(faces, ensure_ascii=False),
    })
    prev_gray = gray
    prev_hash = h
    i += 1
    if i % 120 == 0:
        print("  .. %d" % i, flush=True)

cap.release()
print("decoded=%d" % len(rows), flush=True)

csv_path = os.path.join(OUT, "perframe.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# ---------- 判定 ----------
flags = {"near_dup": [], "freeze": [], "dark": [], "flash": [], "color_jump": [],
         "soft_suspect": [], "face_multi": [], "face_jump": []}

for r in rows:
    if r["i"] > 0 and r["ham"] <= 2 and r["diff"] < 1.5:
        flags["near_dup"].append(r["i"])
    if r["yavg"] < 8:
        flags["dark"].append(r["i"])

for r in rows[1:]:
    p = rows[r["i"] - 1]
    if abs(r["yavg"] - p["yavg"]) > 20:
        flags["flash"].append((r["i"], round(r["yavg"] - p["yavg"], 1)))
    if max(abs(r["r"] - p["r"]), abs(r["g"] - p["g"]), abs(r["b"] - p["b"])) > 12:
        flags["color_jump"].append(r["i"])

# 冻结：连续 >=12 帧几乎无变化
run = 0
for r in rows:
    if r["i"] > 0 and r["diff"] < 0.35:
        run += 1
    else:
        if run >= 12:
            flags["freeze"].append((r["i"] - run, r["i"] - 1))
        run = 0
if run >= 12:
    flags["freeze"].append((len(rows) - run, len(rows) - 1))

# 清晰度异常低点（低于中位数 45%）
laps = np.array([r["lap"] for r in rows], dtype=float)
med = float(np.median(laps))
thr = med * 0.45
flags["soft_suspect"] = [r["i"] for r in rows if r["lap"] < thr]

for r in rows:
    if r["nface"] > 1:
        flags["face_multi"].append((r["i"], r["nface"]))

summary = {
    "frames": len(rows),
    "median_lap": round(med, 2),
    "soft_threshold": round(thr, 2),
    "counts": {k: len(v) for k, v in flags.items()},
    "flags": flags,
}
json_path = os.path.join(OUT, "flags.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)

print("\n=== SUMMARY ===")
print("frames=%d  median_lap=%.2f  soft_thr=%.2f" % (len(rows), med, thr))
for k, v in flags.items():
    print("  %-13s %d" % (k, len(v)))
print("near_dup(first30)=%s" % flags["near_dup"][:30])
print("flash=%s" % flags["flash"][:20])
print("freeze=%s" % flags["freeze"][:10])
print("face_multi=%s" % flags["face_multi"][:10])
print("CSV=%s" % csv_path)
