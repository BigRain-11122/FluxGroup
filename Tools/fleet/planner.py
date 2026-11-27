#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""planner.py - the foreman: plan, assign, keep the machine loaded, verify output.

Lightweight by design: stdlib only, no LLM, one tick is a few file reads plus one
nvidia-smi call, and it never runs a long job itself. It writes a plan, requeues
stalled work whose root cause is provably gone, and only appends a new job to
PRODUCTION-BACKLOG.jsonl (the master's source) when the node is genuinely idle.
The lane executor stays the only thing that burns GPU time.

Duties
  1. SURVEY  capacity (GPU/RAM/lease) + inventory (lane file, backlog, queue, bank)
  2. PLAN    ranked next actions with reasons; written to cph4/fleet/plans/<node>-plan.json
  3. DISPATCH  append one safe job when idle >= threshold (rate limited, deduped)
  4. AUDIT   flag DONE rows whose deliverable is missing/stale (paper claims) and
             FAILED rows that are stubs or fixed-cause retries
  5. IDEA    one low-priority experiment per day from plans/ideas.json, so the
             machine keeps producing something new instead of replaying

Usage
  python Tools/fleet/planner.py --node bm-c --root K:\\Fluxgroup\\FluxGroup [--dry]
Exit code is always 0: a planner tick must never block the lane.
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from datetime import datetime

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
IDLE_MIN_FOR_DISPATCH = 10
DISPATCH_PER_HOUR = 2
RAM_FLOOR_GB = 3.0
GPU_FLOOR_MB = 3000


def now():
    return datetime.now()


def ts():
    return now().strftime("%Y-%m-%dT%H:%M:%S")


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return out


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def sh(args, timeout=20):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                           creationflags=CREATE_NO_WINDOW)
        return p.returncode, (p.stdout or "")
    except Exception:
        return 1, ""


def gpu_state(samples=3, gap_s=2.0):
    """Peak-sample utilisation: one 0% reading between frames is not idleness."""
    best = None
    for i in range(samples):
        rc, out = sh(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                      "--format=csv,noheader,nounits"])
        if rc == 0 and out.strip():
            parts = [p.strip() for p in out.splitlines()[0].split(",")]
            cur = {"util_pct": int(parts[0]), "used_mb": int(parts[1]), "total_mb": int(parts[2])}
            if best is None:
                best = cur
            else:
                best["util_pct"] = max(best["util_pct"], cur["util_pct"])
                best["used_mb"] = max(best["used_mb"], cur["used_mb"])
        if i + 1 < samples:
            time.sleep(gap_s)
    return best or {"util_pct": None, "used_mb": None, "total_mb": None}


