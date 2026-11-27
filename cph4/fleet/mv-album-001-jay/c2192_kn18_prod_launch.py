"""C2192 detached launcher: KN18 768P production burn (one clip, one GPU lane).

Fired with pythonw.exe so the burn survives this CLI window (C2186/C2190 pattern).
Lane bmc, int8 1344x768. The 480P probe cleared this exact prompt (blur p99
22/25/28 against threshold 47), so this is a straight production burn of the cut.
On completion the wave flag (re-pointed by this round) tells the next round to
pull frames, screen them, promote to clips-local-768/KN_A-KN18.mp4 and rebuild
the whole film with kn_full_assembly_c2183.py --encode.
"""

import io
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
RUNNER = os.path.join(PKG, "local-i2v", "h3_i2v_album.py")
LOG = os.path.join(REPO, "media", "mv-album-001-jay", "logs", "kn-galaxy-prod-c2192.log")
STEPS = [
    ("prod-768", ["bmc", os.path.join(PKG, "local-i2v", "run-bmc-kn-galaxy-prod-c2192.json")]),
]


def log(line):
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line.rstrip("\n") + "\n")


def main():
    log("=== C2192 CHAIN START %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    for tag, (lane, manifest) in STEPS:
        log("--- STEP %s lane=%s manifest=%s" % (tag, lane, os.path.basename(manifest)))
        cmd = [sys.executable, RUNNER, "--repo", REPO, "--lane", lane, "--manifest", manifest]
        with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
            rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
        log("--- STEP %s EXIT rc=%d" % (tag, rc))
        if rc != 0:
            log("=== C2192 CHAIN ABORT rc=%d" % rc)
            return rc
    log("=== C2192 CHAIN DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())