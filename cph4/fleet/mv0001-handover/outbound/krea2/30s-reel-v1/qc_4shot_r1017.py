# -*- coding: utf-8 -*-
# qc_4shot_r1017.py — bm-c 4 镜重烧到件六检抽帧器（O-20261017-1020·判据=V5-REBURN-ADDENDUM-4shot 各镜验收行）
# 用法: python qc_4shot_r1017.py
#   对 v5redo 四件抽帧（源 768P 全分辨率）→ 每镜一块 4 联条板 + 时长断言（契约 ≥5.0s）
#   产出: segments/_cut/v51/qc_4shot/<SHOT>-STRIP.jpg（多模态判读面）
# 判据备忘（ADDENDUM 原文）:
#   D01: 背景零拉丁/零可读字母字符；坯料刻字可读楔形；无褶纸；无第二人
#   C04: 全分辨率多模态字形判定=楔形 PASS（楔头粗壮压印+细尾·横排·行线；非卢恩直杆）
#   E01c: 密帧抽检发力瞬间可见+石屑在场（禁编舞式连击·一凿落定止动）
#   INT5: 背线曲率与 KF 一致（疲惫不塌背·the back line staying long and upright）；微动自然
import os, re, subprocess, sys, time
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
V5REDO = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\qc_4shot"
os.makedirs(OUT, exist_ok=True)

SHOTS = [
    ("D01_carver_words_v5.mp4", [1.0, 2.6, 3.4, 4.5]),
    ("C04_words_alive_v5.mp4", [0.8, 2.0, 3.5, 4.5]),
    ("E01c_first_line_v5.mp4", [0.5, 1.0, 1.5, 2.2]),
    ("INT5_head_bow_v5.mp4", [1.0, 2.6, 3.2, 4.0]),
]


def dur_of(p):
    r = subprocess.run([FF, "-i", p], capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return float(m.group(1)) * 3600 + float(m.group(2)) * 60 + float(m.group(3)) if m else None


for fn, times in SHOTS:
    src = os.path.join(V5REDO, fn)
    if not os.path.isfile(src):
        print("MISSING %s" % fn)
        continue
    d = dur_of(src)
    mt = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(src)))
    ok_dur = "OK" if (d and d >= 5.0) else "FAIL"
    print("%s  dur=%.2fs(%s)  mtime=%s" % (fn, d or -1, ok_dur, mt))
    frames = []
    for i, t in enumerate(times):
        f = os.path.join(OUT, "%s_%d.jpg" % (fn[:-4], i))
        subprocess.run([FF, "-y", "-ss", "%.2f" % t, "-i", src, "-frames:v", "1", "-q:v", "3", "-update", "1", f],
                       capture_output=True)
        frames.append(f)
    strip = os.path.join(OUT, "%s-STRIP.jpg" % fn[:-4])
    subprocess.run([FF, "-y", "-i", frames[0], "-i", frames[1], "-i", frames[2], "-i", frames[3],
                    "-filter_complex", "[0][1][2][3]hstack=4[out]", "-map", "[out]", "-q:v", "4", "-update", "1", strip],
                   capture_output=True)
    print("STRIP -> %s" % strip)
print("QC-4SHOT-PROBES-DONE -> " + OUT)
