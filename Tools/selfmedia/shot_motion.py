# -*- coding: utf-8 -*-
"""shot_motion.py — 逐镜量运动曲线，找出「动作峰值」，供剪切入点使用。

为什么（CEO 令「AI 图生视频都是 5 秒、速度很平均，务必用剪辑技巧解决」）：
  AI 镜头内部是匀速微动，直接整段播放 = 5 秒一个节拍，必然发木。
  正法有三：①切在动作峰值前 0.3-0.4s（刀落在"动"上）；②每镜只取 2-3.5s，永不放满；
  ③同一镜重演时换切入 + 推近（punch-in），让观众以为是新镜头。

输出：pool/SHOT-MOTION.json  {id: {dur, peak_t, mean_motion, motion_at:[...]}}
"""
import json
import os
import subprocess

import numpy as np

ROOT = r"K:\Fluxgroup\FluxGroup"
POOL = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "pool", "SHOT-POOL.json")
OUT = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "pool", "SHOT-MOTION.json")
TMP = r"K:\Fluxgroup\.codely-cli\tmp\motion"
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"

os.makedirs(TMP, exist_ok=True)
shots = json.load(open(POOL, encoding="utf-8"))["shots"]
res = {}

for s in shots:
    src = os.path.join(ROOT, "media", "MV", "mv0001", s["path"])
    out = os.path.join(TMP, s["id"].replace(os.sep, "_") + ".mp4")
    # 抽成 6fps 灰度小图，够算运动量
    subprocess.run([FF, "-y", "-i", src, "-vf", "fps=6,scale=192:-2,format=gray",
                    "-c:v", "rawvideo", "-f", "rawvideo", out], capture_output=True)
    try:
        raw = np.fromfile(out, dtype=np.uint8)
        fr = 192 * int(round(192 * s["h"] / s["w"] / 2)) * 2
    except Exception:
        continue
    # 由像素总数反推每帧字节数
    if raw.size == 0:
        continue
    per = None
    for guess_h in range(80, 220, 2):
        if raw.size % (192 * guess_h) == 0:
            per = 192 * guess_h
            if per * 30 <= raw.size <= per * 200:
                break
    if not per:
        continue
    n = raw.size // per
    frames = raw[:n * per].reshape(n, per).astype(np.float32)
    if n < 6:
        continue
    d = np.abs(np.diff(frames, axis=0)).mean(axis=1)      # 每对相邻帧的平均差
    peak_i = int(np.argmax(d))
    res[s["id"]] = {
        "dur": s["dur"], "w": s["w"], "h": s["h"], "path": s["path"],
        "peak_t": round(peak_i / 6.0, 3),
        "mean_motion": round(float(d.mean()), 3),
        "p90_motion": round(float(np.percentile(d, 90)), 3),
        "first_half": round(float(d[:len(d) // 2].mean()), 3),
        "second_half": round(float(d[len(d) // 2:].mean()), 3),
    }

json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("MOTION measured %d shots -> %s" % (len(res), OUT))
for k in sorted(res)[:40]:
    v = res[k]
    print("  %-22s dur=%4.1f peak=%4.2fs  motion=%.2f/%.2f(前半/后半)"
          % (k, v["dur"], v["peak_t"], v["first_half"], v["second_half"]))
