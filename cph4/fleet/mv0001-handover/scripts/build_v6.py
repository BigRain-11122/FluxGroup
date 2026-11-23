# -*- coding: utf-8 -*-
"""build_v6.py — 爱在西元前 30s v6：石板 v2 替换 + AIGC 显式标识 + 片尾署名。

相对 v5 只动三处，时间轴零漂移：
  1) 22.75-24.75s 石碑镜 → stele-v2.png（真楔文 + 裂纹/麻点/崩口 + 左射火炬光；不加推拉，只留光呼吸）
  2) 00.80-03.20s 「AI 生成合成内容」（字高 44px ≥ 画面高 5%，持续 2.4s ≥ 2s）
  3) 27.40-30.00s 片尾署名 + 二创/AIGC 声明
  音轨原样 copy。

判例：drawtext 的中文**不能写进 -filter_complex_script**（ffmpeg 按 ANSI 解析脚本，
中文变乱码并打断引号配对，报 'Invalid argument'）——一律 textfile= 传 UTF-8 文本，
filter 脚本保持纯 ASCII。
"""
import os
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(BASE, "30s_reel_v5_cuneiform.mp4")
STELE = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\v6\stele-v2.png"
TMP = r"K:\Fluxgroup\.codely-cli\tmp\v6"
OUT_DIR = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable"
OUT = os.path.join(OUT_DIR, "爱在西元前-30s-v6-优化版.mp4")
FONT_SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FONT_SANS = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

W, H, FPS = 1344, 768, 24
A, B, C = 22.75, 2.00, 24.75
os.makedirs(TMP, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

for p in (SRC, STELE, FONT_SERIF, FONT_SANS):
    if not os.path.exists(p):
        raise SystemExit("FATAL missing: " + p)


def run(cmd, label, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", cwd=cwd)
    print("[%s] rc=%d" % (label, r.returncode))
    if r.returncode:
        print((r.stderr or "")[-1200:])
        raise SystemExit(1)
    return r


# ---------- 0. 文本文件（UTF-8，无 BOM） ----------
TEXTS = {
    "t_badge.txt": "AI 生成合成内容",
    "t_badge2.txt": "本片画面由人工智能生成",
    "t_credit.txt": "原曲《爱在西元前》　词：方文山　曲：周杰伦",
    "t_statement.txt": "二创致敬 · 非官方 · 画面由 AI 生成",
}
for name, s in TEXTS.items():
    with open(os.path.join(TMP, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

# ---------- 1. 石板板件 ----------
plate = os.path.join(TMP, "plate_v6.mp4")
vf = (
    "scale=%d:%d:flags=lanczos,"
    "eq=brightness='0.055+0.030*sin(2*PI*t*0.85)':contrast=1.16:saturation=1.10:eval=frame,"
    "colorbalance=rs=.06:gs=.01:bs=-.05:rm=.04:gm=.01:bm=-.03,"
    "noise=alls=6:allf=t,format=yuv420p"
) % (W, H)
run(["ffmpeg", "-y", "-loop", "1", "-i", STELE, "-t", "%.3f" % B, "-vf", vf,
     "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium", plate], "plate")

# ---------- 2. 拼接 + 字层（脚本纯 ASCII，中文走 textfile） ----------
SS = FONT_SANS.replace("\\", "/").replace(":", "\\:")
SR = FONT_SERIF.replace("\\", "/").replace(":", "\\:")

fc = (
    "[0:v]trim=0:{A},setpts=PTS-STARTPTS[s0];\n"
    "[1:v]trim=0:{B},setpts=PTS-STARTPTS[s1];\n"
    "[0:v]trim={C}:30,setpts=PTS-STARTPTS[s2];\n"
    "[s0][s1][s2]concat=n=3:v=1:a=0[vc];\n"
    "[vc]drawtext=fontfile='{SS}':textfile='t_badge.txt':fontcolor=white:fontsize=44:"
    "x=(w-text_w)/2:y=h-118:box=1:boxcolor=black@0.42:boxborderw=22:"
    "alpha='if(lt(t,0.80),0,min(1,(t-0.80)/0.35)*min(1,(3.20-t)/0.35))':"
    "enable='between(t,0.80,3.25)'[v1];\n"
    "[v1]drawtext=fontfile='{SS}':textfile='t_badge2.txt':fontcolor=white@0.88:fontsize=26:"
    "x=(w-text_w)/2:y=h-62:box=1:boxcolor=black@0.34:boxborderw=14:"
    "alpha='if(lt(t,0.95),0,min(1,(t-0.95)/0.35)*min(1,(3.20-t)/0.35))':"
    "enable='between(t,0.95,3.25)'[v2];\n"
    "[v2]drawtext=fontfile='{SR}':textfile='t_credit.txt':fontcolor=white@0.92:fontsize=30:"
    "x=(w-text_w)/2:y=h-104:box=1:boxcolor=black@0.40:boxborderw=16:"
    "alpha='if(lt(t,27.40),0,min(1,(t-27.40)/0.90))':enable='gte(t,27.40)'[v3];\n"
    "[v3]drawtext=fontfile='{SS}':textfile='t_statement.txt':fontcolor=white@0.80:fontsize=24:"
    "x=(w-text_w)/2:y=h-52:box=1:boxcolor=black@0.32:boxborderw=12:"
    "alpha='if(lt(t,27.80),0,min(1,(t-27.80)/0.90))':enable='gte(t,27.80)'[vout]\n"
).format(A=A, B=B, C=C, SS=SS, SR=SR)

fc_path = os.path.join(TMP, "v6.filter")
with open(fc_path, "w", encoding="ascii") as f:
    f.write(fc)

run(["ffmpeg", "-y", "-i", SRC, "-i", plate,
     "-filter_complex_script", "v6.filter",
     "-map", "[vout]", "-map", "0:a",
     "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
     "-r", str(FPS), "-c:a", "copy", "-movflags", "+faststart",
     "-metadata", "title=爱在西元前 30s 二创致敬",
     "-metadata", "comment=画面由人工智能生成（AI 生成合成内容，依 GB 45438-2025 标注）；二创致敬、非官方，与原作者及版权方无关联。",
     "-metadata", "artist=大喵没鱼吃",
     OUT], "splice", cwd=TMP)

p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size:stream=width,height,r_frame_rate,codec_name",
                    "-of", "default=nw=1", OUT], capture_output=True, text=True)
print(p.stdout.strip())
print("OUT %s  %.2f MB" % (OUT, os.path.getsize(OUT) / 1048576))
