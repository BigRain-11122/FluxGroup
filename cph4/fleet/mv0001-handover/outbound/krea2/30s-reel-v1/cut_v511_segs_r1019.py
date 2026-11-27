# -*- coding: utf-8 -*-
# cut_v511_segs_r1019.py — V5.11 四替换件切制 + D01v2_t2 全分辨率持稳认证
# 首尾剪除律（CEO §六.2）：take 有效区=[0.30, 4.50]——四件全部取中段
# ① D01 持稳认证：f05-f11 楔痕区帧差（持稳段 diff 须 << 压刻段 diff）
# ② 切制：SING2(2.00s·眨眼拍居窗) / D01(2.80s) / SIL4(1.80s) / E04AB(BAB 3.60 + 1帧黑场 + MOD 3.60)
# E04AB 黑场居窗：窗 212.66-219.84 中央≈216.25；成品件超窗冗余由装配 emit -t 精裁
import os, subprocess, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF = r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
TK = os.path.join(HERE, "v511_takes")
SRC = os.path.join(HERE, "v56src")
os.chdir(HERE)
from PIL import Image, ImageChops
import math

def run(args):
    r = subprocess.run(args, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print("FF-FAIL: " + " ".join(args[:8]) + " ...\n" + "\n".join((r.stderr or "").splitlines()[-8:]))
        raise SystemExit(1)

def cut(src, dst, ss, t):
    run([FF, "-y", "-ss", "%.4f" % ss, "-i", src, "-t", "%.4f" % t, "-an",
         "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", dst])
    print("CUT %s  [%.2f, %.2f)" % (os.path.basename(dst), ss, ss + t))

def frame_at(src, t, out):
    run([FF, "-y", "-ss", "%.3f" % t, "-i", src, "-frames:v", "1", out])
    return Image.open(out).convert("L")

def region_diff(a, b, box):
    ra, rb = a.crop(box), b.crop(box)
    h = ImageChops.difference(ra, rb).histogram()
    n = sum(h)
    return sum(i * v for i, v in enumerate(h)) / n  # mean abs diff 0-255

# ---------- ① D01v2_t2 持稳认证（判读板 f05-f11 hold 段全分辨率复核） ----------
d01 = os.path.join(TK, "D01v2_t2.mp4")
print("== D01v2_t2 hold certification (full-res)")
fa = frame_at(d01, 0.50, os.path.join(TK, "cert_d01_a.png"))
fb = frame_at(d01, 1.50, os.path.join(TK, "cert_d01_b.png"))
fc = frame_at(d01, 2.20, os.path.join(TK, "cert_d01_c.png"))
fd = frame_at(d01, 3.30, os.path.join(TK, "cert_d01_d.png"))
fe = frame_at(d01, 4.40, os.path.join(TK, "cert_d01_e.png"))
# 楔痕工作区（画面中部偏右·判读板实锚：手/凿尖/新楔痕带）
BOX = (int(1344 * 0.28), int(768 * 0.20), int(1344 * 0.68), int(768 * 0.75))
d_press = region_diff(fa, fb, BOX)
d_hold1 = region_diff(fc, fd, BOX)
d_hold2 = region_diff(fd, fe, BOX)
print("press-phase diff(0.50->1.50) = %.2f" % d_press)
print("hold-phase  diff(2.20->3.30) = %.2f" % d_hold1)
print("hold-phase  diff(3.30->4.40) = %.2f" % d_hold2)
ratio = (d_hold1 + d_hold2) / 2.0 / max(d_press, 0.001)
print("hold/press ratio = %.3f" % ratio)
if ratio < 0.45:
    print("CERT-PASS: hold 段帧差 << 压刻段（新楔痕 f05 后冻结实锤·全分辨率认证通过）")
else:
    print("CERT-WARN: hold 段帧差偏高——人工复核 cert_d01_*.png 再定")

# ---------- ② 四替换件切制 ----------
print("== cutting 4 replacement segments (首尾剪除律 0.30/0.50)")
sing2 = os.path.join(TK, "SING2_t2.mp4")   # 选优 t2：眨眼拍 2.10-2.94s 居窗
cut(sing2, os.path.join(SRC, "SING2_v511_seg.mp4"), 1.55, 2.00)
cut(d01,   os.path.join(SRC, "D01_v511_seg.mp4"),   0.30, 2.80)   # 压刻 0.42-2.10 + 持稳尾
sil4 = os.path.join(TK, "SIL4_t1.mp4")    # 选优 t1
cut(sil4, os.path.join(SRC, "SIL4_v511_seg.mp4"),  0.30, 1.80)
bab = os.path.join(TK, "BAB_t1.mp4")      # 选优 t1：凝望抬眼拍 1.68-2.52 在窗
mod = os.path.join(TK, "MOD_t1.mp4")      # 选优 t1：眨眼 2.10-2.52 在窗
pb = os.path.join(TK, "e04ab_bab.mp4")
pm = os.path.join(TK, "e04ab_mod.mp4")
pk = os.path.join(TK, "e04ab_black.mp4")
cut(bab, pb, 0.30, 3.60)
cut(mod, pm, 0.30, 3.60)
run([FF, "-y", "-f", "lavfi", "-i", "color=black:s=1344x768:r=24",
     "-frames:v", "1", "-c:v", "libx264", "-preset", "fast", "-crf", "17",
     "-pix_fmt", "yuv420p", pk])
print("CUT e04ab_black.mp4 (1 frame)")
lst = os.path.join(TK, "e04ab_list.txt")
with open(lst, "w") as f:
    for p in (pb, pk, pm):
        f.write("file '%s'\n" % p)
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
     os.path.join(SRC, "E04AB_v511_seg.mp4")])
print("CONCAT E04AB_v511_seg.mp4 = BAB + 1f black + MOD")

# ---------- ③ 出件验证 ----------
FP = FF.replace("ffmpeg.exe", "ffprobe.exe")
for n in ("SING2_v511_seg", "D01_v511_seg", "SIL4_v511_seg", "E04AB_v511_seg"):
    p = os.path.join(SRC, n + ".mp4")
    r = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-count_packets",
                        "-show_entries", "stream=width,height,r_frame_rate,nb_read_packets,duration",
                        "-of", "default=noprint_wrappers=1", p], capture_output=True, text=True)
    print("VRFY %s: %s" % (n, " | ".join(r.stdout.strip().splitlines())))
print("DONE cut_v511_segs_r1019.py")
