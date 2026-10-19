# -*- coding: ascii -*-
# xq_packa_index_verify_c2132.py - bank job packA-assembly-index-verify-v1.
#
# Why: the assembly index is only trustworthy while it still describes the
# bytes on disk and on origin. This verifier re-hashes every clip listed in the
# index, re-checks the unit list against the C2114 board, and confirms the two
# index files exist on origin/main.
#
# Zero GPU, read-only. PASS gate: INDEX-VERIFY-END ok=1 mismatches=0

import hashlib
import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
IDX_JSON = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-c2132.json")
IDX_MD = "xq-PACKA-ASSEMBLY-INDEX-c2132.md"
BOARD_JSON = os.path.join(OUTDIR, "xq-PACKA-33-FULL-BOARD-c2114.json")
LOG_OUT = os.path.join(REPO, "media", "mv-album-001-jay", "log-packa-index-verify.out.txt")
REL = "cph4/fleet/mv-album-001-jay"


def logline(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG_OUT, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")
    try:
        print(line)
    except Exception:
        pass


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=REPO,
                                   stderr=subprocess.DEVNULL)


def main():
    if os.path.exists(LOG_OUT):
        os.remove(LOG_OUT)
    subprocess.check_call(["git", "fetch", "origin", "--quiet"], cwd=REPO)
    tip = git("rev-parse", "--short", "origin/main").decode("ascii").strip()
    with open(IDX_JSON, encoding="utf-8") as f:
        rec = json.load(f)
    logline("INDEX-VERIFY-START origin/main=%s units=%d" % (tip, rec["units"]))

    bad = 0
    for row in rec["clips"]:
        path = os.path.join(REPO, "media", "mv-album-001-jay",
                            row["file"].replace("/", os.sep))
        if not os.path.exists(path):
            bad += 1
            logline("MISSING %s" % row["file"])
            continue
        got = sha256_of(path)
        if got != row["sha256"]:
            bad += 1
            logline("SHA-DRIFT %s %s!=%s" % (row["file"], got[:12], row["sha256"][:12]))
        elif os.path.getsize(path) != row["bytes"]:
            bad += 1
            logline("SIZE-DRIFT %s" % row["file"])

    with open(BOARD_JSON, encoding="utf-8-sig") as f:
        labels = json.load(f)["labels"]
    if labels != [r["unit"] for r in rec["clips"]]:
        bad += 1
        logline("LABELS-DRIFT board vs index")

    for name in (os.path.basename(IDX_JSON), IDX_MD):
        try:
            git("cat-file", "blob", "origin/main:%s/%s" % (REL, name))
            logline("ORIGIN-OK %s" % name)
        except subprocess.CalledProcessError:
            bad += 1
            logline("ORIGIN-MISSING %s" % name)

    logline("INDEX-VERIFY-END ok=%d mismatches=%d" % (1 if bad == 0 else 0, bad))
    if bad:
        sys.exit(2)


if __name__ == "__main__":
    main()