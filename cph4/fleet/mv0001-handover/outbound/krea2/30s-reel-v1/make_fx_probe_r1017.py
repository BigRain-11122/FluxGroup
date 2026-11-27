# -*- coding: utf-8 -*-
"""FX 17-site probe for full_mv_v52.mp4 (V5.2 FX-garnished layer review).
Per site: pre(-0.25s) / mid(peak) / post(+0.25s) frame -> labeled strip -> sheets.
Also builds close-up sheets for flash/band/echo/smoke/dust/leak mids.
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

FF  = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
MV  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "full_mv_v52.mp4")
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\fx_probe"
os.makedirs(OUT, exist_ok=True)

# (plate, st, dur, drift) -- mirror of build_full_mv_v52.py FX_EVENTS
FX = [
    ("band",  38.62, 0.52, "sweepL"),
    ("band",  40.02, 0.52, "sweepR"),
    ("leak",  47.30, 0.95, "static"),
    ("flash", 77.30, 0.14, "static"),
    ("smoke", 80.05, 0.90, "drift"),
    ("flash", 91.02, 0.13, "static"),
    ("dust",  93.05, 1.35, "drift"),
    ("dust", 102.80, 1.15, "drift"),
    ("smoke",110.42, 1.50, "drift"),
    ("leak", 110.62, 1.45, "static"),
    ("dust", 131.62, 1.25, "drift"),
    ("flash",141.72, 0.14, "static"),
    ("dust", 168.30, 2.20, "drift"),
    ("echo", 187.24, 0.58, "static"),
    ("flash",212.62, 0.13, "static"),
    ("smoke",219.80, 1.25, "drift"),
    ("dust", 231.90, 2.30, "drift"),
]
W, H = 1344, 768

def font(sz):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

def grab(t, tag, s):
    t = max(0.0, round(t * 24) / 24.0)
    p = os.path.join(OUT, "f%02d_%s.png" % (s, tag))
    r = subprocess.run([FF, "-y", "-ss", "%.3f" % t, "-i", MV,
                        "-frames:v", "1", p],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert r.returncode == 0 and os.path.isfile(p), "grab fail %s @%.2f" % (tag, t)
    return p

F44 = font(34)
TMAX = 234.25 - 0.05  # last safe frame time (video len 234.25 @24fps)
strips = []  # (site_idx, img)
mids = {}    # site_idx -> mid frame path
for i, (plate, st, dur, drift) in enumerate(FX):
    s = i + 1
    a = grab(st - 0.25, "pre", s)
    b = grab(min(st + dur / 2.0, TMAX), "mid", s)
    c = grab(min(st + dur + 0.25, TMAX), "post", s)
    mids[s] = b
    strip = Image.new("RGB", (W * 3, 44 + H), (16, 16, 16))
    d = ImageDraw.Draw(strip)
    label = "S%02d %-5s st=%6.2f dur=%.2f %-6s | A=pre(-0.25s) B=mid(peak) C=post(+0.25s)" \
            % (s, plate, st, dur, drift)
    d.text((14, 6), label, fill=(240, 226, 160), font=F44)
    for k, pth in enumerate((a, b, c)):
        strip.paste(Image.open(pth).convert("RGB"), (k * W, 44))
    strips.append((s, strip))
    print("STRIP S%02d %s %.2f pre/mid/post OK" % (s, plate, st))

def sheet(name, items):
    gap = 10
    img = Image.new("RGB", (W * 3, sum(x[1].height for x in items) + gap * (len(items) - 1)), (10, 10, 10))
    y = 0
    for s, st_img in items:
        img.paste(st_img, (0, y)); y += st_img.height + gap
    q = os.path.join(OUT, name)
    img.save(q, quality=84)
    print("SHEET %s" % q)

sheet("FX-PROBE-S1.jpg", strips[0:6])
sheet("FX-PROBE-S2.jpg", strips[6:12])
sheet("FX-PROBE-S3.jpg", strips[12:17])

# ---- close-ups: full-res mids ----
F30 = font(28)
def grid(name, cells, cols):
    rows = (len(cells) + cols - 1) // cols
    g = Image.new("RGB", (W * cols, (44 + H) * rows), (10, 10, 10))
    dd = ImageDraw.Draw(g)
    for k, (lbl, s) in enumerate(cells):
        x = (k % cols) * W; y = (k // cols) * (44 + H)
        dd.text((x + 14, y + 6), lbl, fill=(240, 226, 160), font=F30)
        g.paste(Image.open(mids[s]).convert("RGB"), (x, y + 44))
    q = os.path.join(OUT, name)
    g.save(q, quality=86)
    print("CLOSE %s" % q)

grid("FX-CLOSE-FLASH.jpg",
     [("S04 flash mid @77.37 (chorus1 in)", 4), ("S06 flash mid @91.09", 6),
      ("S12 flash mid @141.79 (chorus2 in)", 12), ("S15 flash mid @212.69", 15)], 2)
grid("FX-CLOSE-MIX.jpg",
     [("S01 band sweepL mid @38.88", 1), ("S02 band sweepR mid @40.28", 2),
      ("S03 leak mid @47.78", 3), ("S05 smoke mid @80.50", 5),
      ("S07 dust mid @93.73", 7), ("S14 echo mid @187.53", 14)], 3)
print("ALL-DONE %d strips / 3 sheets / 2 closeups -> %s" % (len(strips), OUT))
