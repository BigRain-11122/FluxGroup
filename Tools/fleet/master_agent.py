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
ROOT_DIR = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fleet_lane as fl  # noqa: E402

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
# 阈值统一来自 CARD-POLICY-v1.json（唯一源）
import card_policy as _cp
DEFAULT_LEASE = _cp.load().get("lease_minutes") or {"cpu": 45, "gpu": 180, "cloud": 60}
OFFLINE_AFTER_S = 900
MAX_ATTEMPTS = _cp.max_attempts()


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
                           capture_output=True, text=True, errors="replace", timeout=15,
                           creationflags=CREATE_NO_WINDOW)
        for line in reversed((p.stdout or "").splitlines()):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
    except Exception:
        pass
    return None


_PROBE_CACHE = {}       # node -> (ts, payload|None)
PROBE_TTL_S = 120


def _probe_status(node):
    """FleetLink /status 直读（tailnet）。仅在 NATS 与车道文件都不作证时使用。"""
    import time as _t
    c = _PROBE_CACHE.get(node)
    if c and _t.time() - c[0] < PROBE_TTL_S:
        return c[1]
    res = None
    try:
        nodes_path = os.path.join(ROOT_DIR, "Tools", "fleet-nodes.json")
        doc = json.load(open(nodes_path, encoding="utf-8"))
        for item in doc.get("nodes") or []:
            if isinstance(item, dict) and item.get("id") == node:
                ip = item.get("tailnet_ip")
                if not ip:
                    break
                import urllib.request
                url = "http://%s:8790/status" % ip
                with urllib.request.urlopen(url, timeout=3.5) as r:
                    d = json.loads(r.read().decode("utf-8", "ignore"))
                if d.get("ok"):
                    res = {"ram_free_gb": d.get("ram_free_gb"),
                           "gpu_util_pct": d.get("gpu") and None,
                           "probe_ts": d.get("ts"), "host": d.get("host")}
                break
    except Exception:
        res = None
    _PROBE_CACHE[node] = (_t.time(), res)
    return res


