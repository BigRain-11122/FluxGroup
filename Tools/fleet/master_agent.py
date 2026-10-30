#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""master_agent.py - the scheduler that decides, the lanes only execute.

Why: through 2026-10-28 every review ended on the same defect - the fleet had heartbeats
and a queue, but nothing owned the loop, so "no open job" was reported as normal and every
machine sat at 0% while the log looked healthy. This agent owns five decisions per cycle:

  1. SUPPLY   - turn real, already-declared work into queue jobs (deterministic rules +
                the backlog manifest; nothing invented, nothing launched blind)
  2. ROUTE    - local first, cloud only when a job declares a cloud leg and the cost gate
                allows it (>500 credits = CEO confirmation, never inferred)
  3. ASSIGN   - one job per lane, chosen by need + live capacity + work-hour yield
  4. SUPERVISE- lease expiry, silent deaths, receipts without deliverables, requeue
  5. REPORT   - a machine-readable state that says WHY a lane is idle, so idle can never
                look like health

Single-writer: only this process mutates PRODUCTION-QUEUE.jsonl and cph4/fleet/lanes/*.json.
Nodes report results over NATS KV; the master folds them back in. That removes the clone
divergence that made cross-machine claiming unsafe.

Usage:
  python master_agent.py [--root PATH] [--once] [--dry] [--no-push]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fleet_lane as fl  # noqa: E402

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
DEFAULT_LEASE = {"cpu": 45, "gpu": 180, "cloud": 60}
OFFLINE_AFTER_S = 900
MAX_ATTEMPTS = 3


# ---------------------------------------------------------------- sensing
def kv_get(key, root, host=fl.HUB_DEFAULT, port=fl.PORT_DEFAULT):
    """Live node state. Pure-python first so the Mac (no nats.exe) can run the master too;
    the Windows CLI is kept as a fallback for boxes that already rely on it."""
    got = fl.kv_get(key, host, port)
    if got is not None:
        return got
    exe = os.path.join(root, "Tools", "nats", "bin", "nats.exe")
    if not os.path.exists(exe):
        return None
    try:
        p = subprocess.run([exe, "-s", "nats://%s:%d" % (host, port), "kv", "get",
                            fl.KV_BUCKET, key, "--raw"],
                           capture_output=True, text=True, timeout=15,
                           creationflags=CREATE_NO_WINDOW)
        for line in reversed((p.stdout or "").splitlines()):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
    except Exception:
        pass
    return None


def sense(root, nodes):
    out = {}
    now_ms = int(time.time() * 1000)
    for n in nodes:
        s = kv_get("state." + n, root)
        age = None
        if s and s.get("ts_utc_ms"):
            age = round((now_ms - int(s["ts_utc_ms"])) / 1000.0, 1)
        out[n] = {"state": s, "age_s": age,
                  "online": bool(s) and age is not None and age <= OFFLINE_AFTER_S}
    return out


def lane_reports(root, nodes):
    return {n: kv_get(fl.lane_result_key(n), root) for n in nodes}


# ---------------------------------------------------------------- supply
def supply(root, queue, have_ids):
    """Add only work whose inputs physically exist on this machine."""
    added = []
    try:
        sys.path.insert(0, os.path.dirname(HERE))
        from backlog_fill import fill as fill_backlog
        n = fill_backlog(root)
        if n:
            added.append("backlog_manifest+%d" % n)
    except Exception as e:
        added.append("backlog_fill_error:%s" % str(e)[:80])

    rows = fl.read_jsonl(os.path.join(root, fl.QUEUE_REL.replace("/", os.sep)))
    have = {r.get("id") for r in rows}
    rules = fl.read_jsonl(os.path.join(root, fl.RULES_REL.replace("/", os.sep)))
    rule_added = 0
    for r in rules:
        jid = r.get("id")
        if not jid or jid in have:
            continue
        if r.get("state") not in (None, "READY"):
            continue
        # Cross-host cards (2026-10-30 fix): C:/ K:/ E:/ paths live on the assignee box,
        # never on the macOS master. Master must NOT local-check them (that killed every
        # worker card). lane_agent re-checks when_all/when_none locally at claim time.
        def _remote(pth):
            return bool(__import__("re").match(r"^[A-Za-z]:[\\/]", pth))
        if not all(_remote(p) or os.path.exists(p) for p in (r.get("when_all") or [])):
            continue
        if any((not _remote(p)) and os.path.exists(p) for p in (r.get("when_none") or [])):
            continue
        out = r.get("deliverable")
        if out and out.startswith(("C:", "D:", "/")) and os.path.exists(out):
            continue
        rows.append({
            "id": jid, "title": r.get("title"), "cmd": r.get("cmd"),
            "cwd": r.get("cwd") or root, "needs": r.get("needs") or "cpu",
            "deliverable": out, "nodes": r.get("nodes") or [],
            "model": r.get("model") or "none",
            "prompt": r.get("prompt") or "",
            "when_all": r.get("when_all") or [],
            "llm": r.get("llm") or {},
            "prio": r.get("prio") or "P2", "why": r.get("why"),
            "cloud_ok": bool(r.get("cloud_ok")), "cloud_cmd": r.get("cloud_cmd"),
            "cloud_est_credits": r.get("cloud_est_credits"),
            "heavy": bool(r.get("heavy")),
            "timeout_s": r.get("timeout_s"),
            "state": "OPEN", "route": "local",
            "created_by": "master_agent:rule", "created_at": fl.now_iso(),
        })
        have.add(jid)
        added.append(jid)
        rule_added += 1
    if rule_added:
        fl.write_jsonl(os.path.join(root, fl.QUEUE_REL.replace("/", os.sep)), rows)
    return added, rows


# ---------------------------------------------------------------- supervision
def supervise(rows, reports, now_ts, self_node="bm-a"):
    """Close jobs from lane reports; requeue expired leases. Returns list of events."""
    events = []
    by_id = {}
    for r in rows:
        by_id[r.get("id")] = r
    for node, rep in reports.items():
        if not rep or not rep.get("job"):
            continue
        jid = rep.get("job")
        st = str(rep.get("state") or "").upper()
        job = by_id.get(jid)
        if not job or job.get("state") not in ("RUNNING", "OPEN"):
            continue
        # A stale KV report must not resurrect a job that was reset/requeued after it was
        # produced (2026-10-29: a killed rebuild's DONE report re-closed a reset job).
        rep_ts = str(rep.get("ts") or "")
        floor_ts = str(job.get("reset_at") or "")
        if floor_ts and rep_ts and rep_ts <= floor_ts:
            continue
        if st in ("DONE", "FAILED"):
            job["state"] = "DONE" if st == "DONE" else "FAILED"
            job["finished_at"] = rep.get("ts") or now_ts
            job["result"] = {"rc": rep.get("rc"), "seconds": rep.get("seconds"),
                             "deliverable_exists": rep.get("deliverable_exists")}
            events.append("%s %s via %s" % (jid, job["state"], node))
        elif st == "DEFERRED":
            # The lane refused on purpose (work-hour yield). Release it immediately so the
            # lease clock does not burn a slot for 90 minutes.
            job["state"] = "OPEN"
            job["owner"] = ""
            job["note"] = "deferred by %s: %s" % (node, rep.get("reason") or "yield")
            events.append("%s DEFERRED by %s" % (jid, node))
    for r in rows:
        if r.get("state") != "RUNNING":
            continue
        claimed = r.get("claimed_at") or r.get("assign_ts")
        if not claimed:
            continue
        try:
            age_min = (datetime.now() - datetime.strptime(claimed, "%Y-%m-%dT%H:%M:%S")).total_seconds() / 60.0
        except Exception:
            continue
        lease = int(r.get("lease_minutes") or DEFAULT_LEASE.get(r.get("needs") or "cpu", 45))
        if age_min <= lease:
            continue
        attempts = int(r.get("attempts") or 0) + 1
        r["attempts"] = attempts
        if attempts >= MAX_ATTEMPTS:
            r["state"] = "FAILED"
            r["finished_at"] = now_ts
            r["failure"] = "lease-expired-%d-attempts" % attempts
            events.append("%s FAILED after %d attempts (lease %dm)" % (r["id"], attempts, lease))
        else:
            r["state"] = "OPEN"
            r["owner"] = ""
            r["note"] = "requeued after lease expiry (attempt %d)" % attempts
            events.append("%s REQUeued attempt=%d" % (r["id"], attempts))
    # deliverable missing on a DONE job = receipt without evidence; flag, do not silently pass
    for r in rows:
        if r.get("state") == "DONE" and r.get("deliverable"):
            dl = r["deliverable"]
            if dl.startswith(("C:", "D:")) and r.get("owner") == self_node and not os.path.exists(dl):
                r["state"] = "FAILED"
                r["failure"] = "deliverable-missing"
                events.append("%s FAILED deliverable-missing" % r["id"])
    return events


# ---------------------------------------------------------------- routing + assignment
def route_decision(job, fleet, rows=None, policy=None):
    """Allocate by fitness, not by habit (CEO 2026-10-29): local when local can do it,
    cloud when only the smart tier can, and queue rather than pay just to skip a wait.

    Guards: per-job credits <=50 by default, daily <=200, hard ceiling 500 needs the CEO.
    """
    pol = (policy or {}).get("guards") or {}
    per_cap = int(pol.get("per_call_credit_cap") or 50)
    day_cap = int(pol.get("daily_credit_cap") or 200)
    ceil = int(pol.get("hard_ceiling") or 500)
    model = str(job.get("model") or "none")
    needs = str(job.get("needs") or "cpu")
    kind = model if model != "none" else ("gpu-production" if needs == "gpu" else "deterministic")
    busy = {r.get("owner") for r in (rows or [])
            if r.get("state") == "RUNNING" and r.get("owner")}

    def free_lane(need):
        need_cap = job.get("cap") or ("llm" if (job.get("model") or "") == "local-small" else None)
        for n in fl.ACTIVE_LANES:
            if n in busy:
                continue
            if need not in fl.LANES[n]["needs"]:
                continue
            if need_cap and (fl.LANES[n].get("caps")
                             and need_cap not in fl.LANES[n]["caps"]):
                continue
            ok, _why = lane_capacity(n, fleet, need, int(job.get("vram_min_gb") or 0), job)
            if not ok:
                continue
            if need == "gpu" and not fl.gpu_window_open(n):
                continue
            if job.get("heavy") and not fl.heavy_allowed(n):
                continue
            return n
        return None

    if kind == "deterministic":
        return "local", "deterministic script -> local (zero token)"
    if kind == "gpu-production":
        lane = free_lane("gpu")
        if lane:
            return "local", "gpu production -> %s (local GPU is the point)" % lane
        if job.get("cloud_ok") and job.get("blocks_downstream"):
            cred = int(job.get("cloud_est_credits") or 0)
            if cred <= per_cap and cloud_spend_today(rows or []) + cred <= day_cap:
                return "cloud", "overflow: no local GPU lane, blocks downstream (%s credits)" % cred
        return "queue", "no local GPU lane free; held (local GPU is the only production path)"
    if kind == "local-small":
        lane = free_lane("cpu")
        if lane:
            return "local", "text work -> local-llm on %s" % lane
        return "queue", "local lanes busy; wait instead of paying for a short job"
    if model == "cloud-smart":
        cred = int(job.get("cloud_est_credits") or 0)
        if cred > ceil:
            return "blocked", "CEO-CONFIRM required: %s credits > %s" % (cred, ceil)
        if cred > per_cap:
            return "blocked", "over per-call cap: %s > %s credits" % (cred, per_cap)
        used = cloud_spend_today(rows or [])
        if used + cred > day_cap:
            return "blocked", "daily cap: used %s + %s > %s credits" % (used, cred, day_cap)
        return "cloud", "judgment -> smart tier (est %s credits, day used %s/%s)" % (
            cred, used, day_cap)
    if job.get("cloud_ok") and job.get("blocks_downstream") and not free_lane(needs):
        cred = int(job.get("cloud_est_credits") or 0)
        if cred <= per_cap and cloud_spend_today(rows or []) + cred <= day_cap:
            return "cloud", "overflow: no local lane and it blocks downstream (%s credits)" % cred
        return "blocked", "overflow denied by credit guard (%s credits)" % cred
    return "local", "default: local first"


def cloud_spend_today(rows):
    today = datetime.now().strftime("%Y-%m-%d")
    total = 0
    for r in rows:
        if str(r.get("route") or "") == "cloud" and str(r.get("created_at") or "").startswith(today):
            total += int(r.get("cloud_est_credits") or 0)
    return total


def lane_capacity(node, fleet, needs="cpu", vram_min=0, job=None):
    """(ok, reason) for assigning work to this lane right now.

    A GPU job is allowed past the RAM floor because gpu_lease.acquire() stops the resident
    LLM and disables keepwarm before ComfyUI starts - that is the documented reclaim path,
    not something the master can do remotely. A CPU job has no such reclaim, so it obeys
    the floor strictly. VRAM is a hard filter: an 8GB card must never be handed a 768p job.
    A control-plane box (bm-m) refuses heavy work and anything that would eat its disk: it
    exists to schedule, not to produce (CEO 2026-10-29).
    """
    info = fleet.get(node) or {}
    if not info.get("online"):
        return False, "OFFLINE (hb age %ss)" % info.get("age_s")
    st = info.get("state") or {}
    spec = fl.LANES.get(node) or {}
    q = fl.quiet_hours(node)
    if q is not None and not (job is not None and job.get("day_ok")):
        return False, "work machine daytime yield (%02d:00-%02d:00)" % (q[0], q[1])
    if spec.get("role_class") == "control":
        if needs == "gpu":
            return False, "control node: no CUDA, GPU work goes elsewhere"
        if job is not None:
            # 32GB unified memory is real capacity (CEO 2026-10-29): the Mac may take
            # heavy CPU/text work. It just must not fill a 512GB disk or starve its own
            # scheduling duties - hence a size guard, not a heavy-work ban.
            est = int(job.get("est_gb") or 0)
            cap_gb = int(spec.get("max_job_gb") or 2)
            if est > cap_gb:
                return False, "control node: job writes %dGB > %dGB budget" % (est, cap_gb)
        disk = st.get("disk_free_gb")
        need_disk = float(spec.get("disk_free_min_gb") or 0)
        if disk is not None and need_disk and float(disk) < need_disk:
            return False, "control node: disk %.0fGB < %.0fGB reserve" % (float(disk), need_disk)
    if needs == "gpu":
        have = int(spec.get("vram_gb") or 0)
        if vram_min and have < int(vram_min):
            return False, "VRAM %dGB < %dGB" % (have, int(vram_min))
        if not spec.get("cuda", True):
            return False, "no CUDA"
    floor = float(spec.get("ram_floor_gb") or 2.0)
    if needs == "gpu":
        floor = min(floor, 1.0)
    ram = st.get("ram_free_gb")
    if ram is None:
        return True, "ram-unknown"
    ok = float(ram) >= floor
    return ok, "ram %.1f/%.1f GB" % (float(ram), floor)


def choose_lane(job, fleet, busy):
    needs = job.get("needs") or "cpu"
    pref = job.get("nodes") or []
    cap = job.get("cap") or ("llm" if (job.get("model") or "") == "local-small" else None)
    vram_min = int(job.get("vram_min_gb") or 0)
    candidates = [n for n in fl.LANES if needs in fl.LANES[n]["needs"]]
    if cap:
        candidates = [n for n in candidates
                      if cap in (fl.LANES[n].get("caps") or []) or not (fl.LANES[n].get("caps"))]
    if pref:
        candidates = [n for n in pref if n in fl.LANES and n in candidates] or candidates
    scored = []
    for n in candidates:
        if busy.get(n):
            continue
        ok, why = lane_capacity(n, fleet, needs, vram_min, job)
        if not ok:
            continue
        if needs == "gpu" and not fl.gpu_window_open(n):
            continue
        if job.get("heavy") and not fl.heavy_allowed(n):
            continue
        st = (fleet.get(n) or {}).get("state") or {}
        load = float(st.get("cpu_load_pct") or 0)
        # GPU work prefers the production box; CPU work prefers the least loaded lane.
        penalty = 1 if ((fl.LANES[n].get("role_class") == "control" and job.get("heavy"))
                        or fl.LANES[n].get("role_class") == "control") else 0
        score = (0 if (needs == "gpu" and n == "bm-c") else 1, penalty, load)
        scored.append((score, n))
    scored.sort()
    if not scored:
        return None, "NO-CAPACITY"
    return scored[0][1], "assigned"


def assign(rows, fleet, reports, lines=None):
    parked = {ln["id"] for ln in (lines or []) if (ln.get("status") or "") == "PARKED"}
    prio_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    busy = {}
    for r in rows:
        if r.get("state") == "RUNNING" and r.get("owner"):
            busy[r["owner"]] = r
    pending = [r for r in rows if r.get("state") == "OPEN"]
    pending.sort(key=lambda r: (prio_rank.get(str(r.get("prio") or "P2"), 2),
                                str(r.get("created_at") or "")))
    events = []
    for r in pending:
        if r.get("route") in ("blocked", "queue"):
            continue
        if line_of_job(r, lines or []) in parked:
            continue
        # Never let the cron spend cloud money: cloud-smart work waits for the smart seat.
        if (r.get("model") or "none") == "cloud-smart":
            continue
        lane, why = choose_lane(r, fleet, busy)
        if not lane:
            continue
        r["state"] = "RUNNING"
        r["owner"] = lane
        r["claimed_at"] = fl.now_iso()
        r["assign_ts"] = r["claimed_at"]
        r["lease_minutes"] = int(r.get("timeout_s") or 0) // 60 or \
            DEFAULT_LEASE.get(r.get("needs") or "cpu", 45)
        busy[lane] = r
        events.append("%s -> %s (%s)" % (r["id"], lane, r.get("needs") or "cpu"))
    return events


def write_lane_files(root, rows, fleet, dry=False, nodes=None):
    """One job per lane; the lane file also carries WHY the lane is empty."""
    by_lane = {n: [] for n in (nodes or fl.ACTIVE_LANES)}
    for r in rows:
        if r.get("state") == "RUNNING" and r.get("owner") in by_lane:
            by_lane[r["owner"]].append({
                "id": r.get("id"), "title": r.get("title"), "cmd": r.get("cmd"),
                "cwd": r.get("cwd"), "needs": r.get("needs"),
                "deliverable": r.get("deliverable"),
                "need_mb": r.get("need_mb"),
                "model": r.get("model") or "none",
                "prompt": r.get("prompt") or "",
                "when_all": r.get("when_all") or [],
                "llm": r.get("llm"),
                "timeout_s": r.get("timeout_s"),
            })
    written = []
    for n, jobs in by_lane.items():
        ok, why = lane_capacity(n, fleet, "cpu")
        if jobs:
            idle_reason = ""
        elif not ok:
            # A work machine in its daytime window is not a capacity fault - it is policy.
            idle_reason = ("DAY-YIELD: work machine, takes over at 19:00"
                           if fl.quiet_hours(n) else "CAPACITY-BLOCKED-RAM " + why)
        else:
            waiting = [r for r in rows if r.get("state") == "OPEN"
                       and (not (r.get("nodes") or []) or n in (r.get("nodes") or []))
                       and (r.get("needs") or "cpu") in fl.LANES[n]["needs"]]
            day_wait = [r for r in waiting if fl.quiet_hours(n) and not r.get("day_ok")]
            heavy_wait = [r for r in waiting if r.get("heavy") and not fl.heavy_allowed(n)]
            gpu_wait = [r for r in waiting if (r.get("needs") == "gpu")
                        and not fl.gpu_window_open(n)]
            if day_wait:
                idle_reason = "DAY-YIELD: work machine, %d job(s) wait for 19:00" % len(day_wait)
            elif heavy_wait or gpu_wait:
                # Not idle-by-fault: the CEO's own desktop yields during his working day.
                idle_reason = "WORKHOUR-YIELD: %d job(s) wait for the night window" % len(
                    heavy_wait or gpu_wait)
            else:
                # An online lane with spare capacity but no master job is not idle yet: it
                # scans its OWN backlog first (drama/audio tracks exist only on bm-b). Idle
                # is only confirmed when the lane itself reports IDLE back over NATS.
                idle_reason = "SELF-DISPATCH: lane scans its own backlog"
        payload = {"node": n, "ts": fl.now_iso(), "jobs": jobs[:1],
                   "idle_reason": idle_reason,
                   "lane_ok": ok, "capacity_note": why}
        path = fl.lane_file(root, n)
        old = fl.read_json(path, {}) or {}
        if old.get("jobs") == payload["jobs"] and old.get("idle_reason") == idle_reason:
            continue
        if not dry:
            fl.write_json(path, payload)
        written.append(n)
    return written, by_lane


# ---------------------------------------------------------------- main cycle
def cycle(root, dry=False, push=True, node="bm-a"):
    owner_node = master_node(root)
    if node != owner_node:
        # Not the declared master: observe only, never write the queue.
        return {"standby": True, "node": node, "master": owner_node,
                "ts": fl.now_iso(), "cycle": None,
                "queue": {}, "lanes": {}, "lines": {}, "stages": {},
                "judgments": {}, "routing": {}, "violations": [],
                "supply_added": [], "events": [], "lane_files_written": []}
    # Pending boxes (bm-m Mac, bm-d V100 rack) join the moment they report a heartbeat -
    # no code edit, no flag flip, no asking the CEO whether the hardware arrived.
    nodes = list(fl.ACTIVE_LANES)
    pending_fleet = sense(root, fl.AUTO_JOIN)
    joined = [n for n, v in pending_fleet.items() if v.get("online")]
    nodes += joined
    fleet = sense(root, nodes)
    fleet.update({n: pending_fleet[n] for n in joined})
    reports = lane_reports(root, nodes)
    added, rows = supply(root, None, set())
    lines = load_lines(root)
    now_ts = fl.now_iso()
    events = supervise(rows, reports, now_ts, self_node=node)
    policy = fl.load_policy(root)
    for r in rows:
        if r.get("state") == "OPEN":
            route, why = route_decision(r, fleet, rows, policy)
            r["route"] = route
            r["route_note"] = why
    events += assign(rows, fleet, reports, lines)
    if not dry:
        fl.write_jsonl(os.path.join(root, fl.QUEUE_REL.replace("/", os.sep)), rows)
    written, by_lane = write_lane_files(root, rows, fleet, dry, nodes)

    # idle ledger: every empty lane must carry a reason, and persistent emptiness escalates
    prev = fl.read_json(os.path.join(root, fl.STATE_REL.replace("/", os.sep)), {}) or {}
    prev_idle = prev.get("idle_rounds") or {}
    idle_rounds = {}
    lanes_state = {}
    for n in nodes:
        jobs = by_lane.get(n) or []
        rep = reports.get(n) or {}
        confirmed_idle = (not jobs) and str(rep.get("state") or "").upper() == "IDLE"
        if (fl.read_json(fl.lane_file(root, n), {}) or {}).get("idle_reason", "").startswith("DAY-YIELD"):
            confirmed_idle = False  # yielded on purpose: not idleness
        reason = ""
        if not jobs:
            reason = (fl.read_json(fl.lane_file(root, n), {}) or {}).get("idle_reason", "")
        # A lane only counts as idle when it has told us so AND holds no job. "No job
        # assigned yet" is not idle - it may still be scanning its own backlog.
        idle_rounds[n] = (int(prev_idle.get(n) or 0) + 1) if confirmed_idle else 0
        st = (fleet.get(n) or {}).get("state") or {}
        lanes_state[n] = {
            "online": (fleet.get(n) or {}).get("online"),
            "hb_age_s": (fleet.get(n) or {}).get("age_s"),
            "cpu_load_pct": st.get("cpu_load_pct"),
            "ram_free_gb": st.get("ram_free_gb"),
            "gpu_util_pct": st.get("gpu_util_pct"),
            "job": (jobs[0]["id"] if jobs else None),
            "last_result": {k: rep.get(k) for k in ("job", "state", "rc", "ts", "reason")} if rep else None,
            "idle_confirmed": confirmed_idle,
            "idle_reason": reason,
            "idle_rounds": idle_rounds[n],
        }

    queued = {"total": len(rows),
              "open": len([r for r in rows if r.get("state") == "OPEN"]),
              "running": len([r for r in rows if r.get("state") == "RUNNING"]),
              "done": len([r for r in rows if r.get("state") == "DONE"]),
              "failed": len([r for r in rows if r.get("state") == "FAILED"])}
    violations = []
    for n, ls in lanes_state.items():
        if not ls["online"]:
            violations.append("%s OFFLINE" % n)
        elif (ls["idle_confirmed"] and ls["idle_rounds"] >= 2
              and not ls["idle_reason"].startswith("DAY-YIELD")):
            violations.append("%s IDLE-CONFIRMED x%d (%s)" % (
                n, ls["idle_rounds"], ls["idle_reason"][:40]))
        elif ls["idle_reason"].startswith("CAPACITY-BLOCKED-RAM"):
            violations.append("%s CAPACITY-BLOCKED-RAM" % n)
        # DAY-YIELD is compliance with the CEO's own machine, never a violation.

    lines = load_lines(root)
    # stage freshness drives the "which工序 stopped" answer; cached, recomputed every 10 min
    s_ages = stage_ages(root, lines)
    stages_state = stage_states(root, lines, rows, s_ages)
    # Paying the cloud while a capable local lane sits empty is the waste this policy
    # exists to catch. Judgment jobs are exempt: local cannot do them at all.
    busy_now = {r.get("owner") for r in rows
                if r.get("state") == "RUNNING" and r.get("owner")}
    waste = []
    for r in rows:
        if r.get("state") != "OPEN" or r.get("route") != "cloud":
            continue
        if (r.get("model") or "none") == "cloud-smart":
            continue
        need = r.get("needs") or "cpu"
        lane = next((n for n in fl.ACTIVE_LANES if n not in busy_now
                     and need in fl.LANES[n]["needs"]
                     and lane_capacity(n, fleet, need, 0, r)[0]), None)
        if lane:
            waste.append("%s cloud while %s idle" % (r.get("id"), lane))
    routing = {
        "local": len([r for r in rows if r.get("state") == "OPEN" and r.get("route") == "local"]),
        "cloud": len([r for r in rows if r.get("state") == "OPEN" and r.get("route") == "cloud"]),
        "queue": len([r for r in rows if r.get("state") == "OPEN" and r.get("route") == "queue"]),
        "blocked": len([r for r in rows if r.get("state") == "OPEN" and r.get("route") == "blocked"]),
        "cloud_spend_today": cloud_spend_today(rows),
        "waste": waste,
    }
    lines_state = line_states(root, lines, rows, lanes_state)
    # A line can look fine at the top (one fresh stage) while an earlier工序 has stopped.
    # The stage verdict wins: that is the whole point of splitting the line.
    for lid, st in stages_state.items():
        ls = lines_state.get(lid)
        if not ls or not st.get("bottleneck"):
            continue
        if ls["verdict"] in ("WAITING", "WORKING"):
            ls["verdict"] = "STALLED-STAGE"
            ls["stuck_stage"] = st["bottleneck"]["id"]
            ls["stuck_owner"] = st["bottleneck"]["owner"]
    policy = fl.load_policy(root)
    judgments = build_judgments(root, rows, lanes_state, lines_state, fleet, policy) if not dry \
        else {"open": 0, "by_kind": {}, "added": 0,
              "tick_tier": "none", "judgment_tier": "cloud-smart"}
    for lid, ls in lines_state.items():
        bn = (stages_state.get(lid) or {}).get("bottleneck") or {}
        if ls["verdict"] == "STALE":
            violations.append("LINE-STALE %s %sh>%sh (%s%s)" % (
                lid, ls["age_h"], ls["stale_after_h"], ls["owner"] or "no owner",
                (" · 卡在 %s/%s" % (bn.get("name"), bn.get("owner"))) if bn else ""))
        elif ls["verdict"] == "STALLED-STAGE":
            violations.append("STAGE-STALLED %s 卡在 %s/%s (%s)" % (
                lid, bn.get("name") or ls.get("stuck_stage"), bn.get("owner") or "?",
                ls["owner"] or "no owner"))
        elif ls["verdict"] == "BLOCKED":
            violations.append("LINE-BLOCKED %s (%s)" % (lid, (ls["note"] or "")[:50]))

    for w in waste:
        violations.append("CLOUD-WHILE-LOCAL-IDLE " + w)

    state = {"ts": now_ts, "cycle": int(prev.get("cycle") or 0) + 1,
             "queue": queued, "lanes": lanes_state, "idle_rounds": idle_rounds,
             "lines": lines_state,
             "stages": stages_state,
             "judgments": judgments,
             "routing": routing,
             "supply_gap": {k: len([r for r in rows if r.get("state") == "OPEN"
                                    and (r.get("needs") or "cpu") == k])
                            for k in ("cpu", "gpu")},
             "supply_added": added, "events": events, "violations": violations,
             "lane_files_written": written}
    if not dry:
        fl.write_json(os.path.join(root, fl.STATE_REL.replace("/", os.sep)), state)
        write_need_supply(root, lanes_state, queued, state["supply_gap"], lines_state, stages_state)
        log = os.path.join(root, fl.LOG_REL.replace("/", os.sep))
        os.makedirs(os.path.dirname(log), exist_ok=True)
        line = "[%s] cyc=%d q=%d/%d/%d sup=%d ev=%d idle=%s flags=%s" % (
            now_ts, state["cycle"], queued["open"], queued["running"], queued["done"],
            len(added), len(events),
            ",".join("%s:%s" % (n, lanes_state[n]["idle_reason"][:18] or "-")
                     for n in ("bm-a", "bm-b", "bm-c")),
            ";".join(violations)[:180] or "none")
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        if push:
            push_lane_files(root)
    return state


def write_need_supply(root, lanes_state, queued, gap, lines_state=None, stages_state=None):
    """One page a human can read: what each lane and each business line is waiting for.

    Law: the AI layer is not the fallback end-point. If a lane or a line is idle for a
    reason the machine cannot fix (missing declaration, diverged repo, exhausted RAM),
    say so in one line with the exact owner, every cycle, instead of logging a green.
    """
    lines = ["# NEED-SUPPLY - why lanes and business lines are not running (#regenerated)",
             "",
             "- ts: %s" % fl.now_iso(),
             "- queue: open=%d running=%d done=%d failed=%d" % (
                 queued["open"], queued["running"], queued["done"], queued["failed"]),
             "- open jobs by need: cpu=%d gpu=%d" % (gap.get("cpu", 0), gap.get("gpu", 0)),
             ""]
    for n, ls in lanes_state.items():
        if ls["job"]:
            lines.append("- %s: RUNNING %s" % (n, ls["job"]))
            continue
        why = ls["idle_reason"] or "unknown"
        action = {
            "WORKHOUR-YIELD": "no action: waits for the 19:00 night window",
            "CAPACITY-BLOCKED-RAM": "free memory on that box (gpu_lease --acquire reclaims it)",
            "SELF-DISPATCH": "lane is scanning its own backlog; if this persists >2 rounds "
                             "the box has no declared work and needs a new card",
        }
        key = next((k for k in action if why.startswith(k)), "")
        lines.append("- %s: %s -> %s" % (n, why, action.get(key, "assign a card or declare work")))
    lines += ["", "Rules pack: cph4/fleet/WORK-RULES.jsonl (empty = every job must be declared "
                  "by a producing seat; the master will not invent work).", ""]

    if lines_state:
        lines += ["## 业务条线（正身 cph4/fleet/LINE-REGISTRY.json）", "",
                  "| 条线 | 判 | 最近产出 | 阈值 | 卡在 | 负责人 |", "|---|---|---|---|---|---|"]
        order = {"BLOCKED": 0, "STALE": 1, "STALLED-STAGE": 2, "WAITING": 3, "WORKING": 4, "PARKED": 5}
        st_by_line = stages_state or {}
        for lid, ls in sorted(lines_state.items(), key=lambda kv: order.get(kv[1]["verdict"], 9)):
            age = "-" if ls["age_h"] is None else "%.1fh" % ls["age_h"]
            bn = (st_by_line.get(lid) or {}).get("bottleneck") or {}
            stuck = "%s/%s" % (bn.get("name"), bn.get("owner")) if bn else "-"
            lines.append("| %s | %s | %s | %sh | %s | %s |" % (
                ls["name"], ls["verdict"], age, ls["stale_after_h"], stuck,
                ls["owner"] or "-"))
        lines.append("")
        lines.append("- PARKED=CEO 令停，不计闲置；WAITING=没活但未过期；"
                     "STALE=超过阈值无产出；BLOCKED=有活但无可用车道；卡在=最早断供的工段。")
        lines.append("")
    path = os.path.join(root, fl.STATE_REL.replace("/", os.sep).replace(
        "MASTER-STATE.json", "NEED-SUPPLY.md"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------- business lines
LINE_REL = "cph4/fleet/LINE-REGISTRY.json"


def load_lines(root):
    data = fl.read_json(os.path.join(root, LINE_REL.replace("/", os.sep)), {}) or {}
    return data.get("lines") or []


def _git_age_h(root, repo):
    try:
        p = subprocess.run(["git", "-C", os.path.join(root, repo), "log", "-1", "--format=%ct"],
                           capture_output=True, text=True, timeout=20,
                           creationflags=CREATE_NO_WINDOW)
        ts = int((p.stdout or "0").strip() or 0)
        if ts:
            return round((time.time() - ts) / 3600.0, 1)
    except Exception:
        pass
    return None


def _newest_age_h(root, rel, budget_s=20):
    """Newest file under an evidence dir. Bounded: these dirs can be junctions to D:."""
    base = os.path.join(root, rel.replace("/", os.sep))
    if not os.path.isdir(base):
        return None
    newest, t0 = 0.0, time.time()
    for dirpath, _dirs, files in os.walk(base):
        if time.time() - t0 > budget_s:
            break
        for f in files:
            try:
                newest = max(newest, os.path.getmtime(os.path.join(dirpath, f)))
            except Exception:
                pass
    return round((time.time() - newest) / 3600.0, 1) if newest else None


def line_of_job(job, lines):
    if job.get("line"):
        return job.get("line")
    jid = str(job.get("id") or "")
    for ln in lines:
        for pre in ln.get("queue_prefix") or []:
            if jid.startswith(pre):
                return ln["id"]
    return ""


def line_states(root, lines, rows, lanes_state):
    """Per-line: last production age, jobs in flight, and a verdict a human can act on.

    PARKED lines are counted but never flagged: the CEO stopped them on purpose, so an
    old timestamp there is compliance, not idleness.
    """
    out = {}
    for ln in lines:
        ages = [a for a in (_git_age_h(root, r) for r in (ln.get("repos") or [])) if a is not None]
        ages += [a for a in (_newest_age_h(root, e) for e in (ln.get("evidence") or []))
                 if a is not None]
        age = min(ages) if ages else None
        live = [r for r in rows if r.get("state") in ("OPEN", "RUNNING")
                and line_of_job(r, lines) == ln["id"]]
        status = ln.get("status") or "ACTIVE"
        limit = float(ln.get("stale_after_h") or 48)
        if status == "PARKED":
            verdict = "PARKED"
        elif not live and age is not None and age > limit:
            verdict = "STALE"
        elif live:
            verdict = "WORKING"
        elif status == "BLOCKED":
            verdict = "BLOCKED"
        else:
            verdict = "WAITING"
        blockers = []
        for r in live:
            if r.get("state") == "OPEN" and not r.get("owner"):
                blockers.append(r["id"] + ":no-lane")
        out[ln["id"]] = {"name": ln.get("name"), "status": status, "verdict": verdict,
                         "age_h": age, "stale_after_h": limit, "owner": ln.get("owner"),
                         "jobs": [r["id"] for r in live], "no_supply": not live,
                         "blockers": blockers, "note": ln.get("note")}
    return out


def build_judgments(root, rows, lanes_state, lines_state, fleet, policy):
    """Only the calls a rule cannot make get queued for the smart tier.

    CEO 2026-10-29: the master must be the smartest agent, but the 2-minute tick must not
    burn cloud tokens. So the tick stays deterministic and everything genuinely ambiguous
    becomes one line here; the smart seat answers it and the answer is the audit trail.
    """
    wanted = []

    def add(kind, key, question, evidence):
        wanted.append({"key": "%s:%s" % (kind, key), "kind": kind, "subject": key,
                       "question": question, "evidence": evidence,
                       "tier": "cloud-smart", "ts": fl.now_iso(), "state": "OPEN"})

    for r in rows:
        if r.get("state") == "OPEN" and (r.get("model") or "none") == "cloud-smart":
            add("MODEL-DECISION", r.get("id"),
                "这件活被标成需要最强大脑，是否值得花钱、还是改成本地做法或拆小？",
                {"title": r.get("title"), "why": r.get("why"),
                 "est_credits": r.get("cloud_est_credits")})
        if r.get("state") == "OPEN" and int(r.get("attempts") or 0) >= 2:
            add("RETRY", r.get("id"),
                "这件活已重排 %d 次仍未收口，是工具坏了、输入缺失还是车道不合适？" %
                int(r.get("attempts") or 0),
                {"note": r.get("note"), "needs": r.get("needs")})
    for lid, ls in lines_state.items():
        if ls["verdict"] == "STALE":
            add("LINE-STALE", lid,
                "这条线 %.0f 小时没有产出、也没有已声明的活，下一步该做什么？" % (ls["age_h"] or 0),
                {"owner": ls["owner"], "limit_h": ls["stale_after_h"], "note": ls["note"]})
        elif ls["verdict"] == "BLOCKED":
            add("LINE-BLOCKED", lid,
                "这条线有活但没有能跑的车道，是拆活、换机器还是先修车道？",
                {"owner": ls["owner"], "note": ls["note"]})
    for n, ls in lanes_state.items():
        if ls["online"] and not ls["job"] and ls["idle_reason"].startswith("CAPACITY-BLOCKED-RAM"):
            add("CAPACITY", n, "这台机内存不够但 GPU 空着，先释放哪些进程？",
                {"ram_free_gb": ls["ram_free_gb"], "gpu_util_pct": ls["gpu_util_pct"]})

    path = os.path.join(root, fl.JUDGMENT_REL.replace("/", os.sep))
    existing = fl.read_jsonl(path)
    live_ids = {r.get("id") for r in rows}
    # A job that was removed or completed must not keep an open decision hanging.
    existing = [e for e in existing
                if not (e.get("state") == "OPEN"
                        and e.get("kind") in ("MODEL-DECISION", "RETRY")
                        and e.get("subject") not in live_ids)]
    by_key = {e.get("key"): e for e in existing}
    added = 0
    for w in wanted:
        cur = by_key.get(w["key"])
        if cur and cur.get("state") == "OPEN":
            continue
        if cur and cur.get("state") == "ANSWERED" and cur.get("evidence") == w["evidence"]:
            continue  # already decided on the same evidence; do not nag
        by_key[w["key"]] = w
        added += 1
    rows_out = list(by_key.values())[-400:]
    fl.write_jsonl(path, rows_out)
    open_by_kind = {}
    for e in rows_out:
        if e.get("state") == "OPEN":
            open_by_kind[e["kind"]] = open_by_kind.get(e["kind"], 0) + 1
    return {"open": sum(open_by_kind.values()), "by_kind": open_by_kind, "added": added,
            "tick_tier": "none", "judgment_tier": "cloud-smart"}


STAGE_CACHE_REL = "cph4/fleet/dispatcher/STAGE-CACHE.json"


MASTER_NODE_REL = "cph4/fleet/MASTER-NODE.json"


def master_node(root):
    """Who is allowed to write the queue. Exactly one node, declared in a file.

    bm-a and bm-m are separate clones, so there is no shared lock to arbitrate at runtime.
    Two masters would double-assign every job. Switching the master is a decision, so it
    is written down in one line and the other box goes to standby on its next tick.
    """
    data = fl.read_json(os.path.join(root, MASTER_NODE_REL.replace("/", os.sep)), {}) or {}
    return str(data.get("node") or "bm-a")


def stage_ages(root, lines, ttl=600):
    """Freshness per stage, cached: walking every evidence dir each 2 minutes is waste."""
    path = os.path.join(root, STAGE_CACHE_REL.replace("/", os.sep))
    cache = fl.read_json(path, {}) or {}
    if cache.get("ts") and (time.time() - float(cache["ts"])) < ttl and cache.get("ages"):
        return cache["ages"]
    ages = {}
    for ln in lines:
        for st in ln.get("stages") or []:
            vals = [a for a in (_newest_age_h(root, e) for e in (st.get("evidence") or []))
                    if a is not None]
            ages["%s/%s" % (ln["id"], st["id"])] = min(vals) if vals else None
    fl.write_json(path, {"ts": time.time(), "ages": ages})
    return ages


def stage_states(root, lines, rows, ages):
    """Per-stage verdict. The bottleneck is the earliest stage with no output in time.

    A stage whose evidence paths do not exist on this machine reports NO-DATA instead of
    STALLED: that usually means the material lives on another box, not that work stopped.
    """
    out = {}
    for ln in lines:
        stages, bottleneck = [], None
        for st in ln.get("stages") or []:
            key = "%s/%s" % (ln["id"], st["id"])
            age = ages.get(key)
            live = [r for r in rows
                    if r.get("state") in ("OPEN", "RUNNING") and r.get("stage") == st["id"]]
            limit = float(st.get("stale_after_h") or ln.get("stale_after_h") or 48)
            if (ln.get("status") or "") == "PARKED":
                verdict = "PARKED"
            elif live:
                verdict = "WORKING"
            elif age is None:
                verdict = "NO-DATA"
            elif age > limit:
                verdict = "STALLED"
            else:
                verdict = "WAITING"
            stages.append({"id": st["id"], "name": st.get("name"), "owner": st.get("owner"),
                           "model": st.get("model"), "lane": st.get("lane"),
                           "verdict": verdict, "age_h": age, "limit_h": limit,
                           "jobs": [r["id"] for r in live]})
            if bottleneck is None and verdict == "STALLED":
                bottleneck = stages[-1]
        out[ln["id"]] = {"bottleneck": bottleneck, "stages": stages}
    return out


def push_lane_files(root):
    """Ship everything the master produced: lane assignments + dispatcher state.

    One commit per throttle window, all master-owned paths together so the worktree never
    holds mismatched state. Push failures fetch + rebase --autostash and retry twice, so the
    sole writer (this box) converges with concurrent commits from other nodes.

    Throttled so a 2-minute tick does not spam the ledger: lane/state files rarely change
    more often than a job does.
    """
    rels = [
        fl.LANE_DIR_REL,                                  # lanes/<node>.json assignments
        fl.STATE_REL.replace("/", os.sep),                # dispatcher/MASTER-STATE.json
        fl.LOG_REL.replace("/", os.sep),                  # dispatcher/MASTER-LOG.md
        "cph4/fleet/dispatcher/NEED-SUPPLY.md",
        "cph4/fleet/dispatcher/STAGE-CACHE.json",
    ]
    stamp = os.path.join(root, ".codely-cli", "tmp", "lanepush.stamp")
    try:
        if os.path.exists(stamp) and (time.time() - os.path.getmtime(stamp)) < 600:
            return True
    except Exception:
        pass
    try:
        subprocess.run(["git", "-C", root, "add", "--"] + rels, timeout=60,
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
        diff = subprocess.run(["git", "-C", root, "diff", "--cached", "--quiet", "--"] + rels,
                              timeout=30, capture_output=True, creationflags=CREATE_NO_WINDOW)
        if diff.returncode == 0:
            return True
        subprocess.run(["git", "-C", root, "commit", "-m",
                        "master-agent: lane assignments + fleet state", "--"] + rels,
                       timeout=60, capture_output=True, creationflags=CREATE_NO_WINDOW)
        p = subprocess.run(["git", "-C", root, "push", "origin", "HEAD:main"],
                           timeout=120, capture_output=True, creationflags=CREATE_NO_WINDOW)
        for _ in range(2):
            if p.returncode == 0:
                break
            # Concurrent writer on the other side: bring our commit on top of theirs.
            subprocess.run(["git", "-C", root, "fetch", "--quiet", "origin", "main"],
                           timeout=120, capture_output=True, creationflags=CREATE_NO_WINDOW)
            rb = subprocess.run(["git", "-C", root, "rebase", "--autostash",
                                 "origin/main"],
                                timeout=120, capture_output=True,
                                creationflags=CREATE_NO_WINDOW)
            if rb.returncode != 0:
                break
            p = subprocess.run(["git", "-C", root, "push", "origin", "HEAD:main"],
                               timeout=120, capture_output=True,
                               creationflags=CREATE_NO_WINDOW)
        try:
            os.makedirs(os.path.dirname(stamp), exist_ok=True)
            open(stamp, "w").close()
        except Exception:
            pass
        return p.returncode == 0
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=fl.ROOT_DEFAULT)
    ap.add_argument("--once", action="store_true", default=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--node", default="bm-a", help="which node is running this tick")
    ap.add_argument("--json", action="store_true", help="print the full cycle state")
    a = ap.parse_args()
    st = cycle(os.path.abspath(a.root), dry=a.dry, push=not a.no_push, node=a.node)
    if st.get("standby"):
        print("STANDBY node=%s declared_master=%s (observe only, queue untouched)"
              % (a.node, st.get("master")))
        return 0
    if a.json:
        print(json.dumps(st, ensure_ascii=False, indent=1))
    else:
        print("MASTER cyc=%d queue open=%d run=%d done=%d failed=%d supply=%s" % (
            st["cycle"], st["queue"]["open"], st["queue"]["running"],
            st["queue"]["done"], st["queue"]["failed"], st["supply_added"]))
        for n, ls in st["lanes"].items():
            print("  %-5s online=%s idle=%s job=%s %s" % (
                n, ls["online"], ls["idle_reason"][:46] or "-", ls["job"] or "-",
                ("ram=%s gpu=%s" % (ls["ram_free_gb"], ls["gpu_util_pct"]))))
        if st["violations"]:
            print("  FLAGS:", "; ".join(st["violations"]))
        order = {"BLOCKED": 0, "STALE": 1, "STALLED-STAGE": 2, "WAITING": 3, "WORKING": 4, "PARKED": 5}
        if st.get("judgments"):
            j = st["judgments"]
            print("  SMART-TIER: tick=%s judgment=%s open=%d %s" % (
                j.get("tick_tier"), j.get("judgment_tier"), j.get("open", 0),
                j.get("by_kind") or ""))
        ls_all = st.get("lines") or {}
        shown = [kv for kv in sorted(ls_all.items(), key=lambda kv: order.get(kv[1]["verdict"], 9))
                 if kv[1]["verdict"] in ("BLOCKED", "STALE")]
        for lid, ls in shown:
            print("  LINE %-18s %-8s age=%sh limit=%sh owner=%s" % (
                lid, ls["verdict"], ls["age_h"], ls["stale_after_h"], ls["owner"] or "-"))
        if ls_all:
            counts = {}
            for ls in ls_all.values():
                counts[ls["verdict"]] = counts.get(ls["verdict"], 0) + 1
            print("  LINES:", ", ".join("%s=%d" % kv for kv in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())