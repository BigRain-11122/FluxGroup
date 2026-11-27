# -*- coding: utf-8 -*-
# v511_verify_r1019.py — V5.11 全量验证+批4 CEO 眼犁片板生成（不抽样·全 73 镜）
# 出：v511_probe/ 下全部判读板 + pts_scan_v511.txt + flicker_scan_v511.txt
import os, subprocess, sys, re
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "full_mv_v511.mp4")
FF = r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FP = FF.replace("ffmpeg.exe", "ffprobe.exe")
os.chdir(HERE)
OUT = os.path.join(HERE, "v511_probe")
os.makedirs(OUT, exist_ok=True)
from PIL import Image, ImageDraw

def frame_at(t, w=640):
    p = os.path.join(OUT, "_f.jpg")
    subprocess.run([FF, "-y", "-ss", "%.4f" % t, "-i", SRC, "-frames:v", "1",
                    "-vf", "scale=%d:%d" % (w, int(w * 768 / 1344)), "-q:v", "3", p],
                   capture_output=True)
    return p

def board(times, cols, out, tile_w=480, labelfmt="%s"):
    tiles = []
    h = int(tile_w * 768 / 1344)
    for k, tt in enumerate(times):
        src = frame_at(tt, tile_w)
        im = Image.open(src).convert("RGB")
        drw = ImageDraw.Draw(im)
        lbl = labelfmt % tt if isinstance(tt, float) else str(tt)
        drw.rectangle([0, 0, 8 * len(lbl) + 22, 22], fill=(0, 0, 0))
        drw.text((6, 4), lbl, fill=(255, 230, 60))
        tiles.append(im)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, rows * (h + 24)), (10, 10, 10))
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % cols) * tile_w, (k // cols) * (h + 24) + 24))
    sheet.save(os.path.join(OUT, out), quality=86)
    print("BOARD %-40s tiles=%d" % (out, len(tiles)))

def strip(t0, t1, step):
    n = int((t1 - t0) / step)
    return [round(t0 + i * step, 4) for i in range(n + 1)]

# ===== ① PTS 全扫（5622 帧机械面）=====
print("== PTS scan")
r = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
                    "frame=pts_time", "-of", "csv=p=0", SRC], capture_output=True, text=True, errors="replace")
pts = [float(x) for x in r.stdout.split() if x.strip()]
anoms = []
for i in range(1, len(pts)):
    d = pts[i] - pts[i - 1]
    if not (0.03 < d < 0.055):
        anoms.append((i, pts[i], d))
with open(os.path.join(OUT, "pts_scan_v511.txt"), "w", encoding="utf-8") as f:
    f.write("V5.11 PTS full scan: frames=%d last=%.3f anomalies=%d\n" % (len(pts), pts[-1] if pts else -1, len(anoms)))
    for i, p, d in anoms[:40]:
        f.write("  ANOM frame#%d pts=%.4f d=%.5f\n" % (i, p, d))
print("PTS frames=%d anomalies=%d last=%.3f" % (len(pts), len(anoms), pts[-1] if pts else -1))

# ===== ② 四手术镜密集板（CEO 三诉+SIL4·判读主面）=====
print("== surgery dense boards")
board(strip(180.00, 182.00, 0.0834), 8, "D01-SING2-DENSE.jpg", 480, "%.2f")     # SING2 每2帧
board(strip(141.76, 144.56, 0.0834), 8, "D01-TABTEN-DENSE.jpg", 640, "%.2f")   # D01 每2帧
board(strip(207.00, 208.80, 0.0834), 8, "SIL4-DENSE.jpg", 480, "%.2f")          # SIL4 每2帧
board(strip(212.66, 219.84, 0.334), 6, "E04AB-COVER-A.jpg", 640, "%.2f")       # E04AB 每8帧覆盖
board(strip(215.90, 216.60, 0.0417), 6, "E04AB-BLACKFIELD.jpg", 640, "%.2f")   # 黑场带逐帧
board([212.70, 214.00, 216.10, 216.21, 216.23, 216.25, 216.27, 216.30, 218.00, 219.70], 5,
      "E04AB-MATCHCUT-10.jpg", 640, "%.2f")

