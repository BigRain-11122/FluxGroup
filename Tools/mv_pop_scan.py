# -*- coding: utf-8 -*-
"""mv_pop_scan.py —— 区分「真切点」与「单帧弹出(flash/pop)」

判据（不需要计划切点表）：
  对每一处帧差突跳 N，量三个差：
    D1 = |f(N)   - f(N-1)|
    D2 = |f(N+1) - f(N)  |
    D3 = |f(N+1) - f(N-1)|
  · 真切点：画面整体换成新内容 → D3 ≈ D1 + D2（三角不等式接近取等）
  · 单帧弹出：f(N) 是离群帧，前后两帧近似 → D3 远小于 D1 + D2
  outlier = (D1 + D2 - D3) / (D1 + D2)，越接近 1 越像单帧弹出。

用法：python mv_pop_scan.py <video> [spike 列表文件或自动检测]
"""
import os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_gate as RG

VIDEO = sys.argv[1] if len(sys.argv) > 1 else \
    r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\full_mv_v601.mp4"
W, H = 240, 136
FS = W * H * 3


def grab(idx):
    """取指定帧（低分辨率 RGB）：顺序解码全片，只留需要的帧"""
    want = set(idx)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", VIDEO, "-vf",
                          "scale=%d:%d" % (W, H), "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE, bufsize=10**8)
    out = {}
    k = 0
    while True:
        b = p.stdout.read(FS)
        if len(b) < FS:
            break
        if k in want:
            out[k] = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.int16)
        k += 1
    p.stdout.close(); p.wait()
    return out


d = RG.frame_diffs(VIDEO)
_, spikes = RG.islands(d)
print("突跳 %d 处" % len(spikes))

need = []
for s in spikes:
    need += [s - 1, s, s + 1]
fr = grab(need)

rows = []
for s in spikes:
    if not all(k in fr for k in (s - 1, s, s + 1)):
        continue
    a, b, c = fr[s - 1], fr[s], fr[s + 1]
    D1 = float(np.abs(b - a).mean())
    D2 = float(np.abs(c - b).mean())
    D3 = float(np.abs(c - a).mean())
    out = (D1 + D2 - D3) / (D1 + D2) if (D1 + D2) else 0.0
    rows.append((s, s / 24.0, D1, D2, D3, out))

print("%6s %8s %7s %7s %7s %8s %s" % ("帧", "时间", "D1", "D2", "D3", "离群度", "判定"))
pops, cuts = [], []
for s, t, D1, D2, D3, out in rows:
    kind = "单帧弹出" if out >= 0.35 else "真切点"
    (pops if out >= 0.35 else cuts).append((s, t, out))
    print("%6d %8.3f %7.2f %7.2f %7.2f %8.2f %s" % (s, t, D1, D2, D3, out, kind))

print("\n单帧弹出 %d 处：%s" % (len(pops), ", ".join("%.2fs" % t for _, t, _ in pops)))
print("真切点  %d 处" % len(cuts))