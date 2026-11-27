# -*- coding: utf-8 -*-
# packA_qc_strips_v2_c2091.py -- 星晴PACK-A条板v2: redo-r1 6片换装重铸 (X2670 §六装配解锁前置·条板重判底板·bank job p17)
import os, subprocess, sys
from PIL import Image, ImageDraw

REPO = r"K:\Fluxgroup\FluxGroup"
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay", "clips-packA-768")
REDO = os.path.join(REPO, "media", "mv-album-001-jay", "clips-packA-redo-r1")
REDO_UNITS = ("S2-14", "S3-19", "S3-20", "S4-22", "S4-24", "F5-33a")
TMP = os.path.join(CLIPS, "_qcframes_v2")
OUT = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "xq-PACKA-QC-STRIPS-v2-c2091.jpg")
NO_WINDOW = 0x08000000
os.makedirs(TMP, exist_ok=True)

def src_for(fn):
    # redo-r1 swap law (X2670): 6 re-burned units read from clips-packA-redo-r1, others from clips-packA-768
    unit = fn[:-4]
    if unit.startswith("XQ_") and unit[3:] in REDO_UNITS:
        return os.path.join(REDO, unit + "-redo-r1.mp4"), unit + " [REDO-R1]"
    return os.path.join(CLIPS, fn), unit

all_files = [f for f in sorted(os.listdir(CLIPS)) if f.endswith(".mp4")]
missing = [p for p in (src_for(f)[0] for f in all_files) if not os.path.isfile(p)]
if missing:
    # fail-loud input gate: no partial board (while i2v3 S3-19 burns, exactly 1 missing is expected)
    print("STRIPS-V2 MISSING %d input(s):" % len(missing))
    for m in missing:
        print("  " + m)
    sys.exit(1)

def ff(clip, t, outpng):
    r = subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", clip, "-frames:v", "1", outpng],
                       capture_output=True, creationflags=NO_WINDOW, timeout=120)
    return r.returncode == 0 and os.path.isfile(outpng)

strips = []
for fn in all_files:
    clip, label = src_for(fn)
    dur = 5.0
    try:
        p = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", clip],
                           capture_output=True, text=True, creationflags=NO_WINDOW, timeout=60)
        dur = float(p.stdout.strip())
    except Exception:
        pass
    frames = []
    for i, t in enumerate([0.4, dur / 2.0, max(0.2, dur - 0.4)]):
        fp = os.path.join(TMP, "%s_%d.png" % (fn[:-4], i))
        if ff(clip, t, fp):
            frames.append(fp)
    if len(frames) < 2:
        continue
    ims = [Image.open(f).convert("RGB").resize((448, 256)) for f in frames]
    W, H, GAP, LBL = 448, 256, 6, 18
    board = Image.new("RGB", (len(ims) * (W + GAP) + GAP, H + LBL + GAP * 2), (24, 22, 20))
    dr = ImageDraw.Draw(board)
    for i, im in enumerate(ims):
        x = GAP + i * (W + GAP)
        board.paste(im, (x, GAP))
    dr.text((GAP, GAP + H + 2), "%s  [t=0.4 / %.1f / %.1f]" % (label, dur / 2.0, max(0.2, dur - 0.4)),
            fill=(210, 190, 150))
    strips.append((fn, board))

COLS = 2
SW = max(b.size[0] for _, b in strips) + 10
SH = max(b.size[1] for _, b in strips) + 8
rows = (len(strips) + COLS - 1) // COLS
grid = Image.new("RGB", (COLS * SW + 10, rows * SH + 10), (18, 16, 15))
for i, (fn, b) in enumerate(strips):
    grid.paste(b, (10 + (i % COLS) * SW, 10 + (i // COLS) * SH))
if len(strips) != 31:
    print("STRIPS-V2 COUNT-FAIL: %d strips != 31" % len(strips))
    sys.exit(1)
grid.save(OUT, quality=88)
print("STRIPS-V2 DONE: %d clips -> %s" % (len(strips), OUT))
