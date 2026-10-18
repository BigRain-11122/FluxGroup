# -*- coding: utf-8 -*-
# scan_full_v56_quant_r1018.py — V5.6 全片量化扫描（逐镜终审配套·luma 死黑/过曝/重复帧冻结）
# 探针密度 4fps 336x192：>=0.75s 逐帧恒同才记冻结（编码噪声底天然滤除微动画面）
import os, subprocess, json, glob
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
SRC = os.path.join(HERE, "full_mv_v56.mp4")
OUT = os.path.join(HERE, "final_review_quant")
FR = os.path.join(OUT, "fr")
os.makedirs(FR, exist_ok=True)

for f in glob.glob(os.path.join(FR, "fr_*.jpg")):
    os.remove(f)
subprocess.run([FF, "-y", "-i", SRC, "-vf", "fps=4,scale=336:192", "-q:v", "5",
                os.path.join(FR, "fr_%05d.jpg")], check=True)

from PIL import Image
files = sorted(glob.glob(os.path.join(FR, "fr_*.jpg")))
print("frames=%d" % len(files))

def stats(path):
    im = Image.open(path).convert("L")
    px = list(im.getdata())
    n = len(px)
    mean = sum(px) / float(n)
    lo = sum(1 for p in px if p < 10) / float(n)
    hi = sum(1 for p in px if p > 245) / float(n)
    g = im.resize((8, 8))
    gp = list(g.getdata())
    avg = sum(gp) / 64.0
    bits = 0
    for i, p in enumerate(gp):
        if p > avg:
            bits |= (1 << i)
    return mean, lo, hi, bits

rows = []
for i, f in enumerate(files):
    mean, lo, hi, bits = stats(f)
    rows.append({"i": i, "t": round(i / 4.0, 3), "file": os.path.basename(f),
                 "mean": round(mean, 2), "lo_pct": round(lo * 100, 2),
                 "hi_pct": round(hi * 100, 2), "ahash": bits})

def ham(a, b):
    return bin(a ^ b).count("1")

freezes = []
run_start = None
for i in range(1, len(rows)):
    d = ham(rows[i]["ahash"], rows[i - 1]["ahash"])
    rows[i]["dprev"] = d
    if d == 0:
        if run_start is None:
            run_start = i - 1
    else:
        if run_start is not None:
            n = i - run_start
            if n >= 3:
                freezes.append({"t0": round(run_start / 4.0, 2),
                                "t1": round((i - 1) / 4.0, 2),
                                "frames": n + 1, "dur_s": round((n + 1) / 4.0, 2)})
            run_start = None
if run_start is not None:
    n = len(rows) - 1 - run_start
    if n >= 3:
        freezes.append({"t0": round(run_start / 4.0, 2),
                        "t1": round((len(rows) - 1) / 4.0, 2),
                        "frames": n + 1, "dur_s": round((n + 1) / 4.0, 2)})

dead = [r for r in rows if r["mean"] < 22]
hot = [r for r in rows if r["mean"] > 235]
crush = [r for r in rows if r["lo_pct"] > 85 and r["mean"] < 40]
res = {"film": "full_mv_v56.mp4", "fps_probe": 4, "frames": len(files),
       "dur_s": round(len(files) / 4.0, 2),
       "freeze_runs": freezes, "deadblack_frames": dead,
       "overexposed_frames": hot, "crush_frames": crush,
       "luma_min": min(r["mean"] for r in rows),
       "luma_max": max(r["mean"] for r in rows)}
jp = os.path.join(OUT, "QUANT-SCAN-V56-r1018.json")
with open(jp, "w", encoding="utf-8") as f:
    json.dump({"summary": res, "frames": rows}, f, ensure_ascii=False, indent=1)

md = os.path.join(OUT, "QUANT-SCAN-V56-r1018.md")
with open(md, "w", encoding="utf-8") as f:
    f.write("# QUANT-SCAN-V56 r1018 (4fps probe)\n\n")
    f.write("frames=%d dur=%.2fs luma[min]=%.1f luma[max]=%.1f\n\n" % (
        len(files), res["dur_s"], res["luma_min"], res["luma_max"]))
    f.write("## freeze runs (>=0.75s identical @4fps)\n")
    for z in freezes:
        f.write("- %.2f-%.2f (%.2fs, %d frames)\n" % (z["t0"], z["t1"], z["dur_s"], z["frames"]))
    f.write("\n## dead-black frames (mean<22)\n")
    for r in dead:
        f.write("- t=%.2f mean=%.1f\n" % (r["t"], r["mean"]))
    f.write("\n## over-exposed frames (mean>235)\n")
    for r in hot:
        f.write("- t=%.2f mean=%.1f hi%%=%.1f\n" % (r["t"], r["mean"], r["hi_pct"]))
    f.write("\n## crush frames (lo>85%% & mean<40)\n")
    for r in crush:
        f.write("- t=%.2f mean=%.1f lo%%=%.1f\n" % (r["t"], r["mean"], r["lo_pct"]))
print("WROTE " + jp)
print("WROTE " + md)
print("freezes=%d dead=%d hot=%d crush=%d" % (len(freezes), len(dead), len(hot), len(crush)))
