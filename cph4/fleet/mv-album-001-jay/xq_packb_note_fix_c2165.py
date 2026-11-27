# -*- coding: ascii -*-
# xq_packb_note_fix_c2165.py - PACK-B v8 / V7-2 fix: the 226-232s note shot
# (clips-packA-768/XQ_F5-33c.mp4) carries AI pseudo-glyphs on the paper.
#
# Why: DIRECTOR-REVIEW-PACKB-V7-20261024.md item V7-2 - the strokes on the note
# are a continuous ring-scribble, no readable character, sitting mid-frame.
# Fix taken: option (1) of the review = lay real readable handwriting.
#
# How: the pseudo-glyphs left of the pencil tip are inpainted away with the
# surrounding paper (cv2 TELEA, paper is smooth so the fill is clean), then two
# real lines of Xingqing lyric are drawn in warm graphite, rotated onto the
# same baseline the fake strokes used. The last strokes stay untouched: they sit
# under the pencil tip and read as the stroke being written right now.
#
# The camera keeps pushing in over the shot (measured: the glyph cluster grows
# and travels), so the overlay is tracked per frame: the pre-mask stroke bbox is
# measured on every frame and drives the rotate/scale/translate of the text
# layer. Nothing is animated by hand.
#
# Output: media/mv-album-001-jay/clips-local-768/XQ_B-F5-33c-v8.mp4
#         (same 1344x768 / 24fps / frame count as the source; picture only)

import json
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
SRC = os.path.join(MEDIA, "clips-packA-768", "XQ_F5-33c.mp4")
DST = os.path.join(MEDIA, "clips-local-768", "XQ_B-F5-33c-v8.mp4")
WORK = os.path.join(MEDIA, "assembly-packB", "notefix-c2165")
FRAMES = os.path.join(WORK, "src")
FIXED = os.path.join(WORK, "fixed")
FONT = r"C:\Windows\Fonts\STXINGKA.TTF"
LOG = os.path.join(MEDIA, "log-packb-notefix-c2165.txt")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
W, H = 1344, 768

# the fake strokes live here; the right edge stops short of the pencil tip so
# the tip and the glyph being written under it are never inpainted
ROI_X0, ROI_X1 = 380, 658
ROI_Y0, ROI_Y1 = 285, 572
STROKE_ANGLE = 27.0

# real lyric line, two rows to match the two fake rows
LINES = [
    ["\u624b\u727d\u624b", "\u4e00\u6b65\u5169\u6b65"],
    ["\u4e09\u6b65\u56db\u6b65", "\u671b\u8457\u5929"],
]


def log(msg):
    stamp = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (stamp, msg)
    try:
        with open(LOG, "a", encoding="ascii", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def stroke_mask(gray):
    roi = gray[ROI_Y0:ROI_Y1, ROI_X0:ROI_X1]
    th = cv2.adaptiveThreshold(roi, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY_INV, 51, 16)
    m = np.zeros(gray.shape, np.uint8)
    m[ROI_Y0:ROI_Y1, ROI_X0:ROI_X1] = th
    # keep only stroke-sized blobs; drop paper specks and the ruled line stays
    # outside the ROI band by construction
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if a >= 15 and w <= 160 and h <= 160:
            keep[lab == i] = 255
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return keep


# a soft smudge of the old strokes survives the inpaint in the lower rows; the
# paper there is flat, so it is healed with a feathered donor patch instead of
# leaving a dark speck under the new lines
SPOT = (470, 505, 615, 585)
DONOR = (700, 500, 845, 580)


def heal_spot(img):
    x0, y0, x1, y1 = SPOT
    dx0, dy0, _, _ = DONOR
    w, h = x1 - x0, y1 - y0
    patch = img[y0:y1, x0:x1].astype(np.float32)
    donor = img[dy0:dy0 + h, dx0:dx0 + w].astype(np.float32)
    # match the shading so the donor does not sit as a brighter square
    donor = donor + (patch.reshape(-1, 3).mean(axis=0) -
                     donor.reshape(-1, 3).mean(axis=0))
    m = np.zeros((h, w), np.float32)
    cv2.ellipse(m, (w // 2, h // 2), (int(w * 0.46), int(h * 0.46)), 0, 0, 360,
                1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), 9.0)[:, :, None]
    out = img.copy()
    mixed = patch * (1.0 - m) + donor * m
    out[y0:y1, x0:x1] = np.clip(mixed, 0, 255).astype(np.uint8)
    return out


def render_text_layer():
    """Wide-tracked Xingkai lines on a transparent layer, already rotated."""
    font = ImageFont.truetype(FONT, 64)
    pad = 24
    gap = 18
    tracking = 6
    rows = []
    for parts in LINES:
        text = "  ".join(parts)
        width = 0
        for ch in text:
            width += font.getlength(ch) + tracking
        asc, desc = font.getmetrics()
        rows.append((text, width - tracking, asc + desc))
    bw = int(max(r[1] for r in rows))
    bh = int(sum(r[2] for r in rows) + gap * (len(rows) - 1))
    img = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    # graphite core: warm dark brown, slightly transparent so the paper shows
    d = ImageDraw.Draw(img)
    y = pad
    for text, _, h in rows:
        x = pad
        for ch in text:
            d.text((x, y), ch, font=font, fill=(46, 34, 26, 232))
            x += font.getlength(ch) + tracking
        y += h + gap
    # a faint pencil shadow, offset to the lower right, keeps it on the paper
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 70), (0, 0), img.split()[3])
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (3, 4))
    out.alpha_composite(img)
    # break the vector-crisp edge so it does not read as a sticker
    a = np.asarray(out, np.float32)
    rng = np.random.default_rng(2165)
    grain = rng.normal(0.0, 0.10, a.shape[:2]).astype(np.float32)
    a[:, :, :3] = np.clip(a[:, :, :3] + grain[:, :, None] * 26.0, 0, 255)
    edge = (a[:, :, 3] * np.clip(1.0 + grain, 0.80, 1.12)).clip(0, 255)
    a[:, :, 3] = edge
    out = out.rotate(STROKE_ANGLE, resample=Image.BICUBIC, expand=True)
    box = out.getbbox()
    return out.crop(box)


