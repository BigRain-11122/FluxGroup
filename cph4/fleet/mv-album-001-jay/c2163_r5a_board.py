# c2163_r5a_board.py - R5 take verdict board for PACK-B S1-07 (batch C2163).
# Builds a labelled strip of native frames so the body read is reviewable, and
# writes the verdict JSON that the assembly step consumes.
import json
import os
from PIL import Image, ImageDraw, ImageFont

REPO = r"K:\Fluxgroup\FluxGroup"
EVID = os.path.join(REPO, "media", "mv-album-001-jay", "evidence-c2163")
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
STAMPS = (0.5, 1.0, 2.0, 4.0, 6.0, 7.5)
COLS = 3
CELL_W = 672
FONT = r"C:\Windows\Fonts\msyh.ttc"


def main():
    with open(os.path.join(EVID, "r5a-harvest.json"), encoding="utf-8") as f:
        meta = json.load(f)
    tiles = []
    for ts in STAMPS:
        p = os.path.join(EVID, "r5a-%04.2fs.png" % ts)
        im = Image.open(p).convert("RGB")
        ratio = CELL_W / im.size[0]
        im = im.resize((CELL_W, int(im.size[1] * ratio)), Image.LANCZOS)
        tiles.append((ts, im))
    cell_h = tiles[0][1].size[1]
    rows = (len(tiles) + COLS - 1) // COLS
    pad = 8
    head = 34
    board = Image.new("RGB", (COLS * CELL_W + pad * (COLS + 1),
                              head + rows * (cell_h + pad) + pad), (18, 18, 18))
    d = ImageDraw.Draw(board)
    try:
        font = ImageFont.truetype(FONT, 22)
    except Exception:
        font = ImageFont.load_default()
    d.text((pad, 6), "XQ PACK-B S1-07 R5 take r5a - native frames 1344x768 (batch C2163)",
           fill=(240, 240, 240), font=font)
    for i, (ts, im) in enumerate(tiles):
        r, c = divmod(i, COLS)
        x = pad + c * (CELL_W + pad)
        y = head + r * (cell_h + pad)
        board.paste(im, (x, y))
        d.text((x + 8, y + 6), "t=%.2fs" % ts, fill=(255, 235, 120), font=font)
    out = os.path.join(OUTDIR, "xq-S107-R5-TAKE-BOARD-c2163.jpg")
    board.save(out, quality=90)
    print("BOARD %s %dB" % (out, os.path.getsize(out)))

    verdict = {
        "batch": "C2163",
        "project": "XQ-PACK-B",
        "shot": "S1-07",
        "unit": "XQ_B-S1-07-r5a",
        "clip": os.path.relpath(meta["clip"], REPO).replace("\\", "/"),
        "probe": meta["probe"],
        "plate": "media/MV/mv0001/xingqing/xq-s107-r5-plate-c2162/S107_R5_plate_S1-07-r5-1_s924075.png",
        "seed": 457711,
        "body_read": "PASS",
        "body_read_note": (
            "Native-frame read at 0.5/1.0/2.0/4.0/6.0/7.5s: the left-half cloud is a plain "
            "wind-eroded cumulus band with no head, shoulders or limb contour; the couple, the "
            "chrome handlebar and the grass line hold across the window. The R4 defect "
            "(woman-shaped cloud at 1.0s) does not reproduce."
        ),
        "take_decision": "ACCEPT",
        "next": "assemble v6 with r5a in place of r4a, then director pass",
    }
    vp = os.path.join(OUTDIR, "R5-VERDICT-c2163.json")
    with open(vp, "w", encoding="utf-8") as f:
        json.dump(verdict, f, ensure_ascii=False, indent=1)
    print("VERDICT %s" % vp)


if __name__ == "__main__":
    main()