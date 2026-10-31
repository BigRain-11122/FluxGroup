#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent.py - the ONE resident agent each fleet node runs.

Why this replaces "hb task + claim task" (2026-10-31 root cause): the heartbeat task was
alive while the executor task was dead, so the master saw a healthy machine and an empty
execution log all night. Two tasks = two failure modes = a control plane that lies to
itself. This is one task, one process, one chain:

    pull -> heartbeat -> self-check own scheduled task -> claim from lane -> run -> report

Every step is idempotent and writes evidence, so the master can judge four separate
signals instead of one: machine hb, agent report, claim, receipt.

Usage (on the node, once, then register as a scheduled task):
    python Tools/fleet/agent.py --node bm-b
    python Tools/fleet/agent.py --node bm-b --loop 60     # stay resident
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PY = sys.executable or "python"


def run(argv, timeout):
    try:
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        tail = ((r.stdout or "").strip().splitlines() or [""])[-1][:160]
        return r.returncode, tail
    except subprocess.TimeoutExpired:
        return 124, "timeout after %ss" % timeout
    except Exception as e:
        return 1, str(e)[:160]


# Machine-generated state files that the master republishes on every pulse. A node's own
# copy of these is disposable: dropping it costs at most one sensor cycle. Anything outside
# this list (ledgers, orders, logs written by humans or shifts) must never be discarded.
GEN_STATE = [
    "cph4/fleet/dispatcher/SUPERVISOR.md",
    "cph4/fleet/dispatcher/CLOCK-SKEW.json",
    "cph4/fleet/dispatcher/NEED-JUDGMENT.md",
    "docs/audits/selfaudit-report.md",
]


def run_msg(argv, timeout):
    """Like run(), but keeps git's stderr -- merge/checkout refusals are reported there."""
    try:
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        msg = ((r.stderr or "") + " " + (r.stdout or "")).strip().replace("\n", " | ")
        return r.returncode, msg[:240]
    except subprocess.TimeoutExpired:
        return 124, "timeout after %ss" % timeout
    except Exception as e:
        return 1, str(e)[:240]


def pull():
    # Codes must arrive before the executor runs, otherwise the node keeps running the bug
    # we already fixed on the master. Never autostash (it swallowed hand edits once).
    #
    # R2.57: plain `pull --rebase --no-autostash` can never succeed here. SUPERVISOR.md is
    # rewritten by the local steward every 5 min and committed by bm-m on every pulse, so the
    # tree is permanently dirty and pull dies with "cannot pull with rebase: You have unstaged
    # changes" -- silently, for weeks. The tree then drifts thousands of commits behind and any
    # local writer lands on a stale base (the stuck-rebase loop of R2.54/R2.55/R2.56).
    # Fix: fetch, fast-forward when possible, and only fall back to clearing GEN_STATE.
    run_msg(["git", "fetch", "--quiet", "origin", "main"], 120)
    rc, tail = run_msg(["git", "merge", "--ff-only", "origin/main"], 120)
    if rc == 0:
        note("ff-only ok: %s" % tail)
        return rc
    cleared = []
    for p in GEN_STATE:
        r, _ = run_msg(["git", "checkout", "HEAD", "--", p], 60)
        if r == 0:
            cleared.append(p)
    rc2, tail2 = run_msg(["git", "merge", "--ff-only", "origin/main"], 120)
    if rc2 == 0:
        note("ff-only after clear ok: %s" % tail2)
        return rc2
    # Diverged: local commits exist. Rebase onto the master, but only when the tree is clean --
    # git refuses on its own otherwise, so a shift mid-edit is never destroyed.
    rc3, tail3 = run_msg(["git", "rebase", "--no-autostash", "origin/main"], 180)
    if rc3 != 0:
        # Never leave a half-finished rebase behind: that residue is exactly what turned into
        # the stuck-rebase / detached-HEAD loop (D-R256-STUCKREBASE).
        run_msg(["git", "rebase", "--abort"], 60)
    note("ff-only blocked (%s) -> cleared %d gen-state -> rebase rc=%s %s"
         % (tail, len(cleared), rc3, tail3))
    return rc3


def note(msg):
    """Evidence line for the pull leg; media/ is gitignored so this never dirties the tree."""
    try:
        d = os.path.join(ROOT, "media", "logs")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "agent-pull.log"), "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg))
    except Exception:
        pass


def tick(node):
    rc_hb, t_hb = run([PY, "Tools/fleet/fleet_hb.py", "--node", node, "--root", ROOT], 120)
    rc_ln, t_ln = run([PY, "Tools/fleet/lane_agent.py", "--node", node, "--root", ROOT,
                       "--no-fetch"], 3600)
    print("agent %s hb=%s(%s) lane=%s(%s)" % (node, rc_hb, t_hb, rc_ln, t_ln))
    return 0 if rc_hb == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--loop", type=int, default=0, help="0 = one tick; N = every N seconds")
    ap.add_argument("--no-pull", action="store_true")
    a = ap.parse_args()
    if not a.no_pull:
        pull()
    if not a.loop:
        return tick(a.node)
    while True:
        tick(a.node)
        time.sleep(a.loop)


if __name__ == "__main__":
    sys.exit(main())