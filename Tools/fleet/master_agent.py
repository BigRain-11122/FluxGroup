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
        if not all(os.path.exists(p) for p in (r.get("when_all") or [])):
            continue
        if any(os.path.exists(p) for p in (r.get("when_none") or [])):
            continue
        out = r.get("deliverable")
        if out and out.startswith(("C:", "D:", "/")) and os.path.exists(out):
            continue
        rows.append({
            "id": jid, "title": r.get("title"), "cmd": r.get("cmd"),
            "cwd": r.get("cwd") or root, "needs": r.get("needs") or "cpu",
            "deliverable": out, "nodes": r.get("nodes") or [],
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
def supervise(rows, reports, now_ts):
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
            if dl.startswith(("C:", "D:")) and r.get("owner") == "bm-a" and not os.path.exists(dl):
                r["state"] = "FAILED"
                r["failure"] = "deliverable-missing"
                events.append("%s FAILED deliverable-missing" % r["id"])
    return events


# ---------------------------------------------------------------- routing + assignment
def route_decision(job, fleet):
    """Local first. Cloud only on an explicit cloud leg and inside the cost gate."""
    if not job.get("cloud_ok"):
        return "local", "local-first (no cloud leg declared)"
    cred = job.get("cloud_est_credits")
    if cred is not None and int(cred) > 500:
        return "blocked", "CEO-CONFIRM required: %s credits > 500" % cred
    gpu_lanes = [n for n in fl.LANES if fl.LANES[n].get("gpu_hours") is not None]
    local_ok = any(fleet.get(n, {}).get("online") and
                   fl.gpu_window_open(n) for n in gpu_lanes) if job.get("needs") == "gpu" else True
    if local_ok:
        return "local", "local capacity available"
    return "cloud", "local starved; cloud leg allowed (%s credits)" % cred


def lane_capacity(node, fleet, needs="cpu"):
    """(ok, reason) for assigning work to this lane right now.

    A GPU job is allowed past the RAM floor because gpu_lease.acquire() stops the resident
    LLM and disables keepwarm before ComfyUI starts - that is the documented reclaim path,
    not something the master can do remotely. A CPU job has no such reclaim, so it obeys
    the floor strictly.
    """
    info = fleet.get(node) or {}
    if not info.get("online"):
        return False, "OFFLINE (hb age %ss)" % info.get("age_s")
    st = info.get("state") or {}
    floor = float((fl.LANES.get(node) or {}).get("ram_floor_gb") or 2.0)
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
    candidates = [n for n in fl.LANES if needs in fl.LANES[n]["needs"]]
    if pref:
        candidates = [n for n in pref if n in fl.LANES] or candidates
    scored = []
    for n in candidates:
        if busy.get(n):
            continue
        ok, why = lane_capacity(n, fleet, needs)
        if not ok:
            continue
        if needs == "gpu" and not fl.gpu_window_open(n):
            continue
        if job.get("heavy") and not fl.heavy_allowed(n):
            continue
        st = (fleet.get(n) or {}).get("state") or {}
        load = float(st.get("cpu_load_pct") or 0)
        # GPU work prefers the production box; CPU work prefers the least loaded lane.
        score = (0 if (needs == "gpu" and n == "bm-c") else 1, load)
        scored.append((score, n))
    scored.sort()
    if not scored:
        return None, "NO-CAPACITY"
    return scored[0][1], "assigned"


def assign(rows, fleet, reports):
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
        if r.get("route") == "blocked":
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


def write_lane_files(root, rows, fleet, dry=False):
    """One job per lane; the lane file also carries WHY the lane is empty."""
    by_lane = {n: [] for n in fl.ACTIVE_LANES}
    for r in rows:
        if r.get("state") == "RUNNING" and r.get("owner") in by_lane:
            by_lane[r["owner"]].append({
                "id": r.get("id"), "title": r.get("title"), "cmd": r.get("cmd"),
                "cwd": r.get("cwd"), "needs": r.get("needs"),
                "deliverable": r.get("deliverable"),
                "need_mb": r.get("need_mb"),
                "timeout_s": r.get("timeout_s"),
            })
    written = []
    for n, jobs in by_lane.items():
        ok, why = lane_capacity(n, fleet)
        if jobs:
            idle_reason = ""
        elif not ok:
            idle_reason = "CAPACITY-BLOCKED-RAM " + why
        else:
            waiting = [r for r in rows if r.get("state") == "OPEN"
                       and (not (r.get("nodes") or []) or n in (r.get("nodes") or []))
                       and (r.get("needs") or "cpu") in fl.LANES[n]["needs"]]
            heavy_wait = [r for r in waiting if r.get("heavy") and not fl.heavy_allowed(n)]
            gpu_wait = [r for r in waiting if (r.get("needs") == "gpu")
                        and not fl.gpu_window_open(n)]
            if heavy_wait or gpu_wait:
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
def cycle(root, dry=False, push=True):
    nodes = list(fl.ACTIVE_LANES)
    fleet = sense(root, nodes)
    reports = lane_reports(root, nodes)
    added, rows = supply(root, None, set())
    now_ts = fl.now_iso()
    events = supervise(rows, reports, now_ts)
    for r in rows:
        if r.get("state") == "OPEN":
            route, why = route_decision(r, fleet)
            r["route"] = route
            r["route_note"] = why
    events += assign(rows, fleet, reports)
    if not dry:
        fl.write_jsonl(os.path.join(root, fl.QUEUE_REL.replace("/", os.sep)), rows)
    written, by_lane = write_lane_files(root, rows, fleet, dry)

    # idle ledger: every empty lane must carry a reason, and persistent emptiness escalates
    prev = fl.read_json(os.path.join(root, fl.STATE_REL.replace("/", os.sep)), {}) or {}
    prev_idle = prev.get("idle_rounds") or {}
    idle_rounds = {}
    lanes_state = {}
    for n in nodes:
        jobs = by_lane.get(n) or []
        rep = reports.get(n) or {}
        confirmed_idle = (not jobs) and str(rep.get("state") or "").upper() == "IDLE"
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
        elif ls["idle_confirmed"] and ls["idle_rounds"] >= 2:
            violations.append("%s IDLE-CONFIRMED x%d (%s)" % (
                n, ls["idle_rounds"], ls["idle_reason"][:40]))
        elif ls["idle_reason"].startswith("CAPACITY-BLOCKED-RAM"):
            violations.append("%s CAPACITY-BLOCKED-RAM" % n)

    state = {"ts": now_ts, "cycle": int(prev.get("cycle") or 0) + 1,
             "queue": queued, "lanes": lanes_state, "idle_rounds": idle_rounds,
             "supply_gap": {k: len([r for r in rows if r.get("state") == "OPEN"
                                    and (r.get("needs") or "cpu") == k])
                            for k in ("cpu", "gpu")},
             "supply_added": added, "events": events, "violations": violations,
             "lane_files_written": written}
    if not dry:
        fl.write_json(os.path.join(root, fl.STATE_REL.replace("/", os.sep)), state)
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


def push_lane_files(root):
    """Ship assignments to the clones. One path only, so it cannot drag in worktree noise."""
    rel = fl.LANE_DIR_REL
    try:
        subprocess.run(["git", "-C", root, "add", "--", rel], timeout=60, capture_output=True,
                       creationflags=CREATE_NO_WINDOW)
        diff = subprocess.run(["git", "-C", root, "diff", "--cached", "--quiet", "--", rel],
                              timeout=30, capture_output=True, creationflags=CREATE_NO_WINDOW)
        if diff.returncode == 0:
            return True
        subprocess.run(["git", "-C", root, "commit", "-m",
                        "master-agent: lane assignments", "--", rel],
                       timeout=60, capture_output=True, creationflags=CREATE_NO_WINDOW)
        p = subprocess.run(["git", "-C", root, "push", "origin", "HEAD:main"],
                           timeout=120, capture_output=True, creationflags=CREATE_NO_WINDOW)
        if p.returncode != 0:
            subprocess.run(["git", "-C", root, "fetch", "--quiet", "origin", "main"],
                           timeout=120, capture_output=True, creationflags=CREATE_NO_WINDOW)
            p = subprocess.run(["git", "-C", root, "push", "origin", "HEAD:main"],
                               timeout=120, capture_output=True, creationflags=CREATE_NO_WINDOW)
        return p.returncode == 0
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=fl.ROOT_DEFAULT)
    ap.add_argument("--once", action="store_true", default=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--json", action="store_true", help="print the full cycle state")
    a = ap.parse_args()
    st = cycle(os.path.abspath(a.root), dry=a.dry, push=not a.no_push)
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
    return 0


if __name__ == "__main__":
    sys.exit(main())