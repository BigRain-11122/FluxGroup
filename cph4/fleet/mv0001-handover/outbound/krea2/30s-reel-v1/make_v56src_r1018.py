# -*- coding: utf-8 -*-
# make_v56src_r1018.py — V5.6 五件预切源复现脚本（build_full_mv_v56.py 供料·2026-10-18）
# Why：v56src/*.mp4 落 gitignore 媒体红线不入库——本件以精确 ffmpeg 参数入 git 保证可复现
#      （J-32 断言链的可复现性面：任何人拉库后跑本件即可重建五源，字节级一致依赖同版 ffmpeg）。
# 溯源：orders 2026-10-18 11:4x CEO V5.5 终审反馈行·导演席 V5.6 快改四件套。
import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
V5REDO = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo"
SEG = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments"
OUT = os.path.join(HERE, "v56src")
os.makedirs(OUT, exist_ok=True)
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-an"]

JOBS = [
    # R 拓片微距：INT3 源 0.30-1.90s·裁 (0,282,846,476)·lanczos 放大 1.59x·轻锐化
    ("V56_R_rubbing_macro.mp4", [os.path.join(V5REDO, "INT3_photo_stare_v5.mp4")],
     ["-ss", "0.30", "-t", "1.60",
      "-vf", "crop=846:476:0:282,scale=1344:768:flags=lanczos,unsharp=5:5:0.35"]),
    # P 笔尖落笔微距：INT1 源 2.60-4.88s（与 A 镜 0-2.55s 零重叠段）·裁 (188,408,640,360)·2.1x
    ("V56_P_pen_macro.mp4", [os.path.join(V5REDO, "INT1_desk_breath_v5.mp4")],
     ["-ss", "2.60", "-t", "2.28",
      "-vf", "crop=640:360:188:408,scale=1344:768:flags=lanczos,unsharp=5:5:0.40"]),
    # C 凝视续接段：INT3 源 1.90s 起（R 微距的 matched-cut 续接·同动作跨景别）
    ("V56_C_gaze_seg.mp4", [os.path.join(V5REDO, "INT3_photo_stare_v5.mp4")],
     ["-ss", "1.90", "-t", "3.10"]),
    # E2 抬眼段：INT5 源 1.50s 起（避首帧划痕段）·墙面亮块 delogo（修复区 x636-740/y188-312）
    ("V56_E2_lookup_seg.mp4", [os.path.join(V5REDO, "INT5_head_bow_v5.mp4")],
     ["-ss", "1.50", "-t", "3.50", "-vf", "delogo=x=636:y=188:w=104:h=124"]),
    # SING3b 替换源：SING1 火炬尾段 2.88-4.88s（与 78s 头段零重叠）·punch-in 1.12x·微压暗
    ("V56_SING1_reprise.mp4", [os.path.join(SEG, "SING1_torch_song_v2_s9013.mp4")],
     ["-ss", "2.88", "-t", "2.00",
      "-vf", "crop=1196:684:74:42,scale=1344:768:flags=lanczos,eq=brightness=-0.02:saturation=1.03"]),
]

for name, inputs, vf_args in JOBS:
    dst = os.path.join(OUT, name)
    # 解析：vf_args 形如 ["-ss", x, "-t", y, ...]（input 段）+ 可选 ["-vf", ...]（output 段）
    in_args, out_args = [], []
    i = 0
    while i < len(vf_args):
        if vf_args[i] == "-vf":
            out_args = ["-vf", vf_args[i + 1]]
            break
        in_args.append(vf_args[i]); in_args.append(vf_args[i + 1]); i += 2
    full = ["ffmpeg", "-y", "-loglevel", "error"] + in_args + ["-i", inputs[0]] + out_args + ENC + [dst]
    subprocess.run(full, check=True)
    print("SRC -> %s (%.0fKB)" % (dst, os.path.getsize(dst) / 1024), flush=True)
print("V56SRC DONE (5/5)", flush=True)
