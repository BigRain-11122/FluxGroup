# -*- coding: utf-8 -*-
"""V5.3 arrival verification (CEO O-20261017-1330): new FX site probes + fix rechecks + E1 recount.
Sheets: N1 (6 strips), N2 (5 strips), F1 (AIGC/SIL4/R05/S17 full-res cells)."""
import os, json, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF   = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
MV   = os.path.join(HERE, "full_mv_v53.mp4")
OUT  = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\fx_probe_v53"
os.makedirs(OUT, exist_ok=True)
W, H, TMAX = 1344, 768, 234.20

def fnt(sz):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F22, F32, F44 = fnt(22), fnt(32), fnt(44)

def grab(t, path, w=None):
    t = max(0.0, min(TMAX, round(t * 24) / 24.0))
    cmd = [FF, "-y", "-ss", "%.3f" % t, "-i", MV, "-frames:v", "1"]
    if w: cmd += ["-vf", "scale=%d:-2" % w]
    cmd.append(path)
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert r.returncode == 0 and os.path.isfile(path) and os.path.getsize(path) > 1000, "grab fail @%.2f" % t
    return path

# ---- E1 recount with 26 sites ----
TL = json.load(open(os.path.join(HERE, "timeline_v52.json"), encoding="utf-8"))
FX26 = [(17.42,"flash"),(28.76,"dust"),(38.62,"band"),(40.02,"band"),(47.30,"leak"),
        (58.20,"smoke"),(68.62,"dust"),(77.30,"flash"),(80.05,"smoke"),(91.02,"flash"),
        (92.56,"dust"),(102.80,"dust"),(110.42,"smoke"),(110.62,"leak"),(131.62,"dust"),
        (141.72,"flash"),(150.34,"leak"),(159.42,"smoke"),(168.30,"dust"),(176.76,"smoke"),
        (187.24,"echo"),(193.04,"dust"),(199.30,"leak"),(212.62,"flash"),(219.80,"smoke"),
        (231.90,"dust")]
cuts = TL["cuts"]
def covered(c):
    for st, fam in FX26:
        d = 0.70 if fam in ("flash",) else 0.35
        if st - 0.35 <= c["win_b"] <= st + d + 0.35:
            return fam
    return None
hard = [c for c in cuts if c["type"] == "hard"]
garn = [c for c in hard if covered(c)]
bare = [c for c in hard if not covered(c)]
fams = set(f for _, f in FX26) | set(c["type"].split(":")[1] for c in cuts if c["type"] != "hard")
E1 = {"n_cuts": len(cuts), "n_hard": len(hard), "hard_garnished": len(garn),
      "bare_hard": len(bare), "bare_over_total": round(len(bare) / len(cuts), 4),
      "families": sorted(fams)}
print("E1-V53 " + json.dumps(E1, ensure_ascii=False))
json.dump(E1, open(os.path.join(OUT, "e1_v53.json"), "w"), indent=1)

# ---- new-site strips ----
SITES = [(17.42,0.13,"flash"),(28.76,1.05,"dust"),(58.20,1.05,"smoke"),(68.62,1.00,"dust"),
         (92.56,1.35,"dust"),(150.34,0.95,"leak"),(159.42,0.95,"smoke"),(176.76,1.05,"smoke"),
         (193.04,0.85,"dust"),(199.30,1.60,"leak"),(231.90,2.30,"dust_z04")]
strips = []
for i, (st, dur, fam) in enumerate(SITES):
    a = grab(st - 0.25, "n%02d_pre.png" % i)
    b = grab(min(st + dur / 2, TMAX), "n%02d_mid.png" % i)
    c = grab(min(st + dur + 0.25, TMAX), "n%02d_post.png" % i)
    strip = Image.new("RGB", (W * 3, 44 + H), (16, 16, 16))
    ImageDraw.Draw(strip).text((14, 6),
        "N%02d %-8s st=%6.2f dur=%.2f | A=pre B=mid C=post" % (i, fam, st, dur),
        fill=(240, 226, 160), font=F44)
    for k, p in enumerate((a, b, c)):
        strip.paste(Image.open(p).convert("RGB").resize((W, H)), (k * W, 44))
    strips.append(strip)

def sheet(name, items):
    gap = 10
    im = Image.new("RGB", (W * 3, sum(x.height for x in items) + gap * (len(items) - 1)), (10, 10, 10))
    y = 0
    for s in items:
        im.paste(s, (0, y)); y += s.height + gap
    q = os.path.join(OUT, name); im.save(q, quality=84); print("SHEET " + q)
sheet("FXV53-NEW-1.jpg", strips[0:6])
sheet("FXV53-NEW-2.jpg", strips[6:11])

# ---- fix recheck cells (full-res) ----
im = Image.new("RGB", (W * 4, 46 + (34 + H) * 2), (12, 12, 12))
ImageDraw.Draw(im).text((12, 8), "V5.3 fix rechecks: AIGC badge / SIL4 warm / R05 lift / S17 z04 dust",
                        fill=(240, 226, 160), font=F32)
CELLS = [(0, 0.55, "AIGC @0.55 (new fade d=0.5, stronger badge)"),
         (1, 1.80, "AIGC @1.80 peak"),
         (2, None, "SIL4 mid @~207.9 (warm push vs cold-gray)"),
         (3, None, "R05 @126.90 (lifted, subtitle readable?)")]
FRAMES = {0: 0.55, 1: 1.80, 2: 207.90, 3: 126.90}
for k in range(4):
    x = k * W; y = 46
    im.paste(Image.new("RGB", (W, 34), (14, 14, 14)), (x, y))
    ImageDraw.Draw(im).text((x + 10, y + 5), CELLS[k][2], fill=(240, 226, 160), font=F22)
    p = os.path.join(OUT, "fx_cell_%d.png" % k)
    im.paste(Image.open(grab(FRAMES[k], p)).resize((W, H)), (x, y + 34))
S17 = [232.60, 233.20, 233.80, 234.10]
for k, t in enumerate(S17):
    x = k * W; y = 46 + 34 + H
    im.paste(Image.new("RGB", (W, 34), (14, 14, 14)), (x, y))
    ImageDraw.Draw(im).text((x + 10, y + 5), "S17 z04 dust @%.2f (denser plate a=0.50)" % t,
                            fill=(240, 226, 160), font=F22)
    p = os.path.join(OUT, "s17z_%d.png" % k)
    im.paste(Image.open(grab(t, p)).resize((W, H)), (x, y + 34))
q = os.path.join(OUT, "FXV53-FIX-RECHECK.jpg"); im.save(q, quality=86)
print("SHEET " + q)
print("V53-VERIFY-BOARDS-DONE -> " + OUT)
