#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_board.py - one-screen fleet state for the master-control node (stdlib only).

Reads the files the L0 tools already write; no probes, no LLM, no network.
Shows per-lane open/executable/blocked/idle, production queue, clock offsets and flags.
Exit 0 always (a board is a deliverable, not a gate).
"""
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    d = os.path.join(ROOT, "cph4", "fleet", "dispatcher")
    state = load(os.path.join(d, "STATE.json"), {})
    clock = load(os.path.join(d, "CLOCK-SKEW.json"), {})
    pool = load(os.path.join(d, "POOL.json"), [])
    queue = []
    qf = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    try:
        with open(qf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    queue.append(json.loads(line))
    except Exception:
        pass

    print("FLEET BOARD", datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("%-6s %5s %5s %8s  %s" % ("lane", "open", "exec", "blocked", "idle"))
    lanes = state.get("lanes", {})
    if lanes:
        for lane in ("bm-a", "bm-b", "bm-c", "bm-m"):
            v = lanes.get(lane)
            if not v:
                continue
            print("%-6s %5s %5s %8s  %s" % (lane, v.get("open", "-"), v.get("exec", "-"),
                                            v.get("blocked", "-"), v.get("idle", "-")))
    else:
        # Standalone fallback: the Mac master may not run the Windows dispatcher yet.
        status = {c.get("id"): c.get("status") for c in pool}
        counts = {k: {"open": 0, "exec": 0, "blocked": 0} for k in ("bm-a", "bm-b", "bm-c", "bm-m")}
        for c in pool:
            if c.get("status") != "open":
                continue
            lane = c.get("lane") or "bm-a"
            if lane not in counts:
                lane = "bm-a"
            counts[lane]["open"] += 1
            why = ""
            for dep in c.get("depends_on", []) or []:
                if status.get(dep) not in ("done", "closed-superseded", "closed-stale"):
                    why = "dep"
                    break
            if not why and c.get("blocked_by"):
                why = "blocked_by"
            if not why and c.get("deadline"):
                try:
                    if datetime.strptime(c["deadline"][:19], "%Y-%m-%dT%H:%M:%S") < datetime.now():
                        why = "expired"
                except Exception:
                    pass
            if why:
                counts[lane]["blocked"] += 1
            else:
                counts[lane]["exec"] += 1
        for lane in ("bm-a", "bm-b", "bm-c", "bm-m"):
            v = counts[lane]
            if v["open"] == 0:
                continue
            print("%-6s %5d %5d %8d  %s" % (lane, v["open"], v["exec"], v["blocked"], "computed-no-idle"))

    q = state.get("queue", {})
    if not q and queue:
        q = {"total": len(queue), "open": sum(1 for x in queue if x.get("state") == "OPEN"),
             "running": sum(1 for x in queue if x.get("state") == "RUNNING")}
    print("\nQUEUE total=%s open=%s running=%s last=%s" % (
        q.get("total", "?"), q.get("open", "?"), q.get("running", "?"), q.get("last_claim", "")))

    nodes = clock.get("nodes", []) if isinstance(clock, dict) else []
    if nodes:
        print("\nCLOCK max_abs_offset=%sms old_schema=%s missing=%s" % (
            clock.get("max_abs_offset_ms"), clock.get("old_schema"), clock.get("missing")))
        for n in nodes:
            print("  %-5s %-14s offset=%s precision=%s seq=%s" % (
                n.get("node"), n.get("status"), n.get("offset_ms"), n.get("precision_ms"), n.get("seq")))
    print("\nPOOL cards=%d open=%d" % (len(pool), sum(1 for c in pool if c.get("status") == "open")))
    return 0


if __name__ == "__main__":
    sys.exit(main())