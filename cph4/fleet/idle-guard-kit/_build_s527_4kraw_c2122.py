"""Builds the C2122 pre-stow script by copy + anchored replacement (B1276: no transcription)."""
import io
import os

SRC = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit\s527_4k_esrgan_c2119.py"
DST = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit\s527_4kraw_c2122.py"

raw = io.open(SRC, encoding="utf-8", newline="").read()

REPL = [
    ('"""C2119: S5-26/27/28 six-grid 4K line (r1017 sec-8 item-1 / sec-5 row-1).',
     '"""C2122: six-grid 4K RAW (zero grain) plates + artifact address locate.\n\nr1017 sec-8 item-1 pre-condition 1 needs trustworthy addresses for the fine-line /\ndot-matrix cleanup, but locating them on grain plates is unusable (the just-added grain\nsits in the same high-frequency band; C2121 measured 130-357 false candidates per plate).\nThis leg re-upscales the same six source grids at 4K with NO grain, then scores isolated\nhigh-frequency blobs on those raw plates and emits coordinates + a 1:1 zoom board.\nNo pixel of any existing plate is modified.'),
    ('BOARD = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4K-BOARD-c2119.jpg")',
     'BOARD = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4KRAW-BOARD-c2122.jpg")'),
    ('RECEIPT = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4K-RECEIPT-c2119.json")',
     'RECEIPT = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4KRAW-RECEIPT-c2122.json")'),
    ('GRAIN = 0.07', 'GRAIN = 0.0'),
    ('up_name = "c2119_" + os.path.basename(src)', 'up_name = "c2122_" + os.path.basename(src)'),
    ('prefix = "c2119_4k_" + os.path.basename(src).replace(".png", "")',
     'prefix = "c2122_4kraw_" + os.path.basename(src).replace(".png", "")'),
    ('"client_id": "c2119"', '"client_id": "c2122"'),
    ('out = os.path.join(OUT_DIR, "%s_%s_4k.png" % (shot, os.path.basename(fname).replace(".png", "")))',
     'out = os.path.join(OUT_DIR, "%s_%s_4kraw.png" % (shot, os.path.basename(fname).replace(".png", "")))'),
    ('"batch": "c2119-s527-4k-esrgan"', '"batch": "c2122-s527-4kraw-locate"'),
    ('"spec": "r1017 sec-8 item-1 / sec-5 row-1 (six grids ESRGAN x4 + LANCZOS)"',
     '"spec": "r1017 sec-8 item-1 pre-condition 1 (raw ESRGAN 4K, zero grain, for trustworthy artifact addresses)"'),
    ('"pre_repair_note": "sec-5 pre-condition 1 (local line-hallucination / dot-matrix cleanup) NOT applied in this leg; leg-1 = upscale + grain only, 4K monitor recheck decides."',
     '"pre_repair_note": "zero grain by design: this leg exists so the artifact locator is not mixed with the film-grain band. Existing grained plates untouched."'),
    
    ('log("S527-4K-END ok=%d board=%s bytes=%d" % (len(rows), os.path.basename(BOARD), receipt["board_bytes"]))',
     'log("S527-4KRAW-BURN-END ok=%d board=%s bytes=%d" % (len(rows), os.path.basename(BOARD), receipt["board_bytes"]))'),
    ('log("S527-4K-END ok=0 error=%r" % (exc,))', 'log("S527-4KRAW-END ok=0 error=%r" % (exc,))'),
]

for old, new in REPL:
    if old == new:
        continue
    c = raw.count(old)
    if c != 1:
        raise SystemExit("ANCHOR count=%d for %r" % (c, old[:70]))
    raw = raw.replace(old, new)

