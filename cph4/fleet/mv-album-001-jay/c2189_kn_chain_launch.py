"""C2189 detached chain: KN17 + KN18 480P probe iteration 4 (band noun dropped).

Sequential on one GPU lane (never two H3 burns at once on bm-c). Fired with
pythonw.exe so the burn survives the CLI session (C2186/C2187 pattern).
Production 768P is NOT fired here - it waits for the 480P eye gate.
"""

import io
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
RUNNER = os.path.join(PKG, "local-i2v", "h3_i2v_album.py")
LOG = os.path.join(REPO, "media", "mv-album-001-jay", "logs", "kn-galaxy480-c2189.log")

STEPS = [
    ("probe-480", ["bmcverify", os.path.join(PKG, "local-i2v", "run-bmc-kn-galaxy480-c2189.json")]),
]


def log(line):
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line.rstrip("\n") + "\n")


def main():
    log("=== C2189 CHAIN START %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    for tag, (lane, manifest) in STEPS:
        log("--- STEP %s lane=%s manifest=%s" % (tag, lane, os.path.basename(manifest)))
        cmd = [sys.executable, RUNNER, "--repo", REPO, "--lane", lane, "--manifest", manifest]
        with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
            rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
        log("--- STEP %s EXIT rc=%d" % (tag, rc))
        if rc != 0:
            log("=== C2189 CHAIN ABORT rc=%d" % rc)
            return rc
    log("=== C2189 CHAIN DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())