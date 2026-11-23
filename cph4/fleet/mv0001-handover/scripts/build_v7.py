# -*- coding: utf-8 -*-
"""build_v7.py — 30s 卷 v7：仅修一处（全片逐帧体检查出的暗镜），其余与 v6 完全相同。

体检结论（720 帧全查）：13.67–17.29s 这一镜均值亮度 10.3、最低 6.0，
其中前 1.25s（13.67–14.9s）均值仅 6.5–8.5，手机端读作黑场。全片其余各镜无同类问题。

修法：只对 13.67–17.29s 这一镜做**时间变伽马提亮**——
  t<0.25s 固定 1.10，0.25–1.90s 线性回落到 1.00，之后不动。
即"开头那一口气提上来"，后半段自然光弧不变，不触碰其它任何一帧。
（标定实测：gamma 1.10 把 13.7s 帧从 6.4 抬到 ~12，与相邻镜地板 12.6 齐平。）
"""
import os
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(BASE, "30s_reel_v5_cuneiform.mp4")
STELE = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\v6\stele-v2.png"
TMP = r"K:\Fluxgroup\.codely-cli\tmp\v7"
OUT_DIR = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable"
OUT = os.path.join(OUT_DIR, "爱在西元前-30s-v7-优化版.mp4")
FONT_SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FONT_SANS = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

W, H, FPS = 1344, 768, 24
A, B, C = 22.75, 2.00, 24.75      # 石板镜窗（与 v6 相同）
DARK0, DARK1 = 13.67, 17.29       # 待提亮镜的区间（硬切实测）
os.makedirs(TMP, exist_ok=True)

for p in (SRC, STELE, FONT_SERIF, FONT_SANS):
    if not os.path.exists(p):
        raise SystemExit("FATAL missing: " + p)

TEXTS = {
    "t_badge.txt": "AI 生成合成内容",
    "t_badge2.txt": "本片画面由人工智能生成",
    "t_credit.txt": "原曲《爱在西元前》　词：方文山　曲：周杰伦",
    "t_statement.txt": "二创致敬 · 非官方 · 画面由 AI 生成",
}
for name, s in TEXTS.items():
    with open(os.path.join(TMP, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def run(cmd, label, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", cwd=cwd)
    print("[%s] rc=%d" % (label, r.returncode))
    if r.returncode:
        print((r.stderr or "")[-1200:])
        raise SystemExit(1)
    return r


# ---------- 石板板件（与 v6 相同） ----------
plate = os.path.join(TMP, "plate_v7.mp4")
vf = ("scale=%d:%d:flags=lanczos,"
      "eq=brightness='0.055+0.030*sin(2*PI*t*0.85)':contrast=1.16:saturation=1.10:eval=frame,"
      "colorbalance=rs=.06:gs=.01:bs=-.05:rm=.04:gm=.01:bm=-.03,"
      "noise=alls=6:allf=t,format=yuv420p") % (W, H)
run(["ffmpeg", "-y", "-loop", "1", "-i", STELE, "-t", "%.3f" % B, "-vf", vf,
     "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium", plate], "plate")

# ---------- 五段拼接（新增暗镜提亮段） ----------
SS = FONT_SANS.replace("\\", "/").replace(":", "\\:")
SR = FONT_SERIF.replace("\\", "/").replace(":", "\\:")

GAMMA = "if(lt(t,0.25),1.10,if(lt(t,1.90),1.10-0.10*(t-0.25)/1.65,1.0))"

fc = (
    "[0:v]trim=0:{D0},setpts=PTS-STARTPTS[s0];\n"
    "[0:v]trim={D0}:{D1},setpts=PTS-STARTPTS,eq=gamma='{G}':eval=frame[sA];\n"
    "[0:v]trim={D1}:{A},setpts=PTS-STARTPTS[s1];\n"
    "[1:v]trim=0:{B},setpts=PTS-STARTPTS[s2];\n"
    "[0:v]trim={C}:30,setpts=PTS-STARTPTS[s3];\n"
    "[s0][sA][s1][s2][s3]concat=n=5:v=1:a=0[vc];\n"
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
).format(D0=DARK0, D1=DARK1, A=A, B=B, C=C, G=GAMMA, SS=SS, SR=SR)

with open(os.path.join(TMP, "v7.filter"), "w", encoding="ascii") as f:
    f.write(fc)

run(["ffmpeg", "-y", "-i", SRC, "-i", plate,
     "-filter_complex_script", "v7.filter",
     "-map", "[vout]", "-map", "0:a",
     "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
     "-r", str(FPS), "-c:a", "copy", "-movflags", "+faststart",
     "-metadata", "title=爱在西元前 30s 二创致敬",
     "-metadata", "comment=画面由人工智能生成（AI 生成合成内容，依 GB 45438-2025 标注）；二创致敬、非官方，与原作者及版权方无关联。",
     "-metadata", "artist=大喵没鱼吃",
     OUT], "splice", cwd=TMP)

p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size:stream=width,height,r_frame_rate",
                    "-of", "default=nw=1", OUT], capture_output=True, text=True)
print(p.stdout.strip())
print("OUT %s  %.2f MB" % (OUT, os.path.getsize(OUT) / 1048576))
