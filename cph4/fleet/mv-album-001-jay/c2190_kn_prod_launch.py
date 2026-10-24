"""C2190 detached launcher: KN17 768P production burn (one clip, one GPU lane).

Fired with pythonw.exe so the burn survives this CLI window (C2186/C2189 pattern).
Lane bmc, int8 1344x768. On completion the wave flag (written by the harvest round)
tells the next round to pull frames, screen them and map the clip into the assembly.
"""

import io
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
RUNNER = os.path.join(PKG, "local-i2v", "h3_i2v_album.py")
LOG = os.path.join(REPO, "media", "mv-album-001-jay", "logs", "kn-galaxy-prod-c2190.log")
STEPS = [
    ("prod-768", ["bmc", os.path.join(PKG, "local-i2v", "run-bmc-kn-galaxy-prod-c2190.json")]),
]


def log(line):
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line.rstrip("\n") + "\n")


def main():
    log("=== C2190 CHAIN START %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    for tag, (lane, manifest) in STEPS:
        log("--- STEP %s lane=%s manifest=%s" % (tag, lane, os.path.basename(manifest)))
        cmd = [sys.executable, RUNNER, "--repo", REPO, "--lane", lane, "--manifest", manifest]
        with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
            rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
        log("--- STEP %s EXIT rc=%d" % (tag, rc))
        if rc != 0:
            log("=== C2190 CHAIN ABORT rc=%d" % rc)
            return rc
    log("=== C2190 CHAIN DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())