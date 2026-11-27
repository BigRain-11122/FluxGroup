# -*- coding: utf-8 -*-
# qc_v5redo_verify.py — QC 初判存疑件全分辨率实证关
# D01 乱码/道具崩验证(全分辨率6帧) / C04 字形文明判定(4帧) / E01c 发力密帧(8帧) / E04 帧差动态度(10帧条带)
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

V5 = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\qc-v5redo-17"
FR = os.path.join(OUT, "verify_frames")
os.makedirs(FR, exist_ok=True)
FF = "ffmpeg"

def grab(clip, t, tag, scale=None, w=None):
    name = "%s_%s.jpg" % (clip.replace("_v5.mp4", ""), tag)
    p = os.path.join(FR, name)
    cmd = [FF, "-y", "-ss", str(t), "-i", os.path.join(V5, clip), "-frames:v", "1"]
    if scale:
        cmd += ["-vf", "scale=%d:-2" % w]
    cmd += ["-q:v", "2", p]
    subprocess.run(cmd, capture_output=True)
    return p if os.path.exists(p) else None

def board(fname, cells, cols, header, cw=960):
    """cells: flat list of (path,label); cw=cell width, cell height auto 9:16->cw*9/16"""
    rows = (len(cells) + cols - 1) // cols
    ch = int(cw * 768 / 1344)
    im = Image.new("RGB", (cols * cw, rows * (ch + 24) + 30), (16, 16, 18))
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
    except Exception:
        fnt = ImageFont.load_default()
    d.text((8, 6), header, fill=(255, 220, 120), font=fnt)
    for i, (path, label) in enumerate(cells):
        r, c = divmod(i, cols)
        x, y = c * cw, 30 + r * (ch + 24)
        d.text((x + 4, y + 2), label, fill=(200, 200, 210), font=fnt)
        if path and os.path.exists(path):
            fr = Image.open(path).convert("RGB").resize((cw, ch))
            im.paste(fr, (x, y + 22))
    im.save(os.path.join(OUT, fname), quality=92)
    print("BOARD:", fname)

# ---- 1) D01 全分辨率 6 帧 ----
d01 = []
for t, tag in [(0.5, "v1"), (1.5, "v2"), (2.6, "v3"), (3.4, "v4"), (4.2, "v5"), (4.9, "v6")]:
    d01.append((grab("D01_carver_words_v5.mp4", t, tag), "D01 t=%s (full-res)" % t))
board("VERIFY-D01-FULLRES.jpg", d01, 3, "D01 verify: latin chars? accordion tablet? white ball?")

# ---- 2) C04 全分辨率 4 帧 ----
c04 = []
for t, tag in [(0.5, "v1"), (2.0, "v2"), (3.5, "v3"), (4.9, "v4")]:
    c04.append((grab("C04_words_alive_v5.mp4", t, tag), "C04 t=%s (full-res)" % t))
board("VERIFY-C04-GLYPHS.jpg", c04, 2, "C04 verify: runic vs cuneiform glyph style")

# ---- 3) E01c 密帧 8 帧（找发力瞬间+石屑）----
e01 = []
for t, tag in [(0.3, "d1"), (0.9, "d2"), (1.5, "d3"), (2.1, "d4"), (2.7, "d5"), (3.3, "d6"), (3.9, "d7"), (4.6, "d8")]:
    e01.append((grab("E01c_first_line_v5.mp4", t, tag), "E01c t=%s" % t))
board("VERIFY-E01C-DENSE.jpg", e01, 4, "E01c dense: strike moment + stone debris present?")

# ---- 4) E04 帧差动态度条带（10 帧等间隔+逐帧差值量化）----
e04paths = []
for i in range(10):
    t = 0.26 * (i + 0.5)
    e04paths.append(grab("E04_replay_faces_v5.mp4", t, "m%d" % i))
# 帧差量化（640 缩略·均方差）
diffs = []
prev = None
for i, p in enumerate(e04paths):
    if p and os.path.exists(p):
        im = Image.open(p).convert("L").resize((320, 180))
        import numpy as np
        arr = np.asarray(im, dtype=float)
        if prev is not None:
            diffs.append(float(np.abs(arr - prev).mean()))
        prev = arr
# 去掉首差（i=0 无对）
print("E04 frame-diff series (mean abs diff, 320x180):")
print(" ".join("%.2f" % d for d in diffs))
# 差值曲线画成小图
import numpy as np
W, H = 960, 200
im = Image.new("RGB", (W, H), (16, 16, 18))
d = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
except Exception:
    fnt = ImageFont.load_default()
d.text((8, 6), "E04 inter-frame diff curve (0.26s steps)", fill=(255, 220, 120), font=fnt)
if diffs:
    mx = max(diffs) or 1.0
    for i, v in enumerate(diffs):
        x = 20 + i * (W - 40) / max(1, len(diffs))
        h = (H - 50) * (v / mx)
        d.rectangle([x, H - 20 - h, x + 12, H - 20], fill=(120, 200, 255))
    d.text((W - 260, H - 44), "tail freeze: last bars near-zero?", fill=(180, 180, 190), font=fnt)
im.save(os.path.join(OUT, "VERIFY-E04-DIFFCURVE.jpg"), quality=92)
print("BOARD: VERIFY-E04-DIFFCURVE.jpg")
# 原帧也拼一条带
board("VERIFY-E04-STRIP.jpg", [(p, "E04 t=%.2f" % (0.26 * (i + 0.5))) for i, p in enumerate(e04paths)], 5,
      "E04 10-frame strip (uniform steps)")
print("DONE")
