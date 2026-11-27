# -*- coding: utf-8 -*-
# make_fx_echo2_r1017.py — fx_echo2 板：E01b 段件末帧定格残像（V5.4.2 转场顶级令·CEO 2026-10-17 夜）
# 语义=191.60 XF（E01b 沙埋→E01c 初凿）「同一石碑跨千年」残像叠印——本片第二签名时刻
# 工艺承 make_fx_plates_r1017.py §⑥（B04 echo 同法·-sseof 尾取+cover 封装·世界原生物零外来件）
import os, subprocess
from PIL import Image

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
D51 = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51"
OUT = os.path.join(HERE, "fx_plates")

src = os.path.join(D51, "v51_E01b_sand.mp4")
assert os.path.isfile(src), "E01b segment missing: %s" % src
tmp = os.path.join(OUT, "_e01btail.png")
subprocess.run([FF, "-y", "-sseof", "-0.05", "-i", src, "-frames:v", "1", "-update", "1", tmp],
               capture_output=True, check=True)
im = Image.open(tmp).convert("RGBA")
if im.size != (W, H):
    im = im.resize((W, H), Image.LANCZOS)
im.save(os.path.join(OUT, "fx_echo2.png"))
os.remove(tmp)
print("fx_echo2.png  <- E01b segment tail frame (sand-buried stele ghost)")
