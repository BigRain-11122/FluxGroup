# -*- coding: utf-8 -*-
# cert_d01_r2.py — D01v2_t2 持稳认证二法：均值归一化帧差（剔除火光呼吸增益）+ 五帧判读板
import os, subprocess, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF = r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
TK = os.path.join(HERE, "v511_takes")
os.chdir(HERE)
from PIL import Image, ImageChops, ImageDraw

def frame_at(t, tag):
    p = os.path.join(TK, "cert2_d01_%s.png" % tag)
    subprocess.run([FF, "-y", "-ss", "%.3f" % t, "-i", os.path.join(TK, "D01v2_t2.mp4"),
                    "-frames:v", "1", p], capture_output=True)
    return Image.open(p).convert("L")

def norm(img, box):
    r = img.crop(box)
    h = r.histogram(); n = sum(h)
    mean = sum(i * v for i, v in enumerate(h)) / n
    return r.point(lambda x: x - mean), mean

def ndiff(a, b):
    h = ImageChops.difference(a, b).histogram(); n = sum(h)
    return sum(i * v for i, v in enumerate(h)) / n

BOX = (int(1344 * 0.28), int(768 * 0.20), int(1344 * 0.68), int(768 * 0.75))
fa, fb, fc, fd, fe = (frame_at(t, g) for t, g in
                      ((0.50, "a"), (1.50, "b"), (2.20, "c"), (3.30, "d"), (4.40, "e")))
na, ma = norm(fa, BOX); nb, mb = norm(fb, BOX)
nc, mc = norm(fc, BOX); nd, md = norm(fd, BOX); ne, me = norm(fe, BOX)
dp = ndiff(na, nb); dh1 = ndiff(nc, nd); dh2 = ndiff(nd, ne)
print("crop means: press %.1f/%.1f  hold %.1f/%.1f/%.1f (firelight breathing visible)" % (ma, mb, mc, md, me))
print("normalized diff press(0.50->1.50) = %.2f" % dp)
print("normalized diff hold (2.20->3.30) = %.2f" % dh1)
print("normalized diff hold (3.30->4.40) = %.2f" % dh2)
ratio = (dh1 + dh2) / 2.0 / max(dp, 0.001)
print("normalized hold/press ratio = %.3f" % ratio)
print("CERT2-%s: %s" % ("PASS" if ratio < 0.45 else "WARN",
      "hold content 帧差显著低于压刻段（亮度增益剔除后结构冻结实锤）" if ratio < 0.45
      else "结构差仍偏高——以判读板人眼定谳"))

# 五帧判读板（全分辨率缩至 800 宽·标注 ABCDE）
W2, H2 = 800, 457
sheet = Image.new("RGB", (W2, H2 * 5 + 30 * 5), (16, 16, 16))
drw = ImageDraw.Draw(sheet)
for k, (img, tag, lbl) in enumerate(((fa, "a", "A press 0.50s"), (fb, "b", "B press 1.50s"),
                                     (fc, "c", "C hold 2.20s"), (fd, "d", "D hold 3.30s"),
                                     (fe, "e", "E hold 4.40s"))):
    y = k * (H2 + 30)
    im = img.convert("RGB").resize((W2, H2))
    sheet.paste(im, (0, y + 30))
    drw.text((8, y + 6), lbl, fill=(255, 220, 60))
board = os.path.join(TK, "CERT2-D01-HOLD-BOARD.jpg")
sheet.save(board, quality=88)
print("BOARD -> " + board)
