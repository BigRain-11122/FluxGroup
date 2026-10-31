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


def pull():
    # Codes must arrive before the executor runs, otherwise the node keeps running the bug
    # we already fixed on the master. Never autostash (it swallowed hand edits once).
    run(["git", "pull", "--rebase", "--no-autostash", "origin", "main"], 120)


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