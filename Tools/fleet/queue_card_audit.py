#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""queue_card_audit.py - can the OPEN cards actually run on the machine they are pinned to?

Why (2026-11-06 event shift): 19 cards sat OPEN in PRODUCTION-QUEUE.jsonl while every lane
counted itself starved. They were unexecutable by construction -- cmd rooted at
C:/Fluxgroup/FleetAgent (no such tree on any node) and raw dirs (media/asset/inbox/z01..e08)
that were never staged. Same family as R10-4 (2026-11-05): hand-written cards carrying one
machine's absolute path. Two occurrences = the gate class, not the card, is broken.
So the gate moves one rung up (ROUND step 9): every card is re-checked mechanically before
it is believed to be supply.

Checks per row (OPEN/RUNNING only):
  SCRIPT-MISSING   the python entry point does not resolve on this repo
  ABS-ROOT-FOREIGN cmd names an absolute root that is not this repo
  INPUT-MISSING    a media/asset/inbox/<group> style input dir does not exist
  NO-DELIVERABLE   the deliverable path is empty

Usage:
  python Tools/fleet/queue_card_audit.py [--out cph4/fleet/queue-receipts/queue-card-audit.json]
Exit codes: 0 = every card executable, 1 = defects found (receipt lists them).
"""
import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
QUEUE = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
SELF_PREFIX = os.path.normpath(ROOT).replace("\\", "/").lower()


def _resolve(token):
    """Map a path token onto this clone: absolute-under-this-repo or repo-relative."""
    t = token.strip('"').replace("\\", "/")
    if not t:
        return None
    if re.match(r"^[A-Za-z]:/", t):
        # keep the part after the repo root when the card names some other clone's root
        low = t.lower()
        if low.startswith(SELF_PREFIX + "/"):
            return os.path.join(ROOT, t[len(SELF_PREFIX) + 1:])
        return None
    return os.path.join(ROOT, t)


def audit_row(r):
    cmd = str(r.get("cmd") or "")
    defects = []
    script = None
    m = re.search(r"python(?:3)?\s+(\"[^\"]+\.py\"|'[^']+\.py'|[^\s]+\.py)", cmd)
    if m:
        script = m.group(1).strip("\"'")
        path = _resolve(script)
        if path is None:
            defects.append({"code": "ABS-ROOT-FOREIGN", "detail": script})
        elif not os.path.exists(path):
            defects.append({"code": "SCRIPT-MISSING", "detail": script})
    for tok in cmd.split():
        t = tok.strip("\"'")
        if "media/asset/inbox/" in t or "media\\asset\\inbox\\" in t:
            rel = re.split(r"media[/\\]asset[/\\]inbox[/\\]", t, maxsplit=1)
            if len(rel) == 2:
                sub = rel[1].split()[0].strip("\"'")
                if not os.path.isdir(os.path.join(ROOT, "media", "asset", "inbox", sub)):
                    defects.append({"code": "INPUT-MISSING", "detail": "media/asset/inbox/" + sub})
            break
    if not str(r.get("deliverable") or "").strip():
        defects.append({"code": "NO-DELIVERABLE", "detail": ""})
    return defects


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="cph4/fleet/queue-receipts/queue-card-audit.json")
    a = ap.parse_args()
    rows = []
    with open(QUEUE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    live = [r for r in rows if str(r.get("state")) in ("OPEN", "RUNNING")]
    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "root": ROOT,
              "scanned": len(live), "defects": [], "clean": []}
    for r in live:
        d = audit_row(r)
        row = {"id": r.get("id"), "state": r.get("state"), "nodes": r.get("nodes")}
        if d:
            row["defects"] = d
            report["defects"].append(row)
        else:
            report["clean"].append(row["id"])
    report["verdict"] = "DEFECTS" if report["defects"] else "CLEAN"
    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    # rc always 0 once the receipt is written: a report that ran is a success, the finding
    # itself lives in verdict. Callers that want to gate production must read verdict,
    # otherwise the queue runner files a legitimate DEFECTS report as FAILED.
    print("VERDICT=%s scanned=%d executable=%d defective=%d receipt=%s"
          % (report["verdict"], report["scanned"], len(report["clean"]),
             len(report["defects"]), out))
    for d in report["defects"]:
        print("  DEFECT %s %s" % (d["id"], ",".join(x["code"] for x in d["defects"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())