# ===== ③ 14 XFS 切点目检板（切点前后各2帧）=====
print("== XFS cut boards")
XFS = [21.90, 38.82, 40.22, 44.00, 47.50, 80.18, 102.88, 110.52, 126.32,
       131.72, 152.00, 187.26, 191.60, 227.50]
xf_times = []
for a in XFS:
    for d in (-0.12, -0.08, -0.042, 0.042, 0.08, 0.12):
        xf_times.append(round(a + d, 4))
board(xf_times[:42], 6, "XFS-CUTS-1.jpg", 480, "%.2f")
board(xf_times[42:], 6, "XFS-CUTS-2.jpg", 480, "%.2f")

# ===== ④ 73 镜全犁板（批4 项1/3/4：风格一致/AI文字器物/年代穿帮）=====
print("== 73-shot full sweep")
ROWS = [
    ("INT1", 1.5), ("INT2", 4.4), ("V56_R", 6.6), ("INT3", 9.2), ("V56_P", 12.2), ("INT5", 15.5),
    ("S1", 19.7), ("S2", 23.9), ("S3", 27.4), ("SIL1", 30.1), ("S5", 32.9), ("S6", 35.8),
    ("S7", 37.9), ("T", 39.5), ("S8", 41.2), ("S9", 43.1), ("SIL2", 44.6), ("S10", 46.4),
    ("N01", 49.0), ("N02", 52.4), ("N03", 56.3), ("N04", 60.2), ("N05", 65.4), ("N06", 71.7),
    ("N07", 76.0), ("C01", 77.7), ("SING1", 79.1), ("C02", 81.9), ("C03", 85.7), ("C04", 89.4),
    ("C05", 91.8), ("C06", 93.9), ("C07", 97.7), ("C08", 101.5), ("C09", 105.5), ("C09b", 109.4),
    ("R01", 112.6), ("R02", 116.6), ("R03", 120.6), ("R04", 124.6), ("R05", 129.0), ("R06", 135.1),
    ("R07", 140.2), ("D01", 143.2), ("D02", 146.2), ("D03", 149.2), ("D03b", 151.3), ("SIL3", 152.8),
    ("D04", 154.5), ("D05", 157.5), ("D06", 161.3), ("D07", 165.1), ("D08", 169.9), ("B01", 174.8),
    ("B02", 178.5), ("SING2", 181.0), ("B03", 183.0), ("B04", 185.7), ("E01a", 188.6), ("E01b", 190.8),
    ("E01c", 192.4), ("E02a", 195.1), ("SING3b", 198.0), ("E03", 199.9), ("E04a", 202.9),
    ("E05", 206.0), ("SIL4", 207.9), ("E06", 210.7), ("E04AB", 216.2), ("Z01", 221.9),
    ("Z02", 225.8), ("Z03", 229.0), ("Z04", 232.4),
]
tags = []
for name, t in ROWS:
    tags.append(t)
board(tags[:24], 6, "SWEEP-73-A.jpg", 480, "%.2f")
board(tags[24:48], 6, "SWEEP-73-B.jpg", 480, "%.2f")
board(tags[48:], 6, "SWEEP-73-C.jpg", 480, "%.2f")

# ===== ⑤ 15 存量人脸慢放行鬼影板（LEGACY-FACE-SLOW WARN 单）=====
print("== legacy face-slow ghost check")
LEG = [(1.5, 2.9, "INT1"), (4.4, 5.6, "INT2"), (9.2, 10.6, "INT3"), (12.2, 13.2, "P"),
       (15.5, 16.9, "INT5"), (77.7, 78.0, "C01"), (135.1, 138.4, "R06"), (151.3, 152.0, "D03b"),
       (161.3, 163.0, "D06"), (183.0, 184.1, "B03"), (188.6, 191.0, "E01a"),
       (192.4, 193.1, "E01c"), (199.9, 200.8, "E03"), (206.0, 207.0, "E05"), (221.9, 224.0, "Z01")]
