# -*- coding: utf-8 -*-
"""mv_build_r02.py —— 重建 R02 镜（去人群重影，时长不变）

问题：源镜尾部（约等于成片 118.0s 之后）人群里长出一张与女主同脸的头，
      属于 i2v 身份复制，必须切掉；但整镜窗长 90 帧不能变。

做法：干净段 1:1 使用（帧 2754..2803），剩下 40 帧用干净尾段
      （帧 2804..2828，25 帧）做**渐减速**重采样：入点 1.2 倍慢、切点前 2.7 倍慢，
      速度线性过渡，不出现突然定格。输出恒为 90 帧 / CFR 24。
"""
import os, subprocess, sys
import numpy as np

SRC = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\full_mv_v601.mp4"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"D:\FleetWorker\review\R02_fix2.mp4"
W, H = 1344, 768
A0, A1 = 2754, 2804          # 干净段 1:1（50 帧）
B0, B1 = 2804, 2829          # 尾段素材（25 帧）→ 40 帧
NOUT = 90
FS = W * H * 3


def load(idx):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf",
                          "select='between(n\\,%d\\,%d)'" % (idx[0], idx[-1]),
                          "-fps_mode", "passthrough", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE, bufsize=10**8)
    out = {}
    want = set(idx)
    k = idx[0]
    while k <= idx[-1]:
        b = p.stdout.read(FS)
        if len(b) < FS:
            break
        if k in want:
            out[k] = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        k += 1
    p.stdout.close(); p.wait()
    return out


idx = list(range(A0, A1)) + list(range(B0, B1))
fr = load(idx)
if len(fr) != len(idx):
    sys.exit("取帧不足：%d / %d" % (len(fr), len(idx)))

nB = NOUT - (A1 - A0)                        # 40
steps = np.linspace(0.83, 0.37, nB)          # 每输出帧推进多少个源帧
steps *= (B1 - B0 - 1) / steps.sum()         # 归一到正好用完 24 帧跨度

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", "24",
                        "-i", "-", "-an", "-c:v", "libx264", "-crf", "17",
                        "-preset", "fast", "-pix_fmt", "yuv420p", "-r", "24", OUT],
                       stdin=subprocess.PIPE)

n = 0
for f in range(A0, A1):
    enc.stdin.write(fr[f].tobytes()); n += 1

buf = [fr[f].astype(np.float32) for f in range(B0, B1)]
pos = 0.0
for i in range(nB):
    i0 = min(int(pos), len(buf) - 2)
    a = pos - i0
    out = buf[i0] * (1 - a) + buf[i0 + 1] * a
    enc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes()); n += 1
    pos += steps[i]

enc.stdin.close(); enc.wait()
print("R02 重建完成 %s  共 %d 帧（1:1 %d + 渐减速 %d）" % (OUT, n, A1 - A0, nB))