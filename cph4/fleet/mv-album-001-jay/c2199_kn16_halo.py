"""C2199: rebuild KN16's take with the rainbow corona recoloured to a film halo.

The director review of KN full-film v3 blocks PASS on one item only: at
108.9-109.1s the moon carries a full rainbow multi-ring corona, which reads as a
lens-flare effect rather than a 2000s film halo. Both KN16 takes on disk carry it
(the older one additionally has vertical haze streaks), so this is not a
"pick the better take" situation and a sixth generation attempt is a lottery.

The defect is chromatic and the ring is a clean geometric annulus, so the fix is
applied at colour level on the take that already passed every other gate:
  * the ring's luminance structure is kept (it is the halo a film would have);
  * chromatic separation inside the band is dropped and the band is warmed
    slightly, so it reads as a soft warm-white halo;
  * nothing outside the annulus is touched - the sky, the moon and the cloud sea
    keep their grade, and the audio is not involved at all.

The mask is c2199-kn16-halo-mask.png (geometric annulus, feathered, faded above
the cloud line where the take itself drops the ring).

Usage:
  python c2199_kn16_halo.py --build     # rewrite the take (backs up the old one)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
SRC = os.path.join(MEDIA, "clips-local-768", "KN_A-KN16.mp4")
BAK = os.path.join(MEDIA, "clip-archive-c2199", "KN_A-KN16-pre-c2199.mp4")
MASK = os.path.join(MEDIA, "c2199-kn16-halo-mask.png")
QC = os.path.join(MEDIA, "qc-frames-c2199")
BOARD = os.path.join(MEDIA, "qc-boards", "KN16-HALO-C2199.jpg")
VERDICT = os.path.join(MEDIA, "logs", "kn16-halo-c2199.json")
TMP = os.path.join(MEDIA, "clip-archive-c2199", "KN_A-KN16-c2199-tmp.mp4")
TIMES = (2.0, 5.0, 8.3, 11.0)

FILTER = (
    "[0:v]split=2[base][src];"
    "[src]hue=s=0.10,colorbalance=rs=0.09:gs=0.02:bs=-0.07,"
    "eq=contrast=1.01,gblur=sigma=2.0[flat];"
    # The ring only forms after ~5s into the take; before that the same annulus
    # holds plain night sky, so the mask itself is ramped in with the ring's
    # formation instead of tinting sky that has no ring in it.
    "[1:v]format=gray,fade=t=in:st=5.2:d=1.6[m];"
    "[flat]format=rgba[fa];[fa][m]alphamerge[fg];"
    "[base][fg]overlay=format=auto,format=yuv420p"
)


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit("cmd failed: %s\n%s" % (" ".join(cmd), res.stderr[-1500:]))
    return res


def saturation(path):
    """Mean saturation and chroma spread inside the corona band only."""
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype("float32")
    h, w = a.shape[:2]
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1.0)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((xx - 681.1) ** 2 + (yy - 212.7) ** 2)
    band = (r > 250) & (r < 470) & (yy < 500) & (mx > 40)
    vals = sat[band]
    return {"mean": round(float(vals.mean()), 4),
            "p90": round(float(np.percentile(vals, 90)), 4),
            "px": int(band.sum())}


def build():
    os.makedirs(QC, exist_ok=True)
    os.makedirs(os.path.dirname(BOARD), exist_ok=True)
    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if os.path.isfile(SRC) and not os.path.isfile(BAK):
        shutil.copy2(SRC, BAK)
        print("backed up previous take -> %s" % os.path.basename(BAK))
    if not os.path.isfile(BAK):
        raise SystemExit("no original take to rebuild from")
    # Always rebuild from the untouched original: re-running this pass on its own
    # output would stack the recolour and darken the halo each time.
    # The mask is a still, so it has to be looped onto the timeline, and it has
    # to be bounded: an unbounded loop lets overlay keep producing frames after
    # the take has ended (the first attempt wrote 166MB and never stopped).
    run(["ffmpeg", "-y", "-v", "error", "-i", BAK,
         "-loop", "1", "-framerate", "24", "-t", "13", "-i", MASK,
         "-filter_complex", FILTER, "-shortest", "-an", "-c:v", "libx264", "-crf", "16",
         "-preset", "slow", "-r", "24", TMP])
    os.replace(TMP, SRC)
    print("rewrote %s (%d bytes)" % (os.path.basename(SRC), os.path.getsize(SRC)))
    return True


def screen():
    rows, thumbs = [], []
    for t in TIMES:
        after = os.path.join(QC, "KN16_c2199_t%s.png" % t)
        before = os.path.join(QC, "KN16_c2199_before_t%s.png" % t)
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1", after])
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", BAK, "-frames:v", "1", before])
        sa, sb = saturation(after), saturation(before)
        rows.append({"t": t, "after": sa, "before": sb})
        thumbs += [before, after]
    cw = 336
    sized = []
    for p in thumbs:
        im = Image.open(p)
        r = cw / float(im.size[0])
        sized.append(im.resize((cw, max(1, int(im.size[1] * r)))))
    rh = max(i.size[1] for i in sized)
    sheet = Image.new("RGB", (cw * 4, rh * 2), (12, 12, 14))
    for i, im in enumerate(sized):
        sheet.paste(im, ((i % 4) * cw, (i // 4) * rh))
    sheet.save(BOARD, quality=92)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.build or a.report:
        rows = screen()
        payload = {
            "batch": "C2199",
            "method": "chroma-selective recolour of the corona annulus (no generation)",
            "take": SRC,
            "archived_previous": BAK,
            "mask": MASK,
            "band_saturation": rows,
            "board": BOARD,
            "note": ("Band saturation is the objective gate: the rainbow is gone when mean saturation "
                     "inside the annulus collapses while the rest of the frame keeps its grade. "
                     "Visual check is the 1:1 board - the halo must read as soft warm-white rings."),
        }
        with open(VERDICT, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False)
        for r in rows:
            print("t=%s sat before %.3f -> after %.3f" % (r["t"], r["before"]["mean"], r["after"]["mean"]))
        print("board=%s" % os.path.basename(BOARD))
    return 0


if __name__ == "__main__":
    sys.exit(main())