def main():
    if not os.path.exists(SRC):
        log("MISSING %s" % SRC)
        sys.exit(3)
    for p in (FRAMES, FIXED):
        if os.path.isdir(p):
            shutil.rmtree(p)
        os.makedirs(p)

    log("EXTRACT start")
    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-i", SRC, os.path.join(FRAMES, "f%04d.png")])
    names = sorted(os.listdir(FRAMES))
    log("EXTRACT frames=%d" % len(names))

    layer = render_text_layer()
    ls = layer.size
    tracked = []
    for name in names:
        src = os.path.join(FRAMES, name)
        img = cv2.imread(src)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        m = stroke_mask(gray)

        ys, xs = np.where(m > 0)
        if len(xs) < 400:
            # no note in this frame: copy through, nothing to track
            shutil.copyfile(src, os.path.join(FIXED, name))
            tracked.append({"frame": name, "masked": False})
            continue

        # the stroke cluster bbox drives the overlay transform: it lives on the
        # paper, so it carries the camera push-in for free
        bx0, bx1 = int(xs.min()), int(xs.max())
        by0, by1 = int(ys.min()), int(ys.max())
        target_w = float(bx1 - bx0)
        target_h = float(by1 - by0)

        # inpaint the fake strokes away
        m = cv2.dilate(m, np.ones((5, 5), np.uint8), iterations=3)
        fixed = cv2.inpaint(img, m, 7, cv2.INPAINT_TELEA)
        # inpaint flattens the paper, so put the grain back at the paper level
        paper = cv2.GaussianBlur(fixed, (0, 0), 1.2)
        noise = np.random.default_rng(int(name[1:5])).normal(0.0, 3.2,
                                                             fixed.shape[:2])
        paper = np.clip(paper.astype(np.float32) + noise[:, :, None], 0, 255)
        wall = m > 0
        fixed[wall] = paper.astype(np.uint8)[wall]
        fixed = heal_spot(fixed)

        # scale the text layer to the stroke cluster: fit inside the bbox
        scale = min(target_w / float(ls[0]), target_h / float(ls[1])) * 1.06
        scale = max(0.25, min(1.6, scale))
        nw, nh = max(1, int(ls[0] * scale)), max(1, int(ls[1] * scale))
        lay = layer.resize((nw, nh), Image.LANCZOS)

        # anchor: the fake rows start at the cluster's lower-left corner
        px = int(bx0 - 4)
        py = int(by0 - 4)
        base = Image.fromarray(cv2.cvtColor(fixed, cv2.COLOR_BGR2RGB)).convert("RGBA")
        base.alpha_composite(lay, (px, py))
        out = cv2.cvtColor(np.asarray(base.convert("RGB")), cv2.COLOR_RGB2BGR)
        cv2.imwrite(os.path.join(FIXED, name), out)
        tracked.append({"frame": name, "masked": True, "bbox": [bx0, by0, bx1, by1],
                        "scale": round(scale, 3), "at": [px, py]})

    log("FIXED frames=%d masked=%d" % (len(names), sum(1 for t in tracked if t["masked"])))

    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-framerate", "24", "-i", os.path.join(FIXED, "f%04d.png"),
                           "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                           "-pix_fmt", "yuv420p", "-an", DST])
    log("ENCODE %s" % DST)

    track_path = os.path.join(OUTDIR, "xq-PACKB-NOTEFIX-TRACK-c2165.json")
    with open(track_path, "w", encoding="ascii") as f:
        json.dump({"schema": "xq-packb-notefix/1", "batch": "C2165",
                   "src": os.path.relpath(SRC, REPO).replace("\\", "/"),
                   "dst": os.path.relpath(DST, REPO).replace("\\", "/"),
                   "lines": ["".join(p) for p in LINES],
                   "angle": STROKE_ANGLE,
                   "roi": [ROI_X0, ROI_Y0, ROI_X1, ROI_Y1],
                   "frames": len(names),
                   "tracked": tracked}, f, indent=1)
    log("TRACK %s" % track_path)


if __name__ == "__main__":
    main()