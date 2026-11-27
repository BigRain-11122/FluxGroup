#!/usr/bin/env python3
"""node_sync.py - report (and optionally repair) a fleet node's checkout state.

Why: bm-b/bm-c report repo heads that exist nowhere on origin (e.g. 037a2808,
4f5cc086 while origin/main is 2c88a32). Consequence: every tool added on main
after they diverged is MISSING on those boxes, and their cards die as
SCRIPT-MISSING / phantom-blocked. The repair itself must run ON the node.

Default is read-only: fetch refs, then report branch / head / ahead-behind /
dirty tracked files. `--apply` performs `git reset --hard origin/main` ONLY when
the tracked tree is clean; local commits are preserved in the reflog.
"""
import argparse
import json
import os
import subprocess
import sys


def run(args, cwd, timeout=180):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return 1, "", str(exc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--receipt", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    rep = {"node": os.environ.get("COMPUTERNAME", ""), "root": root, "steps": {}}
    rc, out, err = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    rep["branch"] = out if rc == 0 else None
    rc, out, _ = run(["git", "rev-parse", "HEAD"], root)
    rep["head"] = out if rc == 0 else None

    rc, out, err = run(["git", "fetch", "origin", "--prune"], root, timeout=300)
    rep["fetch_rc"] = rc
    rep["fetch_err"] = err[-400:] if rc else ""

    rc, out, _ = run(["git", "rev-parse", "origin/main"], root)
    rep["origin_main"] = out if rc == 0 else None
    if rep["head"] and rep["origin_main"]:
        rc, out, _ = run(["git", "rev-list", "--left-right", "--count",
                          "HEAD...origin/main"], root)
        if rc == 0 and "\t" in out:
            ahead, behind = out.split("\t")[:2]
            rep["ahead"] = int(ahead)
            rep["behind"] = int(behind)

    rc, out, _ = run(["git", "status", "--porcelain", "--untracked-files=no"], root)
    rep["dirty_tracked"] = [ln for ln in out.splitlines() if ln.strip()]

    # Does the head even exist on origin? (phantom local commit detector)
    if rep["head"]:
        rc, out, _ = run(["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], root)
        rep["head_on_origin_main"] = (rc == 0)

    action = "report-only"
    if args.apply:
        if rep["dirty_tracked"]:
            action = "REFUSED dirty tracked files (%d)" % len(rep["dirty_tracked"])
        elif not rep.get("origin_main"):
            action = "REFUSED no origin/main"
        else:
            rc, out, err = run(["git", "reset", "--hard", "origin/main"], root)
            action = "reset rc=%d %s" % (rc, (out or err)[:200])
            rc2, out2, _ = run(["git", "rev-parse", "HEAD"], root)
            rep["head_after"] = out2
    rep["action"] = action

    text = json.dumps(rep, ensure_ascii=False, indent=1)
    print(text)
    if args.receipt:
        path = args.receipt if os.path.isabs(args.receipt) else os.path.join(root, args.receipt)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())