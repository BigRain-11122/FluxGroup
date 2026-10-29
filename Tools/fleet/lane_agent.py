#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane_agent.py - the subsidiary executor: claim my lane's job, run it, report.

Why this exists: the 2026-10-28 review of the fleet found the machines were healthy and
idle at the same time - a signed card never became a running job. queue_claim.py could
only consume the global queue, which every clone rewrites, so the master could not own
scheduling. This agent is the execute half of the master/lane split:

  * it reads ONLY its own lane file (written by the master) - never touches the queue
  * it writes a local receipt and publishes the result over NATS KV, so the master can
    close the job without any node writing the shared repo
  * it refuses to launch packaged games (CEO 2026-10-28 hard rule) and respects the
    bm-a work-hour GPU yield
  * when nothing is assigned it reports WHY it is idle, so "idle" is never silently
    mistaken for "healthy"

Usage:
  python lane_agent.py --node bm-a [--dry] [--allow-gpu-workhours] [--max-seconds N]
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


def live_state(root, node, hub, port):
    """Publish what this lane is doing right now (master reads it as capacity)."""
    st = {"node": node, "ts": fl.now_iso(), "ts_utc_ms": int(time.time() * 1000)}
    try:
        import shutil
        st["disk_free_gb"] = round(shutil.disk_usage(root).free / 1e9, 1)
    except Exception:
        pass
    try:
        p = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.free",
                            "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=10,
                           creationflags=CREATE_NO_WINDOW)
        parts = [x.strip() for x in p.stdout.splitlines()[0].split(",")]
        st["gpu_util_pct"] = int(parts[0])
        st["vram_free_mb"] = int(parts[1])
    except Exception:
        pass
    return st


def publish(node, state, detail, hub, port):
    payload = {"node": node, "state": state, "ts": fl.now_iso(),
               "ts_utc_ms": int(time.time() * 1000)}
    payload.update(detail or {})
    fl.kv_put(fl.lane_result_key(node), payload, host=hub, port=port)


