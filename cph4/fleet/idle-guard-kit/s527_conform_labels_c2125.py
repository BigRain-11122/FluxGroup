# -*- coding: ascii -*-
# s527_conform_labels_c2125.py - r1017 sec-8 item-6 version-management correction.
#
# The S7R evidence boards were drawn with A/B/C column headers while the batch
# receipt (xq-s7r-abatch-receipt-r1058.json) names the variants s7rA.png /
# s7rB.jpg / s7rC.png. This script regenerates the whole board family from the
# variant files already on disk (zero re-generation, zero GPU, no pixel of any
# variant is modified) with headers that match the receipt names, and fixes the
# "ORGINAL" spelling on the S5-26 comparison strip.
#
# Outputs (same paths as r1058, overwritten in place + mirrored to the tracked
# evidence folder cph4/fleet/mv-album-001-jay/):
#   abatch_s7r/xq-AB-S7R-BOARD-1-r1058.jpg
#   abatch_s7r/xq-AB-S7R-BOARD-2-r1058.jpg
#   abatch_s7r/xq-AB-S7R-COMPARE-S5-26-r1058.jpg
#   abatch_s7r/xq-AB-S7R-COMPARE-S0-03-r1058.jpg
#   abatch_s7r/xq-S7R-CONFORM-LABELS-c2125.json   (label map + sha256)
#
# PASS gate: CONFORM-LABELS-END ok=1 with the regenerated board list in the log
# tail and zero 'ORGINAL' occurrences in the new output names or labels.

import hashlib
import json
import os
import time

SRC = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch"
S7R = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch_s7r"
RECEIPT = os.path.join(S7R, "xq_s7r_abatch_receipt_r1058.json")
EVIDENCE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
XQ_ROOT = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
LOG_OUT = os.path.join(LOGDIR, "s527_conformlabels.out.txt")

# Column headers, conform to the receipt variant names.
H_ORIG = "orig %s"
H_A = "s7rA grain 0.14"
H_B = "s7rB shoulder+grain"
H_C = "s7rC esrgan4x+LANCZOS"

# Full-resolution strip headers (same three panels as r1058, corrected text).
STRIPS = [
    ("xq-AB-S7R-COMPARE-S5-26-r1058.jpg", "S5-26_s20185",
     ["S5-26_s20185 ORIGINAL (sky banding)", "s7rA grain-only (0.14)",
      "s7rC esrgan-x4 + LANCZOS down"],
     ["%s.png" % "S5-26_s20185", "S5-26_s20185_s7rA.png", "S5-26_s20185_s7rC.png"]),
    ("xq-AB-S7R-COMPARE-S0-03-r1058.jpg", "S0-03_s20027",
     ["S0-03_s20027 ORIGINAL (oily speculars)", "s7rA grain-only (0.14)",
      "s7rB highlight-shoulder + grain"],
     ["S0-03_s20027.png", "S0-03_s20027_s7rA.png", "S0-03_s20027_s7rB.jpg"]),
]

BAD_TOKEN = "ORGINAL"


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


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def labeled_cell(img, text):
    from PIL import Image, ImageDraw
    tw, th = 448, 256
    cell = img.resize((tw, th), Image.LANCZOS).convert("RGB")
    d = ImageDraw.Draw(cell)
    d.rectangle((0, 0, tw, 26), fill=(0, 0, 0))
    d.text((5, 5), text, fill=(255, 255, 255), font=font(15))
    return cell


def build_board(rows, path):
    from PIL import Image
    tw, th = 448, 256
    board = Image.new("RGB", (tw * 4, th * len(rows)), (24, 24, 24))
    for ri, row in enumerate(rows):
        for ci, (label, img) in enumerate(row):
            if img is None:
                continue
            board.paste(labeled_cell(img, label), (ci * tw, ri * th))
    board.save(path, quality=88)
    return os.path.getsize(path)


def build_strip(paths, labels, out):
    from PIL import Image, ImageDraw
    cells = []
    for p, lab in zip(paths, labels):
        img = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(img)
        w, h = img.size
        d.rectangle((0, 0, w, 30), fill=(0, 0, 0))
        d.text((8, 7), lab, fill=(255, 255, 255), font=font(19))
        cells.append(img)
    w, h = cells[0].size
    strip = Image.new("RGB", (w, h * len(cells)), (24, 24, 24))
    for i, c in enumerate(cells):
        strip.paste(c, (0, i * h))
    strip.save(out, quality=88)
    return os.path.getsize(out)


def mirror(paths):
    """Copy a rebuilt board to the tracked evidence folder."""
    import shutil
    made = []
    for p in paths:
        dst = os.path.join(EVIDENCE, os.path.basename(p))
        shutil.copyfile(p, dst)
        made.append(dst)
    return made


