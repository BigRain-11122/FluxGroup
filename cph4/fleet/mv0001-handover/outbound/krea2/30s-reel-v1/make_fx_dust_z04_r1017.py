# -*- coding: utf-8 -*-
"""fx_dust_z04.png — denser/brighter gold-dust variant for the Z04 ending freeze (site 17).
S17 full-res verdict = WEAK at alpha .40 / 150 particles -> this plate: 240 particles
+14 bright 3px sparkles biased right/down (dark zones), same #E9C87A family."""
import os, random
from PIL import Image, ImageDraw, ImageFilter

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\fx_plates"
W, H = 1344, 768
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
rnd = random.Random(20261017)

def gold(base):
    r = min(255, base + rnd.randint(-14, 14))
    g = int(base * 0.82) + rnd.randint(-10, 10)
    b = int(base * 0.48) + rnd.randint(-8, 8)
    return (r, g, b)

# 240 base particles 1-2px, mild halo
for _ in range(240):
    x, y = rnd.uniform(0, W), rnd.uniform(0, H)
    s = rnd.choice([1, 1, 1, 2, 2])
    a = rnd.randint(90, 215)
    c = gold(rnd.randint(226, 242))
    d.ellipse([x - s, y - s, x + s, y + s], fill=c + (a,))
# 14 bright 3px sparkles biased to right/bottom dark zones (233.8+ readability)
for _ in range(14):
    x = rnd.uniform(W * 0.45, W)
    y = rnd.uniform(H * 0.42, H)
    c = (246, 219, 148)
    d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=c + (235,))
img = img.filter(ImageFilter.GaussianBlur(0.6))
out = os.path.join(HERE, "fx_dust_z04.png")
img.save(out)
print("SAVED %s (240 + 14 sparkles)" % out)
