#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""steward.py - ONE task per node that does the whole loop, no second opinion.

Why: by 2026-10-31 a node needed three scheduled tasks (heartbeat, claim, fallback
scheduler) and each had its own failure mode - the night the executor died while the
heartbeat stayed fresh, the control plane believed the machine was fine. This wrapper
runs the existing, already-verified parts in one process chain and writes one line:

    agent.py          pull -> heartbeat -> claim -> run -> receipt   (executor)
    master_agent.py   only when the declared master's tick is stale  (scheduling fallback)
    fleet_supervisor  refresh SUPERVISOR.md                          (supervision page)

It adds no scheduling logic of its own: a second scheduler would be a second truth.

Usage:  python Tools/fleet/steward.py --node bm-a
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
D = os.path.join(ROOT, "cph4", "fleet", "dispatcher")
TICK = os.path.join(D, "MASTER-TICK.json")
LOG = os.path.join(D, "STEWARD-LOG.md")
PY = sys.executable
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def run(script, args, timeout=3600):
    try:
        p = subprocess.run([PY, os.path.join(HERE, script)] + args, cwd=ROOT,
                           capture_output=True, text=True, errors="replace", timeout=timeout,
                           creationflags=CREATE_NO_WINDOW)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as e:  # never let one leg kill the loop
        return 1, "", str(e)[:200]


def master_stale(limit_s=900):
    try:
        with open(TICK, encoding="utf-8") as f:
            t = json.load(f)
        age = (datetime.now() - datetime.strptime(t.get("ts", ""), "%Y-%m-%dT%H:%M:%S")).total_seconds()
        return age > limit_s, age
    except Exception:
        return True, None


def note(line):
    os.makedirs(D, exist_ok=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), line))
        with open(LOG, encoding="utf-8") as f:
            rows = f.readlines()
        if len(rows) > 2000:
            with open(LOG, "w", encoding="utf-8") as f:
                f.writelines(rows[-2000:])
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default="bm-a")
    ap.add_argument("--no-schedule", action="store_true",
                    help="executor only; never take over scheduling")
    a = ap.parse_args()

    rc_agent, out_agent, err_agent = run("agent.py", ["--node", a.node], timeout=5400)
    stale, age = master_stale()
    rc_master, out_master = 0, ""
    if stale and not a.no_schedule:
        rc_master, out_master, _ = run("master_agent.py", ["--node", a.node], timeout=900)
    rc_sup, _, _ = run("fleet_supervisor.py", [], timeout=300)

    first = (out_agent.splitlines() or ["(no output)"])[0][:110]
    sched = ("stale=%.0fs take-over" % age) if (stale and not a.no_schedule) else "master-fresh"
    line = "agent=%d sup=%d %s :: %s" % (rc_agent, rc_sup, sched, first)
    note(line)
    print("STEWARD", line)
    return 0 if rc_agent == 0 else 0   # a failed job is reported, not a failed loop


if __name__ == "__main__":
    sys.exit(main())