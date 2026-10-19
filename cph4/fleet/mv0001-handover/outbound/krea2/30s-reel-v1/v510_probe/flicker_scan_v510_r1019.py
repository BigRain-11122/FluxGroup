# -*- coding: utf-8 -*-
# flicker_scan_v510_r1019.py — CEO 三镜定位①：刻字族闪烁量化（signalstats YAVG 逐帧差分振荡检测）
# 修：metadata=print 走 :file= 直写（-v error 会压掉 av_log 输出）。
import os, subprocess, sys, re
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "full_mv_v510.mp4")
FF = r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
os.chdir(HERE)
TMP = os.path.join(HERE, "v510_probe", "_yavg_tmp.txt")

SEGS = [
    (34.74,  2.18, "S6_chisel(未deflicker)"),
    (77.34,  2.84, "C01_carver_face(未deflicker)"),
    (100.14, 2.74, "C08_strike_burst(deflicker'd)"),
    (141.76, 2.80, "D01_carver_words(未deflicker)"),
    (159.66, 3.38, "D06_chisel_fingertip(未deflicker)"),
    (208.08, 4.58, "E06_strike(deflicker'd)"),
    (92.62,  2.60, "C06_forever_cut(deflicker'd)"),
    (184.08, 3.18, "B04_embers(deflicker'd)"),
    (230.50, 3.75, "Z04_glyph(deflicker'd)"),
    (25.90,  3.50, "S3_stele(对照)"),
    (131.72, 6.84, "R06_museum(对照)"),
]

out_lines = []
for st, dur, name in SEGS:
    cmd = [FF, "-v", "info", "-ss", "%.3f" % st, "-t", "%.3f" % dur, "-i", SRC,
           "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG",
           "-f", "null", "-"]
    if os.path.isfile(TMP):
        os.remove(TMP)
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    ys = [float(m) for m in re.findall(r"YAVG=([\d.]+)", r.stderr or "")]
    if len(ys) < 4:
        out_lines.append("%s: PROBE-FAIL frames=%d" % (name, len(ys)))
        continue
    ds = [ys[i+1]-ys[i] for i in range(len(ys)-1)]
    osc = sum(1 for i in range(len(ds)-1)
              if abs(ds[i]) >= 0.15 and abs(ds[i+1]) >= 0.15 and ds[i]*ds[i+1] < 0)
    peak = max(abs(d) for d in ds)
    slowdrift = abs(ys[-1]-ys[0])
    out_lines.append("%-32s frames=%3d osc(pulse)=%2d peak|dY|=%6.2f drift=%5.2f" % (name, len(ys), osc, peak, slowdrift))

if os.path.isfile(TMP):
    os.remove(TMP)
out = os.path.join(HERE, "v510_probe", "flicker_scan_v510.txt")
with open(out, "w", encoding="utf-8") as f:
    f.write("V5.10 刻字族闪烁量化扫描（YAVG 逐帧·噪声底0.15）\n")
    f.write("osc 高 + peak 高 = 脉动闪烁实锚；deflicker'd 镜 osc 应≈0\n\n")
    f.write("\n".join(out_lines) + "\n")
print("\n".join(out_lines))
print("-> " + out)
