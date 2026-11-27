# -*- coding: utf-8 -*-
"""build_v14.py — 30s 卷 v14：按评审团仲裁执行（零重烧）。

仲裁裁决（五席辩论后）：
  C1 删发光板 21.38–22.75（黑底 LED 感击穿写实体系；纯剪切不重烧），保写实石板。
  C2 暗墙 13.67–17.29 压缩（3.625→2.6），省出的时间给石板承接文字段功能。
  C3 补人物前史=延后到 V2（本机无古代女性素材）。

时间轴（合计 30.0）：
 1 火 4.417 | 2 楔文墙 4.0 | 3 石碑 3.5 | 4 浮雕 1.75 | 5 暗墙 2.6
 6 凿石手 2.208 | 7 神殿 1.875 | 8 石板 3.6(合成) | 9 女主 3.0417 | 10 走开 3.0417

P0 画面处置：
 A 石碑（8.42–11.92）顶部神像糊/考据错 → 顶部裁 12% + 上方压暗
 B 浮雕（11.92–13.67）左脸崩 → 轻微虚化 + 压暗 + 强化暗角（石雕软焦合理）
 C 神殿（19.5–21.38）冷白天窗光 → 暖色化 + 压高光，归入火光体系
"""
import os
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(BASE, "30s_reel_v5_cuneiform.mp4")
STELE = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\v6\stele-v2.png"
PERF = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\v8-reburn\V8_KF9_PERF3.mp4"
WALK = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\v13-reburn\V13_KF10_WALK.mp4"
TMP = r"K:\Fluxgroup\.codely-cli\tmp\v14"
OUT = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v14-优化版.mp4"
FONT_SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FONT_SANS = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
W, H, FPS = 1344, 768, 24

for p in (SRC, STELE, PERF, WALK, FONT_SERIF, FONT_SANS):
    if not os.path.exists(p):
        raise SystemExit("FATAL missing: " + p)

# 目标时长
D = [4.4167, 4.0, 3.5, 1.75, 2.6, 2.2083, 1.875, 3.6, 3.0417, 3.0417]
D[-1] = round(D[-1] + (30.0 - sum(D)), 4)
assert abs(sum(D) - 30.0) < 1e-6, sum(D)

os.makedirs(TMP, exist_ok=True)
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


# 石板（3.6s，承接文字段）
plate = os.path.join(TMP, "plate.mp4")
run(["ffmpeg", "-y", "-loop", "1", "-i", STELE, "-t", "%.3f" % D[7], "-vf",
     "scale=%d:%d:flags=lanczos,"
     "eq=brightness='0.050+0.028*sin(2*PI*t*0.85)':contrast=1.18:saturation=1.34:eval=frame,"
     "colorbalance=rs=.10:rm=.10:rh=.02:bs=-.08:bm=-.08:bh=.02,"
     "noise=alls=6:allf=t,format=yuv420p" % (W, H),
     "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium", plate], "plate")

SS = FONT_SANS.replace("\\", "/").replace(":", "\\:")
SR = FONT_SERIF.replace("\\", "/").replace(":", "\\:")

# 源区间（v5 reel 真实切点）
S = {"fire": (0.0, 4.4167), "wall": (4.4167, 8.4167), "stele": (8.4167, 11.9167),
     "relief": (11.9167, 13.6667), "dark": (13.6667, 17.2917),
     "chisel": (17.2917, 19.5), "temple": (19.5, 21.375)}


def seg(i, key, a, b, target, extra=""):
    k = round((b - a) / target, 6)
    return ("[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)*{k},fps={fps}{q},setsar=1[p{i}];\n"
            ).format(a=round(a, 4), b=round(b, 4), k=k, fps=FPS, q=extra, i=i)


parts = ""
# 1 火（原速 4.4167）
parts += seg(0, "fire", S["fire"][0], S["fire"][1], D[0])
# 2 楔文墙 4.0
parts += seg(1, "wall", S["wall"][0], S["wall"][1], D[1])
# 3 石碑：顶部裁 12% + 上方压暗（遮糊掉的神像）
# 碑顶神像糊且考据错 → 用垂直渐变压进暗部（不裁画幅，保碑身铭文完整）
STELE_CROP = ("geq=lum='lum(X,Y)*max(0.10,min(1,1-3.4*max(0,(0.46-Y/H))))'"
              ":cb='cb(X,Y)':cr='cr(X,Y)'")
