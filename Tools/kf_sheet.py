# -*- coding: utf-8 -*-
"""kf_sheet.py - contact sheets for a KF (key-frame) still batch.

Why: mv_shot_sheets.py only reads VIDEO. KF batches (30 stills per pack) had no
review surface, so nobody could walk the pack shot by shot (CEO 10-23: "一个个镜头过").

Pure local, stdlib + PIL, no network.

Usage:
  python Tools/kf_sheet.py <img_dir> [--out DIR] [--per-sheet 12] [--cols 4]
                           [--thumb 480] [--prompts prompts.json]

Output: <out>/sheet_01.png ... + <out>/index.json (id -> sheet, cell, source, note)
"""
import argparse
import glob
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

EXTS = (".png", ".jpg", ".jpeg", ".webp")


def load_notes(prompts_path):
    """Map frame id (stem) -> short note from a prompts.json, if present."""
    if not prompts_path or not os.path.exists(prompts_path):
        return {}
    try:
        with io.open(prompts_path, encoding="utf-8-sig") as f:
            rows = json.load(f)
    except Exception:
        return {}
    notes = {}
    for r in rows if isinstance(rows, list) else []:
        fid = str(r.get("id") or "").strip()
        if fid:
            notes[fid] = str(r.get("note") or r.get("title") or "")[:60]
    return notes


def fit_text(draw, text, f, max_w):
    """Trim text to the cell width so labels never bleed into the next cell."""
    if not text:
        return ""
    if draw.textlength(text, font=f) <= max_w:
        return text
    ell = "..."
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if draw.textlength(text[:mid] + ell, font=f) <= max_w:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ell


def font(size):
    for name in ("msyh.ttc", "msyhbd.ttc", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("img_dir")
    ap.add_argument("--out", default="")
    ap.add_argument("--per-sheet", type=int, default=12)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--thumb", type=int, default=480)
    ap.add_argument("--prompts", default="")
    a = ap.parse_args(argv)

    files = sorted(
        p for p in glob.glob(os.path.join(a.img_dir, "*"))
        if p.lower().endswith(EXTS)
    )
    if not files:
        print("KF-SHEET FAIL: no images in %s" % a.img_dir)
        return 1

    out = a.out or os.path.join(a.img_dir, "_sheets")
    os.makedirs(out, exist_ok=True)
    notes = load_notes(a.prompts)

    cols = max(1, a.cols)
    per = max(1, a.per_sheet)
    rows = (per + cols - 1) // cols
    pad = 8
    label_h = 26
    tw = a.thumb
    # uniform cell height; keep aspect by fitting inside the cell
    th = int(round(tw * 9 / 16.0))
    cell_w, cell_h = tw + pad * 2, th + label_h + pad * 2
    f = font(18)

    index = []
    for s in range(0, len(files), per):
        chunk = files[s:s + per]
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (18, 18, 20))
        draw = ImageDraw.Draw(sheet)
        for i, path in enumerate(chunk):
            r, c = divmod(i, cols)
            x0, y0 = c * cell_w + pad, r * cell_h + pad
            try:
                im = Image.open(path).convert("RGB")
            except Exception as e:
                draw.text((x0 + 4, y0 + 4), "UNREADABLE", fill=(255, 90, 90), font=f)
                index.append({"id": os.path.splitext(os.path.basename(path))[0],
                              "source": path, "error": str(e)})
                continue
            im.thumbnail((tw, th))
            ox = x0 + (tw - im.width) // 2
            oy = y0 + (th - im.height) // 2
            sheet.paste(im, (ox, oy))
            stem = os.path.splitext(os.path.basename(path))[0]
            cap = stem
            note = notes.get(stem)
            if note:
                cap = "%s  %s" % (stem, note)
            draw.text((x0, y0 + th + 4), fit_text(draw, cap, f, tw),
                      fill=(235, 235, 235), font=f)
            index.append({"id": stem, "source": path,
                          "sheet": "sheet_%02d.png" % (s // per + 1),
                          "cell": [r, c], "note": note or ""})
        name = "sheet_%02d.png" % (s // per + 1)
        sheet.save(os.path.join(out, name))

    with io.open(os.path.join(out, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"dir": a.img_dir, "count": len(files),
                   "sheets": (len(files) + per - 1) // per,
                   "per_sheet": per, "cols": cols, "items": index},
                  fh, ensure_ascii=False, indent=1)
    print("KF-SHEET OK frames=%d sheets=%d out=%s" % (
        len(files), (len(files) + per - 1) // per, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())