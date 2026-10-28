# -*- coding: utf-8 -*-
"""pool_lint.py - POOL.json supply-truth gate (dispatcher seat).

Why this exists (2026-10-29, 8th consecutive SUPPLY-DRY round):
  The dispatcher counted "5 open POOL cards" as available supply for eight rounds while
  every one of them was unexecutable. A POOL card is a prose spec, not a job: queue_claim.py
  --pool can only emit a claim INTENT, so the same intent was re-emitted 252 times over 21h
  and nothing ran. Counting open cards as supply is the defect; a card is not work.

Law this gate enforces (one line):
  An OPEN card must either name an executable job that actually exists in
  PRODUCTION-QUEUE.jsonl / PRODUCTION-BACKLOG.jsonl (`job_ref`), or carry a typed
  `blocked_by` naming who unblocks it. An open card that is neither is PHANTOM SUPPLY
  and fails this gate.

Recognised blocker prefixes (extend here only when a new unblock owner appears):
  CEO-PHYSICAL:     physical/desk action only the CEO can take (register only, zero-nag)
  no-exec-leg:      structural: no command for this card exists anywhere in the repo
  no-verified-cmd:  the command exists only on another host and is not in git
  receipt-owed:     work executed, evidence receipt still missing
  director-         waits on a judgment seat (director-signoff / director-review ...)
  depends:          waits on another card id

Usage:
  python Tools/pool_lint.py [--pool PATH] [--verbose] [--machine]
Exit: 0 PASS / 1 FAIL phantom supply (or unresolvable job_ref) / 2 read error
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_POOL = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "POOL.json")
QUEUE = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-BACKLOG.jsonl")
OPEN_STATES = ("open",)
TYPED = ("CEO-PHYSICAL:", "no-exec-leg:", "no-verified-cmd:", "receipt-owed", "director", "depends:")


def _ids(path):
    out = set()
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("id"):
                out.add(str(row["id"]))
    return out


def _blocker_type(b):
    for t in TYPED:
        if str(b).startswith(t):
            return t
    return None


def lint(pool_path):
    with open(pool_path, encoding="utf-8") as f:
        cards = json.load(f)
    if not isinstance(cards, list):
        return None, ["pool face is not a list"]

    known_jobs = _ids(QUEUE) | _ids(BACKLOG)
    problems = []
    open_cards = [c for c in cards if str(c.get("status") or "").strip().lower() in OPEN_STATES]

    for c in open_cards:
        cid = c.get("id")
        blockers = [str(b) for b in (c.get("blocked_by") or []) if str(b).strip()]
        job_ref = str(c.get("job_ref") or c.get("job_id") or "").strip()
        if job_ref:
            if job_ref not in known_jobs:
                problems.append("%s: job_ref '%s' not found in PRODUCTION-QUEUE/BACKLOG "
                                "(a card pointing at a job that does not exist is still phantom)"
                                % (cid, job_ref))
            continue
        if not blockers:
            problems.append("%s: OPEN with no blocked_by and no job_ref = PHANTOM SUPPLY "
                            "(prose spec is not a job; materialize it or name the blocker)" % cid)
            continue
        for b in blockers:
            if _blocker_type(b) is None:
                problems.append("%s: blocker '%s' has no recognised owner prefix %s"
                                % (cid, b, list(TYPED)))

    return {"cards": len(cards), "open": open_cards, "known_jobs": len(known_jobs)}, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default=DEFAULT_POOL)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--machine", action="store_true",
                    help="one-line summary suitable for the dispatcher LOG")
    a = ap.parse_args()

    try:
        stat, problems = lint(a.pool)
    except Exception as e:
        print("POOL-LINT ERROR:", e)
        return 2
    if stat is None:
        print("POOL-LINT ERROR:", "; ".join(problems))
        return 2

    lanes = {}
    for c in stat["open"]:
        lanes[str(c.get("lane"))] = lanes.get(str(c.get("lane")), 0) + 1
    lane_s = ",".join("%s=%d" % (k, v) for k, v in sorted(lanes.items())) or "none"

    if a.machine:
        print("POOL-LINT %s open=%d lanes=%s phantom=%d"
              % ("PASS" if not problems else "FAIL", len(stat["open"]), lane_s, len(problems)))
    else:
        print("POOL-LINT %s  cards=%d open=%d (%s)  jobs-resolvable=%d"
              % ("PASS" if not problems else "FAIL", stat["cards"], len(stat["open"]),
                 lane_s, stat["known_jobs"]))
        if a.verbose:
            for c in stat["open"]:
                print("  %-10s %-5s %-6s blocked_by=%s job_ref=%s"
                      % (c.get("id"), c.get("lane"), c.get("priority"),
                         c.get("blocked_by") or [], c.get("job_ref") or c.get("job_id") or "-"))
    for p in problems:
        print("  PHANTOM/INVALID:", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())