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


ap = argparse.ArgumentParser()
ap.add_argument("--node", required=True)
ap.add_argument("--needs", default="")
ap.add_argument("--dry", action="store_true")
ap.add_argument("--allow-gpu-workhours", action="store_true")
a = ap.parse_args()

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