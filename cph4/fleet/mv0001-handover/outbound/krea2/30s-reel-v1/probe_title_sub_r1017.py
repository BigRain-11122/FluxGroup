# -*- coding: utf-8 -*-
# probe_title_sub_r1017.py — 副标三帧叠加探针：INT2 窗首/中/尾实帧 × 新 title_card.png → 竖排合成目检件
# 实帧取自 full_mv_v51_proxy.mp4（4.4/5.5/7.0s·INT2 窗 4.2-7.4s）；代理版=960×540，卡=1344×768，
# → 帧上采样 1344×768（LANCZOS）后叠全分辨率卡 = 终版 768P 出幅实况近似。
# 旧主标已烧入实帧，新卡主标几何与旧卡逐字相同（叠加即重合），副标为唯一新增元素 → 合成件≈新装配实况。
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
card = Image.open(os.path.join(HERE, "title_card.png"))
assert card.size == (1344, 768), card.size
FRAME_FILES = ["int2_probe_44.png", "int2_probe_550.png", "int2_probe_70.png"]
frames = []
for fn in FRAME_FILES:
    p = os.path.join(HERE, fn)
    if not os.path.isfile(p):
        raise SystemExit("MISSING %s (extract with ffmpeg first)" % p)
    base = Image.open(p).convert("RGBA")
    if base.size != (1344, 768):
        base = base.resize((1344, 768), Image.LANCZOS)
    frames.append(Image.alpha_composite(base, card))
sheet = Image.new("RGB", (1344, 768 * len(frames)), (0, 0, 0))
for i, f in enumerate(frames):
    sheet.paste(f.convert("RGB"), (0, i * 768))
out_path = os.path.join(HERE, "int2_sub_probe_3f.png")
sheet.save(out_path)
print("SAVED %s (frames: 4.4/5.5/7.0s, top->bottom)" % out_path)
