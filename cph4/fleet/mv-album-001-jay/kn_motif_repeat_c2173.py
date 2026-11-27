# kn_motif_repeat_c2173.py - motif-level repeat gate for the KN wave (zero GPU).
# Why this exists: C2172 cleared repetition with framemd5 (0 duplicate frames) and grey MAD
# (0 same-picture pairs), and C2173's dhash probe cleared composition (1 pair). All three are
# true and all three miss the thing the board shows: KN06/07/10/11/12/13 are six burns of
# "one large white paper plane over a night city". A viewer never compares pixels - they see
# the same subject filling the same frame six times inside 41 seconds.
# Measure used here: the largest single near-white, low-saturation blob (the plane) as a
# fraction of the frame plus its bounding-box share. City lights are many small blobs, so a
# big contiguous white slab is what separates "the plane is the subject" from "the plane is furniture".
# A run of two or more plane-dominant units inside WINDOW_S of cut time is a SUSPECT run.
import glob
import io
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image

ALBUM = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
CLIPS = os.path.join(ALBUM, "clips-local-768")
EVID = os.path.join(ALBUM, "evidence-c2173")
OUTDIR = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
WINDOW_S = 30.0
LUMA_MIN = 195          # the plane is paper-white
SAT_MAX = 55            # and neutral; warm sodium light and skin are not
AREA_MIN = 0.020        # >=2% of the frame as ONE blob = subject, not background detail
BOX_MIN = 0.16          # width share of that blob
SKIN_MAX = 0.02         # above this a face is in frame = portrait, not a plane-only setup


def largest_blob(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best = (0, None)
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        stack = [(y0, x0)]
        seen[y0, x0] = True
        n, minx, maxx, miny, maxy = 0, x0, x0, y0, y0
        while stack:
            y, x = stack.pop()
            n += 1
            if x < minx: minx = x
            if x > maxx: maxx = x
            if y < miny: miny = y
            if y > maxy: maxy = y
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if n > best[0]:
            best = (n, (minx, miny, maxx, maxy))
    return best


def measure(clip, dur):
    tmp = os.path.join(EVID, "_m.png")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", "%.3f" % (dur * 0.45), "-i", clip,
                    "-frames:v", "1", "-vf", "scale=336:192", tmp], check=True)
    a = np.asarray(Image.open(tmp).convert("RGB"), dtype=np.int16)
    luma = a.mean(axis=2)
    sat = a.max(axis=2) - a.min(axis=2)
    mask = (luma > LUMA_MIN) & (sat < SAT_MAX)
    n, box = largest_blob(mask)
    total = mask.size
    # A portrait that happens to hold the plane is not a repeat of the empty-city setup,
    # so the run rule ignores frames with a face in them. Warm sodium lighting also trips a
    # raw skin test, so this uses the largest contiguous skin-toned blob (a face is one blob;
    # street lamps are many small ones) instead of the raw pixel share.
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    skinmask = ((r > 95) & (g > 40) & (b > 20) & ((r - g) > 15) & (r > g) & (r > b))
    sn, sbox = largest_blob(skinmask)
    skin_frac = round(sn / float(total), 4)
    face_present = bool(sn and (sn / float(total)) >= SKIN_MAX
                        and sbox and (sbox[2] - sbox[0] + 1) / float(skinmask.shape[1]) >= 0.12)
    if not box or n == 0:
        return {"area_frac": 0.0, "box_w_frac": 0.0, "box_h_frac": 0.0, "cx": 0.0, "cy": 0.0,
                "skin_frac": skin_frac, "face_present": face_present}
    minx, miny, maxx, maxy = box
    return {"area_frac": round(n / total, 4),
            "box_w_frac": round((maxx - minx + 1) / mask.shape[1], 3),
            "box_h_frac": round((maxy - miny + 1) / mask.shape[0], 3),
            "cx": round(((minx + maxx) / 2) / mask.shape[1], 3),
            "cy": round(((miny + maxy) / 2) / mask.shape[0], 3),
            "skin_frac": skin_frac, "face_present": face_present}


def main():
    tl = io.open(glob.glob(os.path.join(OUTDIR, "*shots-v2.py"))[0], encoding="utf-8").read()
    first = {}
    for shot, s, e, sp in re.findall(r'\("(KN\d+[a-z]?)",\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)', tl):
        first.setdefault(shot, (float(s), float(e)))
    rows = []
    for clip in sorted(glob.glob(os.path.join(CLIPS, "KN_A-KN*.mp4")),
                       key=lambda p: int(re.search(r"KN(\d+)", os.path.basename(p)).group(1))):
        shot = re.search(r"(KN\d+)", os.path.basename(clip)).group(1)
        if shot not in first:
            continue
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "default=nw=1:nk=1", clip],
                                   capture_output=True, text=True).stdout.strip() or 0)
        if dur <= 0:
            continue
        m = measure(clip, dur)
        m.update({"shot": shot, "t0": first[shot][0]})
        m["plane_dominant"] = bool(m["area_frac"] >= AREA_MIN and m["box_w_frac"] >= BOX_MIN
                                   and not m["face_present"])
        rows.append(m)
    runs, cur = [], None
    for r in rows:
        if r["plane_dominant"]:
            if cur and r["t0"] - cur[-1]["t0"] <= WINDOW_S:
                cur.append(r)
                continue
            if cur and len(cur) >= 2:
                runs.append(cur)
            cur = [r]
        else:
            if cur and len(cur) >= 2:
                runs.append(cur)
            cur = None
    if cur and len(cur) >= 2:
        runs.append(cur)
    rec = {"units": len(rows), "window_s": WINDOW_S,
           "rule": {"luma_min": LUMA_MIN, "sat_max": SAT_MAX, "area_min": AREA_MIN, "box_min": BOX_MIN},
           "suspect_runs": [[r["shot"] for r in run] for run in runs], "rows": rows}
    io.open(os.path.join(EVID, "motif-repeat.json"), "w", encoding="utf-8").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    for r in rows:
        print("%-6s t=%6.2f area=%.3f boxw=%.2f boxh=%.2f c=(%.2f,%.2f) %s"
              % (r["shot"], r["t0"], r["area_frac"], r["box_w_frac"], r["box_h_frac"],
                 r["cx"], r["cy"], "PLANE" if r["plane_dominant"] else "-"))
    print("MOTIF-END units=%d suspect_runs=%d" % (len(rows), len(runs)))
    return 1 if runs else 0


if __name__ == "__main__":
    sys.exit(main())