def main():
    from PIL import Image
    if os.path.exists(LOG_OUT):
        os.remove(LOG_OUT)
    logline("CONFORM-LABELS-START receipt=%s" % RECEIPT)

    with open(RECEIPT, encoding="utf-8") as f:
        receipt = json.load(f)
    frames = [fr["frame"] for fr in receipt["frames"]]
    logline("CONFORM-LABELS frames=%d" % len(frames))

    # 1) rebuild the two 9-row boards with receipt-conform headers
    rows_all = []
    missing = []
    for name in frames:
        paths = [os.path.join(SRC, name + ".png"),
                 os.path.join(S7R, name + "_s7rA.png"),
                 os.path.join(S7R, name + "_s7rB.jpg"),
                 os.path.join(S7R, name + "_s7rC.png")]
        for p in paths[:3]:
            if not os.path.exists(p):
                missing.append(p)
        if missing:
            raise SystemExit("MISSING source variant: %s" % missing[-1])
        imgs = []
        labels = [H_ORIG % name, H_A, H_B]
        for p in paths[:3]:
            imgs.append(Image.open(p))
        if os.path.exists(paths[3]):
            imgs.append(Image.open(paths[3]))
            labels.append(H_C)
        rows_all.append(list(zip(labels, imgs)))

    boards = []
    for bi, chunk in enumerate((rows_all[:9], rows_all[9:18]), 1):
        if not chunk:
            continue
        bpath = os.path.join(S7R, "xq-AB-S7R-BOARD-%d-r1058.jpg" % bi)
        size = build_board(chunk, bpath)
        boards.append((os.path.basename(bpath), size, bpath))
        logline("BOARD %s %dB" % (os.path.basename(bpath), size))

    # 2) rebuild the two full-resolution comparison strips (typo fix included)
    strips = []
    for fname, name, labels, rel in STRIPS:
        for lab in labels:
            if BAD_TOKEN in lab.upper():
                raise SystemExit("bad token in label: %s" % lab)
        paths = [os.path.join(SRC, rel[0])] + [os.path.join(S7R, r) for r in rel[1:]]
        for p in paths:
            if not os.path.exists(p):
                raise SystemExit("MISSING strip panel: %s" % p)
        out = os.path.join(S7R, fname)
        size = build_strip(paths, labels, out)
        strips.append((fname, size, out))
        logline("STRIP %s %dB" % (fname, size))

    # 3) mirror to the tracked evidence folder + place the S5-26 compare where
    #    the bank job expects it (media/MV/mv0001/xingqing root).
    all_boards = [b[2] for b in boards] + [s[2] for s in strips]
    mirrored = mirror(all_boards)
    root_copy = os.path.join(XQ_ROOT, "xq-AB-S7R-COMPARE-S5-26-r1058.jpg")
    import shutil
    shutil.copyfile(os.path.join(S7R, "xq-AB-S7R-COMPARE-S5-26-r1058.jpg"), root_copy)
    logline("MIRROR evidence=%d root_compare=%s" % (len(mirrored), os.path.basename(root_copy)))

    # 4) mechanical self-check: no bad token in any label or output name
    produced = [os.path.basename(p) for p in all_boards] + [os.path.basename(root_copy)]
    labels_all = [lab for _f, _n, ls, _r in STRIPS for lab in ls]
    labels_all += [H_A, H_B, H_C, "orig <frame>"]
    bad = [x for x in produced + labels_all if BAD_TOKEN in x.upper()]
    if bad:
        raise SystemExit("BAD TOKEN in outputs: %s" % bad)
    logline("TOKEN-CHECK ok=1 bad=%d" % len(bad))

    # 5) receipt: label map + sizes + sha256 for every rebuilt board
    out_rec = {
        "batch": "r1017 sec-8 item-6 version-management correction (S7R label conform)",
        "runner": "bm-c C2125",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "variants_source": "abatch_s7r (untouched - no variant pixel was rewritten)",
        "label_map": {"orig": "orig <frame>", "s7rA": H_A, "s7rB": H_B, "s7rC": H_C},
        "boards": [
            {"name": n, "bytes": s, "sha256": sha256(p),
             "mirror": os.path.join(EVIDENCE, n)}
            for n, s, p in boards + strips
        ],
        "receipt_conform": "headers now use s7rA/s7rB/s7rC exactly as named in "
                           "xq-s7r-abatch-receipt-r1058.json",
        "typo_fix": "S5-26 strip header reads ORIGINAL (was ORGINAL)",
        "zero_gpu": True,
    }
    rec_path = os.path.join(S7R, "xq-S7R-CONFORM-LABELS-c2125.json")
    with open(rec_path, "w", encoding="utf-8") as f:
        json.dump(out_rec, f, indent=1, ensure_ascii=False)
    shutil.copyfile(rec_path, os.path.join(EVIDENCE, os.path.basename(rec_path)))
    logline("RECEIPT %s %dB" % (os.path.basename(rec_path), os.path.getsize(rec_path)))

    # 6) PASS gate line: board list in the log tail
    listed = ", ".join("%s(%dB)" % (n, s) for n, s, _p in boards + strips)
    logline("BOARDS-REGENERATED %s" % listed)
    logline("CONFORM-LABELS-END ok=1 boards=%d strips=%d typo_fixed=1 token_bad=0"
            % (len(boards), len(strips)))


if __name__ == "__main__":
    main()