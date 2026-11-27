"""C2194 launcher: KN18 iteration-5 768P burn (sparse-field close-up wording).

Fired detached so the burn outlives this CLI window - the render itself lives in
the ComfyUI server process, so only the submission has to survive, and the
watcher/harvest step adopts by disk either way. Log carries the prompt id so the
next round can screen the exact job without guessing.

Prior: C2192 768P burn was RED (p99 26/79/69, ballooned disks and vertical
striations) on a prompt that had cleared the 480P probe - see
logs/kn18-prod-c2194.json and qc-boards/KN18-PROD-C2194.jpg.
"""

import io
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
RUNNER = os.path.join(PKG, "local-i2v", "h3_i2v_album.py")
LOG = os.path.join(REPO, "media", "mv-album-001-jay", "logs", "kn18-prod-c2194.log")
MANIFEST = os.path.join(PKG, "local-i2v", "run-bmc-kn-galaxy-prod-c2194.json")


def log(line):
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line.rstrip("\n") + "\n")


def main():
    log("=== C2194 CHAIN START %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    log("manifest=%s prompt_rev=v5.0-C2194-sparse-closeup" % os.path.basename(MANIFEST))
    cmd = [sys.executable, "-u", RUNNER, "--repo", REPO, "--lane", "bmc",
           "--manifest", MANIFEST]
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
        fh.write("--- EXIT rc=%d\n" % rc)
        fh.write("=== C2194 CHAIN DONE\n" if rc == 0 else "=== C2194 CHAIN ABORT\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())