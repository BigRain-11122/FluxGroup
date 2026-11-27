# -*- coding: utf-8 -*-
"""build_v8.py — 30s 卷 v8：专家群审修复 + 90s 胶片调色链。

群审驱动的四处改动：
  A. 21.375–22.75s 伪符号板（被四席指为"◀◀ ▮ ▶▶▶ 播放器按键"）→ 真楔文发光板 mv_cuneiform_glow.py
  B. 石板镜过热不足（中部 R-B +48 vs 邻镜 +95~131）→ 提高其暖度，消除风格割裂
  C. 全片黑位 p1=0（数字死黑）→ curves 抬到 ~10 code（胶片密度）
  D. 高光 R-B +61~120（橙到发红）→ 高分带压红提蓝，回到 +20~35（暖白）

调色铁序（承 mv-colorist 席）：归一 → 分带/曲线 → halation → 颗粒 → 暗角 → 输出
颗粒必须放在 curves 之后（放反=满屏数字噪声）；颗粒后禁锐化。
"""
import os
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(BASE, "30s_reel_v5_cuneiform.mp4")
STELE = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\v6\stele-v2.png"
GLOW = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\v8\glow.png"
TMP = r"K:\Fluxgroup\.codely-cli\tmp\v8"
OUT = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v8-优化版.mp4"
FONT_SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FONT_SANS = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

W, H, FPS = 1344, 768, 24
DARK0, DARK1 = 13.67, 17.29        # 暗镜提亮（承 v7）
GLOW0, GLOW1 = 21.375, 22.75       # 伪符号板替换
TAB0, TAB1 = 22.75, 24.75          # 真楔文石板
GLOW_DUR = GLOW1 - GLOW0
TAB_DUR = TAB1 - TAB0

os.makedirs(TMP, exist_ok=True)
for p in (SRC, STELE, GLOW, FONT_SERIF, FONT_SANS):
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
        print((r.stderr or "")[-1400:])
        raise SystemExit(1)
    return r


# ---------- 1) 石板板件（升温，贴近邻镜） ----------
plate = os.path.join(TMP, "plate_v8.mp4")
vf_tab = ("scale=%d:%d:flags=lanczos,"
          "eq=brightness='0.050+0.028*sin(2*PI*t*0.85)':contrast=1.18:saturation=1.34:eval=frame,"
          "colorbalance=rs=.10:rm=.10:rh=.02:bs=-.08:bm=-.08:bh=.02,"
          "noise=alls=6:allf=t,format=yuv420p") % (W, H)
run(["ffmpeg", "-y", "-loop", "1", "-i", STELE, "-t", "%.3f" % TAB_DUR, "-vf", vf_tab,
     "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium", plate], "plate_tab")

# ---------- 2) 真楔文发光板（替换伪符号；两端淡入淡出） ----------
glow = os.path.join(TMP, "glow_v8.mp4")
vf_gl = ("scale=%d:%d:flags=lanczos,"
         "eq=brightness='0.10+0.06*sin(2*PI*t*1.1)':contrast=1.16:saturation=1.18:eval=frame,"
         "fade=t=in:st=0:d=0.14,fade=t=out:st=%.3f:d=0.16,"
         "noise=alls=4:allf=t,format=yuv420p") % (W, H, GLOW_DUR - 0.16)
run(["ffmpeg", "-y", "-loop", "1", "-i", GLOW, "-t", "%.3f" % GLOW_DUR, "-vf", vf_gl,
     "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium", glow], "plate_glow")

# ---------- 3) 五段拼接 ----------
SS = FONT_SANS.replace("\\", "/").replace(":", "\\:")
SR = FONT_SERIF.replace("\\", "/").replace(":", "\\:")
GAMMA = "if(lt(t,0.25),1.10,if(lt(t,1.90),1.10-0.10*(t-0.25)/1.65,1.0))"

parts = (
    "[0:v]trim=0:{D0},setpts=PTS-STARTPTS[s0];\n"
    "[0:v]trim={D0}:{D1},setpts=PTS-STARTPTS,eq=gamma='{G}':eval=frame[sA];\n"
    "[0:v]trim={D1}:{G0},setpts=PTS-STARTPTS[s1];\n"
    "[1:v]trim=0:{GD},setpts=PTS-STARTPTS[s2];\n"
    "[2:v]trim=0:{TD},setpts=PTS-STARTPTS[s3];\n"
    "[0:v]trim={T1}:30,setpts=PTS-STARTPTS[s4];\n"
    "[s0][sA][s1][s2][s3][s4]concat=n=6:v=1:a=0[vc];\n"
).format(D0=DARK0, D1=DARK1, G0=GLOW0, GD=GLOW_DUR, TD=TAB_DUR, T1=TAB1,
         G=GAMMA)

# ---------- 4) 90s 胶片调色链（铁序） ----------
# ① 曲线：先抬黑位到胶片密度（~8 code），再只在高亮端（>0.70）压红提蓝——
#    不用 colorbalance 高分带，因为它的 high(96-255) 与 mid(32-104) 重叠，会把琥珀中调一起压掉
CURVES = ("curves=all='0/0.050 0.20/0.252 0.50/0.545 0.80/0.855 1/1'"
          ":r='0/0.050 0.70/0.712 1/0.978':b='0/0.050 0.70/0.752 1/1'"
          ",eq=contrast=1.05:saturation=1.02")
# ② 分带：只动暗带（加暖）与轻微微调，不碰高亮
BAL = "colorbalance=rs=0.055:gs=0.012:bs=-0.030:rm=0.018:gm=0.003:bm=-0.010"
# ③ halation：只吃真高光（阈值 0.82），轻量 0.20，避免整幅发雾
HAL = ("split=2[hp_base][hp_src];"
       "[hp_src]colorlevels=rimin=0.82:gimin=0.82:bimin=0.82,"
       "gblur=sigma=11,colorchannelmixer=rr=1.0:gg=0.48:bb=0.18[hp_glow];"
       "[hp_base][hp_glow]blend=all_mode=screen:all_opacity=0.20")
# ④ 颗粒：中调 σ≈2.0（alls=5 实测接近），放 curves 之后
GRAIN = "noise=alls=4:allf=t+u"
# ⑤ 暗角：a=0.28 → 角部约 -15.7%（区间内；PI 系禁用）
VIG = "vignette=a=0.28"
# ⑥ 片门轻微抖动（telecine 味，±0.5px，低频）
WEAVE = ("crop=iw-2:ih-2:x='1+0.5*sin(n/9)':y='1+0.5*sin(n/13)',"
         "scale=%d:%d:flags=bicubic" % (W, H))

fc = parts + (
    "[vc]{C},{B},{H},{G},{V},{Wv}[vgraded];\n"
    "[vgraded]drawtext=fontfile='{SS}':textfile='t_badge.txt':fontcolor=white:fontsize=44:"
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
).format(C=CURVES, B=BAL, H=HAL, G=GRAIN, V=VIG, Wv=WEAVE, SS=SS, SR=SR)

with open(os.path.join(TMP, "v8.filter"), "w", encoding="ascii") as f:
    f.write(fc)

run(["ffmpeg", "-y", "-i", SRC, "-i", glow, "-i", plate,
     "-filter_complex_script", "v8.filter",
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