LOCATE = '''

# ---------------------------------------------------------------- artifact locate
# Appended by _build_s527_4kraw_c2122.py: scores isolated high-frequency blobs on the
# raw (zero grain) plates. Same scorer as C2121 but on a grain-free substrate.
LOCATE_BOARD = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-RAW-ARTIFACT-LOCATE-c2122.jpg")
LOCATE_RECEIPT = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-RAW-ARTIFACT-LOCATE-c2122.json")


def locate_main():
    import glob
    import numpy as np
    from scipy import ndimage
    plates = sorted(glob.glob(os.path.join(OUT_DIR, "*_4kraw.png")))
    rows = []
    tiles = []
    for p in plates:
        im = Image.open(p).convert("RGB")
        L = np.asarray(im.convert("L"), dtype=np.float32)
        hp = L - ndimage.median_filter(L, size=5)
        mag = np.abs(hp)
        wide = ndimage.uniform_filter(mag, size=25) + 1e-3
        score = mag / wide
        mask = (score > 6.0) & (mag > 8.0)
        lbl, n = ndimage.label(mask)
        cands = []
        if n:
            objs = ndimage.find_objects(lbl)
            sizes = np.bincount(lbl.ravel())[1:]
            for i, sl in enumerate(objs):
                if sl is None:
                    continue
                h = sl[0].stop - sl[0].start
                w = sl[1].stop - sl[1].start
                if not (3 <= h <= 40 and 3 <= w <= 40):
                    continue
                if sizes[i] > 400:
                    continue
                cands.append({"x": int((sl[1].start + sl[1].stop) // 2),
                              "y": int((sl[0].start + sl[0].stop) // 2),
                              "w": int(w), "h": int(h), "px": int(sizes[i]),
                              "score": round(float(score[sl].max()), 2)})
        cands.sort(key=lambda c: -c["score"])
        rows.append({"plate": os.path.basename(p), "size": list(im.size),
                     "candidates": len(cands), "top": cands[:8]})
        for c in cands[:3]:
            pad = 80
            x0, y0 = max(0, c["x"] - pad), max(0, c["y"] - pad)
            x1, y1 = min(im.width, c["x"] + pad), min(im.height, c["y"] + pad)
            crop = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.NEAREST)
            d = ImageDraw.Draw(crop)
            cx, cy = (c["x"] - x0) * 2, (c["y"] - y0) * 2
            d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], outline=(255, 60, 60), width=3)
            d.text((4, 4), "%s sc%.1f" % (os.path.basename(p).split("_s")[1][:8], c["score"]),
                   fill=(255, 230, 150))
            tiles.append(crop)
    bw = 0
    if tiles:
        cw = max(t.width for t in tiles)
        chh = max(t.height for t in tiles)
        cols = 3
        rws_ = (len(tiles) + cols - 1) // cols
        bd = Image.new("RGB", (cw * cols, chh * rws_), (10, 10, 10))
        for i, t in enumerate(tiles):
            bd.paste(t, ((i % cols) * cw, (i // cols) * chh))
        bd.save(LOCATE_BOARD, "JPEG", quality=91)
        bw = os.path.getsize(LOCATE_BOARD)
    rec = {"batch": "c2122-s527-raw-artifact-locate",
           "spec": "r1017 sec-8 item-1 pre-condition 1 (locate on zero-grain 4K, zero pixel change)",
           "plates": rows, "board": os.path.basename(LOCATE_BOARD), "board_bytes": bw,
           "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(LOCATE_RECEIPT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("RAW-LOCATE-END ok=%d board_bytes=%d candidates=%d"
          % (len(rows), bw, sum(r["candidates"] for r in rows)), flush=True)


if __name__ == "__main__" and os.environ.get("C2122_LOCATE_ONLY") != "1":
    pass

try:
    locate_main()
    print("S527-4KRAW-END ok=%d" % len([1]), flush=True)
except Exception as exc:
    print("S527-4KRAW-END ok=0 error=%r" % (exc,), flush=True)
    raise
'''

raw = raw.rstrip("\n") + "\n" + LOCATE.lstrip("\n")
io.open(DST, "w", encoding="utf-8", newline="").write(raw)
print("WROTE", DST, os.path.getsize(DST))