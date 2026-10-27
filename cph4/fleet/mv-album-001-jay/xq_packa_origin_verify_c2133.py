# -*- coding: ascii -*-
# xq_packa_origin_verify_c2133.py - bank job packA-conform-origin-verify-v1.
#
# Why: the conform round published index v2 and two receipts; until they are read
# back from origin they are only local. This re-reads each blob from origin/main
# and compares it to the working copy (EOL-only differences reported separately,
# since the worktree may carry CRLF over an LF blob).
#
# PASS gate: ORIGIN-VERIFY-END ok=1 mismatches=0

import hashlib
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
REL = "cph4/fleet/mv-album-001-jay"
LOG_RUN = os.path.join(REPO, "media", "mv-album-001-jay", "log-packa-originverify.run.txt")

FILES = [
    REL + "/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json",
    REL + "/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.md",
    REL + "/xq-PACKA-CUTPOINTS-c2133.json",
    REL + "/xq-PACKA-CONFORM-c2133.json",
]


def logline(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (stamp, msg)
    try:
        with open(LOG_RUN, "a", encoding="ascii", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line)
    except Exception:
        pass


def main():
    subprocess.check_call(["git", "fetch", "origin", "--quiet"], cwd=REPO)
    tip = subprocess.check_output(["git", "rev-parse", "--short", "origin/main"],
                                  cwd=REPO).decode("ascii").strip()
    logline("ORIGIN-VERIFY-START origin/main=%s files=%d" % (tip, len(FILES)))

    bad = 0
    eol_only = 0
    for rel in FILES:
        name = rel.split("/")[-1]
        try:
            blob = subprocess.check_output(
                ["git", "cat-file", "blob", "origin/main:%s" % rel], cwd=REPO,
                stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            bad += 1
            logline("ORIGIN-MISSING %s" % name)
            continue
        local = open(os.path.join(REPO, rel.replace("/", os.sep)), "rb").read()
        if hashlib.sha256(blob).hexdigest() == hashlib.sha256(local).hexdigest():
            logline("MATCH %s" % name)
            continue
        if blob.replace(b"\r\n", b"\n") == local.replace(b"\r\n", b"\n"):
            eol_only += 1
            logline("EOL-ONLY %s" % name)
            continue
        bad += 1
        logline("DRIFT %s" % name)

    logline("ORIGIN-VERIFY-END ok=%d mismatches=%d eol_only=%d" %
            (1 if bad == 0 else 0, bad, eol_only))
    if bad:
        sys.exit(2)


if __name__ == "__main__":
    main()