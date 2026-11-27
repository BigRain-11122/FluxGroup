"""C2123 harvest: CEO-viewable shipping contact sheet + small anomaly crop board.

Inputs : xq-S527-STARFILTER-GRAIN-c2123.json (receipt) and the six grain-0.10 4K plates.
Outputs: xq-S527-SHIPPING-CONTACT-c2123.jpg (6-up contact sheet, readable size)
         xq-S527-ANOM-CROPS-c2123.jpg    (320px tiles, small enough for a multimodal eye read)
No plate pixels are modified.
"""
import glob
import json
import os

from PIL import Image, ImageDraw

REPO = r"K:\Fluxgroup\FluxGroup"
OUT_DIR = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "s7r-4k")
RECEIPT = os.path.join(OUT_DIR, "..", "xq-S527-STARFILTER-GRAIN-c2123.json")
CONTACT = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-SHIPPING-CONTACT-c2123.jpg")
CROPS = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-ANOM-CROPS-c2123.jpg")


def contact_sheet(plates):
    cols, cw = 2, 900
    thumbs = []
    for p in plates:
        im = Image.open(p).convert("RGB")
        ch = max(1, int(im.height * cw / im.width))
        thumbs.append((os.path.basename(p), im.resize((cw, ch), Image.LANCZOS)))
    ch = max(t[1].height for t in thumbs)
    rows = (len(thumbs) + cols - 1) // cols
    head = 34
    bd = Image.new("RGB", (cw * cols, (ch + head) * rows), (8, 8, 10))
    d = ImageDraw.Draw(bd)
    for i, (name, t) in enumerate(thumbs):
        x, y = (i % cols) * cw, (i // cols) * (ch + head)
        bd.paste(t, (x, y + head))
        d.text((x + 8, y + 10), name.replace("_4k_grain010.png", "") + "  grain 0.10  4K", fill=(235, 220, 160))
    bd.save(CONTACT, "JPEG", quality=88)
    return os.path.getsize(CONTACT)


def anomaly_crops(rec, plates):
    tiles = []
    for s in rec["plates"]:
        p = [q for q in plates if os.path.basename(q) == s["plate"]]
        if not p:
            continue
        im = Image.open(p[0]).convert("RGB")
        # prefer non-edge anomalies first, then edge ones, cap 2 per plate
        an = sorted(s["top_anomalies"], key=lambda a: (a["edge"], -a["score"]))[:2]
        for a in an:
            pad = 160
            x0, y0 = max(0, a["x"] - pad), max(0, a["y"] - pad)
            crop = im.crop((x0, y0, min(im.width, a["x"] + pad), min(im.height, a["y"] + pad)))
            crop = crop.resize((320, 320), Image.LANCZOS)
            d = ImageDraw.Draw(crop)
            d.ellipse([100, 100, 220, 220], outline=(255, 60, 60), width=3)
            d.text((4, 4), "%s anom sc%.1f bg%d ct%d%s" % (
                s["plate"].split("_s")[1][:6], a["score"], a["bg"], a["contrast"], " EDGE" if a["edge"] else ""),
                fill=(255, 230, 150))
            tiles.append(crop)
    if not tiles:
        return 0
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    bd = Image.new("RGB", (320 * cols, 320 * rows), (8, 8, 10))
    for i, t in enumerate(tiles):
        bd.paste(t, ((i % cols) * 320, (i // cols) * 320))
    bd.save(CROPS, "JPEG", quality=90)
    return os.path.getsize(CROPS)


def main():
    rec = json.load(open(RECEIPT, encoding="utf-8"))
    plates = sorted(glob.glob(os.path.join(OUT_DIR, "*_4k_grain010.png")))
    cb = contact_sheet(plates)
    ab = anomaly_crops(rec, plates)
    print("SHIPPING-CONTACT-END plates=%d contact_bytes=%d crops_bytes=%d anomalies=%d"
          % (len(plates), cb, ab, rec["total_anomalies"]), flush=True)


if __name__ == "__main__":
    main()