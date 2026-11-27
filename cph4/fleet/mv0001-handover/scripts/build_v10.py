# -*- coding: utf-8 -*-
"""build_v9.py — 30s 卷 v9：在 v8 调色链基础上，把 24.75–27.75s 换成重烧的表演 take。

变更：
  1) 24.75–27.75s 女主近景 → v8-reburn/V8_KF9_PERF3.mp4（紧裁 KF 重烧）
     - 原镜量化：3s 内 0 次眨眼、0 个表情 onset、最大帧差 1.99 = 活体静帧
     - 新 take：1 次完整眨眼（第 30 帧闭合）+ 20 帧持续变化（0.83s）+ 头不转出画
  2) 其余与 v8 完全一致（真楔文发光板替换伪符号板 / 石板升温 / 90s 胶片调色链）
局部：新 take 比原镜亮且偏中性，进全局链前先做暖度与亮度对齐，避免一镜跳色。
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
PERF = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\v8-reburn\V8_KF9_PERF3.mp4"
TMP = r"K:\Fluxgroup\.codely-cli\tmp\v10"
OUT = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v10-优化版.mp4"
FONT_SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FONT_SANS = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

W, H, FPS = 1344, 768, 24
DARK0, DARK1 = 13.67, 17.29
GLOW0, GLOW1 = 21.375, 22.75
TAB0, TAB1 = 22.75, 24.75
PERF0, PERF1 = 24.75, 27.75
GLOW_DUR = GLOW1 - GLOW0
TAB_DUR = TAB1 - TAB0
PERF_DUR = PERF1 - PERF0

os.makedirs(TMP, exist_ok=True)
for p in (SRC, STELE, GLOW, PERF, FONT_SERIF, FONT_SANS):
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


plate = os.path.join(TMP, "plate_v9.mp4")
vf_tab = ("scale=%d:%d:flags=lanczos,"
          "eq=brightness='0.050+0.028*sin(2*PI*t*0.85)':contrast=1.18:saturation=1.34:eval=frame,"
          "colorbalance=rs=.10:rm=.10:rh=.02:bs=-.08:bm=-.08:bh=.02,"
          "noise=alls=6:allf=t,format=yuv420p") % (W, H)
run(["ffmpeg", "-y", "-loop", "1", "-i", STELE, "-t", "%.3f" % TAB_DUR, "-vf", vf_tab,
     "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium", plate], "plate_tab")

glow = os.path.join(TMP, "glow_v9.mp4")
vf_gl = ("scale=%d:%d:flags=lanczos,"
         "curves=all='0/0.036 0.35/0.372 1/1',"
         "eq=brightness='0.10+0.06*sin(2*PI*t*1.1)':contrast=1.16:saturation=1.18:eval=frame,"
         "fade=t=in:st=0:d=0.14,fade=t=out:st=%.3f:d=0.16,"
         "noise=alls=4:allf=t,format=yuv420p") % (W, H, GLOW_DUR - 0.16)
run(["ffmpeg", "-y", "-loop", "1", "-i", GLOW, "-t", "%.3f" % GLOW_DUR, "-vf", vf_gl,
     "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium", glow], "plate_glow")

SS = FONT_SANS.replace("\\", "/").replace(":", "\\:")
SR = FONT_SERIF.replace("\\", "/").replace(":", "\\:")
GAMMA = "if(lt(t,0.25),1.10,if(lt(t,1.90),1.10-0.10*(t-0.25)/1.65,1.0))"

parts = (
    "[0:v]trim=0:{D0},setpts=PTS-STARTPTS[s0];\n"
    "[0:v]trim={D0}:{D1},setpts=PTS-STARTPTS,eq=gamma='{G}':eval=frame[sA];\n"
    "[0:v]trim={D1}:{G0},setpts=PTS-STARTPTS[s1];\n"
    "[1:v]trim=0:{GD},setpts=PTS-STARTPTS[s2];\n"
    "[2:v]trim=0:{TD},setpts=PTS-STARTPTS[s3];\n"
    # 新表演 take：先做暖度/亮度对齐（原镜更暗更琥珀），再进全局链
    "[3:v]trim=0:{PD},setpts=PTS-STARTPTS,"
    "eq=brightness=-0.035:contrast=1.05:saturation=1.10,"
    "colorbalance=rs=0.05:rm=0.05:bs=-0.035:bm=-0.03[s4];\n"
    "[0:v]trim={P1}:30,setpts=PTS-STARTPTS[s5];\n"
    "[s0][sA][s1][s2][s3][s4][s5]concat=n=7:v=1:a=0[vc];\n"
).format(D0=DARK0, D1=DARK1, G0=GLOW0, GD=GLOW_DUR, TD=TAB_DUR, PD=PERF_DUR,
         P1=PERF1, G=GAMMA)

CURVES = ("curves=all='0/0.050 0.20/0.252 0.50/0.545 0.80/0.855 1/1'"
          ":r='0/0.050 0.70/0.712 1/0.978':b='0/0.050 0.70/0.752 1/1'"
          ",eq=contrast=1.05:saturation=1.02")
BAL = "colorbalance=rs=0.055:gs=0.012:bs=-0.030:rm=0.018:gm=0.003:bm=-0.010"
HAL = ("split=2[hp_base][hp_src];"
       "[hp_src]colorlevels=rimin=0.82:gimin=0.82:bimin=0.82,"
       "gblur=sigma=11,colorchannelmixer=rr=1.0:gg=0.48:bb=0.18[hp_glow];"
       "[hp_base][hp_glow]blend=all_mode=screen:all_opacity=0.20")
GRAIN = "noise=alls=4:allf=t+u"
VIG = "vignette=a=0.28"
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

with open(os.path.join(TMP, "v9.filter"), "w", encoding="ascii") as f:
    f.write(fc)

run(["ffmpeg", "-y", "-i", SRC, "-i", glow, "-i", plate, "-i", PERF,
     "-filter_complex_script", "v9.filter",
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
