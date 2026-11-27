# -*- coding: utf-8 -*-
# probe_d08_src_r1017.py — D08 two-source texture comparison board
# LEFT col = media segments (current assembly source, 10-15), RIGHT col = cloudv2 archived
import os, subprocess, sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MEDIA = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\D08_world_flip.mp4"
ARCH  = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\cloudv2\_w2_archived\D08_world_flip.mp4"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\v54_probe"

def probe(f):
    r = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",f], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")

dm = float(probe(MEDIA)["format"]["duration"]); da = float(probe(ARCH)["format"]["duration"])
for tag, f, dur in (("MEDIA_SEG", MEDIA, dm), ("CLOUDV2_ARCH", ARCH, da)):
    st = probe(f).get("streams", [])
    res = next((("%dx%d" % (s.get("width",0), s.get("height",0))) for s in st if s.get("codec_type")=="video"), "?")
    print("%s  size=%.2fMB  dur=%.2fs  res=%s" % (tag, os.path.getsize(f)/1048576.0, dur, res))

def grab(f, t, path):
    subprocess.run(["ffmpeg","-y","-ss","%.2f"%t,"-i",f,"-frames:v","1","-q:v","3",path], capture_output=True)
    return os.path.isfile(path)

# 5 sample points: head / 25% / 50% / 75% / tail-0.4 (catch the glare-peak wireframe window)
pts = [0.6, 0.25, 0.5, 0.75, 0.93]
from PIL import Image, ImageDraw, ImageFont
cw, ch = 640, 366
im = Image.new("RGB", (2*(cw+6), len(pts)*(ch+24)+40), (12,12,14))
d = ImageDraw.Draw(im)
try: fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
except Exception: fnt = ImageFont.load_default()
d.text((8,6),"D08 source texture audit  L=media segments (assembly) | R=cloudv2 archived", fill=(255,220,120), font=fnt)
for r, frac in enumerate(pts):
    tm, ta = dm*frac, da*frac
    y = 34+r*(ch+24)
    for c, (f, t, tag) in enumerate(((MEDIA, tm, "media"), (ARCH, ta, "arch"))):
        p = os.path.join(OUT, "d08_%s_%d.jpg" % (tag, r))
        if grab(f, t, p):
            d.text((c*(cw+6)+4, y+2), "%s t=%.2fs (%d%%)" % (tag, t, int(frac*100)), fill=(200,200,210), font=fnt)
            im.paste(Image.open(p).convert("RGB").resize((cw,ch)), (c*(cw+6), y+20))
board = os.path.join(OUT, "D08-SRC-BOARD.jpg")
im.save(board, quality=90)
print("BOARD:", board)
