# -*- coding: ascii -*-
# s7r_ratify_board_c2126.py - one-page ratification index for the conformed S7R
# board family (r1017 sec-8 item-6 follow-up, bank job s7r-conform-ratify-board).
#
# The four conformed boards are separate files; the director has to open four
# images to ratify the family. This script composes a single index sheet:
# two labelled thumbnails per row, each carrying its filename, size, sha256
# short id and the labels it proves (s7rA/s7rB/s7rC or ORIGINAL spelling).
#
# Zero GPU, reads the boards on disk only, touches no board bytes.
# PASS gate: RATIFY-BOARD-END ok=1 in the log tail + board >= 150KB.

import hashlib
import json
import os
import time

S7R = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch_s7r"
EVIDENCE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
LOG_OUT = os.path.join(LOGDIR, "s7r_ratifyboard.out.txt")
OUT = os.path.join(S7R, "xq-S7R-FAMILY-RATIFY-BOARD-c2126.jpg")

ITEMS = [
    ("xq-AB-S7R-BOARD-1-r1058.jpg", "9 rows: 4 cols on s7rC frames (S5-26/27/28), else 3"),
    ("xq-AB-S7R-BOARD-2-r1058.jpg", "9 rows x 3 cols: s7rA / s7rB headers (no s7rC)"),
    ("xq-AB-S7R-COMPARE-S5-26-r1058.jpg", "3 panels full-res: ORIGINAL spelling fixed"),
    ("xq-AB-S7R-COMPARE-S0-03-r1058.jpg", "3 panels full-res: s7rA / s7rB"),
]


def logline(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG_OUT, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")
    try:
        print(line)
    except Exception:
        pass


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


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
    if os.path.exists(LOG_OUT):
        os.remove(LOG_OUT)
    logline("RATIFY-BOARD-START items=%d" % len(ITEMS))

    cw, ch, pad, bar = 760, 560, 16, 52
    canvas_w = cw * 2 + pad * 3
    canvas_h = (ch + bar) * 2 + pad * 3 + 70
    board = Image.new("RGB", (canvas_w, canvas_h), (20, 20, 22))
    d = ImageDraw.Draw(board)
    d.text((pad, 16), "S7R board family - label conform ratification index (C2126)",
           fill=(255, 255, 255), font=font(22))

    recs = []
    for i, (name, note) in enumerate(ITEMS):
        src = os.path.join(S7R, name)
        if not os.path.exists(src):
            raise SystemExit("MISSING board: " + src)
        img = Image.open(src).convert("RGB")
        scale = min(cw / float(img.width), ch / float(img.height))
        thumb = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))),
                           Image.LANCZOS)
        col, row = i % 2, i // 2
        x = pad + col * (cw + pad)
        y = 70 + pad + row * (ch + bar + pad)
        board.paste(thumb, (x + (cw - thumb.width) // 2, y + (ch - thumb.height) // 2))
        d.rectangle((x, y, x + cw - 1, y + ch - 1), outline=(70, 70, 76))
        label = "%s  %dB  sha %s" % (name, os.path.getsize(src), sha16(src))
        d.rectangle((x, y + ch, x + cw, y + ch + bar), fill=(0, 0, 0))
        d.text((x + 8, y + ch + 8), label, fill=(255, 255, 255), font=font(15))
        d.text((x + 8, y + ch + 28), note, fill=(180, 200, 220), font=font(14))
        recs.append({"board": name, "bytes": os.path.getsize(src), "sha256": sha16(src),
                     "proves": note})

    board.save(OUT, quality=88)
    size = os.path.getsize(OUT)
    if size < 150000:
        raise SystemExit("board too small: %d" % size)

    for dst in (EVIDENCE,):
        import shutil
        shutil.copyfile(OUT, os.path.join(dst, os.path.basename(OUT)))

    rec = {
        "batch": "S7R board family ratification index (r1017 sec-8 item-6 follow-up)",
        "runner": "bm-c C2126",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "board": os.path.basename(OUT),
        "bytes": size,
        "items": recs,
        "label_map": {"orig": "orig <frame>", "s7rA": "s7rA grain 0.14",
                      "s7rB": "s7rB shoulder+grain", "s7rC": "s7rC esrgan4x+LANCZOS"},
        "zero_gpu": True,
    }
    rp = os.path.join(S7R, "xq-S7R-FAMILY-RATIFY-c2126.json")
    json.dump(rec, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import shutil
    shutil.copyfile(rp, os.path.join(EVIDENCE, os.path.basename(rp)))
    logline("BOARD %s %dB" % (os.path.basename(OUT), size))
    logline("RATIFY-BOARD-END ok=1 thumbnails=%d board_bytes=%d" % (len(recs), size))


if __name__ == "__main__":
    main()