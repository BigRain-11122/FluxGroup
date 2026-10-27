# -*- coding: ascii -*-
# xq_packa_index_verify_c2133.py - bank job packA-assembly-index-verify-v1, v2 face.
#
# Why: the C2132 verifier died before it verified anything (it tried to delete the
# very log file the bank guard held open, PermissionError WinError 32). This rewrite
# keeps the same PASS gate, never touches its own log, verifies the v2 ordering
# against the authored pack manifest, re-hashes all 33 clips and confirms the shipped
# index pair on origin. Zero GPU, read-only.
#
# PASS gate: INDEX-VERIFY-END ok=1 mismatches=0

import hashlib
import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay")
V2_JSON = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json")
V1_JSON = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-c2132.json")
PACK_JSON = os.path.join(OUTDIR, "\u661f\u6674-i2v-PACK-A-v1.json")
CONFORM = os.path.join(CLIPS, "assembly-packA", "XQ-PACKA-CONFORM-v1-c2133.mp4")
REL = "cph4/fleet/mv-album-001-jay"
LOG_RUN = os.path.join(CLIPS, "log-packa-index-verify-c2133.run.txt")


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
    subprocess.check_call(["git", "fetch", "origin", "--quiet"], cwd=REPO)
    tip = git("rev-parse", "--short", "origin/main").decode("ascii").strip()

    with open(V2_JSON, encoding="utf-8") as f:
        rec = json.load(f)
    with open(PACK_JSON, encoding="utf-8-sig") as f:
        pack = json.load(f)

    logline("INDEX-VERIFY-START origin/main=%s units=%d" % (tip, rec["units"]))
    bad = 0

    want = [u["id"] for u in pack["units"]]
    want.insert(want.index("XQ_F5-34"), "XQ_F5-33c")
    got = [r["unit"] for r in rec["clips"]]
    if got != want:
        bad += 1
        first = next((i for i, (a, b) in enumerate(zip(got, want)) if a != b), None)
        logline("ORDER-DRIFT first_diff=%s" % first)
    else:
        logline("ORDER-OK authored=%d finale_tail=%s" %
                (len(want), ",".join(got[-4:])))

    if rec["units"] != 33 or len(rec["clips"]) != 33:
        bad += 1
        logline("COUNT-DRIFT units=%s rows=%d" % (rec["units"], len(rec["clips"])))

    for row in rec["clips"]:
        path = os.path.join(CLIPS, row["file"].replace("/", os.sep))
        if not os.path.exists(path):
            bad += 1
            logline("MISSING %s" % row["file"])
            continue
        if sha256_of(path) != row["sha256"]:
            bad += 1
            logline("SHA-DRIFT %s" % row["file"])
        elif os.path.getsize(path) != row["bytes"]:
            bad += 1
            logline("SIZE-DRIFT %s" % row["file"])
    logline("CLIPS-DONE hashed=%d" % len(rec["clips"]))

    # v1 pair must still be on origin (it is the published face), v2 is verified on
    # disk here and joins origin with this round's push (next round can flip it).
    for name in (os.path.basename(V1_JSON), "xq-PACKA-ASSEMBLY-INDEX-c2132.md"):
        try:
            git("cat-file", "blob", "origin/main:%s/%s" % (REL, name))
            logline("ORIGIN-OK %s" % name)
        except subprocess.CalledProcessError:
            bad += 1
            logline("ORIGIN-MISSING %s" % name)
    logline("ORIGIN-PENDING %s (dry twin on disk)" % os.path.basename(V2_JSON))

    with open(V1_JSON, encoding="utf-8") as f:
        v1 = json.load(f)
    if sorted(r["unit"] for r in v1["clips"]) != sorted(got):
        bad += 1
        logline("V1-V2-SET-DRIFT")
    else:
        logline("V1-V2-SET-OK both carry the same 33 units")

    if os.path.exists(CONFORM):
        logline("CONFORM-PRESENT bytes=%d" % os.path.getsize(CONFORM))
    else:
        bad += 1
        logline("CONFORM-MISSING")

    logline("INDEX-VERIFY-END ok=%d mismatches=%d" % (1 if bad == 0 else 0, bad))
    if bad:
        sys.exit(2)


if __name__ == "__main__":
    main()