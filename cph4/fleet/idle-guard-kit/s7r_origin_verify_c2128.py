# -*- coding: ascii -*-
# s7r_origin_verify_c2128.py - confirm the conformed S7R boards and receipts on
# origin/main are byte-identical to the local files this lane delivered
# (bank job s7r-origin-verify-v1; C2125 pushed through a detached worktree, so
# the twin risk is real and worth a mechanical check).
#
# Zero GPU, read-only. PASS gate: ORIGIN-VERIFY-END ok=5 mismatches=0.

import hashlib
import json
import os
import subprocess
import time

REPO = r"K:\Fluxgroup\FluxGroup"
REL = "cph4/fleet/mv-album-001-jay"
FILES = [
    "xq-AB-S7R-BOARD-1-r1058.jpg",
    "xq-AB-S7R-BOARD-2-r1058.jpg",
    "xq-AB-S7R-COMPARE-S5-26-r1058.jpg",
    "xq-AB-S7R-COMPARE-S0-03-r1058.jpg",
    "xq-S7R-CONFORM-LABELS-c2125.json",
    "xq-S7R-FAMILY-RATIFY-BOARD-c2126.jpg",
    "xq-S7R-FAMILY-RATIFY-c2126.json",
    "xq-S527-PROXY-CONTACT-c2129.jpg",
]
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
LOG_OUT = os.path.join(LOGDIR, "s7r_originverify.out.txt")


def logline(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG_OUT, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")
    try:
        print(line)
    except Exception:
        pass


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=REPO,
                                   stderr=subprocess.DEVNULL)


def main():
    if os.path.exists(LOG_OUT):
        os.remove(LOG_OUT)
    subprocess.check_call(["git", "fetch", "origin", "--quiet"], cwd=REPO)
    tip = git("rev-parse", "--short", "origin/main").decode("ascii").strip()
    logline("ORIGIN-VERIFY-START origin/main=%s files=%d" % (tip, len(FILES)))

    rows = []
    ok = 0
    bad = 0
    for name in FILES:
        rel = REL + "/" + name
        local = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", name)
        row = {"file": name}
        if not os.path.exists(local):
            row["status"] = "LOCAL_MISSING"
            bad += 1
            rows.append(row)
            logline("LOCAL-MISSING %s" % name)
            continue
        lb = open(local, "rb").read()
        try:
            rb = git("cat-file", "blob", "origin/main:" + rel)
        except subprocess.CalledProcessError:
            row["status"] = "ORIGIN_MISSING"
            bad += 1
            rows.append(row)
            logline("ORIGIN-MISSING %s" % name)
            continue
        same = sha_bytes(lb) == sha_bytes(rb)
        norm_same = lb.replace(b"\r\n", b"\n") == rb.replace(b"\r\n", b"\n")
        row.update({"status": "OK" if same else ("EOL-ONLY" if norm_same else "MISMATCH"),
                    "local_sha256": sha_bytes(lb)[:16],
                    "origin_sha256": sha_bytes(rb)[:16],
                    "bytes": len(lb)})
        if same or norm_same:
            ok += 1
        else:
            bad += 1
        logline("CHECK %s %s %dB %s" % (name, row["status"], len(lb), row["local_sha256"]))

    rec = {
        "batch": "S7R conformed boards origin integrity verify",
        "runner": "bm-c C2128",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "origin_main": tip,
        "ok": ok, "mismatches": bad,
        "files": rows,
    }
    rp = os.path.join(REPO, REL, "xq-S7R-ORIGIN-VERIFY-c2128.json")
    json.dump(rec, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    logline("RECEIPT %s" % os.path.basename(rp))
    logline("ORIGIN-VERIFY-END ok=%d mismatches=%d" % (ok, bad))
    if bad:
        raise SystemExit("origin verify failed mismatches=%d" % bad)


if __name__ == "__main__":
    main()