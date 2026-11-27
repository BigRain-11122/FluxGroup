"""Subtitle-band pseudo-text probe for i2v clips (zero GPU).

Why this exists
---------------
C2170 found that KN02 (768P, i2v from a clean signed keyframe) carries a
*static, caption-shaped glyph string* burned into the bottom-centre band for
frames 21..175.  The keyframe is clean, so the text is a generator prior, not a
frame defect.  The eye-based sample gate (C2167 verified KN04/KN21/KN22b at
480P) never drew a full-body frontal unit, so the class slipped through and the
30-unit 768P wave started.

This probe makes the class mechanically checkable per unit, at the earliest
station that can see it (the moment a clip lands).

Signal
------
A burned-in caption is (a) near-white, (b) confined to the subtitle band, and
(c) *identical across time* while the scene underneath moves.  So we compare
the binarised band mask of an early frame with a late frame: a real object that
happens to sit in the band changes shape, a burned caption does not.

Usage
-----
    python kn_pseudotext_probe.py --clip <path.mp4>
    python kn_pseudotext_probe.py --scan-dir <dir> [--out verdict.json]

Exit code 0 = every clip PASS/SKIP, 1 = at least one SUSPECT (fail-loud).
"""
import argparse
import glob
import json
import os
import subprocess
import sys

# Subtitle band as fractions of the frame: bottom-centre, where captions sit.
BAND_X0, BAND_X1 = 0.30, 0.70
BAND_Y0, BAND_Y1 = 0.845, 0.975

BRIGHT = 200          # near-white threshold on 0..255 luma
CORE = 215            # glyph stroke luma floor
CONTRAST = 60         # v minus 5x5 mean must exceed this
BRIGHT_MIN_PX = 60    # ignore single specular pixels
STATIC_IOU = 0.55     # mask overlap between early and late frame => burned-in
COVERAGE = 0.50       # fraction of sampled frames that must carry the band


def _band_raw(clip, w, h, n_frames):
    """Yield (index, bytes) of the cropped grey band for n_frames samples."""
    xs, xe = int(w * BAND_X0), int(w * BAND_X1)
    ys, ye = int(h * BAND_Y0), int(h * BAND_Y1)
    bw, bh = xe - xs, ye - ys
    vf = "crop=%d:%d:%d:%d,format=gray" % (bw, bh, xs, ys)
    cmd = ["ffmpeg", "-v", "error", "-i", clip, "-vf", vf,
           "-vsync", "0", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    size = bw * bh
    idx = 0
    try:
        while idx < n_frames:
            buf = proc.stdout.read(size)
            if not buf or len(buf) < size:
                break
            yield idx, buf, bw, bh
            idx += 1
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()


def _mask_stats(buf, bw, bh):
    """Isolate near-white glyph pixels by local contrast.

    A caption stroke is near-white *and* sits against a much darker local
    background (its drop outline), so v - mean(5x5) is large.  A white object
    (sneaker, lit floor, shirt) has bright neighbours, so the contrast term
    collapses.  Summed-area table keeps this O(pixels).
    """
    stride = bw + 1
    sat = [0] * ((bh + 1) * stride)
    for y in range(bh):
        row_sum = 0
        base = y * bw
        for x in range(bw):
            row_sum += buf[base + x]
            sat[(y + 1) * stride + (x + 1)] = sat[y * stride + (x + 1)] + row_sum
    r = 2
    mask = bytearray(bw * bh)
    hit = 0
    for y in range(bh):
        y0, y1 = max(0, y - r), min(bh, y + r + 1)
        base = y * bw
        for x in range(bw):
            v = buf[base + x]
            if v <= CORE:
                continue
            x0, x1 = max(0, x - r), min(bw, x + r + 1)
            area = (x1 - x0) * (y1 - y0)
            s = (sat[y1 * stride + x1] - sat[y0 * stride + x1]
                 - sat[y1 * stride + x0] + sat[y0 * stride + x0])
            if v - (s / float(area)) >= CONTRAST:
                mask[base + x] = 1
                hit += 1
    return hit, hit / float(bw * bh), mask


def _iou(mask_a, mask_b):
    inter = sum(1 for a, b in zip(mask_a, mask_b) if a and b)
    union = sum(1 for a, b in zip(mask_a, mask_b) if a or b)
    return (inter / float(union)) if union else 0.0


def probe_meta(clip):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,r_frame_rate:format=duration",
           "-of", "json", clip]
    d = json.loads(subprocess.check_output(cmd).decode("utf-8", "replace"))
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return (int(st["width"]), int(st["height"]),
            round(float(num) / float(den), 3), float(d["format"]["duration"]))


