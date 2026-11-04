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
import threading
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fleet_lane as fl  # noqa: E402
import flux_contracts as fc  # noqa: E402

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
# 长任务存活上报间隔：既不刷爆 NATS，又能让主控在 1-2 分钟内看出一台机"在忙"而不是"死了"。
PROGRESS_EVERY = 45


def live_state(root, node, hub, port):
    """Publish what this lane is doing right now (master reads it as capacity)."""
    st = {"node": node, "ts": fl.now_iso(), "ts_utc_ms": int(time.time() * 1000)}
    try:
        import shutil
        st["disk_free_gb"] = round(shutil.disk_usage(root).free / 1e9, 1)
    except Exception:
        pass
    # CPU 遥测（此前完全缺失：调度只能看内存与显存，CPU 是瞎的）
    try:
        st["cpu_cores"] = os.cpu_count() or 1
    except Exception:
        pass
    pct = fl.cpu_load_pct(root, node)
    if pct is not None:
        st["cpu_load_pct"] = pct
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


def git_publish(root, node, jid, paths):
    """Commit + push this job's artifact so the fleet can actually see it.

    Why (2026-11-01): the lane used to leave its output on the local disk and report
    "done" over NATS. Every verifier lives on git, so a produced card looked unproven from
    every other machine. Publishing here makes "done" mean "on the shared surface".
    Returns a short status string; never raises past this function.
    """
    keep = []
    for p in paths:
        if not p:
            continue
        full = p if os.path.isabs(p) else os.path.join(root, p)
        rel = os.path.relpath(full, root).replace("\\", "/")
        if rel.startswith("..") or rel.startswith("media/") or rel.startswith("gaming/") or rel.startswith("quant/"):
            # Untracked trees: committing them would blow the repo up (media is GBs).
            continue
        if os.path.exists(full):
            keep.append(rel)
    # R2.61 (2026-11-02): the status write this job makes to the shared queue is part of its
    # output, but it was never committed. The tree therefore stayed dirty, so when a push lost
    # the race to the master's once-a-minute commit the retry's own `pull --rebase` refused on
    # "unstaged changes", the local commit was stranded, and every later ff-only/rebase refused
    # too -- bm-c sat ahead/behind 1/2 and kept running stale code. Commit it alongside the
    # artifact so the tree is clean whenever we go to the wire.
    queue_rel = "cph4/fleet/PRODUCTION-QUEUE.jsonl"
    try:
        st = subprocess.run(["git", "-C", root, "status", "--porcelain"], capture_output=True,
                            text=True, timeout=60, creationflags=CREATE_NO_WINDOW).stdout or ""
        for ln in st.splitlines():
            p = ln[3:].strip()
            if p.startswith("cph4/fleet/") and p.endswith((".jsonl", ".json", ".md")):
                keep.append(p)
    except Exception:
        pass
    if not keep:
        return "nothing-tracked"
    def git(args, timeout=90):
        return subprocess.run(["git", "-C", root] + args, capture_output=True, text=True,
                              timeout=timeout, creationflags=CREATE_NO_WINDOW)
    git(["add", "--"] + keep)
    # Nothing actually changed -> do not create another commit for the same artifact.
    # The night of 11-01/02 produced 14 identical commits for one triage file.
    st = git(["status", "--porcelain", "--"] + keep)
    if not (st.stdout or "").strip():
        return "unchanged"
    msg = "job(%s): %s [via %s]" % (jid, "artifact", node)
    r = git(["commit", "-q", "-m", msg, "--"] + keep)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout or "") + (r.stderr or ""):
        return "commit-failed:%s" % (r.stderr or r.stdout)[:80]
    # R2.61: one retry was not enough against a master that commits every ~60s -- the second
    # attempt often lost the same race and the artifact stayed local. Give it three, and never
    # leave a half-finished rebase behind (that residue is what turned into the stuck loop).
    last = ""
    for _ in range(3):
        r = git(["push", "origin", "HEAD:main"], timeout=120)
        if r.returncode == 0:
            return "pushed"
        last = r.stderr or r.stdout
        # 2026-11-04：禁 rebase。多机同推时 pull --rebase 会在共享工作树留 UU 冲突，实测把
        # 主控仓卡在 98 步 rebase 中段（冲突标记进队列、读方静默跳过 21 行卡）。只快进；
        # 快进不了就放弃本轮，产物留本地，由主控脉按 merge 口径收口。
        rb = git(["pull", "--ff-only", "--no-rebase", "origin", "main"], timeout=120)
        if rb.returncode != 0:
            break
    return "push-failed:%s" % (last or "")[:80]