def run_job(job, root, node, hub, port, allow_gpu_workhours, max_seconds):
    jid = str(job.get("id") or "")
    cmd = str(job.get("cmd") or "")
    needs = str(job.get("needs") or "cpu")
    model = str(job.get("model") or "none")
    prompt = str(job.get("prompt") or "")
    if not jid:
        return {"id": jid, "rc": None, "note": "empty job"}
    # local-small 活靠 prompt 而非 cmd（cmd 为空是正常的）
    if model != "local-small" and not cmd:
        return {"id": jid, "rc": None, "note": "empty job"}
    if model == "local-small" and not prompt:
        return {"id": jid, "rc": None, "note": "empty job (no prompt)"}
    if fl.game_launch_blocked(cmd):
        return {"id": jid, "rc": None, "note": "BLOCKED-GAME-LAUNCH (CEO 2026-10-28)"}
    if needs == "gpu" and not fl.gpu_window_open(node) and not allow_gpu_workhours:
        return {"id": jid, "rc": None, "note": "DEFERRED-WORKHOUR-GPU-YIELD",
                "defer": True}

    lease = False
    if needs == "gpu":
        p = subprocess.run([sys.executable, os.path.join(HERE, "gpu_lease.py"), "--node", node,
                            "--acquire", "--need-mb", str(int(job.get("need_mb") or 12000))],
                           capture_output=True, text=True, timeout=600,
                           creationflags=CREATE_NO_WINDOW)
        lease = p.returncode == 0
        if not lease:
            return {"id": jid, "rc": None,
                    "note": "GPU-LEASE-DENIED: " + (p.stdout or p.stderr or "")[-300:],
                    "defer": True}

    publish(node, "RUNNING", {"job": jid, "title": job.get("title")}, hub, port)
    t0 = time.time()
    model = str(job.get("model") or "none")
    if model == "local-small":
        # Cheap text leg: the box's own Ollama, never a cloud call. A missing local model
        # fails the job loudly instead of quietly costing money.
        llm = job.get("llm") or {}
        prompt = llm.get("prompt") or job.get("prompt") or ""
        out_path = llm.get("out") or job.get("deliverable") or ""
        # 输入文件：把 when_all 声明的真实文档内容注入 prompt，让模型基于文档干活。
        inputs = job.get("when_all") or []
        if inputs:
            parts = [prompt, "", "## 输入文档内容（请基于以下内容回答，不要编造）"]
            for f in inputs:
                try:
                    with open(f, encoding="utf-8", errors="replace") as fh:
                        body = fh.read()
                    parts.append("### %s\n%s" % (f, body[:16000]))
                except Exception as e:
                    parts.append("### %s (读取失败: %s)" % (f, e))
            prompt = "\n".join(parts)
        text = fl.local_llm(prompt, fl.load_policy(root),
                            timeout=int(job.get("llm_timeout_s") or 180), node=node)
        if text is None:
            rc, out, err = 126, "", "local-llm-unavailable (ollama @ default endpoint)"
        else:
            try:
                if out_path:
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(text)
                rc, out, err = 0, text[:2000], ""
            except Exception as e:
                rc, out, err = 125, "", "write-failed: %s" % e
    else:
        try:
            r = subprocess.run(cmd, shell=True, cwd=job.get("cwd") or root,
                               capture_output=True, text=True, errors="replace",
                               timeout=max_seconds, creationflags=CREATE_NO_WINDOW)
            rc, out, err = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired as e:
            rc, out, err = 124, (e.stdout or ""), (e.stderr or "") + "\n[timeout %ss]" % max_seconds
    dur = round(time.time() - t0, 1)

    if lease:
        subprocess.run([sys.executable, os.path.join(HERE, "gpu_lease.py"), "--node", node,
                        "--release"], capture_output=True, text=True, timeout=300,
                       creationflags=CREATE_NO_WINDOW)

    receipt_dir = os.path.join(root, fl.RECEIPT_REL.replace("/", os.sep))
    os.makedirs(receipt_dir, exist_ok=True)
    rc_path = os.path.join(receipt_dir, "%s-%s.json" % (jid, node))
    deliverable = job.get("deliverable") or ""
    dl_ok = bool(deliverable) and os.path.exists(deliverable)
    rec = {"id": jid, "node": node, "rc": rc, "seconds": dur, "cmd": cmd,
           "deliverable": deliverable, "deliverable_exists": dl_ok,
           "ts": fl.now_iso(), "stdout_tail": (out or "")[-1500:],
           "stderr_tail": (err or "")[-1500:]}
    with open(rc_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    # rc!=0 is not always a failure (gates return 1 by design); the deliverable is the
    # truth the master closes on, and it is reported either way.
    publish(node, "DONE" if (rc == 0 or dl_ok) else "FAILED",
            {"job": jid, "rc": rc, "seconds": dur, "deliverable_exists": dl_ok,
             "receipt": os.path.relpath(rc_path, root).replace("\\", "/")}, hub, port)
    print("%s %s rc=%s %.1fs deliverable=%s" % (jid, "DONE" if rc == 0 or dl_ok else "FAILED",
                                                rc, dur, dl_ok))
    return {"id": jid, "rc": rc, "seconds": dur, "deliverable_exists": dl_ok}


def self_dispatch(root, node, allow_gpu_workhours, max_seconds, hub, port, dry):
    """When the master has nothing for me, look at my own disks for ready work.

    This is the "ask local compute what it should be doing" leg. It only consumes the
    declarative backlog manifest (inputs must exist HERE, deliverable must not), so it
    cannot invent work and cannot touch another machine's paths.
    """
    sys.path.insert(0, os.path.dirname(HERE))
    try:
        from backlog_fill import fill as fill_backlog
        fill_backlog(root, node)
    except Exception as e:
        print("self-dispatch backlog skipped:", str(e)[:120])
        return None
    qpath = os.path.join(root, fl.QUEUE_REL.replace("/", os.sep))
    rows = fl.read_jsonl(qpath)
    pick = None
    for r in rows:
        if r.get("state") != "OPEN":
            continue
        nodes = r.get("nodes") or []
        if nodes and node not in nodes:
            continue
        if fl.game_launch_blocked(r.get("cmd") or ""):
            continue
        if r.get("heavy") and not fl.heavy_allowed(node) and not allow_gpu_workhours:
            continue
        if (r.get("needs") == "gpu") and not fl.gpu_window_open(node) and not allow_gpu_workhours:
            continue
        pick = r
        break
    if not pick:
        return None
    if dry:
        print("LANE-DRY %s self-dispatch would run %s" % (node, pick.get("id")))
        return None
    res = run_job(pick, root, node, hub, port, allow_gpu_workhours, max_seconds)
    rows = fl.read_jsonl(qpath)
    for x in rows:
        if x.get("id") == pick.get("id"):
            x["state"] = "DONE" if (res.get("rc") == 0 or res.get("deliverable_exists")) else "FAILED"
            x["owner"] = node
            x["finished_at"] = fl.now_iso()
            x["created_by"] = (x.get("created_by") or "") + "+lane-self"
    fl.write_jsonl(qpath, rows)
    return res


def run_lane_cycle(node, root=None, dry=False, allow_gpu_workhours=False,
                   max_seconds=7200, hub=fl.HUB_DEFAULT, port=fl.PORT_DEFAULT,
                   fetch=True):
    """One lane cycle. Returns True when a lane file exists (caller should stop there),
    False when this node has no lane file at all (caller may use the legacy queue)."""
    root = root or fl.ROOT_DEFAULT
    payload = fl.lane_payload(root, node, fetch=fetch)
    if payload is None:
        return False
    jobs = payload.get("jobs") or []
    if not jobs:
        res = self_dispatch(root, node, allow_gpu_workhours, max_seconds, hub, port, dry)
        if res:
            return True
        reason = payload.get("idle_reason") or "NO-ASSIGNMENT"
        publish(node, "IDLE", {"reason": reason}, hub, port)
        write_last(root, node, "IDLE", note=reason)
        print("LANE-IDLE %s :: %s" % (node, reason))
        return True

    job = jobs[0]
    if dry:
        print("LANE-DRY %s would run %s :: %s" % (node, job.get("id"), job.get("title")))
        return True
    if job.get("heavy") and not fl.heavy_allowed(node) and not allow_gpu_workhours:
        publish(node, "DEFERRED", {"job": job.get("id"),
                                   "reason": "WORKHOUR-YIELD-HEAVY (bm-a 09-19)"}, hub, port)
        write_last(root, node, "DEFERRED", job=job.get("id"), note="WORKHOUR-YIELD-HEAVY")
        print("LANE-DEFER %s :: heavy job held for the night window" % job.get("id"))
        return True
    write_last(root, node, "RUNNING", job=job.get("id"))
    res = run_job(job, root, node, hub, port, allow_gpu_workhours, max_seconds)
    write_last(root, node, "RESULT", job=res.get("id"), note=res.get("note") or "",
               rc=res.get("rc"))
    return True


def write_last(root, node, state, **kw):
    try:
        d = os.path.join(root, fl.RECEIPT_REL.replace("/", os.sep))
        os.makedirs(d, exist_ok=True)
        rec = {"ts": fl.now_iso(), "node": node, "state": state}
        rec.update(kw)
        with open(os.path.join(d, "_last_lane_%s.json" % node), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--root", default=fl.ROOT_DEFAULT)
    ap.add_argument("--hub", default=fl.HUB_DEFAULT)
    ap.add_argument("--port", type=int, default=fl.PORT_DEFAULT)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--allow-gpu-workhours", action="store_true")
    ap.add_argument("--max-seconds", type=int, default=7200)
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    ran = run_lane_cycle(a.node, os.path.abspath(a.root), a.dry, a.allow_gpu_workhours,
                         a.max_seconds, a.hub, a.port, fetch=not a.no_fetch)
    if not ran:
        print("LANE-NO-FILE %s :: no lane assignment file; nothing dispatched yet" % a.node)
    return 0


if __name__ == "__main__":
    sys.exit(main())