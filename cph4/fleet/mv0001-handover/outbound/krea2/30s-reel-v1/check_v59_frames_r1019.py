# -*- coding: utf-8 -*-
# check_v59_frames_r1019.py — V5.9 终渲帧级复验抽取器（七批修复点全探针）
# 抽 14 帧全分辨率 + 拼两板（板A=字卡/硬切/T桥/收束·板B=N02/D08/SING2/SING3b 内容镜）
import os, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, "full_mv_v59.mp4")
O = os.path.join(HERE, "final_review_director", "v59fix_locate")
os.makedirs(O, exist_ok=True)

PROBES = [
    # (序号, 秒, 板位)  板A=a 板B=b
    ("a", 5.00),   # 字卡：主标+L1 错峰态
    ("a", 6.20),   # 字卡：三行全显+渐变带
    ("a", 21.86),  # 硬切前帧（S1 火焰尾+火焰贴缘修复继承）
    ("a", 21.96),  # 硬切后帧（S2 起·riff 拍卡点）
    ("a", 39.30),  # T 桥金字 match dissolve 中段
    ("a", 41.20),  # T→G0 dissolve 出段
    ("a", 228.30), # 227.50 灯暗黑场 fade 落位（Z03 灯灭）
    ("b", 52.00),  # N02 观展表演（转身读楔文）
    ("b", 53.50),  # N02 俯身凝视
    ("b", 169.00), # D08 沙掠碑面（替换乱入动画）
    ("b", 171.00), # D08 后段
    ("b", 181.00), # SING2 开口唱
    ("b", 198.00), # SING3b 张口回环
    ("b", 232.80), # 尾段字存
]
for i, (board, ts) in enumerate(PROBES):
    subprocess.run([FF, "-y", "-ss", "%.2f" % ts, "-i", V, "-frames:v", "1", "-q:v", "3",
                    "-update", "1", os.path.join(O, "v59chk_%s%d.jpg" % (board, i))],
                   capture_output=True)

def board(letter, name):
    files = sorted((f for f in os.listdir(O) if f.startswith("v59chk_%s" % letter)),
                   key=lambda f: int(re.findall(r"\d+", f)[-1]))
    for j, f in enumerate(files):
        os.replace(os.path.join(O, f), os.path.join(O, "p%d.jpg" % j))
    subprocess.run([FF, "-y", "-framerate", "1", "-i", os.path.join(O, "p%d.jpg"),
                    "-vf", "scale=480:270,tile=%dx1" % len(files), "-frames:v", "1",
                    "-q:v", "4", "-update", "1", os.path.join(O, name)], capture_output=True)
    print("BOARD -> %s (%d frames)" % (name, len(files)), flush=True)

board("a", "V59CHK-BOARD-A.jpg")
board("b", "V59CHK-BOARD-B.jpg")
print("V59CHK DONE", flush=True)
