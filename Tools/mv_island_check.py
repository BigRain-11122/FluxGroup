# -*- coding: utf-8 -*-
"""mv_island_check.py —— 孤岛真伪判定（跨岛净变化量）

对每个孤岛 (s..e)：
  D3 = |f(e) - f(s-1)|   —— 跨岛之后画面到底变了多少
  Dm = 岛内最大单帧差
真转场：D3 大（画面确实换掉），岛只是"切点 + 新镜首帧还在动"；
真假叠化/鬼影：D3 小（画面几乎没变）却被抬高的中间帧撑成"双峰"。
判据：D3 < 12 → 真缺陷（闪烁/残影）；否则 = 转场。
"""
import os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_gate as RG

VIDEO = sys.argv[1] if len(sys.argv) > 1 else r"D:\FleetWorker\review\full_mv_v602.mp4"
W, H = 240, 136
FS = W * H * 3

d = RG.frame_diffs(VIDEO)
isl, spike = RG.islands(d)
need = set()
for s, e in isl:
    need |= {s - 1, e}
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", VIDEO, "-vf",
                      "scale=%d:%d" % (W, H), "-fps_mode", "passthrough",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     stdout=subprocess.PIPE, bufsize=10**8)
fr, k = {}, 0
while True:
    b = p.stdout.read(FS)
    if len(b) < FS:
        break
    if k in need:
        fr[k] = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.int16)
    k += 1
p.stdout.close(); p.wait()

bad = []
print("%7s %7s %6s %8s %8s" % ("起帧", "止帧", "最大差", "跨岛净变", "判定"))
for s, e in isl:
    if s - 1 not in fr or e not in fr:
        continue
    D3 = float(np.abs(fr[e] - fr[s - 1]).mean())
    Dm = max(float(d[s - 1]), float(d[e - 1]))
    kind = "真缺陷" if D3 < 12 else "转场"
    if kind == "真缺陷":
        bad.append((s, e, D3))
    print("%7d %7d %6.1f %8.1f %8s" % (s, e, Dm, D3, kind))

print("\n孤岛 %d 处，其中真缺陷 %d 处%s" %
      (len(isl), len(bad), ("：" + ", ".join("%.2fs-%.2fs" % (a / 24, b / 24) for a, b, _ in bad)) if bad else ""))