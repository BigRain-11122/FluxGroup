# -*- coding: utf-8 -*-
# proxy_review_probes.py — V5 PROXY 导演拉片探针集（装配完成后跑）
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROXY = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\full_mv_v5_proxy.mp4"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\qc-v5redo-17\proxy_probes"
os.makedirs(OUT, exist_ok=True)
FF = "ffmpeg"

PROBES = [
    # (song_t, tag, note)
    (1.00,  "aigc_1s",      "AIGC badge"),
    (5.80,  "title_580",    "title card mid (new INT2 + 2-line)"),
    (7.30,  "int2_end",     "INT2 window end"),
    (43.92, "s9_mid",       "s9 lyric zone"),
    (29.50, "sil1_a",       "SIL1 pattern drift A"),
    (30.40, "sil1_b",       "SIL1 pattern drift B"),
    (77.60, "c01_flash",    "C01 0.66s flash window"),
    (78.20, "sing1",        "SING1 insert after C01"),
    (156.20,"d05_a",        "D05 texture crawl A"),
    (158.80,"d05_b",        "D05 texture crawl B"),
    (151.00,"d03b_win",     "D03b window content"),
    (152.00,"d03b_tail",    "D03b tail/cut edge"),
    (152.50,"d03b_next",    "post-D03b (flame bleed check)"),
    (3.40,  "int1_end",     "INT1 end (outfit A)"),
    (7.40,  "int2_mid2",    "INT2 late (outfit A)"),
    (8.00,  "int3_a",       "INT3 (outfit B)"),
    (12.00, "int4_mid",     "INT4 (outfit C)"),
    (15.00, "int5_mid",     "INT5 (outfit D)"),
    (173.50,"b01_mid",      "B01 weary mid"),
    (199.00,"e03_mid",      "E03 gaze meet"),
    (215.00,"e04_slow",     "E04 slow exchange"),
    (218.90,"e04_tail",     "E04 tail"),
]

def board(fname, items, cols, header, cw=960):
    rows = (len(items) + cols - 1) // cols
    ch = int(cw * 540 / 960)
    im = Image.new("RGB", (cols * cw, rows * (ch + 24) + 30), (16, 16, 18))
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
    except Exception:
        fnt = ImageFont.load_default()
    d.text((8, 6), header, fill=(255, 220, 120), font=fnt)
    for i, (path, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = c * cw, 30 + r * (ch + 24)
        d.text((x + 4, y + 2), label, fill=(200, 200, 210), font=fnt)
        if path and os.path.exists(path):
            fr = Image.open(path).convert("RGB").resize((cw, ch))
            im.paste(fr, (x, y + 22))
    im.save(os.path.join(OUT, fname), quality=90)
    print("BOARD:", fname)

probes = []
for t, tag, note in PROBES:
    p = os.path.join(OUT, "probe_%s.jpg" % tag)
    subprocess.run([FF, "-y", "-ss", str(t), "-i", PROXY, "-frames:v", "1", "-q:v", "2", p], capture_output=True)
    if os.path.exists(p):
        probes.append((p, "%s  t=%.2f  %s" % (tag, t, note)))
        print("OK", tag)

# 拼四张审板（每板 6 格）
for bi in range(0, len(probes), 6):
    chunk = probes[bi:bi + 6]
    board("PROXY-REVIEW-%d.jpg" % (bi // 6 + 1), chunk, 3,
          "V5 proxy director pull probes board %d" % (bi // 6 + 1))
print("DONE", len(probes), "probes")
