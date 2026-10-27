"""C2195: locate the KN18 glow origin by measuring the keyframes, not the wording.

Why: two 768P burns of KN18 with the same keyframe and seed disagreed on wording
only (dense v4 vs sparse v5) and both landed at p99 ~79-80 against a threshold of
47, while the sibling KN17 at the same resolution and workflow is green at
32/31/32. That rules out star density as the variable and points at the frame the
burn starts from. This measures the same blurred-sky p99 on the keyframes of both
units so the next iteration changes the right input.
"""

import io
import json
import os
import sys

from PIL import Image, ImageFilter
import numpy as np

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
FRAMES = os.path.join(MEDIA, "frames")


def glow(path):
    im = Image.open(path).convert("L")
    w, h = im.size
    sky = im.crop((0, 0, w, int(h * 0.55)))
    bl = sky.filter(ImageFilter.GaussianBlur(radius=max(6, w // 40)))
    a = np.asarray(bl).astype("float32")
    return {
        "file": os.path.basename(path),
        "size": [w, h],
        "med": round(float(np.median(a)), 1),
        "p95": round(float(np.percentile(a, 95)), 1),
        "p99": round(float(np.percentile(a, 99)), 1),
        "mean": round(float(a.mean()), 1),
    }


def main():
    picks = []
    for name in sorted(os.listdir(FRAMES)):
        low = name.lower()
        if not low.endswith(".png"):
            continue
        if "kn17" in low or "kn18" in low:
            picks.append(os.path.join(FRAMES, name))
    rows = [glow(p) for p in picks]
    out = os.path.join(MEDIA, "logs", "kn-keyframe-glow-c2195.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"frames_dir": FRAMES, "rows": rows}, fh, indent=1, ensure_ascii=False)
    for r in rows:
        print("%-28s %sx%s med=%s p95=%s p99=%s mean=%s" % (
            r["file"], r["size"][0], r["size"][1], r["med"], r["p95"], r["p99"], r["mean"]))
    print("verdict_json=%s rows=%d" % (out, len(rows)))


if __name__ == "__main__":
    sys.exit(main())