class MEMSTATUS(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def ram_free_gb():
    try:
        st = MEMSTATUS()
        st.dwLength = ctypes.sizeof(MEMSTATUS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
        return round(st.ullAvailPhys / (1024.0 ** 3), 2)
    except Exception:
        return None


def newest_mtime(paths):
    best = 0.0
    for p in paths:
        if os.path.isfile(p):
            best = max(best, os.path.getmtime(p))
            continue
        if os.path.isdir(p):
            try:
                for root, _dirs, files in os.walk(p):
                    for name in files:
                        try:
                            best = max(best, os.path.getmtime(os.path.join(root, name)))
                        except OSError:
                            pass
            except OSError:
                pass
    return best


def paused(root):
    flag = os.path.join(os.path.dirname(root), ".codely-cli", "machine-state.flag")
    try:
        with open(flag, encoding="utf-8", errors="ignore") as f:
            return "paused" in f.read().lower()
    except Exception:
        return False


def node_capacity(node, gpu, ram, lease):
    lease_ours = False
    if lease and lease.get("node") == node:
        age = time.time() - float(lease.get("epoch") or 0)
        lease_ours = age < float(lease.get("ttl_s") or 7200)
    vram_free = None
    if gpu.get("used_mb") is not None and gpu.get("total_mb"):
        vram_free = gpu["total_mb"] - gpu["used_mb"]
    return {
        "gpu": gpu,
        "ram_free_gb": ram,
        "vram_free_mb": vram_free,
        "lease_held": lease_ours,
        "can_gpu": bool(vram_free is not None and vram_free >= GPU_FLOOR_MB
                        and ram is not None and ram >= RAM_FLOOR_GB),
        "can_cpu": bool(ram is not None and ram >= RAM_FLOOR_GB),
    }


def job_needs(job):
    return str(job.get("needs") or "cpu").lower()


def feasible(job, cap):
    if job_needs(job) == "gpu":
        return cap["can_gpu"]
    return cap["can_cpu"]


def score(job):
    prio = str(job.get("prio") or "P2").upper()
    weight = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(prio, 4)
    return (0 if job.get("heavy") else 1, weight, str(job.get("id")))


def build_plan(node, root, cap, lanes, backlog, queue, bank, idle_min):
    actions = []
    seen = set()

    def add(kind, job, reason):
        jid = str(job.get("id"))
        if jid in seen:
            return
        seen.add(jid)
        actions.append({"kind": kind, "id": jid,
                        "title": (job.get("title") or "")[:90],
                        "prio": job.get("prio"), "needs": job_needs(job),
                        "feasible": bool(feasible(job, cap)),
                        "reason": reason})

    for j in (lanes.get("jobs") or []):
        add("assigned", j, "master lane file (authority)")
    for j in backlog:
        if j.get("state") == "OPEN" and node in (j.get("nodes") or []):
            add("backlog", j, "OPEN in PRODUCTION-BACKLOG for this node")
    for j in queue:
        if j.get("state") in ("OPEN", "RUNNING") and node in (j.get("nodes") or []):
            add("queue", j, "queue row %s" % j.get("state"))
    for j in ((bank.get("jobs") or []) if isinstance(bank, dict) else []):
        if j.get("status") == "pending" and j.get("cmd"):
            add("bank", j, "work-bank pending (pre-hang law)")

    actions.sort(key=lambda a: (0 if a["kind"] == "assigned" else 1, a["feasible"] is False, a["prio"] or "P9"))
    return actions


def audit(node, root, queue):
    flags = []
    cutoff = time.time() - 24 * 3600
    for r in queue:
        if node not in (r.get("nodes") or []):
            continue
        st = str(r.get("state") or "").upper()
        res = r.get("result") or {}
        if st == "DONE":
            dl = r.get("deliverable")
            if dl:
                if not os.path.exists(dl):
                    flags.append({"id": r.get("id"), "kind": "paper-claim",
                                  "detail": "DONE but deliverable missing: %s" % dl})
                else:
                    try:
                        start = r.get("claimed_at") or r.get("assign_ts") or ""
                        start_ts = datetime.fromisoformat(start).timestamp() if start else 0
                        if start_ts and os.path.getmtime(dl) + 5 < start_ts:
                            flags.append({"id": r.get("id"), "kind": "stale-deliverable",
                                          "detail": "deliverable predates the run (file not produced by it)"})
                    except Exception:
                        pass
            if res.get("rc") not in (0, 2, None) and not res.get("note"):
                flags.append({"id": r.get("id"), "kind": "silent-failure",
                              "detail": "rc=%s with no explanation" % res.get("rc")})
        elif st == "FAILED":
            if not r.get("cmd"):
                flags.append({"id": r.get("id"), "kind": "stub",
                              "detail": "FAILED row with no cmd (authored stub, never runnable)"})
            else:
                rj = str(res.get("note") or "")
                if "self-lock" in rj or (res.get("rc") == 2 and float(res.get("seconds") or 0) < 2):
                    flags.append({"id": r.get("id"), "kind": "fast-fail-retry",
                                  "detail": "rc=2 in <2s: usually a lock/usage error, not real work failure"})
    return flags


def ideas(root):
    path = os.path.join(root, "cph4", "fleet", "plans", "ideas.json")
    data = read_json(path)
    if data is None:
        data = {"_law": "each idea: id/title/cmd/needs/why/requires; planner promotes at most one per 24h when idle",
                "ideas": [
                    {"id": "IDEA-LINE-TRIAGE", "title": "全线体检：证据陈旧与跨机路径误判扫描",
                     "cmd": "python Tools/fleet/line_triage.py --root .",
                     "needs": "cpu", "prio": "P3",
                     "requires": ["Tools/fleet/line_triage.py"],
                     "why": "把'这条线多久没产出'从印象变成证据，顺带抓 offnode 假缺口"},
                    {"id": "IDEA-PROMPT-BUDGET", "title": "提示词预算全库扫描",
                     "cmd": "python Tools/prompt_budget_check.py --selftest",
                     "needs": "cpu", "prio": "P3",
                     "requires": ["Tools/prompt_budget_check.py"],
                     "why": "超限提示词会让模型静默截断，属于看不见的质量损失"},
                    {"id": "IDEA-AUTOWORK", "title": "重复作业归因与回执日报",
                     "cmd": "python Tools/fleet/autowork.py --once",
                     "needs": "cpu", "prio": "P3",
                     "requires": ["Tools/fleet/autowork.py"],
                     "why": "把'为什么同一件事做了三遍'变成日报里的一行"},
                ]}
        write_json(path, data)
    return data


def dispatch_candidate(root, node, cap, actions, state, bank):
    """Return a job dict to append, or None. Never returns GPU work unless the
    GPU is actually free and the lane has nothing assigned."""
    now_epoch = time.time()
    recent = [t for t in (state.get("dispatched") or []) if now_epoch - t < 3600]
    if len(recent) >= DISPATCH_PER_HOUR:
        return None
    open_ids = {a["id"] for a in actions}
    bank_jobs = (bank.get("jobs") or []) if isinstance(bank, dict) else []
    for j in bank_jobs:
        if j.get("status") != "pending" or not j.get("cmd") or j.get("id") in open_ids:
            continue
        needs = "gpu" if any("python" in str(j.get("cmd")) for _ in [0]) and j.get("needs") == "gpu" else "cpu"
        needs = str(j.get("needs") or "cpu").lower()
        if needs == "gpu" and not cap["can_gpu"]:
            continue
        if needs == "cpu" and not cap["can_cpu"]:
            continue
        cmd = j["cmd"]
        cmd = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        return {"id": j.get("id"), "title": (j.get("title") or j.get("id"))[:90],
                "cmd": cmd, "needs": needs, "prio": "P2",
                "why": "planner pre-hang promotion: machine idle with no assigned work (%s)" % node,
                "deliverable": j.get("deliverable") or ""}
    # innovation slot: one per 24h
    last = float(state.get("last_idea_epoch") or 0)
    if now_epoch - last < 24 * 3600:
        return None
    used = set(state.get("ideas_used") or [])
    for idea in ideas(root)["ideas"]:
        if idea["id"] in used or idea["id"] in open_ids:
            continue
        if not all(os.path.exists(os.path.join(root, r)) for r in idea.get("requires") or []):
            continue
        if idea.get("needs") == "gpu" and not cap["can_gpu"]:
            continue
        return {"id": idea["id"], "title": idea["title"], "cmd": idea["cmd"],
                "needs": idea.get("needs", "cpu"), "prio": idea.get("prio", "P3"),
                "why": idea["why"], "deliverable": "", "is_idea": True}
    return None


def append_backlog(root, node, cand):
    path = os.path.join(root, "cph4", "fleet", "PRODUCTION-BACKLOG.jsonl")
    row = {
        "id": cand["id"], "title": cand["title"], "cmd": cand["cmd"],
        "cwd": root.replace("\\", "/"), "requires": [], "deliverable": cand.get("deliverable") or "",
        "needs": cand["needs"], "nodes": [node], "prio": cand["prio"], "day_ok": True,
        "heavy": False, "why": cand["why"], "created_by": "planner:%s" % node,
        "created_at": ts(), "state": "OPEN",
    }
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--assume-idle-min", type=float, default=None,
                    help="test hook: pretend the node has been idle this long")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    node = a.node
    plan_dir = os.path.join(root, "cph4", "fleet", "plans")
    os.makedirs(plan_dir, exist_ok=True)
    plan_path = os.path.join(plan_dir, "%s-plan.json" % node)
    state = read_json(plan_path) or {}

    if paused(root):
        state.update({"ts": ts(), "node": node, "paused": True,
                      "verdict": "PAUSED (CEO machine-state flag): planner stands down"})
        write_json(plan_path, state)
        print("PLANNER-PAUSED %s" % node)
        return 0

    gpu = gpu_state()
    ram = ram_free_gb()
    lease = read_json(os.path.join(root, "Tools", "nats", "data", "gpu.%s.lease.json" % node))
    cap = node_capacity(node, gpu, ram, lease)

    lane = read_json(os.path.join(root, "cph4", "fleet", "lanes", "%s.json" % node), {}) or {}
    backlog = read_jsonl(os.path.join(root, "cph4", "fleet", "PRODUCTION-BACKLOG.jsonl"))
    queue = read_jsonl(os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl"))
    bank = read_json(os.path.join(root, "cph4", "fleet", "work-bank", "%s-gpu-bank.json" % node), {}) or {}

    last_activity = newest_mtime([
        os.path.join(root, "cph4", "fleet", "queue-receipts"),
        os.path.join(root, "cph4", "fleet", "lanes"),
        os.path.join(root, "media", "mv-album-001-jay", "logs"),
    ])
    idle_min = round((time.time() - last_activity) / 60.0, 1) if last_activity else None
    if a.assume_idle_min is not None:
        idle_min = a.assume_idle_min

    actions = build_plan(node, root, cap, lane, backlog, queue, bank, idle_min)
    flags = audit(node, root, queue)

    verdict = "BUSY"
    dispatched = None
    gpu_busy = (gpu.get("util_pct") or 0) >= 20
    has_work = any(x["kind"] in ("assigned", "backlog", "queue") for x in actions)
    if not has_work and gpu_busy:
        verdict = "BURNING"
    elif not has_work and (idle_min is None or idle_min >= IDLE_MIN_FOR_DISPATCH):
        verdict = "IDLE"
        cand = dispatch_candidate(root, node, cap, actions, state, bank)
        if cand:
            if not a.dry:
                append_backlog(root, node, cand)
                state.setdefault("dispatched", []).append(time.time())
                if cand.get("is_idea"):
                    state["last_idea_epoch"] = time.time()
                    used = state.setdefault("ideas_used", [])
                    used.append(cand["id"])
                dispatched = cand["id"]
                verdict = "DISPATCHED"
            else:
                dispatched = "DRY:" + cand["id"]
    elif has_work and actions and not actions[0]["feasible"]:
        verdict = "BLOCKED-CAPACITY"

    state.update({
        "ts": ts(), "node": node, "paused": False, "verdict": verdict,
        "capacity": cap, "idle_min": idle_min,
        "assigned": [x for x in actions if x["kind"] == "assigned"],
        "next_actions": actions[:8], "flags": flags,
        "dispatched_now": dispatched,
        "counts": {"open_backlog": sum(1 for j in backlog if j.get("state") == "OPEN"),
                   "open_queue": sum(1 for j in queue if j.get("state") in ("OPEN", "RUNNING")),
                   "bank_pending": sum(1 for j in (bank.get("jobs") or []) if j.get("status") == "pending")},
    })
    write_json(plan_path, state)

    log = os.path.join(plan_dir, "planner.log")
    with open(log, "a", encoding="utf-8") as f:
        f.write("%s %s verdict=%s idle=%s gpu=%s/%sMB ram=%sGB open=%s disp=%s flags=%d\n" % (
            ts(), node, verdict, idle_min, gpu.get("util_pct"), gpu.get("used_mb"), ram,
            state["counts"]["open_backlog"] + state["counts"]["open_queue"], dispatched, len(flags)))
    print("PLANNER %s verdict=%s idle=%s dispatched=%s flags=%d" % (node, verdict, idle_min, dispatched, len(flags)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("PLANNER-ERROR %s" % e)
        sys.exit(0)