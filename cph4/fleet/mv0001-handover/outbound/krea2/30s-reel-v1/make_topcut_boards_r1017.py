# -*- coding: utf-8 -*-
# make_topcut_boards_r1017.py — top-16 bare-cut candidates -> 2 review boards (8 pairs each)
# Quantitative pre-ranking from judge_bare_cuts_r1017.py; multimatal review per board next.
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FR = os.path.join(HERE, "v54_probe", "bare_cuts")
OUT = os.path.join(HERE, "v54_probe")

# (b_id, cut_ts) top-16 by score from judge_bare_cuts_r1017.py run
TOP = [(33,172.50),(25,138.56),(38,191.60),(24,126.32),(22,118.46),(17,87.74),(5,31.14),
       (36,184.08),(28,152.00),(37,190.00),(16,83.56),(27,147.84),(9,44.00),(40,200.80),
       (29,153.60),(26,144.56)]

from PIL import Image, ImageDraw, ImageFont
try: fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
except Exception: fnt = ImageFont.load_default()
cw, ch = 560, 320
per = 8
for half in (0, 1):
    grp = TOP[half*per:(half+1)*per]
    im = Image.new("RGB", (2*(cw+6), per*(ch+24)+40), (12,12,14))
    d = ImageDraw.Draw(im)
    d.text((8,6),"BARE-CUT jump review board %d: PRE | POST  (cut@t)" % (half+1), fill=(255,220,120), font=fnt)
    for r, (bid, t) in enumerate(grp):
        y = 34+r*(ch+24)
        d.text((4, y+2), "b%02d cut@%.2f" % (bid, t), fill=(255,255,160), font=fnt)
        for c, tag in ((0,"pre"),(1,"post")):
            p = os.path.join(FR, "b%02d_%s.jpg" % (bid, tag))
            if os.path.isfile(p):
                im.paste(Image.open(p).convert("RGB").resize((cw,ch)), (c*(cw+6), y+20))
    bp = os.path.join(OUT, "TOPCUT-BOARD-%d.jpg" % (half+1))
    im.save(bp, quality=88)
    print("BOARD:", bp)
