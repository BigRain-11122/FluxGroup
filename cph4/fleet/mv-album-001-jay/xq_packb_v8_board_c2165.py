# -*- coding: ascii -*-
# Nine frame director board for PACK-B v8 (c2165).
import os
from PIL import Image, ImageDraw, ImageFont

B = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\assembly-packB"
OUT = os.path.join(B, "XQ-PACKB-v8-DIRECTOR-BOARD-c2165.jpg")
FONT = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"

FRAMES = ["2.5", "30.4", "54", "84", "119", "176", "218.5", "232", "236.5"]
LABEL = {"2.5": "2.5s title card", "30.4": "30.4s reference day sky",
         "54": "54.0s S2-10 (V7-1 fixed)", "84": "84.0s day ref",
         "119": "119.0s silhouette (V7-3 carry)",
         "176": "176.0s astronomy", "218.5": "218.5s tail plate",
         "232": "232.0s note (V7-2 fixed)", "236.5": "236.5s end credit"}

cols, rows = 3, 3
tw, th = 640, 366
pad = 10
label_h = 26
W = cols * tw + pad * (cols + 1)
H = rows * (th + label_h) + pad * (rows + 1)
board = Image.new("RGB", (W, H), (18, 18, 18))
d = ImageDraw.Draw(board)
f = ImageFont.truetype(FONT, 19)

for i, t in enumerate(FRAMES):
    r, c = divmod(i, cols)
    x = pad + c * (tw + pad)
    y = pad + r * (th + label_h + pad)
    im = Image.open(os.path.join(B, "v8g_%s.png" % t)).convert("RGB")
    im = im.resize((tw, th), Image.LANCZOS)
    board.paste(im, (x, y))
    d.text((x + 3, y + th + 3), LABEL[t], font=f, fill=(235, 230, 220))

board.save(OUT, quality=90)
print("WROTE", OUT, board.size)