def _strip_span(mask, bw, bh, frac=0.90):
    """Row span (count of rows) that holds `frac` of the glyph pixels."""
    rows = [sum(mask[y * bw:(y + 1) * bw]) for y in range(bh)]
    total = sum(rows)
    if not total:
        return 0
    acc, first, last = 0, None, None
    for y, n in enumerate(rows):
        if not n:
            continue
        acc += n
        if first is None:
            first = y
        last = y
        if acc >= total * frac:
            break
    return last - first + 1


def scan(clip, step=4, keep_band_dir=None):
    """Return the pseudo-text verdict for one clip.

    A generated caption shows up as a sustained, narrow horizontal band of
    high-contrast near-white glyph pixels.  Two conditions must hold: a large
    share of sampled frames carry glyph pixels, and those pixels sit in a tight
    row span (a strip) rather than smeared across the band by a bright object
    or a lighting edge.  The strip may drift vertically while the camera pushes
    in, so a fixed position is not required.
    """
    w, h, fps, dur = probe_meta(clip)
    total = max(1, int(round(dur * fps)))
    picks = list(range(0, total, step))
    masks, ratios, brights, spans = {}, [], [], []
    bw = bh = 1
    for idx, buf, bw, bh in _band_raw(clip, w, h, total):
        if idx not in picks:
            continue
        bright, ratio, mask = _mask_stats(buf, bw, bh)
        ratios.append(ratio)
        brights.append(bright)
        if bright > BRIGHT_MIN_PX:
            masks[idx] = mask
            spans.append(_strip_span(mask, bw, bh))
        if keep_band_dir:
            os.makedirs(keep_band_dir, exist_ok=True)
            from PIL import Image
            Image.frombytes("L", (bw, bh), buf).save(
                os.path.join(keep_band_dir, "b%04d.png" % idx))
    carriers = sum(1 for b in brights if b > BRIGHT_MIN_PX)
    coverage = (carriers / float(len(brights))) if brights else 0.0
    narrow = (sum(1 for s in spans if s and s <= 0.32 * bh) / float(len(spans))) if spans else 0.0

    iou = 0.0
    if len(masks) >= 2:
        keys = sorted(masks)
        early = keys[len(keys) // 4]
        late = keys[-max(1, len(keys) // 4)]
        iou = _iou(masks[early], masks[late])

    suspect = coverage >= COVERAGE and narrow >= 0.5
    return {
        "clip": os.path.basename(clip),
        "path": clip,
        "res": "%dx%d" % (w, h),
        "fps": fps,
        "duration": round(dur, 3),
        "frames_sampled": len(picks),
        "bright_px_max": max(brights) if brights else 0,
        "peak_ratio": round(max(ratios) if ratios else 0.0, 5),
        "coverage": round(coverage, 3),
        "narrow_strip": round(narrow, 3),
        "static_iou": round(iou, 3),
        "verdict": "SUSPECT" if suspect else "PASS",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip")
    ap.add_argument("--scan-dir")
    ap.add_argument("--glob", default="*.mp4")
    ap.add_argument("--step", type=int, default=4, help="sample every N frames")
    ap.add_argument("--out")
    ap.add_argument("--keep-band-dir")
    a = ap.parse_args()

    if a.clip:
        clips = [a.clip]
    elif a.scan_dir:
        clips = sorted(glob.glob(os.path.join(a.scan_dir, a.glob)))
    else:
        ap.error("need --clip or --scan-dir")
    if not clips:
        print("NO_CLIPS")
        return 0

    rows = [scan(c, step=a.step, keep_band_dir=a.keep_band_dir) for c in clips]
    bad = [r for r in rows if r["verdict"] == "SUSPECT"]
    for r in rows:
        print("%-26s %-8s cov=%.2f narrow=%.2f iou=%.2f max=%d %s"
              % (r["clip"], r["verdict"], r["coverage"], r["narrow_strip"],
                 r["static_iou"], r["bright_px_max"], r["res"]))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump({"scanned": len(rows), "suspect": len(bad), "rows": rows},
                      f, ensure_ascii=False, indent=1)
        print("VERDICT ->", a.out)
    print("PSEUDOTEXT-END scanned=%d suspect=%d" % (len(rows), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())