def sense(root, nodes):
    out = {}
    now_ms = int(time.time() * 1000)
    for n in nodes:
        s = kv_get("state." + n, root)
        age = None
        if s and s.get("ts_utc_ms"):
            age = round((now_ms - int(s["ts_utc_ms"])) / 1000.0, 1)
        online = bool(s) and age is not None and age <= OFFLINE_AFTER_S
        if not online:
            # The KV read is one signal, not the truth (2026-11-01: bm-b reported
            # "OFFLINE (hb age Nones)" - i.e. no ts at all - while its own lane file was
            # 40s old and it was busy with TTS). A dead NATS client on either side must
            # not remove a working box from dispatch, or the queue starves while the
            # machine is up. git is the authoritative surface, so fall back to the lane
            # file the box commits every cycle.
            try:
                lp = os.path.join(root, "cph4", "fleet", "lanes", "%s.json" % n)
                lane_age = time.time() - os.path.getmtime(lp)
                lj = json.load(open(lp, encoding="utf-8"))
                if lane_age <= OFFLINE_AFTER_S:
                    online = True
                    age = age if age is not None else round(lane_age, 1)
                    s = s or {"source": "lanes-file", "ts_utc_ms": None,
                              "ram_free_gb": None, "gpu_util_pct": None}
                    s["state_source"] = "lanes-file"
                    s["lane"] = lj
            except Exception:
                pass
        if not online:
            # 第三信号（2026-11-07 实测）：NATS 死、车道文件又因为我这侧没重写而过期，
            # 于是三台在线机器全被判 OFFLINE、卡一张都派不出去。FleetLink 的 tailnet
            # /status 是活的（bm-b 100.82.175.0:8790 直读 200），所以最后一层用它。
            pr = _probe_status(n)
            if pr:
                online = True
                age = age if age is not None else 0.0
                s = s or {"source": "fleeklink-status"}
                s["state_source"] = "fleeklink-status"
                s.update(pr)
        out[n] = {"state": s, "age_s": age, "online": online}
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
    # 查重（2026-11-02）：同一 cmd 的活已在排队/在跑，就不再进队列第二张。
    # 实测 6 组同名卡、8 组同 cmd 卡（每日体检卡每天一张），是"重复指挥"的主要来源。
    live_cmds = {(r.get("cmd") or "").strip() for r in rows
                 if r.get("state") in ("OPEN", "RUNNING") and r.get("cmd")}
    live_cmds.discard("")
    dup_skipped = 0
    rules = fl.read_jsonl(os.path.join(root, fl.RULES_REL.replace("/", os.sep)))
    rule_added = 0
    for r in rules:
        jid = r.get("id")
        if not jid or jid in have:
            continue
        if r.get("state") not in (None, "READY"):
            continue
        if (r.get("cmd") or "").strip() and (r.get("cmd") or "").strip() in live_cmds:
            dup_skipped += 1
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
            # day_ok must survive promotion or bm-a daytime cards wait until 19:00
            # (2026-10-30: R-LLM-BMA-PROBE lost its day_ok right here).
            "day_ok": bool(r.get("day_ok")),
            "when_none": r.get("when_none") or [],
            "need_mb": r.get("need_mb"), "est_gb": r.get("est_gb"),
            "state": "OPEN", "route": "local",
            "created_by": "master_agent:rule", "created_at": fl.now_iso(),
        })
        have.add(jid)
        added.append(jid)
        rule_added += 1
    if rule_added:
        # merge, never blind-overwrite: closer/workgen may have touched other rows in the
        # same cycle, and a whole-list dump erased their work (2026-11-02 review).
        # Push only the rows this rule pass created (D-R272-MASTER-FULLLIST-CLOBBER).
        _new_ids = set(str(x) for x in added if ":" not in str(x))
        _new_rows = [r for r in rows if r.get("id") in _new_ids]
        if _new_rows:
            fl.merge_jsonl(os.path.join(root, fl.QUEUE_REL.replace("/", os.sep)), _new_rows)
    if dup_skipped:
        added.append("dedup_skipped:%d" % dup_skipped)
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
            de = rep.get("deliverable_exists")
            declares = bool(job.get("deliverable"))
            # rc=0 is the executor's opinion; the artifact is the fact. A card that
            # declares a deliverable and reports "not produced" must never close as DONE
            # (2026-11-01: 17 rows were DONE with no artifact, no audit and no receipt -
            # they came from this branch trusting rc alone).
            if st == "DONE" and declares and de is False:
                job["state"] = "FAILED"
                job["note"] = "closed without artifact: lane reported DONE but deliverable missing"
                job["finished_at"] = rep.get("ts") or now_ts
                job["result"] = {"rc": rep.get("rc"), "seconds": rep.get("seconds"),
                                 "deliverable_exists": False}
                events.append("%s FAILED(no-artifact) via %s" % (jid, node))
                continue
            # Master-visible paths are checked by the master itself: the lane's own word is
            # not enough. A repo-relative deliverable that is not on this clone is
            # UNVERIFIED, and closer.py upgrades it to DONE the moment the file lands
            # (2026-11-01: C-VB-DISCOVER-V03 closed DONE with no file anywhere).
            rel_out = job.get("deliverable") or ""
            # Only judge paths that live on a surface this clone actually has. media/,
            # quant/ and gaming/ are gitignored or separate repos, so their absence here
            # proves nothing (OFFBOX). A cph4/... path, by contrast, must be committed by
            # the producing node; if it is not here, the closure is unproven.
            _root_dir = rel_out.split("/")[0] if rel_out and not os.path.isabs(rel_out) else ""
            _root = os.environ.get("FLUX_ROOT") or fl.ROOT_DEFAULT
            _visible = bool(_root_dir) and os.path.isdir(os.path.join(_root, _root_dir))
            if (st == "DONE" and rel_out and not os.path.isabs(rel_out) and _visible
                    and not os.path.exists(os.path.join(_root, rel_out))):
                job["state"] = "UNVERIFIED"
                job["finished_at"] = rep.get("ts") or now_ts
                job["result"] = {"rc": rep.get("rc"), "seconds": rep.get("seconds"),
                                 "deliverable_exists": False}
                job["evidence"] = "UNVERIFIED: lane said DONE, %s not on disk yet" % rel_out
                events.append("%s UNVERIFIED(no-artifact-yet) via %s" % (jid, node))
                continue
            job["state"] = "DONE" if st == "DONE" else "FAILED"
            job["finished_at"] = rep.get("ts") or now_ts
            job["result"] = {"rc": rep.get("rc"), "seconds": rep.get("seconds"),
                             "deliverable_exists": de}
            if job["state"] == "DONE" and declares and de is None:
                # The lane could not tell (foreign path, tool silent). Keep the closure but
                # label it, so supervision never counts an unproven card as delivered.
                job["evidence"] = "UNVERIFIED: deliverable declared, lane returned no existence flag"
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
        # 2026-11-09 本地优先闸：没有"本地 4B/8B 都试过"的证据，不许直接上云；
        # 宁可排队等本地判读，也不静默花云钱。
        if not job.get("local_tried"):
            return "queue", "local-first gate: local 4B/8B attempt required before cloud"
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


