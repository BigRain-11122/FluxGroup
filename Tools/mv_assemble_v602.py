# -*- coding: utf-8 -*-
"""mv_assemble_v602.py —— 在 v601 上做单次成型修补（不重复编码多次）

修补项：
  · R02 整镜替换（2754..2843 共 90 帧，来自 R02_fix3.mp4）
  · 单帧弹出平滑（对指定帧把突变摊到 7 帧，不删帧不动时间轴）

用法：
  python mv_assemble_v602.py <out.mp4> [--pops 139,856,...]
"""
import argparse, os, subprocess, sys
import numpy as np

SRC = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\full_mv_v601.mp4"
R02 = r"D:\FleetWorker\review\R02_fix3.mp4"
W, H = 1344, 768
FPS = 24
R0, R1 = 2754, 2844          # R02 窗（含头不含尾）
FS = W * H * 3

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--pops", default="")
a = ap.parse_args()
pops = [int(x) for x in a.pops.split(",") if x.strip()]

# ---- 读 R02 新段 ----
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", R02, "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10**8)
r02 = []
while True:
    b = p.stdout.read(FS)
    if len(b) < FS:
        break
    r02.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
p.stdout.close(); p.wait()
assert len(r02) == R1 - R0, "R02 帧数 %d != %d" % (len(r02), R1 - R0)

# ---- 弹出平滑计划：s-2..s+3 用 f(s-3)..f(s+4) 线性过渡 ----
plan = {}                     # idx -> (i0, i1, t)  取值 = lerp(A,B,t)
for s in pops:
    for k in range(s - 2, s + 4):
        plan[k] = (s - 3, s + 4, (k - (s - 3)) / 7.0)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10**8)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
                        "-i", "-", "-an", "-c:v", "libx264", "-crf", "17",
                        "-preset", "fast", "-profile:v", "high", "-g", "12",
                        "-pix_fmt", "yuv420p", "-r", str(FPS), a.out],
                       stdin=subprocess.PIPE)

LOOK = 14
buf = {}
nxt = 0


def frame(i):
    global nxt
    while nxt <= i:
        b = dec.stdout.read(FS)
        if len(b) < FS:
            return None
        buf[nxt] = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        nxt += 1
    return buf.get(i)


n = 0
i = 0
while True:
    if i >= R0 and i < R1:
        out = r02[i - R0]
    elif i in plan:
        i0, i1, t = plan[i]
        A, B = frame(i0), frame(i1)
        if A is None or B is None:
            break
        out = (A.astype(np.float32) * (1 - t) + B.astype(np.float32) * t)
        out = np.clip(out, 0, 255).astype(np.uint8)
    else:
        out = frame(i)
        if out is None:
            break
    enc.stdin.write(out.tobytes())
    n += 1
    buf.pop(i - LOOK, None)
    i += 1

enc.stdin.close(); enc.wait()
dec.stdout.close(); dec.wait()
print("视频成型完成 %s  %d 帧" % (a.out, n))
if n != 5623:
    sys.exit("FATAL 帧数 %d != 5623" % n)

# ---- 合回原音轨（不变）----
tmp = a.out + ".v.mp4"
os.replace(a.out, tmp)
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", SRC,
                    "-map", "0:v", "-map", "1:a", "-c", "copy",
                    "-movflags", "+faststart", a.out], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("合音轨失败: " + r.stderr[:400])
os.remove(tmp)
print("已成片（含原音轨）:", a.out)