def already_closed(root, jid):
    """True when the shared queue already considers this card finished.

    Why: a stale lane file (or a takeover master that disagrees with origin) keeps handing
    the same card back, so the box re-runs a finished job every cycle - the same triage
    artifact was rewritten and re-committed 14 times on the night of 11-01/02. The lane
    must trust the shared queue's terminal states, not only its local assignment.
    """
    try:
        qp = os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
        with open(qp, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                r = json.loads(ln)
                if r.get("id") == jid:
                    return str(r.get("state") or "").upper() in ("DONE", "UNVERIFIED", "CANCELLED")
    except Exception:
        pass
    return False


def _card_gate(row, root, node):
    """卡片可执行性体检（2026-11-03）：返回 (ok, why)。

    把"卡片写错了"和"任务跑失败了"分开：前者不该消耗一台机的可靠性账，
    更不该让主控以为这台机器不行而把活全自己扛。判据见 card_gate.py。
    """
    try:
        import card_gate as _cg
        g = _cg.check(row, _cg.default_roots(root), node)
        if not g["ok"]:
            why = "; ".join("%s %s" % (i["code"], i["detail"]) for i in g["issues"] if i["fatal"])
            return False, why
        return True, ""
    except Exception as e:
        return True, "gate-skipped:%s" % str(e)[:80]


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

    # 解释器归一（2026-11-02 实测）：卡在 Windows 上写成 `python ...`，Mac 执行器 PATH 里
    # 只有 python3，于是 rc=127 且 0.0 秒、零产物（回执 R-TRIAGE-BIGSTREAMDRAMA 实锚）。
    # 这里按"本机有没有 python"决定是否改写，而不是靠人记得写对。
    # 2026-11-04 补：反过来也成立——Windows 执行器（服务/SYSTEM 上下文）PATH 里没有
    # `python`，实测 bm-a/bm-c 的 caption 卡双双 rc=127 CARD-DEFECT，看着像卡写错，
    # 其实是解释器名字本机不存在。按 python → py -3 → python3 → 当前解释器 逐个探。
    import shutil as _sh
    _head = cmd.split(" ", 1)[0] if cmd else ""
    if _head in ("python", "python3"):
        _rest = cmd[len(_head):]
        if not _sh.which(_head):
            for cand in ("py -3", "python3"):
                _exe = cand.split(" ", 1)[0]
                if _sh.which(_exe):
                    cmd = cand + _rest
                    break
            else:
                # 最后兜底：跑 lane 的这个解释器一定存在，且一定有 stdlib。
                cmd = sys.executable + _rest
            job["cmd_resolved"] = cmd
    # CEO 2026-10-30 "缺什么让他自己装啊": self-heal the toolchain on THIS box, in the
    # lane's own process, before spending a claim on a command that cannot run.
    try:
        import env_selfheal
        _tool = env_selfheal.first_tool(cmd)
        if _tool and not env_selfheal.have(_tool):
            _ok, _det = env_selfheal.ensure(_tool)
            if not _ok:
                return {"id": jid, "rc": None,
                        "note": "SELFHEAL-FAILED %s: %s" % (_tool, _det)}
    except Exception as _e:
        print("selfheal skipped:", str(_e)[:100])
    # 卡面闸（第二道，2026-11-03）：主控指定给本机的卡也验一次。写错的卡当场记
    # CARD-DEFECT 并落回执，不拿 4 秒"失败"去污染这台机的可靠性账。
    _gate_cwd = None
    if cmd:
        try:
            import card_gate as _cg2
            _g = _cg2.check(dict(job, cmd=cmd), _cg2.default_roots(root), node)
            if not _g["ok"]:
                _gwhy = "; ".join("%s %s" % (i["code"], i["detail"]) for i in _g["issues"] if i["fatal"])
                _rp = ""
                try:
                    _rd = os.path.join(root, fl.RECEIPT_REL.replace("/", os.sep))
                    os.makedirs(_rd, exist_ok=True)
                    _rp = os.path.join(_rd, "%s-%s.json" % (jid, node))
                    with open(_rp, "w", encoding="utf-8") as _f:
                        json.dump({"id": jid, "node": node, "rc": 127, "seconds": 0.0,
                                   "cmd": cmd, "outcome": "CARD-DEFECT",
                                   "card_defect": _gwhy, "ts": fl.now_iso()},
                                  _f, ensure_ascii=False, indent=1)
                except Exception:
                    pass
                publish(node, "FAILED", {"job": jid, "card_defect": _gwhy[:300],
                                         "receipt": _rp}, hub, port)
                print("%s CARD-DEFECT %s" % (jid, _gwhy[:200]))
                return {"id": jid, "rc": 127, "note": "CARD-DEFECT: " + _gwhy[:400],
                        "card_defect": True}
            _gate_cwd = _g["cwd"]
        except Exception as _ge:
            print("card gate skipped:", str(_ge)[:100])

    if needs == "gpu" and not fl.gpu_window_open(node) and not allow_gpu_workhours:
        return {"id": jid, "rc": None, "note": "DEFERRED-WORKHOUR-GPU-YIELD",
                "defer": True}

    lease = False
    if needs == "gpu":
        p = subprocess.run([sys.executable, os.path.join(HERE, "gpu_lease.py"), "--node", node,
                            "--acquire", "--need-mb", str(int(job.get("need_mb") or 12000)),
                            "--owner", node, "--job", jid],
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
        # 2026-11-02：原来是裸 subprocess.run，整段阻塞到任务结束——长任务（如 57 集配音批）
        # 期间一个字节都不上报，主控只能看到"心跳停了 137 分钟"，把正在干活的机器判成掉线，
        # 还可能按租约超时把卡重排。改为后台线程跑命令、主线程每 PROGRESS_EVERY 秒发一次
        # BUSY 进度（只报活性与已跑时长，不改任务语义、不改 stdout/stderr 处理）。
        _box = {}

        def _exec():
            try:
                r = subprocess.run(cmd, shell=True, cwd=_gate_cwd or job.get("cwd") or root,
                                   capture_output=True, text=True, errors="replace",
                                   timeout=max_seconds, creationflags=CREATE_NO_WINDOW)
                _box.update(rc=r.returncode, out=r.stdout, err=r.stderr)
            except subprocess.TimeoutExpired as e:
                _box.update(rc=124, out=(e.stdout or ""),
                            err=(e.stderr or "") + "\n[timeout %ss]" % max_seconds)
            except Exception as e:
                _box.update(rc=125, out="", err="exec-failed: %s" % e)

        _t = threading.Thread(target=_exec, daemon=True)
        _t.start()
        while _t.is_alive():
            _t.join(timeout=PROGRESS_EVERY)
            if not _t.is_alive():
                break
            try:
                fl.kv_put(fl.lane_result_key(node),
                          {"node": node, "state": "BUSY", "job": jid,
                           "elapsed_s": int(time.time() - t0), "ts": fl.now_iso()},
                          host=hub, port=port)
            except Exception:
                pass
        rc = _box.get("rc", 125)
        out = _box.get("out", "")
        err = _box.get("err", "")
    dur = round(time.time() - t0, 1)

    if lease:
        subprocess.run([sys.executable, os.path.join(HERE, "gpu_lease.py"), "--node", node,
                        "--release", "--owner", node], capture_output=True, text=True, timeout=300,
                       creationflags=CREATE_NO_WINDOW)

    receipt_dir = os.path.join(root, fl.RECEIPT_REL.replace("/", os.sep))
    os.makedirs(receipt_dir, exist_ok=True)
    rc_path = os.path.join(receipt_dir, "%s-%s.json" % (jid, node))
    deliverable = job.get("deliverable") or ""
    # Resolve against the repo root: lane_agent may run from anywhere, and a relative
    # deliverable checked against the wrong cwd reported "missing" for a file that exists.
    dl_abs = deliverable if os.path.isabs(deliverable) else (
        os.path.join(root, deliverable) if deliverable else "")
    dl_ok = fc.artifact_ok(dl_abs)
    # Success is a contract, not a feeling (2026-11-02): rc must be in the card's ok_rc
    # AND the declared deliverable must be on disk. Until today "a file exists" alone
    # booked rc=9009 (command not found) as DONE, so the books said done while nothing ran.
    ok = fc.is_ok(job, rc, dl_ok)
    if ok:
        err_cls = None
    elif rc == 0:
        err_cls = "E-ARTIFACT"      # ran cleanly but did not produce what the card promised
    elif ("MISSING " in (out or "")) or ("No such file" in ((out or "") + (err or ""))):
        # Input path absent on THIS box (D-R270-NO-INPUT-PRECHECK). Naming it stops the
        # next reader from re-issuing the same card here: the fix is another node, not a retry.
        err_cls = "E-INPUT"
    else:
        err_cls = fc.error_class(rc)
    rec = {"id": jid, "node": node, "rc": rc, "seconds": dur, "cmd": cmd,
           "ok_rc": fc.ok_rc(job), "outcome": "OK" if ok else "FAIL",
           "error_class": err_cls,
           "deliverable": deliverable, "deliverable_exists": dl_ok,
           "ts": fl.now_iso(), "stdout_tail": (out or "")[-1500:],
           "stderr_tail": (err or "")[-1500:]}
    with open(rc_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    # 影子期事件（2026-11-03 S1）：回执同时记一条 RECEIPT 事件。只写不读，失败不影响执行。
    try:
        import flux_eventlog as _ev
        _ev.emit("RECEIPT", jid, node, 1,
                 {"rc": rc, "outcome": rec["outcome"], "error_class": err_cls,
                  "deliverable_exists": dl_ok, "seconds": dur})
        # 远端机没有常驻主控脉，只在自己出件时把本机 outbox 推一次：
        # 否则每台机的 outbox 会永远积压，事件流永远只看得见主控那台。
        _ev.relay(50)
    except Exception:
        pass

    # Push the artifact back to the shared surface. Until 2026-11-01 the lane wrote its
    # receipt on the local disk and told the master "done" over NATS; the file never
    # entered git, so no other node could verify it - that is why dozens of cards were
    # DONE with no artifact anywhere. Best effort: a failed push must not lose the result.
    landed = ""
    if dl_ok or os.path.exists(rc_path):
        try:
            landed = git_publish(root, node, jid,
                                 [deliverable, os.path.relpath(rc_path, root)])
        except Exception as e:
            landed = "publish-error:%s" % str(e)[:80]

    # rc!=0 is not always a failure (gate cards declare ok_rc:[0,1]); the card decides.
    publish(node, "DONE" if ok else "FAILED",
            {"job": jid, "rc": rc, "seconds": dur, "deliverable_exists": dl_ok,
             "error_class": err_cls, "outcome": "OK" if ok else "FAIL",
             "landed": landed or "not-needed",
             "receipt": os.path.relpath(rc_path, root).replace("\\", "/")}, hub, port)
    print("%s %s rc=%s %.1fs deliverable=%s error=%s"
          % (jid, "DONE" if ok else "FAILED", rc, dur, dl_ok, err_cls or "-"))
    return {"id": jid, "rc": rc, "seconds": dur, "deliverable_exists": dl_ok,
            "ok": ok, "error_class": err_cls}


def self_dispatch(root, node, allow_gpu_workhours, max_seconds, hub, port, dry, only=None):
    """When the master has nothing for me, look at my own disks for ready work.

    This is the "ask local compute what it should be doing" leg. It only consumes the
    declarative backlog manifest (inputs must exist HERE, deliverable must not), so it
    cannot invent work and cannot touch another machine's paths.

    only: 只认这一张卡（端到端自检用）。走的是同一条 pick→claim→run→receipt→state 链，
    不另写一条捷径——否则测的就不是生产路径了。
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

    # 2026-11-02 换挡：卡的 nodes 是偏好，不是硬过滤。
    # 实测两张开给 bm-c 的 CPU 卡在队列里躺了 15 分钟没动（bm-c 心跳 882s 沉默），
    # 而 bm-m/bm-a 空着——"等指定机器"就是流程缺陷。规则：
    #   第一轮只认本机在名单里的卡；第二轮允许接"名单上的机器已失联"的卡（附 fallback 标记）。
    GRACE_S = 600

    def _pins_stale(nodes):
        if not nodes:
            return True
        ms = fl.read_json(os.path.join(root, "cph4", "fleet", "dispatcher", "MASTER-STATE.json"), {}) or {}
        lanes = ms.get("lanes") or {}
        # 2026-11-03 bm-b 实锚：稀疏控制面克隆没有 dispatcher/MASTER-STATE.json，lanes={}
        # 曾把"我读不到主控状态"当成"所有钉机都失联"，于是偷跑他机的体检卡
        # （--node bm-a 在 bm-b 上执行=审计错标机器）。读不到=未知=按钉机还活着处理，
        # 宁可少接不可错接。
        if not lanes:
            return False
        for n in nodes:
            v = lanes.get(n) or {}
            hb = v.get("hb_age_s")
            if v.get("online") and hb is not None and float(hb) <= GRACE_S:
                return False
        return True

    def trust_allows(row):
        """本机信任级是否允许接这张卡（与主控同一判据，来自 lane_trust 一处定义）。
        2026-11-03 实测：主控已按真回执降级 bm-b，但它自己 self-dispatch 时仍会挑重卡，
        闸就变成装饰——本机必须用同一条规则。"""
        try:
            import lane_trust as _lt
            _tier = _lt.tier(node)[0]
        except Exception:
            return True
        if _tier in ("production", "unknown"):
            return True
        return bool(row.get("probe"))

    def _eligible(r, strict):
        if only and r.get("id") != only:
            return False
        if not trust_allows(r):
            return False
        if not fl.card_os_ok(r, node):
            return False
        # 2026-11-03：hard_nodes 存在却无人执法（字段只挂在卡上）。机器身份卡
        # （体检某台机器/读某台机的盘）被回落顶班=错机器执行，比不执行更糟。
        hard = r.get("hard_nodes") or []
        if hard and node not in hard:
            return False
        nodes = r.get("nodes") or []
        # 2026-11-02：控制面不接生产活。CEO 立法：这台机第一任务是主控——调度、监督、
        # 协调、解题，外加常驻轻量模型；生产活一律路由出去。实测它抢走了本该给传家宝的
        # 音色库发现卡，主控在跟机队抢算力。fleet-ops 线（自检/巡检）仍允许在本机跑。
        _role = ((fl.LANES.get(node) or {}).get("role_class") or "")
        if _role == "control" and node not in nodes \
                and (r.get("line") or "") not in ("fleet-ops", ""):
            return False
        if strict:
            if nodes and node not in nodes:
                return False
        else:
            if node in nodes:
                return False          # 已在第一轮处理
            if not _pins_stale(nodes):
                return False          # 指定机器还活着，先让它干
        # 2026-10-30 master fix: when_all on C:/D:/ paths is not checkable on the master
        # box (macOS + sparse checkout). The lane owns its own filesystem -> verify here.
        wa = r.get("when_all") or []
        if wa and not all(os.path.exists(x) for x in wa):
            return False
        req = r.get("requires") or []
        if req and not all(os.path.exists(x) for x in req):
            return False
        # 2026-11-03 root cause: a card's command can name its real input without
        # declaring it (`--dir media/drama-tts-out` with requires: []). The Mac and the
        # other Windows boxes then "ran" it and wrote MISSING receipts three times over.
        # An input this box cannot see is a skip, never a failure.
        _imp = [p for p in fl.implicit_inputs(r) if not os.path.exists(os.path.join(root, p))]
        if _imp:
            print("SKIP %s: input not on this box: %s" % (r.get("id"), ",".join(_imp[:3])))
            return False
        if not fl.requires_bin_ok(r):
            print("SKIP %s: requires_bin missing" % r.get("id"))
            return False
        if fl.game_launch_blocked(r.get("cmd") or ""):
            return False
        _gok, _gwhy = _card_gate(r, root, node)
        if not _gok:
            print("CARD-DEFECT skip %s: %s" % (r.get("id"), _gwhy[:180]))
            return False
        if r.get("heavy") and not fl.heavy_allowed(node) and not allow_gpu_workhours:
            return False
        if (r.get("needs") == "gpu") and not fl.gpu_window_open(node) and not allow_gpu_workhours:
            return False
        return True

    pick = None
    for strict in (True, False):
        for r in rows:
            if r.get("state") != "OPEN":
                continue
            if _eligible(r, strict):
                pick = r
                if not strict:
                    pick["fallback_from"] = r.get("nodes")
                    pick["fallback_why"] = "pinned lane silent >%ds; any capable lane may take it" % GRACE_S
                break
        if pick:
            break
    if not pick:
        return None
    if dry:
        print("LANE-DRY %s self-dispatch would run %s" % (node, pick.get("id")))
        return None
    res = run_job(pick, root, node, hub, port, allow_gpu_workhours, max_seconds)
    # 单写入口（2026-11-02）：只把自己改的那一行按 id 合并回去。
    # 旧写法读全表、改一行、再整表覆盖，等于把别人同时写进来的行一起抹掉。
    rows = fl.read_jsonl(qpath)
    for x in rows:
        if x.get("id") == pick.get("id"):
            # Take run_job's verdict instead of re-deriving it loosely. The old rule
            # ("rc==0 OR deliverable exists") is exactly how rc=3 BLOCKED receipts got
            # booked DONE: the refusal file satisfied the second half.
            ok = bool(res.get("ok"))
            x["state"] = "DONE" if ok else "FAILED"
            x["owner"] = node
            x["finished_at"] = fl.now_iso()
            x["rc"] = res.get("rc")
            x["seconds"] = res.get("seconds")
            if not ok:
                # A FAILED card with no reason is what made every incident a surprise
                # (2026-10-31: R-MV-GATE-1D failed on bm-a and nothing recorded why).
                x["failure"] = (res.get("stderr_tail") or res.get("stdout_tail")
                                or res.get("reason") or "rc=%s, no output captured"
                                % res.get("rc"))[:400]
            x["created_by"] = (x.get("created_by") or "") + "+lane-self"
            fl.merge_jsonl(qpath, [x])
            break
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
    if already_closed(root, job.get("id")):
        # Finished on the shared surface: never replay it (re-running closes 14x churn).
        # But never strand the lane on a stale assignment either: 2026-11-04 one
        # already-closed card held bm-b's ONLY lane slot for 8h+ while 26 OPEN jobs
        # waited, and the box kept reporting IDLE because this branch returned early.
        # A lane whose assignment is dead has nothing to do - the same situation as an
        # empty assignment - so it takes the same self-dispatch leg.
        print("LANE-SKIP %s :: already closed in queue" % job.get("id"))
        if self_dispatch(root, node, allow_gpu_workhours, max_seconds, hub, port, dry):
            return True
        publish(node, "IDLE", {"reason": "ALREADY-CLOSED %s" % job.get("id")}, hub, port)
        write_last(root, node, "IDLE", note="ALREADY-CLOSED")
        return True
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