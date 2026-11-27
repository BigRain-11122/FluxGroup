# -*- coding: utf-8 -*-
"""C2200b: strip the rain-streak prior from the KN16 re-burn.

The C2200 re-burn fixed the defect it was fired for - the concentric rainbow
rings are gone (radial bump 4.04 -> 0.98, halo chroma 0.405 -> 0.131) - but it
paid with two new generator priors: thin near-vertical rain streaks across the
whole sky, and the same green glow blot under the cloud deck.

Neither needs another 30-minute generation. The streaks are thin, near vertical
and locally brighter than their neighbourhood, while everything the shot needs
(moon disc, cloud deck, stars, paper plane) is broad in the horizontal
direction. So a horizontal median gives the local baseline, and a pixel is only
treated as streak where its excess over that baseline is (a) positive and
(b) part of a run that stays bright down the column. Small bright points such
as stars fail the vertical-run test and survive.

Guarded the same way as the C2199 pass: the rebuild always starts from the
archived original, so re-running never stacks corrections.

Usage:
  python c2200_kn16_streaks.py --build
  python c2200_kn16_streaks.py --report
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
SRC = os.path.join(MEDIA, "clips-local-768", "KN_A-KN16.mp4")
BAK = os.path.join(MEDIA, "clip-archive-c2200", "KN_A-KN16-c2200-fresh.mp4")
TMP = os.path.join(MEDIA, "clip-archive-c2200", "KN_A-KN16-c2200b-tmp.mp4")
QC = os.path.join(MEDIA, "qc-frames-c2200")
BOARD = os.path.join(MEDIA, "qc-boards", "KN16-STREAK-C2200B.jpg")
VERDICT = os.path.join(MEDIA, "logs", "kn16-streak-c2200b.json")

W, H, FPS = 1344, 768, 24
HMED = 9          # horizontal median width: wider than any streak, narrower than a cloud lobe
THR = 3.0          # luminance excess that can belong to a streak
RUN = 25           # vertical run length used by the coherence test
RUN_FRAC = 0.5    # share of that run that must stay bright
GAIN = 1.0        # how much of the measured excess is removed
GREEN_CX, GREEN_CY, GREEN_R = 645.0, 640.0, 92.0


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit("cmd failed: %s\n%s" % (" ".join(cmd), res.stderr[-1500:]))
    return res


def hmedian(y, width):
    """Median along x with edge padding (no scipy dependency)."""
    pad = width // 2
    p = np.pad(y, ((0, 0), (pad, pad)), mode="edge")
    win = np.lib.stride_tricks.sliding_window_view(p, width, axis=1)
    return np.median(win, axis=2)


DS = 4  # mask is solved on a 4x downscale: streaks are far wider than that


def downsample(y):
    h, w = y.shape[0] // DS, y.shape[1] // DS
    return y[:h * DS, :w * DS].reshape(h, DS, w, DS).mean(axis=(1, 3))


def upsample_mask(m):
    im = Image.fromarray((m * 255.0).astype(np.uint8), mode="L")
    im = im.resize((W, H), Image.BILINEAR)
    return np.asarray(im).astype(np.float32) / 255.0


def vmean(m, rows):
    """Box mean along y with edge padding."""
    pad = rows // 2
    p = np.pad(m, ((pad, pad), (0, 0)), mode="edge")
    c = np.cumsum(p, axis=0)
    c = np.vstack([np.zeros((1, c.shape[1])), c])
    return (c[rows:] - c[:-rows]) / float(rows)


def streak_mask(y):
    base = hmedian(y, HMED)
    excess = y - base
    hit = (excess > THR).astype(np.float32)
    wide = np.maximum.reduce([np.roll(hit, k, axis=1) for k in (-1, 0, 1)])
    coh = vmean(wide, RUN)
    mask = np.clip((coh - RUN_FRAC) / 0.2, 0.0, 1.0)
    return mask, base


def process_frame(img):
    a = img.astype(np.float32)
    y = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    mask, baseline = streak_mask(y)
    excess = np.maximum(y - baseline, 0.0)
    cut = (mask * np.minimum(excess, 40.0) * GAIN)[:, :, None]
    out = a - cut
    # green blot under the deck: cap the green channel inside a feathered disc
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - GREEN_CX) ** 2 + (yy - GREEN_CY) ** 2)
    gm = np.clip(1.0 - d / GREEN_R, 0.0, 1.0) ** 1.5
    if gm.max() > 0:
        lum = 0.299 * out[:, :, 0] + 0.587 * out[:, :, 1] + 0.114 * out[:, :, 2]
        flat = np.stack([lum, lum, lum], axis=2)
        cap = np.maximum(np.maximum(out[:, :, 0], out[:, :, 2]) + 6.0, 0.0)
        out[:, :, 1] = np.minimum(out[:, :, 1], cap)
        blend = (0.6 * gm)[:, :, None]
        out = out * (1.0 - blend) + flat * blend
    return np.clip(out, 0, 255).astype(np.uint8)


def build():
    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if os.path.isfile(SRC) and not os.path.isfile(BAK):
        shutil.copy2(SRC, BAK)
        print("archived fresh re-burn -> %s" % os.path.basename(BAK))
    if not os.path.isfile(BAK):
        raise SystemExit("no source take to rebuild from")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", BAK,
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
                            "-i", "-", "-an", "-c:v", "libx264", "-crf", "16",
                            "-preset", "slow", "-pix_fmt", "yuv420p", "-r", str(FPS), TMP],
                           stdin=subprocess.PIPE)
    n = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        img = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3)
        enc.stdin.write(process_frame(img).tobytes())
        n += 1
        if n % 48 == 0:
            print("  %d frames" % n)
            sys.stdout.flush()
    enc.stdin.close()
    enc.wait()
    dec.wait()
    if enc.returncode != 0:
        raise SystemExit("encode failed")
    os.replace(TMP, SRC)
    print("rewrote %s frames=%d bytes=%d" % (os.path.basename(SRC), n, os.path.getsize(SRC)))
    return n


def frame(path, t):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path,
                        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True)
    if not p.stdout:
        raise SystemExit("frame extract failed: %s @%s" % (path, t))
    return np.asarray(Image.open(io.BytesIO(p.stdout)).convert("RGB")).astype(np.float32)


def streak_energy(path, t):
    a = frame(path, t)
    y = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    mask, base = streak_mask(y)
    excess = np.maximum(y - base, 0.0)
    strong = mask > 0.5
    return {
        "streak_px": int(strong.sum()),
        "excess_mean": round(float(excess[strong].mean()) if strong.any() else 0.0, 2),
        "yavg": round(float(y.mean()), 2),
    }


def report():
    os.makedirs(QC, exist_ok=True)
    os.makedirs(os.path.dirname(BOARD), exist_ok=True)
    rows, thumbs = [], []
    for t in (2.0, 6.0, 9.0, 12.0):
        before = os.path.join(QC, "streak_t%s_before.png" % t)
        after = os.path.join(QC, "streak_t%s_after.png" % t)
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", BAK, "-frames:v", "1", before])
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1", after])
        rows.append({"t": t, "before": streak_energy(BAK, t), "after": streak_energy(SRC, t)})
        thumbs += [before, after]
    cw = 336
    sized = [Image.open(p).resize((cw, int(cw * H / float(W)))) for p in thumbs]
    rh = sized[0].size[1]
    sheet = Image.new("RGB", (cw * 4, rh * 2), (10, 10, 12))
    for i, im in enumerate(sized):
        sheet.paste(im, ((i // 2) * cw, (i % 2) * rh))
    sheet.save(BOARD, quality=93)
    payload = {"batch": "C2200b",
               "method": "horizontal-median baseline + vertical-coherence mask (no generation)",
               "src": SRC, "archived_fresh_take": BAK, "rows": rows, "board": BOARD,
               "note": ("Top row = the fresh re-burn, bottom row = after the streak pass. "
                        "streak_px counts coherent vertical bright runs over the frame.")}
    with open(VERDICT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
    for r in rows:
        print("t=%s streak_px %d -> %d (excess %.1f -> %.1f) yavg %.1f -> %.1f"
              % (r["t"], r["before"]["streak_px"], r["after"]["streak_px"],
                 r["before"]["excess_mean"], r["after"]["excess_mean"],
                 r["before"]["yavg"], r["after"]["yavg"]))
    print("board=%s" % os.path.basename(BOARD))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.build or a.report:
        report()
    return 0


if __name__ == "__main__":
    sys.exit(main())