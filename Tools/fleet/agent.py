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
    # R2.59: lane writes this pointer every round and it is tracked, so the tree was
    # permanently dirty and every ff-only/rebase refused -- the same class of bug as
    # R2.57's SUPERVISOR.md. Regenerated on the next lane round, so dropping it is free.
    "cph4/fleet/queue-receipts/_last_lane_*.json",
    # R2.60: the R2.57/R2.59 lists named four files, but the master republishes a wider set
    # of derived state and each local sensor rewrites its own copy. On 11-01 13:5x the tree
    # carried 22 dirty tracked files, so the clear step freed 5 of them and the fast-forward
    # still refused for hours -- the node sat 23 commits behind and every local writer landed
    # on a stale base. Only derived state belongs here: the authoritative copy is on origin,
    # written by the master, and a node's own copy costs at most one sensor cycle to rebuild.
    # Human/shift ledgers (DISPATCH-LOG, DEADLINES, MASTER-LOG, PATROL-FLEET/*) and the queue
    # itself (PRODUCTION-QUEUE/BACKLOG, queue-receipts) are deliberately NOT listed: those
    # carry work that exists nowhere else, so they must block the pull and be resolved.
    "cph4/fleet/dispatcher/MASTER-STATE.json",
    "cph4/fleet/dispatcher/MASTER-TICK.json",
    "cph4/fleet/dispatcher/PULSE.json",
    "cph4/fleet/dispatcher/SOLVER.md",
    "cph4/fleet/dispatcher/DIGEST.md",
    "cph4/fleet/dispatcher/digest-cache.json",
    "cph4/fleet/dispatcher/CONTINGENCY-STATE.json",
    "cph4/fleet/dispatcher/NEED-SUPPLY.md",
    "cph4/fleet/dispatcher/AUTOWORK.md",
    "cph4/fleet/dispatcher/ROUTED-WORK.jsonl",
    "cph4/fleet/dispatcher/events.jsonl",
    "cph4/fleet/social/DIGEST.md",
    "cph4/fleet/lanes/*.json",
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
    if rc3 != 0:
        # R2.60: git's refusal message is truncated to 240 chars and names only the first few
        # colliding paths, so a 22-file dirty tree looked like a 4-file problem and every shift
        # re-diagnosed it from scratch. Log the whole remaining set: whatever is here is either
        # work that exists nowhere else (resolve it) or machine state missing from GEN_STATE.
        rc_s, dirty = run_msg(["git", "status", "--porcelain"], 60)
        blocked = [ln[3:] for ln in dirty.split("|") if ln.strip()]
        note("blocking paths (%d): %s" % (len(blocked), ", ".join(blocked)[:900]))
    return rc3


def note(msg, fname="agent-pull.log"):
    """Evidence line; media/ is gitignored so this never dirties the tree."""
    try:
        d = os.path.join(ROOT, "media", "logs")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, fname), "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg))
    except Exception:
        pass


def push():
    """R2.59: the pull leg had no counterpart. Lane/night rounds commit work locally and it
    never left the box, so every `reset --mixed origin/main` closeout (R2.54/R2.56/R2.57)
    silently destroyed that work -- 4 night-round commits sat unpushed for 70 minutes on
    11-01 and were one closeout away from being lost.

    Safety: never force, and only push after a rebase has proven the branch is origin/main
    plus our commits (an append). A diverged tree that will not rebase is left alone and the
    skip is logged, so a broken worktree can never overwrite the master's history."""
    rc, tail = run_msg(["git", "push", "origin", "HEAD:main"], 300)
    if rc == 0:
        note("ok: %s" % tail, "agent-push.log")
        return 0
    # origin moved under us (the master pulses every minute): re-anchor and retry once.
    run_msg(["git", "fetch", "--quiet", "origin", "main"], 120)
    rc1, t1 = run_msg(["git", "rebase", "--no-autostash", "origin/main"], 180)
    if rc1 != 0:
        run_msg(["git", "rebase", "--abort"], 60)
        note("skip (rebase refused): %s" % t1, "agent-push.log")
        return rc1
    rc2, tail2 = run_msg(["git", "push", "origin", "HEAD:main"], 300)
    note("retry rc=%s %s" % (rc2, tail2), "agent-push.log")
    return rc2


def tick(node, do_push=False):
    rc_hb, t_hb = run([PY, "Tools/fleet/fleet_hb.py", "--node", node, "--root", ROOT], 120)
    rc_ln, t_ln = run([PY, "Tools/fleet/lane_agent.py", "--node", node, "--root", ROOT,
                       "--no-fetch"], 3600)
    t_ps = "-"
    if do_push:
        t_ps = "rc=%s" % push()
    print("agent %s hb=%s(%s) lane=%s(%s) push=%s" % (node, rc_hb, t_hb, rc_ln, t_ln, t_ps))
    return 0 if rc_hb == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--loop", type=int, default=0, help="0 = one tick; N = every N seconds")
    ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--push", action="store_true",
                    help="push locally authored commits after each tick (append-only; see push())")
    a = ap.parse_args()
    if not a.no_pull:
        pull()
    if not a.loop:
        return tick(a.node, a.push)
    while True:
        tick(a.node, a.push)
        time.sleep(a.loop)


if __name__ == "__main__":
    sys.exit(main())