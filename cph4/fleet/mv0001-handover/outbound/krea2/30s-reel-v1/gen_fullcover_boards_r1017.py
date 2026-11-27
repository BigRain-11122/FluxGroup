# -*- coding: utf-8 -*-
"""V5.2 full-coverage review boards — CEO O-20261017-1340 逐镜全审令.
Every shot / every cut / every character / color. Boards:
  SHOT-1..6 (12 cells ea, 672x384), CUT-1..9 (8 rows ea, 480x274 trios),
  TONE (72 thumbs), CHAR-HER / CHAR-HIM, OBS (6 obs items), HOOK (0-3s),
  AIGC (badge 2 frames), S17-DUST, S08S10 recheck.
Program: E1 recount (FX matched on win_b = on-screen), luma scan, aHash dup pairs.
"""
import os, json, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF   = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
MV   = os.path.join(HERE, "full_mv_v52.mp4")
OUT  = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\fullcover"
os.makedirs(OUT, exist_ok=True)
TL = json.load(open(os.path.join(HERE, "timeline_v52.json"), encoding="utf-8"))
W, H = 1344, 768
TMAX = 234.20

FX = [(38.62,"band"),(40.02,"band"),(47.30,"leak"),(77.30,"flash"),(80.05,"smoke"),
      (91.02,"flash"),(93.05,"dust"),(102.80,"dust"),(110.42,"smoke"),(110.62,"leak"),
      (131.62,"dust"),(141.72,"flash"),(168.30,"dust"),(187.24,"echo"),(212.62,"flash"),
      (219.80,"smoke"),(231.90,"dust")]

def fnt(sz):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

F22, F26, F32 = fnt(22), fnt(26), fnt(32)

def grab(t, path, w=None):
    if os.path.isfile(path) and os.path.getsize(path) > 1000:
        return path
    t = max(0.0, min(TMAX, round(t * 24) / 24.0))
    cmd = [FF, "-y", "-ss", "%.3f" % t, "-i", MV, "-frames:v", "1"]
    if w: cmd += ["-vf", "scale=%d:-2" % w]
    cmd.append(path)
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert r.returncode == 0 and os.path.isfile(path) and os.path.getsize(path) > 1000, "grab fail @%.2f" % t
    return path

def label_bar(w, h, txt, f=F26):
    img = Image.new("RGB", (w, h), (14, 14, 14))
    ImageDraw.Draw(img).text((10, 4), txt, fill=(240, 226, 160), font=f)
    return img

shots = TL["shots"]; cuts = TL["cuts"]
for s in shots:
    s["mid"] = round((s["win"][0] + s["win"][1]) / 2.0, 3)

# ---------- E1 recount (win_b = on-screen cut time) ----------
for c in cuts:
    c["fxhit"] = [f for (f, fam) in FX if abs(f - c["win_b"]) <= 0.35]
hard  = [c for c in cuts if c["type"] == "hard"]
soft  = [c for c in cuts if c["type"] != "hard"]
ghard = [c for c in hard if c["fxhit"]]
bare  = [c for c in hard if not c["fxhit"]]
fams = set()
for c in cuts:
    if c["type"] != "hard":
        fams.add(c["type"].split(":")[1])
    for f in c["fxhit"]:
        fams.add(dict(FX)[f])
inshot = [f for (f, fam) in FX if fam and all(abs(f - c["win_b"]) > 0.35 for c in cuts)]
E1 = {"n_cuts": len(cuts), "n_hard": len(hard), "n_soft": len(soft),
      "hard_garnished": len(ghard), "bare_hard": len(bare),
      "bare_over_total": round(len(bare)/len(cuts), 4),
      "hard_over_total": round(len(hard)/len(cuts), 4),
      "families": sorted(fams), "inshot_fx": inshot}