def _has_next_step(root, line_id):
    """True when LINE-NEXT-STEPS.json already declares this line's next product.

    Keeps the judgment queue for real direction gaps only. A line that already has a
    declared next artifact does not need a model's opinion - it needs a card.
    """
    try:
        with open(os.path.join(root, "cph4", "fleet", "LINE-NEXT-STEPS.json"), encoding="utf-8") as f:
            steps = json.load(f)
        return bool(((steps.get("lines") or {}).get(line_id) or {}).get("cards"))
    except Exception:
        return False


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
    # 僵尸机排除（2026-11-08 实锚）：bm-a 的 FleetLink 活着、能收 poke、能报 online，
    # 但它的 Windows 唤醒清单是空的（/status 的 wakes=[]），所以卡派过去只会被
    # 一直挂在 RUNNING 上等到停摆判据来救。判据=「在线但 6 小时零产出」=不接受新活，
    # 让它如实报 EXECUTOR-DEAD，而不是继续假派。
    if info.get("online") and node != "bm-m":
        try:
            import blocker_loop as _bl
            idle_h = (time.time() - _bl._node_last_output().get(node, time.time())) / 3600.0
            if idle_h > _bl._stalled_worker_hours():
                return False, "EXECUTOR-DEAD (%.1fh 零产出，唤醒清单空)" % idle_h
        except Exception:
            pass          # 判不了就不排除（宁可不排除，也不许凭空拦活）
    if not info.get("online"):
        # 2026-11-07 去堵点：sense() 已经会用「车道文件新鲜度」给死掉的 NATS 客户端兜底，
        # 但这里只认心跳，于是同一台机器出现「online=True 却 CAPACITY-BLOCKED-RAM
        # OFFLINE (hb age Nones)」的自相矛盾——bm-a 明明在线在推产物，2 张 MV 卡却派不出去。
        # 判据统一：心跳没有记录不等于机器死了，车道文件新鲜就算在线。
        try:
            lp = os.path.join(ROOT, "cph4", "fleet", "lanes", "%s.json" % node)
            if os.path.exists(lp) and (time.time() - os.path.getmtime(lp)) <= OFFLINE_AFTER_S:
                info = dict(info, online=True,
                            state=info.get("state") or {"source": "lanes-file"})
            else:
                return False, "OFFLINE (hb age %ss, lane stale)" % info.get("age_s")
        except Exception:
            return False, "OFFLINE (hb age %ss)" % info.get("age_s")
    st = info.get("state") or {}
    spec = fl.LANES.get(node) or {}
    q = fl.quiet_hours(node)
    if q is not None and not (job is not None and job.get("day_ok")):
        # CEO 2026-11-02：公司工作机配置很高，白天可以跑**轻量**任务，只有重活让位。
        # 轻量判定=纯 CPU、非 heavy、不写大文件（est_gb<=2）、不用模型。
        light = bool(job is not None
                     and (job.get("needs") or "cpu") == "cpu"
                     and not job.get("heavy")
                     and int(job.get("est_gb") or 0) <= 2
                     and not (job.get("model") or ""))
        if not light:
            return False, "daytime heavy-yield (%02d:00-%02d:00); light CPU allowed" % (q[0], q[1])
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
    # A CPU job that declares no memory need is a script, not a model load: python +
    # a search/QC pass fits in well under 1GB. Keeping the full 2-3GB floor for those
    # left bm-c "CAPACITY-BLOCKED-RAM at 2.0GB free" while it could have run them -
    # idle caused by the gate itself (CEO 2026-11-01: 门槛太多导致闲置).
    # A rescue card exists to RECLAIM memory; blocking it because memory is low is
    # circular (2026-11-02: bm-b sat at 0.0GB free and nothing could run - not even the
    # script that frees memory). Rescue cards are allowed down to 0.2GB.
    if job is not None and job.get("rescue"):
        floor = 0.2
    elif needs == "cpu" and not job:
        floor = min(floor, 1.0)
    elif needs == "cpu":
        est = float(job.get("est_gb") or 0)
        if est <= 0 and not (job.get("model") or ""):
            floor = min(floor, 1.0)
    # CPU 饱和保护：一台机 CPU 已被占满时再派 CPU 活只会互相拖慢（此前没有这一维，
    # 因为机队根本不报 CPU 占用；2026-11-02 补遥测后才有依据）。
    if needs == "cpu":
        cpu = st.get("cpu_load_pct")
        if cpu is not None and float(cpu) >= 95:
            return False, "CPU-SATURATED %s%%" % cpu
    ram = st.get("ram_free_gb")
    if ram is None:
        return True, "ram-unknown"
    ok = float(ram) >= floor
    return ok, "ram %.1f/%.1f GB" % (float(ram), floor)