parts += seg(2, "stele", S["stele"][0], S["stele"][1], D[2], "," + STELE_CROP)
# 4 浮雕：轻虚化 + 压暗 + 强暗角（遮左脸崩坏）
RELIEF_FIX = "gblur=sigma=1.1,eq=brightness=-0.015:contrast=1.04,vignette=a=0.34"
parts += seg(3, "relief", S["relief"][0], S["relief"][1], D[3], "," + RELIEF_FIX)
# 5 暗墙：压缩到 2.6s（取中段较亮部分）
parts += seg(4, "dark", 14.4, 17.0, D[4])
# 6 凿石手
parts += seg(5, "chisel", S["chisel"][0], S["chisel"][1], D[5])
# 7 神殿：暖色化 + 压高光（去掉冷白天窗）
TEMPLE_FIX = ("eq=brightness=0.02:contrast=1.04:saturation=1.12,"
              "colorbalance=rs=0.06:rm=0.05:rh=0.02:bs=-0.05:bm=-0.04:bh=0.01,"
              "curves=all='0/0.02 0.78/0.80 1/0.92'")
parts += seg(6, "temple", S["temple"][0], S["temple"][1], D[6], "," + TEMPLE_FIX)
# 8 石板（合成件）
parts += ("[1:v]trim=0:{t},setpts=PTS-STARTPTS,fps={fps},setsar=1[p7];\n".format(t=round(D[7], 4), fps=FPS))
# 9 女主（表演重烧）
k9 = round(min(3.0417, D[8] + 0.6) / D[8], 6)
parts += ("[2:v]trim=0:{d},setpts=(PTS-STARTPTS)*{k},fps={fps},setsar=1[p8];\n").format(
    d=round(min(3.0417, D[8] + 0.6), 4), k=k9, fps=FPS)
# 10 走开（新烧）
k10 = round(min(3.0417, D[9] + 0.6) / D[9], 6)
parts += ("[3:v]trim=0:{d},setpts=(PTS-STARTPTS)*{k},fps={fps},setsar=1[p9];\n").format(
    d=round(min(3.0417, D[9] + 0.6), 4), k=k10, fps=FPS)

parts += "[p0][p1][p2][p3][p4][p5][p6][p7][p8][p9]concat=n=10:v=1:a=0[vc];\n"

CURVES = ("curves=all='0/0.050 0.20/0.252 0.50/0.545 0.80/0.855 1/1'"
          ":r='0/0.050 0.70/0.712 1/0.978':b='0/0.050 0.70/0.752 1/1'"
          ",eq=contrast=1.05:saturation=1.02")
BAL = "colorbalance=rs=0.055:gs=0.012:bs=-0.030:rm=0.018:gm=0.003:bm=-0.010"
HAL = ("split=2[hp_base][hp_src];"
       "[hp_src]colorlevels=rimin=0.82:gimin=0.82:bimin=0.82,"
       "gblur=sigma=11,colorchannelmixer=rr=1.0:gg=0.48:bb=0.18[hp_glow];"
       "[hp_base][hp_glow]blend=all_mode=screen:all_opacity=0.20")
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
).format(C=CURVES, B=BAL, H=HAL, G="noise=alls=4:allf=t+u", V=VIG, Wv=WEAVE, SS=SS, SR=SR)

with open(os.path.join(TMP, "v14.filter"), "w", encoding="ascii") as f:
    f.write(fc)

run(["ffmpeg", "-y", "-i", SRC, "-i", plate, "-i", PERF, "-i", WALK,
     "-filter_complex_script", "v14.filter",
     "-map", "[vout]", "-map", "0:a",
     "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
     "-r", str(FPS), "-frames:v", "720", "-c:a", "copy", "-movflags", "+faststart",
     "-metadata", "title=爱在西元前 30s 二创致敬",
     "-metadata", "comment=画面由人工智能生成（AI 生成合成内容，依 GB 45438-2025 标注）；二创致敬、非官方，与原作者及版权方无关联。",
     "-metadata", "artist=大喵没鱼吃",
     OUT], "splice", cwd=TMP)

p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                    "-show_entries", "stream=nb_read_frames", "-show_entries",
                    "format=duration,size", "-of", "default=nw=1", OUT],
                   capture_output=True, text=True)
print(p.stdout.strip())
print("OUT %s  %.2f MB" % (OUT, os.path.getsize(OUT) / 1048576))