# ---------- shot mids: full PNG + luma + aHash ----------
luma, ahash, fulls = [], [], {}
for i, s in enumerate(shots):
    sid = s["sid"]; t = s["mid"]
    p = os.path.join(OUT, "shot_%02d.png" % i)
    grab(t, p)
    img = Image.open(p); fulls[i] = (p, img.size)
    g = img.convert("L"); px = list(g.getdata()); n = len(px)
    sx = sorted(px)
    luma.append({"i": i, "sid": sid, "t": t,
                 "mean": round(sum(px)/n, 1), "p5": sx[int(n*.05)], "p95": sx[int(n*.95)]})
    h = g.resize((8, 8)); bits = 0
    med = sorted(h.getdata())[32]
    for b, v in enumerate(h.getdata()):
        if v > med: bits |= 1 << b
    ahash.append(bits)
dups = []
for a in range(len(ahash)):
    for b in range(a + 1, len(ahash)):
        d = bin(ahash[a] ^ ahash[b]).count("1")
        if d <= 6:
            dups.append((shots[a]["sid"], shots[b]["sid"], d))
LU = {"e1": E1,
      "underexposed": [x for x in luma if x["mean"] < 30],
      "overexposed": [x for x in luma if x["p95"] >= 252 and x["mean"] > 205],
      "dupe_pairs": dups, "luma": luma}