_PAUSED_CACHE = {}


def _paused_nodes():
    """CEO 暂停窗内的机器集合（AUTONOMY-CONFIG nodes.<id>.paused_by_ceo）。

    Why（2026-11-06 11:46 CEO 原话「我在工作」）：bm-a 被让路令暂停后，主控派单只看
    needs/心跳，照样把生产卡派到 CEO 正在用的桌面机上。暂停必须是一等状态。
    """
    try:
        cfg = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                           "cph4", "fleet", "AUTONOMY-CONFIG.json")
        if not os.path.exists(cfg):
            return set()
        if "_ts" in _PAUSED_CACHE and time.time() - _PAUSED_CACHE["_ts"] < 60:
            return _PAUSED_CACHE["s"]
        d = json.load(open(cfg, encoding="utf-8"))
        out = {k for k, v in (d.get("nodes") or {}).items()
               if isinstance(v, dict) and v.get("paused_by_ceo")}
        _PAUSED_CACHE.update({"s": out, "_ts": time.time()})
        return out
    except Exception:
        return set()


_SLOTS_CACHE = {}


def _slots_of(node):
    """一台机可同时接几张卡（AUTONOMY-CONFIG.supply.slots_per_node，缺省 1）。
    注意：本模块没有全局 ROOT（各函数都收 root 参数），这里自行解析，
    否则会抛异常静默回落到 1——首版就是这么写的，槽位等于没改。"""
    if _SLOTS_CACHE:
        return _SLOTS_CACHE.get(node, 1)
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.dirname(os.path.dirname(here))
        with open(os.path.join(root, "cph4", "fleet", "AUTONOMY-CONFIG.json"),
                  encoding="utf-8") as f:
            m = (json.load(f).get("supply") or {}).get("slots_per_node") or {}
        _SLOTS_CACHE.update({k: int(v) for k, v in m.items()})
    except Exception:
        pass
    return _SLOTS_CACHE.get(node, 1)


def _cmd_key(r):
    """同一件活的判据是命令本身，不是 id——三个生成器会给同一条命令发三张卡。"""
    return " ".join(str(r.get("cmd") or "").split())


def dedupe_pending(rows, pending):
    """同一命令同一刻只派一张（DUP-AT-CLAIM，2026-11-07/08 实锚）。

    line_triage 这类卡由 workgen(R-TRIAGE)、night_plan(R-PLAN)、line_agents(Q-TRIAGE)
    各发一张：id 前缀不同、cmd 一模一样，于是三台机同时跑同一份分诊，回执互相覆盖。
    去重只作用在"待派"这一层：已经在飞的命令整轮跳过，其余每种命令只留第一张。
    """
    inflight = {_cmd_key(r) for r in rows
                if r.get("state") == "RUNNING" and r.get("cmd")}
    kept, seen = [], set(inflight)
    for r in pending:
        k = _cmd_key(r)
        if k and k in seen:
            continue
        if k:
            seen.add(k)
        kept.append(r)
    return product_first(kept)


