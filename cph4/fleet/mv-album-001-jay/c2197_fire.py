"""C2197: fire KN18 iteration-7 at 768P from the cropped KN17 plate.

The shot keeps its window (117.46-126.52) and its role (main breathing shot 2, the
close partner to the KN17 wide). What changed is the input frame: a real crop into
the proven KN17 band (median 23, p99 38 - inside the green zone) instead of a
generated near-empty sky. The wording keeps the point vocabulary that KN17 cleared
with, because the evidence says the vocabulary was never the problem.
"""

import io
import json
import os
import sys

PKG = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
LOCAL = os.path.join(PKG, "local-i2v")
SRC = os.path.join(LOCAL, "run-bmc-kn-galaxy-prod-c2196.json")
OUT = os.path.join(LOCAL, "run-bmc-kn-galaxy-prod-c2197.json")
WATCH_SRC = os.path.join(PKG, "c2196_kn18_watch_harvest.py")
WATCH_OUT = os.path.join(PKG, "c2197_kn18_watch_harvest.py")

PROMPT = (
    "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera slides laterally with small "
    "amplitude in shallow focus, easing in at the start and settling to a stop at the end. A dense field of "
    "separate round points of warm gold light holding across the whole frame, every point small and round and "
    "distinct, the points drifting apart at the slowest breath, a faint milky band of star dust crossing behind "
    "them and staying soft. Warm 2000 Taiwanese telecine grade, warm skin tones, milky lifted blacks. Visible "
    "35mm film grain. Restrained continuous motion, camera and subject motion only."
)

POLICY = (
    "C2197 KN18 iteration-7 at 768P. Three takes failed on a generated keyframe: dense close-up wording gave a "
    "lattice of glowing lamps with vertical streaks (p99 26/79/69 and 27/80/74), and dust-haze wording gave "
    "molten gold blobs (126/143/155). Keyframe measurements explain all three - the generated KN18 keyframes "
    "could not be aimed between nearly empty (p99 19-22) and milky bright (89, then 145), while the sibling "
    "KN17 plate holds the right field (median 18, p99 37) and cleared 768P at 32/31/32. So KN18's keyframe is "
    "now a real crop into that same band (median 23, p99 38, irregular natural stars, verified by eye), which "
    "also makes the two breathing shots continuous in the cut. The point vocabulary is kept because KN17 cleared "
    "with it. Lane bmc int8 1344x768. Writes clips-local-768/KN_G8-KN18.mp4."
)


def build_manifest():
    with io.open(SRC, encoding="utf-8") as fh:
        man = json.load(fh)
    unit = dict(man["units"][0])
    unit["id"] = "KN_G8-KN18"
    unit["frame"] = "media/mv-album-001-jay/frames/KN_KN18.png"
    unit["i2v_prompt"] = PROMPT
    unit["prompt_words"] = len(PROMPT.split())
    unit["prompt_rev"] = "v7.0-C2197-kn17-crop-plate"
    man["units"] = [unit]
    man["batch"] = "C2197"
    man["policy"] = POLICY
    man["prompt_rev"] = "v7.0-C2197-kn17-crop-plate"
    man["gate"] = ("keyframe gate: logs/kn18-kf-crop-c2197.json (median 23, p99 38, inside the KN17 green zone) "
                   "+ three archived red takes in clips-red/")
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return unit


def build_watcher():
    with io.open(WATCH_SRC, encoding="utf-8") as fh:
        src = fh.read()
    for old, new in [('BATCH = "C2196"', 'BATCH = "C2197"'),
                     ("kn18-prod-c2196.json", "kn18-prod-c2197.json"),
                     ("kn18-watch-c2196.log", "kn18-watch-c2197.log"),
                     ("KN18-PROD-C2196.jpg", "KN18-PROD-C2197.jpg"),
                     ("qc-frames-c2196", "qc-frames-c2197")]:
        if old not in src:
            raise SystemExit("watcher anchor missing: %r" % old)
        src = src.replace(old, new)
    with io.open(WATCH_OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    return WATCH_OUT


def main():
    unit = build_manifest()
    w = build_watcher()
    print("manifest=%s unit=%s frame=%s words=%d" % (os.path.basename(OUT), unit["id"],
                                                     unit.get("frame"), unit["prompt_words"]))
    print("watcher=%s" % os.path.basename(w))
    return 0


if __name__ == "__main__":
    sys.exit(main())