json.dump(LU, open(os.path.join(OUT, "fullcover_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("E1 " + json.dumps(E1, ensure_ascii=False))
print("UNDER " + json.dumps(LU["underexposed"], ensure_ascii=False))
print("OVER  " + json.dumps(LU["overexposed"], ensure_ascii=False))
print("DUPS  " + json.dumps(dups, ensure_ascii=False))

# ---------- SHOT sheets (12 cells 672x384, 4x3) ----------
CW, CH = 672, 384
for sheet_i in range(6):
    idxs = list(range(sheet_i * 12, min((sheet_i + 1) * 12, len(shots))))
    cols = 4; rows = (len(idxs) + cols - 1) // cols
    sh = Image.new("RGB", (CW * cols, 46 + (38 + CH) * rows), (12, 12, 12))
    ImageDraw.Draw(sh).text((12, 8), "FULLCOVER SHOT-%d  V5.2 full_mv_v52.mp4  cell=shot mid frame  [t0-t1]" % (sheet_i + 1),
                            fill=(240, 226, 160), font=F32)
    for k, i in enumerate(idxs):
        s = shots[i]; x = (k % cols) * CW; y = 46 + (k // cols) * (38 + CH)
        sh.paste(label_bar(CW, 38, "%02d %s [%.2f-%.2f] mid=%.2f" % (i, s["sid"], s["win"][0], s["win"][1], s["mid"])), (x, y))
        sh.paste(Image.open(fulls[i][0]).resize((CW, CH)), (x, y + 38))
    q = os.path.join(OUT, "SHOT-%d.jpg" % (sheet_i + 1)); sh.save(q, quality=84)
    print("SHEET " + q)

# ---------- CUT sheets (8 rows x 3 cells 480px) ----------
CW2 = 480
for sheet_i in range(9):
    rows = cuts[sheet_i * 8:(sheet_i + 1) * 8]
    if not rows: break
    im = Image.new("RGB", (CW2 * 3, 46 + (34 + 274) * len(rows)), (12, 12, 12))
    ImageDraw.Draw(im).text((12, 8), "FULLCOVER CUT-%d  rows=cut point: A=pre(-0.08s) B=at/blend C=post  [type]" % (sheet_i + 1),
                            fill=(240, 226, 160), font=F32)
    for r, c in enumerate(rows):
        y = 46 + r * (34 + 274)
        if c["type"] == "hard":
            ts = [c["win_b"] - 0.08, c["win_b"] + 0.08, c["win_b"] + 0.34]
            cap = "A=pre B=post C=+0.34s"
        else:
            D = float(c["type"].split(":")[2])
            ts = [c["win_b"] - 0.08, c["win_b"] + D / 2, c["win_b"] + D + 0.08]
            cap = "A=pre B=blend-mid C=after"
        tag = c["type"].upper() + (" +" + ",".join(dict(FX)[f] for f in c["fxhit"]) if c["fxhit"] else " BARE")
        im.paste(label_bar(CW2 * 3, 34, "#%02d %s > %s @%.2f %s | %s" % (c["k"], c["prev"], c["next"], c["win_b"], tag, cap), F22), (0, y))
        for k, t in enumerate(ts):
            p = os.path.join(OUT, "cut_%02d_%d.jpg" % (c["k"], k))
            grab(t, p, w=CW2)
            im.paste(Image.open(p).resize((CW2, 274)), (k * CW2, y + 34))
    q = os.path.join(OUT, "CUT-%d.jpg" % (sheet_i + 1)); im.save(q, quality=84)
    print("SHEET " + q)

def shot_by(prefix):
    for s in shots:
        base = s["sid"].split("@")[0]
        if base == prefix or base.startswith(prefix):
            return s
    raise SystemExit("sid missing " + prefix)

def sid_frame(prefix, frac, name, w=None):
    s = shot_by(prefix)
    t = s["win"][0] + (s["win"][1] - s["win"][0]) * frac
    p = os.path.join(OUT, name)
    grab(t, p, w=w)
    return p

# ---------- TONE sheet (72 thumbs 224x128) ----------
tw, th = 224, 128
cols = 8
rows = (len(shots) + cols - 1) // cols
im = Image.new("RGB", (tw * cols, 46 + (20 + th) * rows), (12, 12, 12))
ImageDraw.Draw(im).text((12, 8), "FULLCOVER TONE  chronological shot-mid thumbnails (color/exposure sweep)",
                        fill=(240, 226, 160), font=F32)
for k, s in enumerate(shots):
    x = (k % cols) * tw; y = 46 + (k // cols) * (20 + th)
    im.paste(label_bar(tw, 20, "%02d %s" % (k, s["sid"][:14]), F22), (x, y))
    im.paste(Image.open(fulls[k][0]).resize((tw, th)), (x, y + 20))
q = os.path.join(OUT, "TONE.jpg"); im.save(q, quality=84)
print("SHEET " + q)

# ---------- CHAR sheets ----------
HER = ["INT2_paper_fight", "INT3_photo_stare", "INT5_head_bow", "N02_crowd_her", "R02_she_turns",
       "D02_she_reads", "D03b_direct_gaze", "D04_her_brush", "B03_last_look", "E03_gaze_meet",
       "SING2", "E04_replay_faces"]
HIM = ["INT1_desk_breath", "C01_carver_face", "D01_carver_words", "D06_chisel_fingertip",
       "E01a_carver", "E01c_first_line", "E06_strike", "C04_words_alive", "S6_chisel"]
def char_sheet(name, sids, who):
    cols = 3; rows = (len(sids) + cols - 1) // cols
    im = Image.new("RGB", (CW * cols, 46 + (36 + CH) * rows), (12, 12, 12))
    ImageDraw.Draw(im).text((12, 8), "FULLCOVER CHAR-%s  identity consistency (same person across shots?)" % who,
                            fill=(240, 226, 160), font=F32)
    for k, pf in enumerate(sids):
        s = shot_by(pf)
        x = (k % cols) * CW; y = 46 + (k // cols) * (36 + CH)
        im.paste(label_bar(CW, 36, "%s [%.2f-%.2f]" % (s["sid"], s["win"][0], s["win"][1])), (x, y))
        p = os.path.join(OUT, "char_%s_%d.jpg" % (who, k))
        grab(s["mid"], p, w=CW)
        im.paste(Image.open(p).resize((CW, CH)), (x, y + 36))
    q = os.path.join(OUT, name); im.save(q, quality=86)
    print("SHEET " + q)
char_sheet("CHAR-HER.jpg", HER, "HER")
char_sheet("CHAR-HIM.jpg", HIM, "HIM")

# ---------- OBS sheet (6 observation items, full-res 3x2) ----------
OBS = [("SING1_v2", 0.5, "SING1_v2 bg relief civilization purity"),
       ("SIL3_v2", 0.5, "SIL3_v2 corridor paintings non-ghost"),
       ("E03", 0.4, "E03 his-side firelight weak?"),
       ("D03b", 0.9, "D03b tail-flame color recheck"),
       ("C01", 0.85, "C01 closed-eye 'carving' semantics"),
       ("D05", 0.5, "D05 floating dust motes")]
im = Image.new("RGB", (W * 3, 46 + (36 + H) * 2), (12, 12, 12))
ImageDraw.Draw(im).text((12, 8), "FULLCOVER OBS  V5-proxy 768P review carryover items (full-res)",
                        fill=(240, 226, 160), font=F32)
for k, (pf, fr, desc) in enumerate(OBS):
    s = shot_by(pf)
    x = (k % 3) * W; y = 46 + (k // 3) * (36 + H)
    im.paste(label_bar(W, 36, "%s @%.2f | %s" % (pf, s["mid"], desc)), (x, y))
    im.paste(Image.open(sid_frame(pf, fr, "obs_%d.png" % k)).resize((W, H)), (x, y + 36))
q = os.path.join(OUT, "OBS.jpg"); im.save(q, quality=86)
print("SHEET " + q)

# ---------- HOOK (0-3s) ----------
im = Image.new("RGB", (W * 3, 46 + 36 + H), (12, 12, 12))
ImageDraw.Draw(im).text((12, 8), "FULLCOVER HOOK  first-3-seconds frames (CHK-E7)", fill=(240, 226, 160), font=F32)
im.paste(label_bar(W * 3, 36, "0.50s | 1.50s | 2.50s"), (0, 46))
for k, t in enumerate((0.50, 1.50, 2.50)):
    p = os.path.join(OUT, "hook_%d.png" % k); grab(t, p)
    im.paste(Image.open(p).resize((W, H)), (k * W, 46 + 36))
q = os.path.join(OUT, "HOOK.jpg"); im.save(q, quality=86)
print("SHEET " + q)

# ---------- AIGC badge recheck (full-res pair) ----------
im = Image.new("RGB", (W * 2, 46 + 36 + H), (12, 12, 12))
ImageDraw.Draw(im).text((12, 8), "AIGC badge recheck @1.00s (CHK-T2 f_00 dim?) vs @1.80s (peak)", fill=(240, 226, 160), font=F32)
im.paste(label_bar(W * 2, 36, "@1.00s (probe frame) | @1.80s (badge peak window 1.2-2.4)"), (0, 46))
for k, t in enumerate((1.00, 1.80)):
    p = os.path.join(OUT, "aigc_%d.png" % k); grab(t, p)
    im.paste(Image.open(p).resize((W, H)), (k * W, 46 + 36))
q = os.path.join(OUT, "AIGC.jpg"); im.save(q, quality=88)
print("SHEET " + q)

# ---------- S17 dust recheck + S08/S10 strength ----------
im = Image.new("RGB", (W * 3, 46 + 36 + H), (12, 12, 12))
ImageDraw.Draw(im).text((12, 8), "S17 dust recheck @232.60/233.20/233.80 (probe FAIL at 233.05?)", fill=(240, 226, 160), font=F32)
im.paste(label_bar(W * 3, 36, "232.60 | 233.20 | 233.80  (fx_dust 231.90 dur 2.30 alpha .40 fade_in .70)"), (0, 46))
for k, t in enumerate((232.60, 233.20, 233.80)):
    p = os.path.join(OUT, "s17_%d.png" % k); grab(t, p)
    im.paste(Image.open(p).resize((W, H)), (k * W, 46 + 36))
q = os.path.join(OUT, "S17-DUST.jpg"); im.save(q, quality=88)
print("SHEET " + q)

im = Image.new("RGB", (W * 2, 46 + 36 + H), (12, 12, 12))
ImageDraw.Draw(im).text((12, 8), "S08 dust @103.37 / S10 leak @111.34 strength recheck (full-res)", fill=(240, 226, 160), font=F32)
im.paste(label_bar(W * 2, 36, "S08 dust mid | S10 leak mid"), (0, 46))
for k, t in enumerate((103.37, 111.34)):
    p = os.path.join(OUT, "s08s10_%d.png" % k); grab(t, p)
    im.paste(Image.open(p).resize((W, H)), (k * W, 46 + 36))
q = os.path.join(OUT, "S08S10.jpg"); im.save(q, quality=88)
print("SHEET " + q)

print("ALL-DONE -> " + OUT)
