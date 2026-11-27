# -*- coding: utf-8 -*-
# make_fx_plates_r1017.py — V5.2 特效伴切层板材生成（CEO 令 O-20261017-1300·R-20261017-mv-fx-transitions-01 §二）
# 六板全 1344×768 原生·世界原生物（自片源帧采样+PIL 程序化）·年代律合规面·零新增生成。
import os, subprocess, random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
W, H = 1344, 768
HERE = os.path.dirname(os.path.abspath(__file__))
V5REDO = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo"
D51 = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51"
OUT = os.path.join(HERE, "fx_plates")
os.makedirs(OUT, exist_ok=True)
random.seed(1017)

def grab(src, t, out_png):
    subprocess.run([FF, "-y", "-ss", "%.2f" % t, "-i", src, "-frames:v", "1", "-update", "1", out_png],
                   capture_output=True, check=True)
    return Image.open(out_png).convert("RGBA")

def cover(im):
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return im

# ① 火光闪帧板：S1 段件（装配切制件=成片观感材质）提亮+微糊+暖饱和
f1 = cover(grab(os.path.join(D51, "v51_S1_fire_wake.mp4"), 2.00, os.path.join(OUT, "_s1.png")))
f1 = ImageEnhance.Brightness(f1).enhance(1.55)
f1 = ImageEnhance.Color(f1).enhance(1.35)
f1 = f1.filter(ImageFilter.GaussianBlur(2.2))
f1.save(os.path.join(OUT, "fx_flash.png"))
print("fx_flash.png  <- S1 fire frame brightened")

# ② 烟雾漫过板：B04 段件帧压暗+强糊
f2 = cover(grab(os.path.join(D51, "v51_B04_embers.mp4"), 2.50, os.path.join(OUT, "_b4.png")))
f2 = ImageEnhance.Brightness(f2).enhance(0.62)
f2 = f2.filter(ImageFilter.GaussianBlur(14))
f2.save(os.path.join(OUT, "fx_smoke.png"))
print("fx_smoke.png  <- B04 embers frame blurred dark")

# ③ 楔形刻痕擦除带：C04 段件帧中部 840px 条带·对比强化+90px 边缘羽化·余域透明
f3 = cover(grab(os.path.join(D51, "v51_C04_words_alive.mp4"), 2.00, os.path.join(OUT, "_c04.png")))
f3 = ImageEnhance.Contrast(f3).enhance(1.30)
f3 = ImageEnhance.Color(f3).enhance(1.10)
band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
x0 = (W - 840) // 2
band.paste(f3.crop((x0, 0, x0 + 840, H)), (x0, 0))
FE = 90
grad = Image.new("L", (840, 1))
gp = grad.load()
for x in range(840):
    v = 255
    if x < FE:
        v = int(255 * x / FE)
    elif x > 840 - FE:
        v = int(255 * (840 - x) / FE)
    gp[x, 0] = v
feather = grad.resize((840, H))
ba = band.getchannel("A")
region = ImageChops.multiply(ba.crop((x0, 0, x0 + 840, H)), feather)
ba.paste(region, (x0, 0))
band.putalpha(ba)
band.save(os.path.join(OUT, "fx_band.png"))
print("fx_band.png   <- C04 cuneiform strip feathered")

# ④ 暖橙漏光板：右缘程序化渐层（f^1.7）+streak 噪纹
leak = Image.new("RGBA", (W, H), (0, 0, 0, 0))
lp = leak.load()
for x in range(W - 300, W):
    f = (x - (W - 300)) / 300.0
    base = int(235 * (f ** 1.7))
    for y in range(H):
        lp[x, y] = (255, 152, 58, int(base * (0.55 + 0.45 * random.random())))
leak = leak.filter(ImageFilter.GaussianBlur(2.5))
leak.save(os.path.join(OUT, "fx_leak.png"))
print("fx_leak.png   <- procedural warm edge leak")

# ⑤ 金尘板：150 粒 #E9C87A 族金点+大颗微光晕
dust = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(dust)
GOLDS = [(233, 200, 122), (240, 214, 150), (210, 175, 95)]
for _ in range(150):
    x, y = random.randint(0, W - 1), random.randint(0, H - 1)
    r = random.choice([1, 1, 1, 2, 2, 3])
    a = random.randint(90, 220)
    d.ellipse([x - r, y - r, x + r, y + r], fill=random.choice(GOLDS) + (a,))
for _ in range(14):  # 大颗微光晕
    x, y = random.randint(0, W - 1), random.randint(0, H - 1)
    r = random.randint(4, 7)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(233, 200, 122, random.randint(45, 80)))
dust = dust.filter(ImageFilter.GaussianBlur(0.6))
dust.save(os.path.join(OUT, "fx_dust.png"))
print("fx_dust.png   <- procedural gold specks")

# ⑥ 回环定格板：B04 块件末帧（v51 build 落件后提取）
b4block = os.path.join(D51, "v51_B04_embers.mp4")
assert os.path.isfile(b4block), "B04 block missing at %s (run v51 final build first)" % b4block
subprocess.run([FF, "-y", "-sseof", "-0.05", "-i", b4block, "-frames:v", "1", "-update", "1",
                os.path.join(OUT, "_b4tail.png")], capture_output=True, check=True)
echo = cover(Image.open(os.path.join(OUT, "_b4tail.png")).convert("RGBA"))
echo.save(os.path.join(OUT, "fx_echo.png"))
print("fx_echo.png   <- B04 block tail frame")

# 临时件清扫
for t in ("_s1.png", "_b4.png", "_c04.png", "_b4tail.png"):
    p = os.path.join(OUT, t)
    if os.path.isfile(p):
        os.remove(p)
print("PLATES-DONE -> " + OUT)
