# -*- coding: utf-8 -*-
# triage_freeze_v56_r1018.py — 量化扫描 aHash 冻结旗的像素级定谳（真冻结 vs 8x8 哈希碰撞）
# 判据：帧对 pixDiff(|Δ|>12 占比%) <1.0% = 真冻结（≈编码噪声底 0.5%）；>3% = 活画面（哈希碰撞假阳性）
import os, subprocess
from PIL import Image
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
SRC = os.path.join(HERE, "full_mv_v56.mp4")
TD = os.path.join(HERE, "final_review_quant", "triage")
os.makedirs(TD, exist_ok=True)

RUNS = [
    (132.25, 138.25, "R06_museum_verse"),
    (188.00, 189.75, "E01a_carver"),
    (11.00, 13.25, "V56_P_pen_macro"),
    (9.25, 10.75, "INT3_photo_stare(C镜已裁活画面)"),
    (37.25, 38.50, "S7_hall尾"),
    (95.75, 97.00, "C07_stele_sink"),
    (146.25, 147.50, "D02_she_reads"),
    (175.50, 176.75, "B01_weary"),
    (199.00, 200.25, "E03_gaze_meet"),
    (218.50, 219.75, "E04_replay(tpad定格=设计)"),
    (227.50, 228.75, "Z03_lights_out(灯灭=设计)"),
]

def grab(t, name):
    p = os.path.join(TD, name + ".jpg")
    subprocess.run([FF, "-y", "-ss", "%.2f" % t, "-i", SRC, "-frames:v", "1",
                    "-update", "1", "-q:v", "2", p], check=True, capture_output=True)
    return p

def cmp_frames(p1, p2):
    a = Image.open(p1).convert("L")
    b = Image.open(p2).convert("L")
    pa, pb = list(a.getdata()), list(b.getdata())
    n = len(pa)
    diff = sum(1 for x, y in zip(pa, pb) if abs(x - y) > 12) / float(n) * 100.0
    dluma = abs(sum(pa) / n - sum(pb) / n)
    return diff, dluma

for (t0, t1, label) in RUNS:
    tm = (t0 + t1) / 2.0
    f0 = grab(t0 + 0.04, "z_%06.2f_a" % t0)
    fm = grab(tm, "z_%06.2f_b" % tm)
    f1 = grab(t1 - 0.04, "z_%06.2f_c" % t1)
    d01, l01 = cmp_frames(f0, f1)
    d0m, l0m = cmp_frames(f0, fm)
    verdict = "FREEZE" if d01 < 1.0 and d0m < 1.0 else ("NEAR-STATIC" if d01 < 2.5 else "ALIVE")
    print("%-30s %.2f-%.2f  pixDiff(a-c)=%.2f%% dLuma=%.1f  pixDiff(a-b)=%.2f%%  -> %s"
          % (label, t0, t1, d01, l01, d0m, verdict), flush=True)
print("TRIAGE-DONE")
