# -*- coding: utf-8 -*-
"""queue_claim.py - the self-serving work loop the fleet was missing.

Problem it fixes: the machines had hundreds of "Ready" supervision tasks but no queue of
actual production work, so a free GPU had nothing to claim. This script is the claim side:
take the next OPEN job from the production queue, run its command, write a receipt, mark it
DONE or FAILED. Any machine can run it; whoever is idle claims first.

2026-10-27 hardening (CEO: idling must never look healthy):
  - always writes _last_claim.json (QUEUE-EMPTY included) so the dispatcher can flag
    SUPPLY-DRY instead of trusting a silent exit 0
  - bm-a refuses GPU jobs during the CEO work-hour yield (09:00-19:00) unless
    --allow-gpu-workhours is passed

Queue file: cph4/fleet/PRODUCTION-QUEUE.jsonl (append-only, one JSON object per line)
Job fields: id, title, cmd, cwd, needs (gpu|cpu), deliverable, state

Usage:
  py queue_claim.py --node bm-a [--needs gpu] [--dry] [--allow-gpu-workhours]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
RECEIPT_DIR = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
LAST = os.path.join(RECEIPT_DIR, "_last_claim.json")


def load():
    if not os.path.exists(QUEUE):
        return []
    rows = []
    with open(QUEUE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save(rows):
    tmp = QUEUE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, QUEUE)


def write_last(state, **kw):
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    rec = {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "state": state}
    rec.update(kw)
    with open(LAST, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)


# ---- dispatcher POOL cards (bm-b r1186, OB-20261027-182254-574) --------------
# Why this exists: queue_claim only knew cph4/fleet/PRODUCTION-QUEUE.jsonl, so the
# numbered cards in cph4/fleet/dispatcher/POOL.json were structurally unclaimable by
# any machine - POOL-0018/0019 sat RE-OFFERED for 8 days with no claim task anywhere.
# Law boundary: POOL.json state transitions are written by the dispatcher-proxy seat,
# not by nodes. So this mode NEVER edits POOL.json; it emits a claim INTENT receipt
# the proxy consumes (that is what clears blocked_by=no-claim-task:<node>).
POOL_REL = "cph4/fleet/dispatcher/POOL.json"
POOL_JSON = os.path.join(ROOT, *POOL_REL.split("/"))
POOL_PRIO = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _pool_source():
    """Pool face + where it came from (origin blob is fresh by construction)."""
    try:
        sha = subprocess.run(["git", "-C", ROOT, "rev-parse", "origin/main"],
                             capture_output=True, text=True, timeout=30)
        if sha.returncode == 0:
            blob = subprocess.run(["git", "-C", ROOT, "show", "origin/main:" + POOL_REL],
                                  capture_output=True, timeout=60)
            if blob.returncode == 0 and blob.stdout.strip():
                return (json.loads(blob.stdout.decode("utf-8")),
                        {"face": "origin", "origin_sha": sha.stdout.strip()})
    except Exception:
        pass
    with open(POOL_JSON, encoding="utf-8") as f:
        return json.load(f), {"face": "worktree", "origin_sha": None}


CLAIM_CLEARS = "no-claim-task:"   # this tool's intent receipt is exactly what clears it


def _pool_gate(card, node):
    """(claimable, blockers). A card blocked by anything other than 'no claim task on
    this node' is not ours to claim - that block names a different fix (a receipt, a
    physical part, another lane), and claiming it would bury the real blocker."""
    blockers = [str(b) for b in (card.get("blocked_by") or []) if str(b).strip()]
    foreign = [b for b in blockers if b != CLAIM_CLEARS + node]
    return (not foreign), (foreign or blockers)


def _pick_pool(cards, node):
    """OPEN, unblocked cards for this lane, priority then id. Pure - selftest covers it."""
    mine = [c for c in cards
            if str(c.get("lane") or "").strip() == node
            and str(c.get("status") or "").strip().lower() == "open"
            and _pool_gate(c, node)[0]]
    mine.sort(key=lambda c: (POOL_PRIO.get(str(c.get("priority") or "").upper(), 9),
                             str(c.get("id"))))
    return mine


def run_pool(a):
    try:
        cards, src = _pool_source()
    except Exception as e:
        write_last("POOL-UNAVAILABLE", node=a.node, error=str(e)[:300])
        print("POOL-UNAVAILABLE:", e)
        return 2
    if not isinstance(cards, list):
        write_last("POOL-UNAVAILABLE", node=a.node, error="pool face is not a list")
        print("POOL-UNAVAILABLE: pool face shape")
        return 2
    mine = _pick_pool(cards, a.node)
    if a.pool_list:
        for c in mine:
            print("%-10s %-3s %s" % (c.get("id"), c.get("priority"), str(c.get("title"))[:80]))
        print("POOL-OPEN %d node=%s face=%s" % (len(mine), a.node, src["face"]))
        return 0
    if not mine:
        held = [{"id": c.get("id"), "blocked_by": _pool_gate(c, a.node)[1]}
                for c in cards
                if str(c.get("lane") or "").strip() == a.node
                and str(c.get("status") or "").strip().lower() == "open"]
        write_last("POOL-EMPTY", node=a.node, face=src["face"], blocked=held)
        print("POOL-EMPTY node=%s face=%s blocked=%s" % (a.node, src["face"], held))
        return 0
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    for c in mine[:1]:
        cid = str(c.get("id"))
        rc_f = os.path.join(RECEIPT_DIR, "%s-%s.json" % (cid, a.node))
        prev = None
        if os.path.exists(rc_f):
            try:
                with open(rc_f, encoding="utf-8") as f:
                    prev = json.load(f)
            except Exception:
                prev = None
        if prev and prev.get("first_ts") and not a.pool_republish:
            prev["last_seen_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            prev["seen_count"] = int(prev.get("seen_count") or 1) + 1
            prev["face"] = src["face"]
            prev["origin_sha"] = src["origin_sha"]
            with open(rc_f, "w", encoding="utf-8") as f:
                json.dump(prev, f, ensure_ascii=False, indent=1)
            write_last("POOL-CLAIMED", node=a.node, id=cid, face=src["face"],
                       seen_count=prev["seen_count"])
            print("POOL-ALREADY-CLAIMED %s (intent from %s, seen %d)"
                  % (cid, prev["first_ts"], prev["seen_count"]))
            return 0
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        rec = {"card": cid, "node": a.node, "action": "claimed", "kind": "claim-intent",
               "lane": c.get("lane"), "priority": c.get("priority"), "title": c.get("title"),
               "first_ts": now, "last_seen_ts": now, "seen_count": 1,
               "face": src["face"], "origin_sha": src["origin_sha"],
               "note": ("claim INTENT only - POOL.json transitions are proxy-written (pool law). "
                        "Dispatcher clears blocked_by on this receipt; the lane executes the card "
                        "and reports done with this card id + evidence pointer.")}
        with open(rc_f, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
        write_last("POOL-CLAIMED", node=a.node, id=cid, face=src["face"])
        print("POOL-CLAIM %s %s :: %s" % (cid, c.get("priority"), str(c.get("title"))[:70]))
        print("receipt:", os.path.relpath(rc_f, ROOT))
    return 0


def pool_selftest():
    cards = [
        {"id": "POOL-9002", "lane": "bm-b", "status": "open", "priority": "P1"},
        {"id": "POOL-9001", "lane": "bm-b", "status": "open", "priority": "P1"},
        {"id": "POOL-9000", "lane": "bm-b", "status": "open", "priority": "P0"},
        {"id": "POOL-9003", "lane": "bm-c", "status": "open", "priority": "P0"},
        {"id": "POOL-9004", "lane": "bm-b", "status": "claimed", "priority": "P0"},
        {"id": "POOL-9005", "lane": "bm-b", "status": "OPEN", "priority": "P2"},
        {"id": "POOL-9006", "lane": "bm-b", "status": "open", "priority": "P1",
         "blocked_by": ["no-claim-task:bm-b"]},
        {"id": "POOL-9007", "lane": "bm-b", "status": "open", "priority": "P0",
         "blocked_by": ["receipt-owed"]},
        {"id": "POOL-9008", "lane": "bm-b", "status": "open", "priority": "P0",
         "blocked_by": ["no-claim-task:bm-c"]},
    ]
    got = [c["id"] for c in _pick_pool(cards, "bm-b")]
    legs = [
        ("lane filter drops other nodes", got == ["POOL-9000", "POOL-9001", "POOL-9002",
                                                   "POOL-9006", "POOL-9005"]),
        ("a foreign block (receipt-owed) holds the card", "POOL-9007" not in got),
        ("another node's no-claim-task block is not ours", "POOL-9008" not in got),
        ("this node's no-claim-task block stays claimable", "POOL-9006" in got),
        ("foreign block wins over a clearable one", _pool_gate(
            {"blocked_by": ["receipt-owed", "no-claim-task:bm-b"]}, "bm-b") == (
                False, ["receipt-owed"])),
        ("claimed card is not claimable", "POOL-9004" not in got),
        ("status match is case-insensitive", "POOL-9005" in got),
        ("priority order P0 before P1", got[0] == "POOL-9000"),
        ("unknown priority sorts last", _pick_pool([{"id": "x", "lane": "bm-b", "status": "open",
                                                   "priority": "P9"},
                                                   {"id": "y", "lane": "bm-b", "status": "open",
                                                    "priority": "P2"}], "bm-b")[0]["id"] == "y"),
    ]
    bad = [n for n, ok in legs if not ok]
    print("pool selftest %d/%d %s" % (len(legs) - len(bad), len(legs),
                                     "PASS" if not bad else "FAIL: " + ", ".join(bad)))
    return 0 if not bad else 1


ap = argparse.ArgumentParser()
ap.add_argument("--node", required=True)
ap.add_argument("--needs", default="")
ap.add_argument("--dry", action="store_true")
ap.add_argument("--allow-gpu-workhours", action="store_true")
ap.add_argument("--pool", action="store_true",
                help="emit a claim-intent receipt for an OPEN dispatcher POOL card in this node lane")
ap.add_argument("--pool-list", action="store_true", help="list claimable POOL cards and exit")
ap.add_argument("--pool-republish", action="store_true",
                help="re-emit an existing intent receipt instead of only bumping last_seen")
ap.add_argument("--pool-selftest", action="store_true", help="offline selftest of the pool picker")
a = ap.parse_args()
if a.pool_selftest:
    sys.exit(pool_selftest())

if a.pool or a.pool_list:
    sys.exit(run_pool(a))


rows = load()
hour = datetime.now().hour
weekday = datetime.now().weekday() < 5
# CEO work-hour yield on bm-a: GPU production is off 09:00-19:00 on weekdays.
gpu_blocked = (a.node == "bm-a" and weekday and 9 <= hour < 19 and not a.allow_gpu_workhours)

def pick(candidates):
    skipped = 0
    for r in candidates:
        if r.get("state") != "OPEN":
            continue
        if a.needs and r.get("needs") and r["needs"] != a.needs:
            continue
        if gpu_blocked and r.get("needs") == "gpu":
            skipped += 1
            continue
        return r, skipped
    return None, skipped


job, skipped_gpu = pick(rows)
if job is None:
    # Self-refill: enqueue only jobs whose inputs already exist on this machine.
    try:
        from backlog_fill import fill as fill_backlog
        if fill_backlog(ROOT) > 0:
            rows = load()
            job, skipped_gpu = pick(rows)
    except Exception as e:
        print("backlog_fill skipped:", e)

if not job:
    note = "QUEUE-EMPTY (no OPEN job%s)" % (" for " + a.needs if a.needs else "")
    if skipped_gpu:
        note += " [gpu jobs skipped: %d, bm-a work-hour yield]" % skipped_gpu
    write_last("QUEUE-EMPTY", node=a.node, needs=a.needs, skipped_gpu=skipped_gpu)
    print(note)
    sys.exit(0)

print("CLAIM %s :: %s" % (job["id"], job["title"]), flush=True)
if a.dry:
    print("cmd:", job.get("cmd"))
    sys.exit(0)

job["state"] = "RUNNING"
job["owner"] = a.node
job["claimed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
save(rows)
write_last("RUNNING", node=a.node, needs=a.needs, id=job["id"])

t0 = time.time()
r = subprocess.run(job["cmd"], shell=True, cwd=job.get("cwd") or ROOT,
                   capture_output=True, text=True, errors="replace")
dur = time.time() - t0

os.makedirs(RECEIPT_DIR, exist_ok=True)
receipt = os.path.join(RECEIPT_DIR, "%s-%s.json" % (job["id"], a.node))
ok = r.returncode == 0
with open(receipt, "w", encoding="utf-8") as f:
    json.dump({"id": job["id"], "node": a.node, "rc": r.returncode, "seconds": round(dur, 1),
               "cmd": job["cmd"], "stdout_tail": r.stdout[-2000:], "stderr_tail": r.stderr[-2000:]},
              f, ensure_ascii=False, indent=1)

rows = load()
for x in rows:
    if x["id"] == job["id"]:
        x["state"] = "DONE" if ok else "FAILED"
        x["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        x["receipt"] = os.path.relpath(receipt, ROOT)
save(rows)
write_last("DONE" if ok else "FAILED", node=a.node, needs=a.needs, id=job["id"],
           rc=r.returncode, seconds=round(dur, 1))
print("%s %s (%.1fs) receipt=%s" % (job["id"], "DONE" if ok else "FAILED", dur, receipt))
if not ok:
    print((r.stderr or r.stdout)[-800:])
    sys.exit(1)