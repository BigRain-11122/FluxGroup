# -*- coding: ascii -*-
# s527_proxy_1080_c2129.py - flip-through proxies for the six S527 shipping
# plates (bank job s527-4k-proxy-1600).
#
# The delivery plates are 3840x2194 PNGs at 15MB each, slow to open one by one.
# This writes 1600px-wide JPEG proxies plus a 2x3 contact board, so review can
# page through the pack quickly. Source plates are read-only; pixels are only
# resampled into the proxy copies.
#
# PASS gate: PROXY-END ok=6 in the log tail + board >= 100KB.

import json
import math
import os
import time

XQ = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
DELIVERY = os.path.join(XQ, "delivery")
MANIFEST = os.path.join(DELIVERY, "MANIFEST-s527-4k.json")
OUTDIR = os.path.join(DELIVERY, "proxy")
EVIDENCE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
LOG_OUT = os.path.join(LOGDIR, "s527_proxy.out.txt")
WIDTH = 1600


def logline(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG_OUT, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")
    try:
        print(line)
    except Exception:
        pass


def font(size):
    from PIL import ImageFont
    for name in ("arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def main():
    from PIL import Image, ImageDraw
    os.makedirs(OUTDIR, exist_ok=True)
    if os.path.exists(LOG_OUT):
        os.remove(LOG_OUT)
    man = json.load(open(MANIFEST, encoding="utf-8-sig"))
    entries = man["entries"]
    logline("PROXY-START entries=%d width=%d" % (len(entries), WIDTH))

    made = []
    thumbs = []
    for e in entries:
        src = os.path.join(DELIVERY, e["file"])
        if not os.path.exists(src):
            raise SystemExit("MISSING plate: " + src)
        img = Image.open(src).convert("RGB")
        h = int(round(img.height * (WIDTH / float(img.width))))
        small = img.resize((WIDTH, h), Image.LANCZOS)
        out = os.path.join(OUTDIR, os.path.splitext(e["file"])[0] + "_proxy1600.jpg")
        small.save(out, quality=88)
        made.append({"file": os.path.basename(out), "bytes": os.path.getsize(out),
                     "size": [WIDTH, h], "source": e["file"]})
        logline("PROXY %s %dB %dx%d" % (os.path.basename(out), os.path.getsize(out), WIDTH, h))
        thumbs.append((os.path.basename(out), small))

    # 2 x 3 contact board
    tw, th = 800, int(round(800 * 2194 / 3840.0))
    cols, rows = 2, int(math.ceil(len(thumbs) / 2.0))
    bar = 26
    board = Image.new("RGB", (cols * tw, rows * (th + bar)), (20, 20, 22))
    d = ImageDraw.Draw(board)
    for i, (name, img) in enumerate(thumbs):
        c, r = i % cols, i // cols
        cell = img.resize((tw, th), Image.LANCZOS)
        board.paste(cell, (c * tw, r * (th + bar) + bar))
        d.rectangle((c * tw, r * (th + bar), c * tw + tw - 1, r * (th + bar) + bar - 1),
                    fill=(0, 0, 0))
        d.text((c * tw + 6, r * (th + bar) + 5), name, fill=(255, 255, 255), font=font(14))
    bpath = os.path.join(OUTDIR, "xq-S527-PROXY-CONTACT-c2129.jpg")
    board.save(bpath, quality=86)
    bsize = os.path.getsize(bpath)
    logline("BOARD %s %dB" % (os.path.basename(bpath), bsize))
    if bsize < 100000:
        raise SystemExit("board too small: %d" % bsize)

    rec = {
        "batch": "S527 delivery 1600px flip-through proxies",
        "runner": "bm-c C2129",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "proxy_dir": "media/MV/mv0001/xingqing/delivery/proxy",
        "width": WIDTH, "count": len(made),
        "proxies": made,
        "board": os.path.basename(bpath),
        "note": "source plates untouched; proxies are resampled review copies only, "
                "never delivery substrate",
    }
    rp = os.path.join(OUTDIR, "xq-S527-PROXY-c2129.json")
    json.dump(rec, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import shutil
    shutil.copyfile(bpath, os.path.join(EVIDENCE, os.path.basename(bpath)))
    logline("PROXY-END ok=%d" % len(made))


if __name__ == "__main__":
    main()