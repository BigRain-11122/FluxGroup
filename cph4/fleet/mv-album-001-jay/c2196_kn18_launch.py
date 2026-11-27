"""C2196 launcher: KN18 iteration-6 768P burn (dust-haze close-up wording).

Same shape as the C2194 launcher: the burn is submitted detached so it outlives
this CLI window, the log carries the ComfyUI prompt id, and the harvest is
adopted from disk by c2196_kn18_watch_harvest.py.
"""

import io
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
RUNNER = os.path.join(PKG, "local-i2v", "h3_i2v_album.py")
LOG = os.path.join(REPO, "media", "mv-album-001-jay", "logs", "kn18-prod-c2196.log")
MANIFEST = os.path.join(PKG, "local-i2v", "run-bmc-kn-galaxy-prod-c2196.json")


def log(line):
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line.rstrip("\n") + "\n")


def main():
    log("=== C2196 CHAIN START %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    log("manifest=%s prompt_rev=v6.0-C2196-dust-closeup" % os.path.basename(MANIFEST))
    cmd = [sys.executable, "-u", RUNNER, "--repo", REPO, "--lane", "bmc",
           "--manifest", MANIFEST]
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
        fh.write("--- EXIT rc=%d\n" % rc)
        fh.write("=== C2196 CHAIN DONE\n" if rc == 0 else "=== C2196 CHAIN ABORT\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())