# -*- coding: utf-8 -*-
"""mv_local_patch.py —— 局部去鬼影补丁（羽化椭圆内做模糊+压暗）

用途：玻璃/镜面里淡入的可辨人脸，用"该区域失焦"的方式消掉可辨认度，
      不改变构图、不改帧数、不动时间轴。

用法：
    python mv_local_patch.py in.mp4 out.mp4 --cx 1240 --cy 240 --rx 110 --ry 140 \
        [--feather 45] [--blur 14] [--darken 0.10] [--f0 0] [--f1 9999]
"""
import argparse, os, subprocess, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("--cx", type=int, required=True)
ap.add_argument("--cy", type=int, required=True)
ap.add_argument("--rx", type=int, required=True)
ap.add_argument("--ry", type=int, required=True)
ap.add_argument("--feather", type=int, default=45)
ap.add_argument("--blur", type=int, default=16)
ap.add_argument("--darken", type=float, default=0.10)
ap.add_argument("--f0", type=int, default=0, help="起始帧(含)")
ap.add_argument("--f1", type=int, default=10**9, help="结束帧(不含)")
a = ap.parse_args()

probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", a.src],
                       capture_output=True, text=True)
W, H = [int(x) for x in probe.stdout.strip().split(",")[:2]]

# 羽化掩膜：中心 1，向外平滑降到 0（无硬边）
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dx = (xx - a.cx) / float(a.rx)
dy = (yy - a.cy) / float(a.ry)
r = np.sqrt(dx * dx + dy * dy)                      # 椭圆归一化半径
soft = a.feather / float(max(a.rx, a.ry))           # 羽化占半径比例
t = np.clip((1.0 - r) / max(soft, 1e-3), 0.0, 1.0)
mask = (t * t * (3.0 - 2.0 * t)).astype(np.float32)  # smoothstep
mask3 = mask[:, :, None]

# 模糊图先由 ffmpeg 生成（boxblur 两遍逼近高斯）；blur=0 表示只压暗不模糊
blur_src = a.src + ".blur.mp4"
if a.blur > 0:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src,
                    "-vf", "boxblur=%d:%d" % (a.blur, max(1, a.blur // 3)),
                    "-an", "-c:v", "libx264", "-crf", "14", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", blur_src], check=True)

def reader(p):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-i", p, "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE, bufsize=10**8)

p1 = reader(a.src)
p2 = reader(blur_src) if a.blur > 0 else None
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", "24",
                        "-i", "-", "-an", "-c:v", "libx264", "-crf", "17",
                        "-preset", "fast", "-pix_fmt", "yuv420p", a.dst],
                       stdin=subprocess.PIPE)
fs = W * H * 3
k = 0
touched = 0
while True:
    b1 = p1.stdout.read(fs)
    b2 = p2.stdout.read(fs) if p2 else b""
    if len(b1) < fs or (p2 and len(b2) < fs):
        break
    if a.f0 <= k < a.f1:
        f = np.frombuffer(b1, np.uint8).reshape(H, W, 3).astype(np.float32)
        f = f * (1.0 - a.darken * mask3)
        if p2:
            g = np.frombuffer(b2, np.uint8).reshape(H, W, 3).astype(np.float32)
            out = f * (1.0 - mask3) + g * mask3
        else:
            out = f
        enc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
        touched += 1
    else:
        enc.stdin.write(b1)
    k += 1

enc.stdin.close()
enc.wait()
p1.stdout.close()
p1.wait()
if p2:
    p2.stdout.close()
    p2.wait()
try:
    os.remove(blur_src)
except OSError:
    pass
print("补丁完成 %s  共 %d 帧，处理 %d 帧  区域=(%d,%d) r=(%d,%d)" %
      (a.dst, k, touched, a.cx, a.cy, a.rx, a.ry))