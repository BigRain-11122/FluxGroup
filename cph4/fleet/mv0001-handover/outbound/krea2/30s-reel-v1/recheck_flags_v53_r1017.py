# -*- coding: utf-8 -*-
"""V5.3 flag-recheck boards (CEO O-20261017-1330 full-cover review).
Resolves the FLAGS raised by the FXV53-FIX-RECHECK sheet read:
  cell3 SIL4 warm push  -> A) SIL4-COMPARE: v52(before) vs v53(after) @ 206.90/207.90/208.90
  cell4 R05 lift+lyric  -> B) R05-LIFT-LYRIC: v52 vs v53 @ 126.90(inter-line gap, lift delta)
                           + 127.60/128.60/129.60 (lyric window 当古文明只剩下难解的语言 127.04-132.38)
  cell7/8 S17 tail      -> C) S17-TAIL-ZOOM: sparkle-zone 2x crops @ 232.60-234.10
                           (envelope (0.70,0.90): fade-out 233.30->234.20 designed to ride
                            the global finale fade 232.00->234.00; board = evidence, not defect)
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF   = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
V52  = os.path.join(HERE, "full_mv_v52.mp4")
V53  = os.path.join(HERE, "full_mv_v53.mp4")
OUT  = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\fx_probe_v53"
W, H, TMAX = 1344, 768, 234.20

def fnt(sz):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

def grab(vf, t, path):
    t = max(0.0, min(TMAX, round(t * 24) / 24.0))
    r = subprocess.run([FF, "-y", "-ss", "%.3f" % t, "-i", vf, "-frames:v", "1", path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert r.returncode == 0 and os.path.isfile(path) and os.path.getsize(path) > 1000, \
        "grab fail %s @%.2f" % (os.path.basename(vf), t)
    return path

def grid_board(name, header, rows, col_caps):
    """rows=[(label, video)]; col_caps=[(t, caption)] -> full-res grid, one row per version."""
    cap, gap, head = 34, 8, 46
    im = Image.new("RGB", (W * len(col_caps), head + len(rows) * (cap + H) + (len(rows) - 1) * gap), (12, 12, 12))
    d = ImageDraw.Draw(im)
    d.text((12, 8), header, fill=(240, 226, 160), font=fnt(30))
    y = head
    for label, vf in rows:
        for ci, (t, sub) in enumerate(col_caps):
            x = ci * W
            d.rectangle([x, y, x + W, y + cap], fill=(16, 16, 16))
            d.text((x + 10, y + 6), "%s | %s" % (label, sub), fill=(240, 226, 160), font=fnt(22))
            p = os.path.join(OUT, "%s_%s_c%d.png" % (name, label, ci))
            im.paste(Image.open(grab(vf, t, p)).convert("RGB"), (x, y + cap))
        y += cap + H + gap
    q = os.path.join(OUT, name + ".jpg")
    im.save(q, quality=86)
    print("SHEET " + q)

# A) SIL4 before/after
grid_board("SIL4-COMPARE",
           "SIL4 warm push: V52(before) vs V53(after) @206.90/207.90/208.90 - cold-gray seam removed?",
           [("V52", V52), ("V53", V53)],
           [(206.90, "t=206.90"), (207.90, "t=207.90"), (208.90, "t=208.90")])

# B) R05 lift + lyric window
grid_board("R05-LIFT-LYRIC",
           "R05 segment lift: V52 vs V53 @126.90(inter-line gap) / 127.60/128.60/129.60 (lyric 127.04-132.38 on)",
           [("V52", V52), ("V53", V53)],
           [(126.90, "t=126.90 gap"), (127.60, "t=127.60 lyric-on"),
            (128.60, "t=128.60 lyric-on"), (129.60, "t=129.60 lyric-on")])

# C) S17 tail sparkle-zone 2x zoom
crop_box = (604, 322, 1344, 768)          # sparkle-biased zone: x>=0.45W, y>=0.42H
cw, ch = crop_box[2] - crop_box[0], crop_box[3] - crop_box[1]
sc = 2
tw, th = cw * sc, ch * sc
times_c = [232.60, 233.20, 233.80, 234.10]
im = Image.new("RGB", (tw * 2 + 8, 46 + (34 + th) * 2 + 8), (12, 12, 12))
d = ImageDraw.Draw(im)
d.text((12, 8), "S17 z04 tail: sparkle-zone 2x zoom (x604-1344 y322-768) - envelope fade-out 233.30->234.20 rides finale fade 232.00->234.00",
       fill=(240, 226, 160), font=fnt(26))
for k, t in enumerate(times_c):
    x = (k % 2) * (tw + 8)
    y = 46 + (k // 2) * (34 + th + 8)
    d.rectangle([x, y, x + tw, y + 34], fill=(16, 16, 16))
    d.text((x + 10, y + 6), "S17 tail @%.2f (2x zoom)" % t, fill=(240, 226, 160), font=fnt(22))
    p = os.path.join(OUT, "s17c_%d.png" % k)
    f = Image.open(grab(V53, t, p)).convert("RGB").crop(crop_box).resize((tw, th), Image.LANCZOS)
    im.paste(f, (x, y + 34))
q = os.path.join(OUT, "S17-TAIL-ZOOM.jpg")
im.save(q, quality=88)
print("SHEET " + q)
print("V53-FLAG-RECHECK-BOARDS-DONE -> " + OUT)
