# kn_wave_repeat_probe_c2172.py - repetition faces for the KN 768P wave (C2172).
# The sampled board showed three paper-plane-over-the-city units (KN06/KN07/KN10).
# Two deterministic questions, both cheap and CPU-only:
#   1. intra-clip: is any unit actually frozen (pixel-identical frame pairs)?
#      confirmed by framemd5, the method that caught the 3.2 s replay in the XQ pack.
#   2. inter-clip: are those three units near-duplicate compositions? measured as
#      mean absolute difference on an 84x48 grey grid of the mid frame, normalised
#      to 0..1. below 0.5 % => the same picture, 0.5-2 % => suspicious, else distinct.
import glob
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

REPO = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(ALBUM, "clips-local-768")
EVID = os.path.join(ALBUM, "evidence-c2172")
FRZ = os.path.join(EVID, "frames")
GRID = (84, 48)


def frame_grey(path, sec):
    tmp = os.path.join(FRZ, "_tmp.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ss", "%.3f" % sec,
                    "-frames:v", "1", tmp], check=True)
    im = Image.open(tmp).convert("L").resize(GRID, Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


def dup_pairs(path):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "framemd5", "-"],
                         capture_output=True, text=True).stdout
    hashes = []
    for line in out.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 6:
            hashes.append(parts[-1])
    seen = {}
    dups = 0
    for h in hashes:
        if h in seen:
            dups += 1
        else:
            seen[h] = 1
    return len(hashes), dups


def main():
    os.makedirs(FRZ, exist_ok=True)
    clips = sorted(glob.glob(os.path.join(CLIPS, "KN_A-KN*.mp4")))
    mid = {}
    intra = []
    for clip in clips:
        name = os.path.splitext(os.path.basename(clip))[0]
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", clip], capture_output=True, text=True).stdout.strip())
        mid[name] = frame_grey(clip, dur / 2.0)
        n, dups = dup_pairs(clip)
        intra.append({"unit": name, "frames": n, "dup_pairs": dups,
                      "dup_ratio": round(dups / max(1, n), 4)})

    names = sorted(mid)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = mid[names[i]], mid[names[j]]
            mad = float(np.abs(a - b).mean())
            pairs.append({"a": names[i], "b": names[j], "mad": round(mad, 5)})
    pairs.sort(key=lambda p: p["mad"])
    same = [p for p in pairs if p["mad"] < 0.005]
    suspect = [p for p in pairs if 0.005 <= p["mad"] < 0.02]
    payload = {
        "batch": "C2172",
        "grid": list(GRID),
        "intra_clip": intra,
        "frozen_units": [r["unit"] for r in intra if r["dup_ratio"] >= 0.05],
        "closest_pairs": pairs[:8],
        "same_picture_pairs": same,
        "suspect_pairs": suspect,
        "method_note": ("framemd5 gives pixel-exact duplicate counting; a walking or "
                        "handheld shot legitimately repeats nothing, a frozen clip repeats "
                        "most frames. Cross-clip MAD on a grey grid is composition overlap, "
                        "not content judgement - the eye decides."),
    }
    out = os.path.join(EVID, "repeat-probe.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("REPEAT-PROBE landed=%d frozen=%d same_pairs=%d suspect_pairs=%d -> %s"
          % (len(intra), len(payload["frozen_units"]), len(same), len(suspect), out))
    for p in pairs[:6]:
        print("  %.5f %s vs %s" % (p["mad"], p["a"], p["b"]))
    for r in intra:
        print("  %s frames=%d dups=%d ratio=%.3f" % (r["unit"], r["frames"], r["dup_pairs"], r["dup_ratio"]))


if __name__ == "__main__":
    sys.exit(main())