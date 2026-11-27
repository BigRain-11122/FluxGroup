# -*- coding: utf-8 -*-
"""asset_board.py - contact-sheet board + inventory receipt for image-set audits.

DE-AI-SPEC B1/B2/B3: the anti-AI-face gate is a HUMAN gate (director's seat), but its
INPUT must be machine-made and reproducible: one board, deterministic selection, one
receipt listing what exists. No curation = no cherry-picking.

Usage:
  python asset_board.py --dir <images-or-children-dirs> --out board.jpg \
      --json receipt.json [--cols 4] [--limit 16] [--per-child 2]

Selection rule: if --dir holds subdirectories, take up to --per-child images from each
(sorted by name), else take the first --limit images. Tiles are letterboxed onto a
neutral dark grid with 8px gutters and a 28px caption strip (child/file name).

Exit: 0 board written | 3 BLOCKED (no images / no PIL) | 1 failure
"""
import argparse
import json
import os
import sys
import time

IMG = (".png", ".jpg", ".jpeg", ".webp")


def pick(dirpath, per_child, limit):
    ents = sorted(os.listdir(dirpath))
    out = []
    for e in ents:
        p = os.path.join(dirpath, e)
        if os.path.isfile(p) and e.lower().endswith(IMG):
            out.append((os.path.basename(dirpath), e, p))
        elif os.path.isdir(p):
            for f in sorted(os.listdir(p))[:per_child]:
                if f.lower().endswith(IMG):
                    out.append((e, f, os.path.join(p, f)))
    return out[:limit]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", default="")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--limit", type=int, default=16)
    ap.add_argument("--per-child", type=int, default=2)
    a = ap.parse_args(argv)

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "dir": a.dir,
           "spec": "DE-AI-SPEC-v1 B1/B2/B3", "verdict": "INIT"}

    def emit(verdict, rc, extra=None):
        rec.update({"verdict": verdict, "rc": rc})
        if extra:
            rec.update(extra)
        if a.json:
            os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
            json.dump(rec, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("BOARD %s %s" % (verdict, a.out))
        return rc

    if not os.path.isdir(a.dir):
        return emit("BLOCKED", 3, {"gaps": ["dir missing: %s" % a.dir]})
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return emit("BLOCKED", 3, {"gaps": ["PIL missing on this node"]})

    items = pick(a.dir, a.per_child, a.limit)
    if not items:
        return emit("BLOCKED", 3, {"gaps": ["no images under %s" % a.dir]})

    tile, gut, cap = 320, 8, 28
    rows = (len(items) + a.cols - 1) // a.cols
    W = a.cols * (tile + gut) + gut
    H = rows * (tile + cap + gut) + gut
    board = Image.new("RGB", (W, H), (24, 24, 26))
    draw = ImageDraw.Draw(board)
    try:
        font = ImageFont.truetype("consola.ttf", 14)
    except Exception:
        font = ImageFont.load_default()

    placed = []
    for i, (child, name, p) in enumerate(items):
        x = gut + (i % a.cols) * (tile + gut)
        y = gut + (i // a.cols) * (tile + cap + gut)
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((tile, tile))
            board.paste(im, (x + (tile - im.width) // 2, y + (tile - im.height) // 2))
            draw.text((x, y + tile + 4), ("%s/%s" % (child, name))[:44],
                      fill=(200, 200, 200), font=font)
            placed.append([child, name])
        except Exception:
            draw.rectangle([x, y, x + tile, y + tile], outline=(120, 30, 30))
            draw.text((x, y + 4), "unreadable", fill=(200, 80, 80), font=font)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    board.save(a.out, quality=88)
    return emit("PASS", 0, {"tiles": placed, "board": a.out,
                             "counts": {"picked": len(items)}})


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))