lg = []
for a, b, n in LEG:
    mid = (a + b) / 2
    lg += [round(a + (b - a) * 0.25, 3), round(mid, 3), round(a + (b - a) * 0.85, 3)]
board(lg[:30], 6, "LEGACY-FACE-1.jpg", 480, "%.2f")
board(lg[30:], 6, "LEGACY-FACE-2.jpg", 480, "%.2f")

# ===== ⑥ 运镜抽样板（推/横移/prechorus 各抽 1 镜×5 帧）=====
print("== camera-move spot boards")
board([33.0, 33.7, 34.4, 35.1, 35.8], 5, "MOVE-PUSH-S5.jpg", 480, "%.2f")       # 主歌慢推
board([132.2, 133.4, 134.6, 135.8, 137.0], 5, "MOVE-PAN-R06.jpg", 480, "%.2f")  # 博物馆横移
board([212.7, 213.9, 215.1, 216.4, 217.7], 5, "MOVE-PAN-E04AB.jpg", 480, "%.2f")
board([74.8, 75.6, 76.4, 77.0, 77.32], 5, "MOVE-PRECHORUS-N07.jpg", 480, "%.2f")  # 推→拉→定格
board([225.0, 226.2, 227.4, 228.6, 229.8], 5, "MOVE-PULLOUT-Z03.jpg", 480, "%.2f")

# ===== ⑦ 分段调色对板（巴比伦琥珀 vs 博物馆青灰 vs E04AB 双半）=====
print("== zone grade board")
board([19.7, 49.0, 81.9, 105.5, 143.2, 161.3, 135.1, 203.0, 207.9, 213.5, 217.8, 229.0],
      6, "ZONE-GRADE-12.jpg", 480, "%.2f")

# ===== ⑧ 闪烁量化复扫（YAVG·新 D01 + deflicker 族 + 对照）=====
print("== flicker scan")
SEGS = [
    (34.74, 2.18, "S6_chisel"), (77.34, 2.84, "C01_carver_face"),
    (100.14, 2.74, "C08_strike_burst"), (141.76, 2.80, "D01_carver_words_NEW"),
    (159.66, 3.38, "D06_chisel_fingertip"), (208.08, 4.58, "E06_strike"),
    (92.62, 2.60, "C06_forever_cut"), (184.08, 3.18, "B04_embers"),
    (230.50, 3.75, "Z04_glyph"), (180.00, 2.00, "SING2_NEW"), (207.00, 1.80, "SIL4_NEW"),
    (25.90, 3.50, "S3_stele_CTRL"), (131.72, 6.84, "R06_CTRL"),
]
fl = []
for st, dur, name in SEGS:
    r2 = subprocess.run([FF, "-v", "info", "-ss", "%.3f" % st, "-t", "%.3f" % dur, "-i", SRC,
                         "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    ys = [float(m) for m in re.findall(r"YAVG=([\d.]+)", r2.stderr or "")]
    if len(ys) < 4:
        fl.append("%-28s PROBE-FAIL frames=%d" % (name, len(ys)))
        continue
    ds = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    osc = sum(1 for i in range(len(ds) - 1)
              if abs(ds[i]) >= 0.15 and abs(ds[i + 1]) >= 0.15 and ds[i] * ds[i + 1] < 0)
    peak = max(abs(d) for d in ds)
    fl.append("%-28s frames=%3d osc=%2d peak|dY|=%6.2f" % (name, len(ys), osc, peak))
with open(os.path.join(OUT, "flicker_scan_v511.txt"), "w", encoding="utf-8") as f:
    f.write("V5.11 YAVG flicker rescan (noise floor 0.15)\n\n" + "\n".join(fl) + "\n")
print("\n".join(fl))
print("ALL DONE -> " + OUT)
