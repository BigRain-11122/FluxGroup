"""C2120: grain band A/B (r1017 sec-5 row-1 pre-condition 2 endpoints 0.05 / 0.10).

Fresh ESRGAN x4 pass on two representative grids (S5-27 s20193, S5-28 s20202),
then two grain levels each, plus a 2x2 compare board. Reuses the proven C2119
module so the upscale path stays identical.
"""
import importlib.util
import os
import sys

from PIL import Image, ImageDraw

KIT = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit"
spec = importlib.util.spec_from_file_location("c2119", os.path.join(KIT, "s527_4k_esrgan_c2119.py"))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

OUT_DIR = base.OUT_DIR
BOARD = os.path.join(base.REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-GRAIN-AB-BOARD-c2120.jpg")
GRIDS = [("S5-27", "S5-27_s20193_s7rC.png"), ("S5-28", "S5-28_s20202_s7rC.png")]
LEVELS = [0.05, 0.10]

os.makedirs(OUT_DIR, exist_ok=True)
shots = []
for shot, fname in GRIDS:
    files, secs = base.run_one(shot, fname)
    tmp = base.fetch_out(files)
    variants = []
    for g in LEVELS:
        base.GRAIN = g
        rec = "grain%.2f" % g
        im = Image.open(tmp).convert("RGB")
        w, h = im.size
        if w > base.TARGET_W:
            im = im.resize((base.TARGET_W, int(round(h * base.TARGET_W / float(w)))), Image.LANCZOS)
        # reuse the grain + save body of finish_frame without its hardcoded name
        import numpy as np
        arr = np.asarray(im).astype(np.int16)
        rng = np.random.default_rng(20210228)
        noise = rng.normal(0.0, 255 * g / 3.0, size=(arr.shape[0], arr.shape[1], 1))
        im2 = Image.fromarray(np.clip(arr + noise, 0, 255).astype("uint8"), "RGB")
        out = os.path.join(OUT_DIR, "%s_%s_4k_%s.png" % (shot, os.path.basename(fname).replace(".png", ""), rec))
        im2.save(out, "PNG", optimize=True)
        variants.append((g, out, im2))
        print("WROTE %s %.2f %dB" % (os.path.basename(out), g, os.path.getsize(out)), flush=True)
    os.remove(tmp)
    shots.append((shot, variants))

cw, ch, pad, lab = 768, 432, 12, 26
bw = 2 * cw + 3 * pad
bh = 2 * (2 * (ch + lab) + pad) + pad
board = Image.new("RGB", (bw, bh), (14, 14, 16))
d = ImageDraw.Draw(board)
for r, (shot, variants) in enumerate(shots):
    for c, (g, out, im) in enumerate(variants):
        x = pad + c * (cw + pad)
        y = pad + r * (2 * (ch + lab) + pad)
        w, h = im.size
        board.paste(im.crop((int(w * 0.5 - w * 0.281), int(h * 0.42 - h * 0.281),
                             int(w * 0.5 + w * 0.281), int(h * 0.42 + h * 0.281))).resize((cw, ch), Image.LANCZOS), (x, y))
        d.text((x + 4, y + 4), "%s grain %.2f" % (shot, g), fill=(255, 232, 170))
board.save(BOARD, "JPEG", quality=90)
print("GRAIN-AB-END ok=4 board=%s bytes=%d" % (os.path.basename(BOARD), os.path.getsize(BOARD)))