def product_first(rows):
    """产物优先：视频/图片/构建/回测先占槽位，流程文档类卡排在后面。

    CEO 2026-11-08「验收只看产物和质量，中间流程文档不算数」——派单口径必须同源，
    否则槽位会被分诊/审计/看板吃掉，一天下来验收面还是 0（实测 56 张完成=0 件产物）。
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import acceptance as ac
        cls = ac.classify
    except Exception:
        return rows
    order = {"PRODUCT": 0, "UNKNOWN": 1, "BOOKKEEPING": 2, "NONE": 3}
    return sorted(rows, key=lambda r: order.get(cls(r.get("deliverable")), 3))


def choose_lane(job, fleet, busy):
    needs = job.get("needs") or "cpu"
    pref = job.get("nodes") or []
    cap = job.get("cap") or ("llm" if (job.get("model") or "") == "local-small" else None)
    vram_min = int(job.get("vram_min_gb") or 0)
    candidates = [n for n in fl.LANES if needs in fl.LANES[n]["needs"]]
    _paused = _paused_nodes()
    if _paused:
        candidates = [n for n in candidates if n not in _paused]
    # hard_nodes = 真钉子（2026-11-03）：依赖本机私有服务（如 127.0.0.1:8188 的 ComfyUI）
    # 的卡必须在指定机上跑。nodes 只是偏好，hard_nodes 不许回落——否则卡会落到
    # 没有该服务的机器上，跑出"连不上"的假失败（实测 char-probe 落到主控即如此）。
    hard = job.get("hard_nodes") or []
    if hard:
        candidates = [n for n in candidates if n in hard]
    # OS-pinned cards (2026-11-03): an audit of the Windows box's ollama cannot be
    # answered by the Mac. Falling back there produced a BLOCKED receipt that the
    # closers booked as delivery - three times. Wait for the right box instead.
    if job.get("node_os"):
        candidates = [n for n in candidates if fl.card_os_ok(job, n)]
    if cap:
        candidates = [n for n in candidates
                      if cap in (fl.LANES[n].get("caps") or []) or not (fl.LANES[n].get("caps"))]
    if pref:
        # Preference, NOT a filter (2026-11-02): cards generated with nodes=["bm-c"]
        # made the dispatcher answer NO-CAPACITY while bm-a sat idle with 20GB free.
        # A pinned node now only ranks first; any compatible lane may take the job.
        pass
    scored = []
    stale_ok = []
    HB_STALE_S = 600
    for n in candidates:
        # 槽位并发（2026-11-08）：一台机同时能接几张由 AUTONOMY-CONFIG.supply.slots_per_node
        # 决定；GPU 活仍按物理卡串行（同一时刻只给一张），避免两个 ComfyUI 抢显存。
        _cur = busy.get(n) or []
        if len(_cur) >= _slots_of(n):
            continue
        if needs == "gpu" and any((j.get("needs") or "cpu") == "gpu" for j in _cur):
            continue
        # 心跳不新鲜就不是候选（2026-11-03 实测）：此前 lane_capacity 拿不到遥测时直接判
        # "ram-unknown → 可派"，于是 bm-b（执行器已死、无心跳）照样被派卡，0.1 秒 rc=2 回来
        # 再被反复重排——队列看起来在转，实际是一台死机在吃活。
        age = (fleet.get(n) or {}).get("age_s")
        # 2026-11-08：age 为 None 只表示"这个来源没读到"，不等于机器死了。
        # lane_capacity 已经会用车道文件兜底，这里也必须一致，否则 bm-c 明明在跑卡
        # 却因为 KV 没读到被判 ALL-OFFLINE-NO-HB，队列在排、机器在空。
        if age is None:
            try:
                lp = os.path.join(ROOT, "cph4", "fleet", "lanes", "%s.json" % n)
                fresh = os.path.exists(lp) and (time.time() - os.path.getmtime(lp)) <= HB_STALE_S
            except Exception:
                fresh = False
            if not fresh:
                stale_ok.append(n)
                continue
        elif float(age) > HB_STALE_S:
            stale_ok.append(n)
            continue
        # 机器准入按"真回执"判（2026-11-03）：心跳在线但近 7 天没回执的机器只接探针卡。
        # 证据：bm-b 心跳新鲜、近 7 天 3 份回执（24h 2 份），此前照派 20 分钟的重卡，
        # 结果是活被吃掉再重排——账上 RUNNING，产出为零。
        try:
            import lane_trust as _lt
            tier, _st, why_t = _lt.tier(n)
        except Exception:
            tier, why_t = "production", ""
        if tier in ("silent", "unknown"):
            stale_ok.append("%s(%s)" % (n, tier))
            continue
        # probe-only 的机器不是永远不能用：短活（est_min<=5）派的成本低、又必须让它交回执
        # 才能爬回 production。旧逻辑一律拒派，于是 bm-b 连续 18 轮 IDLE——越不派越没回执，
        # 永远出不了 probe-only（自我强化的死循环，2026-11-04 实测）。
        if tier == "probe-only" and not job.get("probe") and int(job.get("est_min") or 0) > 5:
            stale_ok.append("%s(probe-only: 只接短活/探针卡)" % n)
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
        rank = (0 if n in pref else 1, score)
        scored.append((rank, n))
    scored.sort()
    if not scored:
        # 全员失联时不让活停在队列里（CEO 2026-11-01：不许因环境原因闲置）：
        # 回落到心跳最近的那台并留痕，账面上能看出这是"没得选"。
        if stale_ok:
            # 只在"曾经报过心跳、只是刚刚过期"的机器里回落。age_s is None 表示从来没有
            # 心跳记录（bm-d 2026-10-29 起未入网）——派给它等于把卡扔进黑洞，实测
            # 2026-11-03 13:12 DUPES-SCAN 被派到 bm-d，白占一张卡一个租约周期。
            # 全部在线机都在忙时，正确动作是让卡排队，不是塞给死机。
            known = [n for n in stale_ok if (fleet.get(n) or {}).get("age_s") is not None]
            if not known:
                return None, "ALL-OFFLINE-NO-HB"
            best = min(known, key=lambda n: float((fleet.get(n) or {}).get("age_s") or 10 ** 9))
            return best, "assigned-stale-hb"
        return None, "NO-CAPACITY"
    return scored[0][1], "assigned"


def assign(rows, fleet, reports, lines=None):
    parked = {ln["id"] for ln in (lines or []) if (ln.get("status") or "") == "PARKED"}
    prio_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    busy = {}
    for r in rows:
        if r.get("state") == "RUNNING" and r.get("owner"):
            # 2026-11-08：busy 从「一机一卡」改成「一机一个卡列表」。
            # 以前 busy[owner]=卡 只记最后一张，choose_lane 又用 if busy.get(n) 一票否决，
            # 于是配置里 bm-a 8 槽 / bm-c 6 槽形同虚设——每台机永远只干一张，
            # 队列里排着 GPU 出图卡、机器却在报 SELF-DISPATCH。
            busy.setdefault(r["owner"], []).append(r)
    pending = [r for r in rows if r.get("state") == "OPEN"]
    pending = dedupe_pending(rows, pending)
    # 优先级（CEO 2026-11-02：所有子公司都保留，只分优先级）：P0 内容 > P1 游戏 >
    # P2 量化与前台 > P3 城市与渠道。低优先级不关停，只是排在后面，有书余算力就跑。
    try:
        reg = json.load(open(os.path.join(root, "cph4", "fleet", "LINE-REGISTRY.json"),
                             encoding="utf-8-sig"))
        pmap = {l.get("id"): int(str(l.get("priority") or "P2").lstrip("Pp")[0])
                for l in (reg.get("lines") or [])}
    except Exception:
        pmap = {}
    # 红了的线要插队，不是停摆：I14（P0 24h 无产物）红说明这条线缺产出，它手上的卡
    # 应当先跑出来，而不是被别的线挤在后面（2026-11-02 自审发现"断言红了没后果"）。
    # 组配额（2026-11-02）：只按优先级排队会让 P0 内容把 P0 游戏饿死。每组 24 小时
    # 有硬上限，超了就等下一窗口，保证四条线都有产能。
    org_of, caps, window_h = {}, {}, 24
    try:
        org_of = {l.get("id"): (l.get("org") or "platform") for l in (reg.get("lines") or [])}
        q = json.load(open(os.path.join(root, "cph4", "fleet", "QUOTA.json"), encoding="utf-8"))
        caps = q.get("caps") or {}
        window_h = int(q.get("window_h") or 24)
    except Exception:
        pass
    cutoff = __import__("datetime").datetime.now() - __import__("datetime").timedelta(hours=window_h)
    used = {}
    for r2 in rows:
        ts = str(r2.get("created_at") or "")
        try:
            if __import__("datetime").datetime.fromisoformat(ts) >= cutoff:
                o = org_of.get(r2.get("line") or line_of_job(r2, lines or []), "platform")
                used[o] = used.get(o, 0) + 1
        except Exception:
            pass

    red_lines = set()
    try:
        inv = json.load(open(os.path.join(root, "cph4", "fleet", "state", "invariants.json"),
                             encoding="utf-8"))
        for c in inv.get("checks") or []:
            if c.get("id") != "I14":
                continue
            for s in (c.get("samples") or []):
                if s.startswith("p0:"):
                    red_lines.add(s.split(":")[1])
    except Exception:
        pass
    # 解锁下游数量优先（CEO 2026-11-03 定的排序判据 A：解锁下游多者先做）。
    # 2026-11-04 实测病：产物回传卡挂在 fleet-ops（P3），于是永远让给 P0 内容卡，
    # 3 条线（mv/drama/game）其实都在等它的产物——线优先级压住了真实解锁量，通道卡永远排不上。
    _unlocks = {}
    _deliv = {}
    for _r in list(pending) + [r for r in rows]:
        _d = _r.get("deliverable")
        if _d:
            _deliv[os.path.basename(str(_d).replace("\\", "/"))] = _r.get("id")
    for _r in pending:
        for _req in (_r.get("requires") or []):
            _b = os.path.basename(str(_req).replace("\\", "/"))
            _prod = _deliv.get(_b)
            if _prod:
                _unlocks[_prod] = _unlocks.get(_prod, 0) + 1
    def _is_product(r):
        d = str(r.get("deliverable") or "").replace(chr(92), "/")
        return d.startswith(("gaming/", "media/", "quant/", "domain/", "life/",
                             "compute/", "house/", "research/")) or "/outbound/" in d

    pending.sort(key=lambda r: (0 if (r.get("line") or line_of_job(r, lines or [])) in red_lines else 1,
                                -_unlocks.get(r.get("id"), 0),
                                0 if _is_product(r) else 1,
                                pmap.get(r.get("line") or line_of_job(r, lines or []), 2),
                                prio_rank.get(str(r.get("prio") or "P2"), 2),
                                str(r.get("created_at") or "")))
    events = []
    for r in pending:
        if r.get("route") in ("blocked", "queue"):
            continue
        if line_of_job(r, lines or []) in parked:
            continue
        _org = org_of.get(r.get("line") or line_of_job(r, lines or []), "platform")
        if caps and used.get(_org, 0) >= int(caps.get(_org, 999)):
            continue          # 该组本窗口配额已满，让位给别的组
        # Never let the cron spend cloud money: cloud-smart work waits for the smart seat.
        if (r.get("model") or "none") == "cloud-smart":
            continue
        lane, why = choose_lane(r, fleet, busy)
        if not lane:
            continue
        r["state"] = "RUNNING"
        r["owner"] = lane
        if why == "assigned-stale-hb":
            r["dispatch_note"] = "全员心跳过期，回落 %s（其余机器无心跳，非优选）" % lane
        # 2026-11-02：卡声明了 nodes 却被别的机器接走时，必须留下痕迹。
        # 实测：一张 nodes=["bm-a"] 的卡被 bm-m 领走、无 fallback 标记、直接判 DONE，
        # 从账面上看像是"公司生产力跑通了"，其实根本没到那台机——静默改派=假绿。
        _pref = r.get("nodes") or []
        if _pref and lane not in _pref:
            r["fallback_from"] = _pref
            r["fallback_why"] = "pinned node(s) not available at dispatch time"
        r["claimed_at"] = fl.now_iso()
        r["assign_ts"] = r["claimed_at"]
        r["lease_minutes"] = int(r.get("timeout_s") or 0) // 60 or \
            DEFAULT_LEASE.get(r.get("needs") or "cpu", 45)
        busy.setdefault(lane, []).append(r)
        used[_org] = used.get(_org, 0) + 1
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
        # 并发槽位（CEO 2026-11-05「不许没满负荷」）：一次只给一张卡 = 空槽是假容量。
        # 槽位数在 AUTONOMY-CONFIG.supply.slots_per_node；GPU 卡由车道侧再串行一层。
        try:
            with open(os.path.join(root, "cph4", "fleet", "AUTONOMY-CONFIG.json"),
                      encoding="utf-8") as _cf:
                _slots = int((((json.load(_cf).get("supply") or {}).get("slots_per_node")
                               or {}).get(n, 1)) or 1)
        except Exception:
            _slots = 1
        payload = {"node": n, "ts": fl.now_iso(), "jobs": jobs[:max(1, _slots)],
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
def cycle(root, dry=False, push=True, node="bm-a", fallback_stale_s=900):
    owner_node = master_node(root)
    masquerade = False
    if node != owner_node:
        # The declared master is the Mac, which is on-demand by CEO order - so it can be
        # asleep for hours while jobs sit unassigned (2026-10-31: 13h45m dark). A fallback
        # node may take over ONLY when the declared master's own last tick is stale.
        # MASTER-STATE is also refreshed by the Mac's pulse snapshot, which is why staleness
        # reads a dedicated tick file that only a real scheduler run writes.
        tick = fl.read_json(os.path.join(root, TICK_REL.replace("/", os.sep)), {}) or {}
        prev_ts = str(tick.get("ts") or "")
        prev_by = str(tick.get("last_tick_by") or "")
        stale = True
        try:
            age = (datetime.now() - datetime.strptime(prev_ts, "%Y-%m-%dT%H:%M:%S")).total_seconds()
            stale = age > fallback_stale_s
        except Exception:
            stale = True
        if prev_by and prev_by != owner_node:
            stale = True   # the last tick was itself a fallback: the real master is still dark
        if not stale:
            pass
        else:
            masquerade = True
    if node != owner_node and not masquerade:
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
    # Dispatcher edits must survive this cycle (D-R272-MASTER-FULLLIST-CLOBBER, 2026-11-03):
    # merge_jsonl merges by id, but passing the whole cycle-start list rewrites EVERY row,
    # silently reverting whatever another leg wrote after we read. Push only what changed.
    _qsnap = {r.get("id"): json.dumps(r, sort_keys=True, default=str) for r in rows}
    # BUSY-SILENT: a box that holds a RUNNING card and has gone quiet is producing, not
    # dead. Dropping it from dispatch because lane_agent is blocked inside a long job is
    # how a TTS batch looked "offline" while it was working (2026-11-01). Mark it online
    # with an explicit note so supervision can tell silence from absence.
    try:
        for _r in rows:
            if _r.get("state") != "RUNNING":
                continue
            for _n in (_r.get("nodes") or []):
                _f = fleet.get(_n) or {}
                if not _f.get("online") and (_r.get("owner") == _n or _n in fl.LANES):
                    _f["online"] = True
                    _f["busy_silent"] = True
                    _f["note"] = "busy-silent: RUNNING %s, heartbeat stale" % _r.get("id")
                    fleet[_n] = _f
    except Exception:
        pass
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
        # merge by id under a lock; a whole-list dump lost concurrent closer/workgen edits
        # and also reverted dispatcher pins (D-R272-MASTER-FULLLIST-CLOBBER): push only the
        # rows this cycle actually changed.
        _qchg = [r for r in rows if _qsnap.get(r.get("id"))
                 != json.dumps(r, sort_keys=True, default=str)]
        if _qchg:
            fl.merge_jsonl(os.path.join(root, fl.QUEUE_REL.replace("/", os.sep)), _qchg)
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
            "last_result": {k: rep.get(k) for k in ("job", "state", "rc", "ts", "reason", "out_bytes", "elapsed_s")} if rep else None,
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
             "master_node": owner_node, "masquerade_by": node if masquerade else None,
             "master_tick_ts": (prev.get("master_tick_ts") or prev.get("ts") or now_ts)
                               if masquerade else now_ts,
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
        fl.write_json(os.path.join(root, TICK_REL.replace("/", os.sep)),
                      {"declared_master": owner_node, "last_tick_by": node,
                       "ts": now_ts, "masquerade": masquerade})
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
                           capture_output=True, text=True, errors="replace", timeout=20,
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
            # CEO 2026-10-30: cloud quota nearly exhausted -> default answer is LOCAL.
            # The judgment seat itself is now bm-m's resident 35B (local_judge.py), so
            # this stays a decision record, never a spend request.
            add("MODEL-DECISION", r.get("id"),
                "此活要走云端(codely)吗？先判：本地模型或 bm-m 共享大脑(100.75.133.10:11434)能否完成？能则降级 local-small，不能才放行云端并记 est_credits。",
                {"title": r.get("title"), "why": r.get("why"),
                 "est_credits": r.get("cloud_est_credits"), "seat": "local-only"})
        if r.get("state") == "OPEN" and int(r.get("attempts") or 0) >= 2:
            add("RETRY", r.get("id"),
                "这件活已重排 %d 次仍未收口，是工具坏了、输入缺失还是车道不合适？" %
                int(r.get("attempts") or 0),
                {"note": r.get("note"), "needs": r.get("needs")})
    for lid, ls in lines_state.items():
        if ls["verdict"] == "STALE":
            # LINE-STALE questions are answered by machinery now, not by a model:
            # night_plan reads LINE-NEXT-STEPS.json and dispatches that line's declared
            # next product. Asking a 4B「这条线该做什么」produced 20+ identical rows that
            # nobody could answer usefully (2026-11-01) - so only ask when there is NO
            # declared next step, i.e. when a direction decision is genuinely missing.
            if not _has_next_step(root, lid):
                add("LINE-STALE", lid,
                    "这条线 %.0f 小时没有产出、且没有已声明的下一步产物，方向该怎么定？" % (ls["age_h"] or 0),
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
TICK_REL = "cph4/fleet/dispatcher/MASTER-TICK.json"


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
    # 2026-11-05 止血（部署设计 v1 §八）：git.mode=off 时不做任何 push/rebase。
    # 实测这段每次派单要卡 120s（git push 超时 + fetch + rebase 重试），且 rebase
    # 是"人工提交被摘掉"的另一个源头。关掉后派单回到秒级，同步交给 S4 账房。
    try:
        with open(os.path.join(root, "cph4", "fleet", "AUTONOMY-CONFIG.json"),
                  encoding="utf-8") as _gf:
            if str(((json.load(_gf).get("git") or {}).get("mode") or "full")) == "off":
                return True
    except Exception:
        pass
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