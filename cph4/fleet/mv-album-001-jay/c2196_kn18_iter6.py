"""C2196: KN18 iteration-6 - re-spec the shot instead of re-wording it a third time.

Evidence chain that drove this:
  * iteration-4 (v4.0 dense close-up)   -> 768P RED  p99 26/79/69
  * iteration-5 (v5.0 sparse close-up)  -> 768P RED  p99 27/80/74   (no improvement)
  * sibling KN17, same workflow/seed discipline, but an extreme wide -> GREEN 32/31/32
  * keyframe measurement (c2195_kn_keyframe_glow.py): KN18 KN_KN18.png is p99 19 /
    med 16 (nearly empty), KN17 KN_KN17.png is p99 37 / med 18 (holds the field)
  * the RED board reads as a regular lattice of glowing amber lamps with vertical
    streaks, i.e. the model inventing structure into an empty sky

So star density is not the variable and neither is the "evenly" vocabulary - KN17
uses more of it and is green. The variable is that a *close-up of a point-light
field* on a nearly empty keyframe makes the model tile the frame. The shot is
therefore re-specified as a close-up of drifting dust haze with no point lights at
all: same time window, same role in the cut (a tight breathing beat between the
wide galaxy shots), but nothing for the model to tile.
"""

import io
import json
import os
import re
import shutil
import sys

PKG = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
LOCAL = os.path.join(PKG, "local-i2v")
SRC_MANIFEST = os.path.join(LOCAL, "run-bmc-kn-galaxy-prod-c2194.json")
OUT_MANIFEST = os.path.join(LOCAL, "run-bmc-kn-galaxy-prod-c2196.json")
WATCH_SRC = os.path.join(PKG, "c2194_kn18_watch_harvest.py")
WATCH_OUT = os.path.join(PKG, "c2196_kn18_watch_harvest.py")

PROMPT = (
    "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera drifts slowly to one side "
    "with small amplitude in shallow focus, easing in at the start and settling to a stop at the end. Fine "
    "warm dust suspended in near darkness: a continuous soft veil of out-of-focus motes and faint warm "
    "grains, drifting slowly and unevenly the way dust moves through a lamp-lit room, the grains clumping "
    "here and thinning there at their own pace, some soft and rounded, others a faint short streak carried "
    "along by the drift. The darkness behind the veil stays deep, unlit and empty, opening out gently to the "
    "edges of frame. Warm 2000 Taiwanese telecine grade, milky lifted blacks. Visible 35mm film grain. "
    "Restrained continuous motion, camera and subject motion only."
)

POLICY = (
    "C2196 KN18 iteration-6 at 768P. Two close-up burns of a point-light sky both came back RED at 768P "
    "(p99 26/79/69 then 27/80/74 against a threshold of 47) while the wide sibling KN17 is green at 32/31/32 "
    "on the same workflow. Keyframe measurement settles the cause: KN_KN18.png is nearly empty (p99 19, "
    "median 16) where KN_KN17.png already holds its field (p99 37). An empty sky plus point-light vocabulary "
    "makes the model tile the frame with regular glowing lamps and vertical streaks. This iteration keeps "
    "the shot's window and its job in the cut (a tight breathing beat between the two wide galaxy shots) but "
    "re-specifies the subject as drifting warm dust haze with no point lights at all, so there is nothing to "
    "tile. Lane bmc int8 1344x768, seed 102675 unchanged. Writes clips-local-768/KN_G6-KN18.mp4."
)


def build_manifest():
    with io.open(SRC_MANIFEST, encoding="utf-8") as fh:
        man = json.load(fh)
    unit = dict(man["units"][0])
    unit["id"] = "KN_G7-KN18"
    unit["i2v_prompt"] = PROMPT
    unit["prompt_words"] = len(PROMPT.split())
    unit["prompt_rev"] = "v6.0-C2196-dust-closeup"
    man["units"] = [unit]
    man["batch"] = "C2196"
    man["policy"] = POLICY
    man["prompt_rev"] = "v6.0-C2196-dust-closeup"
    man["gate"] = "C2195 harvest verdict (p99 27/80/74 RED) + keyframe glow audit logs/kn-keyframe-glow-c2195.json"
    with io.open(OUT_MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return man, unit


def build_watcher():
    """Clone the proven watcher with this batch's file names, nothing else changed."""
    with io.open(WATCH_SRC, encoding="utf-8") as fh:
        src = fh.read()
    swaps = [
        ('BATCH = "C2194"', 'BATCH = "C2196"'),
        ("kn18-prod-c2194.json", "kn18-prod-c2196.json"),
        ("kn18-watch-c2194.log", "kn18-watch-c2196.log"),
        ("KN18-PROD-C2194.jpg", "KN18-PROD-C2196.jpg"),
        ("qc-frames-c2194", "qc-frames-c2196"),
        ("KN-FULL-v1-%s.mp4", "KN-FULL-v1-%s.mp4"),
    ]
    for old, new in swaps:
        if old not in src and old != new:
            raise SystemExit("watcher swap anchor missing: %r" % old)
        src = src.replace(old, new)
    with io.open(WATCH_OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    return WATCH_OUT


def main():
    man, unit = build_manifest()
    w = build_watcher()
    print("manifest=%s unit=%s frame=%s words=%d" % (
        os.path.basename(OUT_MANIFEST), unit["id"], unit.get("frame"), unit["prompt_words"]))
    print("watcher=%s" % os.path.basename(w))
    print("policy_words=%d" % len(man["policy"].split()))
    return 0


if __name__ == "__main__":
    sys.exit(main())