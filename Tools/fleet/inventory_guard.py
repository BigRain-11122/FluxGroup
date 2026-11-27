# -*- coding: utf-8 -*-
"""inventory_guard.py - the "no machine may sit idle" gate (bm-m master).

Root cause it closes (2026-10-30): supply, promotion and claiming each broke silently at
different times, and nothing ever cross-checked the RESULT: a node can be online, healthy
and starved at the same way. This guard measures the only thing that matters -- how much
runnable work each node actually has -- and escalates until it is fixed.

Rule (CEO O-20261030 满负荷令): every active node keeps MIN_STOCK runnable cards in its
own lane at all times. Daytime on bm-a is the ONE sanctioned exception (CEO's work box:
only day_ok cards, heavy waits for the 19:00 window).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_lane as fl

MIN_STOCK = 2
LOG = "/tmp/inventory-guard.log"
BACKLOG_REL = "cph4/fleet/PRODUCTION-BACKLOG.jsonl"


def now_iso():
    return fl.now_iso()


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]
    except Exception:
        return []


def stock(root, node, when=None):
    """Runnable cards for this node right now (lane jobs + OPEN queue rows)."""
    have = {}
    lane = os.path.join(root, "cph4/fleet/lanes", "%s.json" % node)
    try:
        with open(lane, encoding="utf-8") as f:
            lj = (json.load(f) or {}).get("jobs") or []
    except Exception:
        lj = []
    for j in lj:
        have[j.get("id")] = j
    for r in _read(os.path.join(root, fl.QUEUE_REL.replace("/", os.sep))):
        if r.get("state") not in ("OPEN", "RUNNING"):
            continue
        nodes = r.get("nodes") or []
        if nodes and node not in nodes:
            continue
        if r.get("heavy") and not fl.heavy_allowed(node, when):
            continue
        if (r.get("needs") == "gpu") and not fl.gpu_window_open(node, when) \
           and not (when and when.weekday() >= 5):
            continue
        if fl.quiet_hours(node, when) and not r.get("day_ok"):
            continue
        have[r.get("id")] = r
    return len(have), sorted(have)


def refill(root, node, need):
    """Auto-make-up supply: promote READY backlog cards for this node (master duty)."""
    try:
        import backlog_fill
        return backlog_fill.fill(root)
    except Exception as e:
        return "fill_err:%s" % str(e)[:60]


def main():
    root = fl.ROOT_DEFAULT
    from datetime import datetime
    when = datetime.now()
    lines, alerts = [], []
    for node in fl.ACTIVE_LANES:
        spec = fl.LANES.get(node) or {}
        if not spec.get("enabled"):
            continue
        n, ids = stock(root, node, when)
        lines.append("%s stock=%d %s" % (node, n, ids[:3]))
        q = fl.quiet_hours(node, when)
        if n < MIN_STOCK:
            added = refill(root, node, MIN_STOCK - n)
            n2, ids2 = stock(root, node, when)
            if q is not None and n2 == 0:
                # sanctioned exception: CEO's work box yields daytime CPU to the CEO
                lines.append("%s DAY-YIELD ok (night-only, %02d:00-%02d:00; %d cards waiting)"
                             % (node, q[0], q[1],
                                sum(1 for r in _read(os.path.join(root, fl.QUEUE_REL.replace("/", os.sep)))
                                    if (r.get("nodes") or []) == [node] and r.get("state") == "OPEN")))
                continue
            tag = "STARVED" if n2 == 0 else "LOW"
            alerts.append("%s %s (had %d, refilled->%s +%s)" % (node, tag, n, n2, added))
            lines.append("%s after-refill=%d" % (node, n2))
    msg = "[%s] %s%s" % (now_iso(), " | ".join(lines),
                         ("  !! " + " ;; ".join(alerts)) if alerts else "  (all stocked)")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)
    return 1 if alerts else 0


if __name__ == "__main__":
    sys.exit(main())
