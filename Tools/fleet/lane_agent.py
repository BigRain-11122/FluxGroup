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
PROGRESS_EVERY = 10   # 2026-11-05 CEO「状态要及时」：45s 对分钟级卡等于不报；默认 10s


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
    # attempt often lost the same race and the artifact stayed local. Give it three.
    # 2026-11-05（R11 事件班）：共享工作树禁 rebase。push 失败后 `pull --rebase` 会把本机
    # 生成态快照逐个重放、每次都撞同一批队列/lane 冲突，`rebase --abort` 只是把分叉原样
    # 留回去——实测 02:44-02:46 每 30 秒空转一轮，ahead/behind 只增不减（5/8）。
    # 改走 merge 收口：生成态取远端，Tools/ 等手写件冲突立即放弃本轮。
    last = ""
    for _ in range(3):
        r = git(["push", "origin", "HEAD:main"], timeout=120)
        if r.returncode == 0:
            return "pushed"
        last = r.stderr or r.stdout
        recon = _merge_origin(root)
        if recon != "ok":
            break
    # 2026-11-06 实测：主干推送在分叉时永远失败，产物于是留在本机、主控看不见
    # （bm-c 出了图但 origin 上没有）。兜底=推自己的分支 node/<node>：单写者、永不冲突，
    # 主控侧按分支取产物。这一步成功就算"产物上了共享面"。
    try:
        r = git(["push", "-f", "origin", "HEAD:refs/heads/node/%s" % node], timeout=180)
        if r.returncode == 0:
            return "pushed:node/%s" % node
        return "push-failed:%s (node-branch:%s)" % (
            (last or "")[:50], (r.stderr or r.stdout or "")[:50])
    except Exception as e:
        return "push-failed:%s (node-branch-err:%s)" % ((last or "")[:40], str(e)[:40])


def _git_ro(root, args, timeout=120):
    # encoding 必须写死 utf-8：Windows 的 text=True 走 cp936，而 git 输出的是 UTF-8
    # （中文提交信息/回执名），解码错会让整个收口被判成 merge-failed（2026-11-05 实测）。
    return subprocess.run(["git", "-C", root] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, creationflags=CREATE_NO_WINDOW)


# 生成态路径（镜像 master_pulse.GENERATED；那边 import 了 fcntl，Windows 导不进来，
# 所以这里留一份同名清单，两边语义必须一致）。
GENERATED_PREFIXES = (
    "cph4/fleet/dispatcher/", "cph4/fleet/lanes/", "cph4/fleet/queue-receipts/",
    "cph4/fleet/chief/", "cph4/fleet/social/", "cph4/fleet/plans/",
    "cph4/fleet/state/", "cph4/fleet/PRODUCTION-QUEUE.jsonl",
    "cph4/fleet/PRODUCTION-BACKLOG.jsonl", "cph4/fleet/SHOWCASE.md",
    "cph4/fleet/HANDOFF.md", "cph4/fleet/ri/PROPOSALS.json",
    "cph4/fleet/vault/index.jsonl",
)
QUEUE_FILES = ("cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/PRODUCTION-BACKLOG.jsonl")


def _card_rows(root, spec):
    """解析队列某个版本（HEAD / origin/main）成 {id: row}；坏行跳过不动。"""
    r = _git_ro(root, ["show", spec], timeout=60)
    if r.returncode != 0:
        return {}
    rows = {}
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("id"):
            rows[row["id"]] = row
    return rows


def _local_only_cards(root):
    """合并前留底本机独有的 OPEN/READY 卡：取远端版本会把它们一起抹掉。"""
    keep = []
    for path in QUEUE_FILES:
        ours = _card_rows(root, "HEAD:" + path)
        theirs = _card_rows(root, "origin/main:" + path)
        for cid, row in ours.items():
            if cid in theirs:
                continue
            if str(row.get("state") or "").upper() in ("OPEN", "READY"):
                keep.append((path, row))
    return keep


def _restore_cards(root, keep):
    """把留底的卡补回队列并提交；不补 = 卡片凭空消失（读队列的一律静默跳坏行）。"""
    if not keep:
        return 0
    by_path = {}
    for path, row in keep:
        by_path.setdefault(path, []).append(row)
    restored = 0
    for path, rows in by_path.items():
        full = os.path.join(root, path)
        have = set()
        try:
            with open(full, encoding="utf-8-sig") as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("{"):
                        try:
                            cid = json.loads(line).get("id")
                        except Exception:
                            continue
                        if cid:
                            have.add(cid)
        except FileNotFoundError:
            pass
        add = [r for r in rows if r.get("id") not in have]
        if not add:
            continue
        with open(full, "a", encoding="utf-8", newline="\n") as fh:
            for row in add:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        _git_ro(root, ["add", "--", path], timeout=60)
        _git_ro(root, ["commit", "-q", "-m",
                       "lane: restore %d local-only card(s) after merge" % len(add)], timeout=90)
        restored += len(add)
    return restored


def _merge_origin(root):
    """分叉收口一律走 merge，禁 rebase（2026-11-04 硬律 / 2026-11-05 R11 复发实证）。

    为什么：本仓是多机共用同一工作树，push 失败后 rebase 要逐个重放本机生成态快照，
    每个都撞同一批队列/lane 冲突，abort 之后下一轮再来——2026-11-04 实测卡死 98 步，
    2026-11-05 02:44-02:46 又每 30 秒复发一轮、ahead/behind 只增不减。
    口径照抄 master_pulse.rebase_generated 的实证做法（它在 Windows 因 fcntl 导不进来）：
    生成态取远端、把本机独有 OPEN 卡补回、Tools/ 等手写件冲突立即放弃本轮。
    """
    for d in ("rebase-merge", "rebase-apply"):
        if os.path.isdir(os.path.join(root, ".git", d)):
            _git_ro(root, ["rebase", "--abort"], timeout=90)
            break
    if _git_ro(root, ["fetch", "--prune", "origin"], timeout=180).returncode != 0:
        return "fetch-failed"
    behind = (_git_ro(root, ["rev-list", "--count", "HEAD..origin/main"], timeout=30).stdout or "0").strip()
    if behind in ("", "0"):
        return "ok"
    keep = _local_only_cards(root)
    r = _git_ro(root, ["merge", "--no-edit", "-m",
                       "lane: merge origin (generated files take remote)", "origin/main"], timeout=240)
    for _ in range(3):
        d = _git_ro(root, ["diff", "--name-only", "--diff-filter=U"], timeout=30)
        conflicts = [p for p in (d.stdout or "").split() if p]
        if not conflicts:
            break
        if any(not p.startswith(GENERATED_PREFIXES) for p in conflicts):
            _git_ro(root, ["merge", "--abort"], timeout=90)
            return "hand-edit-conflict:%s" % conflicts[0][:60]
        for p in conflicts:
            _git_ro(root, ["checkout", "--theirs", "--", p], timeout=60)
            # 2026-11-04 毒标记守门：带冲突标记的一侧永不许入库。
            try:
                with open(os.path.join(root, p), encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                if "<<<<<<<" in text and ">>>>>>>" in text:
                    _git_ro(root, ["merge", "--abort"], timeout=90)
                    return "poison-guard:%s" % p[:60]
            except Exception:
                pass
            _git_ro(root, ["add", "--", p], timeout=60)
    else:
        _git_ro(root, ["merge", "--abort"], timeout=90)
        return "loop-limit"
    if _git_ro(root, ["rev-parse", "-q", "--verify", "MERGE_HEAD"], timeout=20).returncode == 0:
        if _git_ro(root, ["commit", "-q", "--no-edit"], timeout=120).returncode != 0:
            _git_ro(root, ["merge", "--abort"], timeout=90)
            return "merge-commit-failed"
    elif r.returncode != 0:
        _git_ro(root, ["merge", "--abort"], timeout=90)
        return "merge-failed"
    _restore_cards(root, keep)
    return "ok"


def already_closed(root, jid):
    """True when the shared queue already considers this card finished.

    Why: a stale lane file (or a takeover master that disagrees with origin) keeps handing
    the same card back, so the box re-runs a finished job every cycle - the same triage
    artifact was rewritten and re-committed 14 times on the night of 11-01/02. The lane
    must trust the shared queue's terminal states, not only its local assignment.
    """
    # 2026-11-06 实测（bm-c 同一张 SELF-IMPROVE 每 2 分钟重跑一次）：本函数只读本地队列
    # 文件，而 Windows 节点的本地队列是**分叉的陈旧副本**——主控在 origin 上翻成 UNVERIFIED
    # 的卡，节点永远看不到，于是无限重跑。正解：先读 origin/main 的 blob（那是权威面），
    # 本地文件只作离线兜底。这与 already_closed 的既有判例同源（11-05 记录）。
    def _states(text):
        out = {}
        for ln in (text or "").splitlines():
            ln = ln.strip()
            if not ln.startswith("{"):
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("id") == jid:
                out[r.get("id")] = r
        return out
    try:
        blob = subprocess.run(["git", "-C", root, "show",
                               "origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl"],
                              capture_output=True, timeout=30).stdout.decode("utf-8", "replace")
        for r in _states(blob).values():
            return str(r.get("state") or "").upper() in ("DONE", "UNVERIFIED", "CANCELLED")
    except Exception:
        pass
    try:
        qp = os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
        with open(qp, encoding="utf-8") as fh:
            for r in _states(fh.read()).values():
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


def _hub_post(path, payload, timeout=5):
    """状态直推主控（tailnet HTTP，毫秒级）。失败一律吞掉：这条腿坏不许影响执行。"""
    try:
        import urllib.request as _u
        host = os.environ.get("FLEET_HUB") or "http://100.75.133.10:8791"
        req = _u.Request(host + path, data=json.dumps(payload).encode(),
                         headers={"Content-Type": "application/json"})
        with _u.urlopen(req, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _progress_every(root):
    try:
        with open(os.path.join(root, "cph4", "fleet", "AUTONOMY-CONFIG.json"),
                  encoding="utf-8-sig") as f:
            return max(3, int(((json.load(f).get("progress") or {})
                               .get("report_every_s") or PROGRESS_EVERY)))
    except Exception:
        return PROGRESS_EVERY


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
    import shutil as _sh
    if cmd.startswith("python ") and not _sh.which("python"):
        cmd = "python3 " + cmd[len("python "):]
        job["cmd_resolved"] = cmd
    # 2026-11-05 远端实测（rc=9009）：Windows 没有 `python3` 这个命令，所有写
    # `python3 Tools/...` 的卡在 bm-a/b/b/c 全部 0 秒失败——机队"在跑但没产出"的根源。
    # 反向归一：本机没有 python3 但有 python 时改写；两个都没有则保留原命令让它报错（可见）。
    # 2026-11-06 二次实测（bm-c 复跑 SELF-IMPROVE 卡仍 rc=9009）：Windows 自带一个
    # **商店占位别名** %LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe——`which`
    # 查得到，一执行就 9009（"不是可用的应用"）。所以"能不能解析"不等于"能不能跑"，
    # 旧判据在这类机器上永远不改写，整队 python3 卡全部 0 秒失败。正解：Windows 上
    # 只要 `python` 在就直接改写；解析不到时再退一步做真跑一次（-c print）验证。
    def _runs(exe):
        try:
            return subprocess.run([exe, "-c", "import sys;sys.exit(0)"],
                                  capture_output=True, timeout=15).returncode == 0
        except Exception:
            return False
    if cmd.startswith("python3 "):
        py = _sh.which("python")
        if os.name == "nt" and py:
            cmd = "python " + cmd[len("python3 "):]
            job["cmd_resolved"] = cmd
        else:
            p3 = _sh.which("python3")
            if p3 and py and not _runs(p3):
                cmd = "python " + cmd[len("python3 "):]
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
    # 本机能力闸（2026-11-05 实测包络）：GPU 卡开工前必须确认
    # ①swap 没有在涨 ②可用内存减去保留量够用 ③退掉不该驻留的模型。
    if str(needs).lower() in ("gpu", "gpu-encode", "gpu-vision"):
        try:
            import capacity_guard as _cg
            _ok, _why = _cg.before_gpu(need_gb=float(job.get("need_gb") or 10))
            if not _ok:
                return {"id": jid, "rc": None, "note": "CAPACITY-BLOCK %s" % _why}
        except Exception as _e:
            print("capacity guard skipped:", str(_e)[:80])

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
        _box = {"rc": 125, "out": "", "err": "", "out_bytes": 0}

        def _reader(pipe, key, ctr):
            parts = []
            try:
                # 2026-11-05 实测：text 模式 pipe.read(4096) 会攒满或等 EOF 才返回，
                # 小批量输出（每秒一行）一个字节都读不到 → out_bytes 恒 0 → 主控的
                # "字节有没有增长"判据失效，慢卡全被判成假忙。改为按行读。
                while True:
                    line = pipe.readline()
                    if not line:
                        break
                    parts.append(line)
                    _box[ctr] = _box.get(ctr, 0) + len(line)
            except Exception as e:
                parts.append("[read-error %s]" % e)
            finally:
                try:
                    pipe.close()
                except Exception:
                    pass
            _box[key] = "".join(parts)

        def _exec():
            try:
                p = subprocess.Popen(cmd, shell=True, cwd=_gate_cwd or job.get("cwd") or root,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, errors="replace",
                                     creationflags=CREATE_NO_WINDOW)
            except Exception as e:
                _box.update(rc=125, err="exec-failed: %s" % e)
                return
            t_out = threading.Thread(target=_reader, args=(p.stdout, "out", "out_bytes"), daemon=True)
            t_err = threading.Thread(target=_reader, args=(p.stderr, "err", "err_bytes"), daemon=True)
            t_out.start()
            t_err.start()
            try:
                _box["rc"] = p.wait(timeout=max_seconds)
            except subprocess.TimeoutExpired:
                p.kill()
                _box["rc"] = 124
                _box["err"] = (_box.get("err") or "") + "\n[timeout %ss]" % max_seconds
            except Exception as e:
                _box.update(rc=125, err="exec-failed: %s" % e)
            t_out.join(timeout=10)
            t_err.join(timeout=10)

        _t = threading.Thread(target=_exec, daemon=True)
        _t.start()
        while _t.is_alive():
            _t.join(timeout=_progress_every(root))
            if not _t.is_alive():
                break
            try:
                # out_bytes = 子进程已产出的 stdout 字节数。主控用它判"有没有新输出"，
                # 光靠 elapsed_s 只能证明进程还在，卡死的进程也会一直报 elapsed。
                _prog = {"node": node, "state": "BUSY", "job": jid,
                         "elapsed_s": int(time.time() - t0),
                         "out_bytes": int(_box.get("out_bytes") or 0),
                         "ts": fl.now_iso()}
                fl.kv_put(fl.lane_result_key(node), _prog, host=hub, port=port)
                _hub_post("/status", _prog)
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
    # 产出即验收（CEO 2026-11-08）：在这台机器上立刻分类+过质量席，写 <id>-acceptance.json。
    try:
        import produce_run as _pr
        _res = _pr.judge(deliverable, job.get("line") or "")
        _pr.write_receipt(jid, _res)
        rec["accept_verdict"] = _res.get("verdict")
        rec["accept_score"] = _res.get("score")
        print("LANE-ACCEPT %s :: %s %s" % (jid, _res.get("verdict"), _res.get("score")))
    except Exception as _e:
        print("W-ACCEPT %s" % str(_e)[:80])
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
    # 2026-11-05 实测：远端 FAILED 时主控只收到"FAILED"三个字，原因留在对方盘上，
    # 于是永远无法科学处理。回执内容必须随状态一起上报（截断，几十字节级）。
    _hub_post("/status", {"node": node, "state": "DONE" if ok else "FAILED", "job": jid,
                          "rc": rc, "seconds": dur, "error_class": err_cls,
                          "deliverable": deliverable, "deliverable_exists": dl_ok,
                          "cmd": cmd[:300], "ts": fl.now_iso(),
                          "stderr_tail": (err or "")[-600:], "stdout_tail": (out or "")[-400:]})
    publish(node, "DONE" if ok else "FAILED",
            {"job": jid, "rc": rc, "seconds": dur, "deliverable_exists": dl_ok,
             "error_class": err_cls, "outcome": "OK" if ok else "FAIL",
             "landed": landed or "not-needed",
             "stderr_tail": (err or "")[-600:], "stdout_tail": (out or "")[-400:],
             "cmd": cmd[:300],
             "receipt": os.path.relpath(rc_path, root).replace("\\", "/")}, hub, port)
    print("%s %s rc=%s %.1fs deliverable=%s error=%s"
          % (jid, "DONE" if ok else "FAILED", rc, dur, dl_ok, err_cls or "-"))
    return {"id": jid, "rc": rc, "seconds": dur, "deliverable_exists": dl_ok,
            "ok": ok, "error_class": err_cls}


def _need_work_flag(root, node, on, why=""):
    """2026-11-04 CEO 令「机队没活就赶紧找主控要，并通知主控早早准备好」。

    没活不能静默闲着：写显式 NEED-WORK 状态件（走代理自己的 state 推送腿，
    全队 git 可见=可审计的「要活」请求），主控据此优先派单/备单；一旦接活立即撤标。
    写失败不致命——信号缺失最多回到旧的静默态，不允许它打断执行链。
    """
    try:
        p = os.path.join(root, "cph4", "fleet", "state", "need-work", node + ".json")
        if on:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"node": node, "ts": fl.now_iso(), "why": why},
                          f, ensure_ascii=False, indent=1)
        elif os.path.exists(p):
            os.remove(p)
    except Exception:
        pass


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

    _DEAD_CACHE = {}

    def _pins_dead(nodes):
        """钉住的机器是否已停产（最后产出 >6h）。停产=可以接管，失联=不接管。"""
        if not nodes:
            return True
        for n in nodes:
            if n not in _DEAD_CACHE:
                try:
                    import subprocess as _sp
                    out = _sp.run(["git", "-C", root, "log", "-1", "--format=%ct",
                                   "--grep=via %s" % n], capture_output=True, text=True,
                                  timeout=15).stdout.strip()
                    _DEAD_CACHE[n] = (time.time() - int(out) > 6 * 3600) if out else True
                except Exception:
                    _DEAD_CACHE[n] = False
            if not _DEAD_CACHE[n]:
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
            # 2026-11-05 CEO「我更关心机队的产出，现在的状态等待」：钉住的机器已经停产
            # （>6h 无产出）时，控制面接管是唯一让活出产物的办法，否则卡永远躺着。
            # 接管必须留痕（fallback_from/why），可审计、可在机器恢复后停止。
            if not _pins_stale(nodes) or not _pins_dead(nodes):
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
    # 2026-11-05 R9 事件班实证：本地队列副本会被并发 auto-sync 覆盖/半写（一小时内两次），
    # 车道据此选卡会把已钉他机（hard_nodes）或已关闭的卡当活干——bm-a 连续领到
    # hard_nodes=[bm-c] 的 char-gen，白烧 GPU lease 并霸占供给位。执行前按 origin 复核一次。
    _orows = {}
    try:
        _raw = subprocess.run(["git", "-C", root, "show", "origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl"],
                              capture_output=True, timeout=20).stdout.decode("utf-8", "replace")
        for _l in _raw.split("\n"):
            _l = _l.strip()
            if not _l.startswith("{"):
                continue
            try:
                _d = json.loads(_l)
            except Exception:
                continue
            if _d.get("id"):
                _orows[_d["id"]] = _d
    except Exception:
        _orows = {}

    pick = None
    for strict in (True, False):
        for r in rows:
            if r.get("state") != "OPEN":
                continue
            if _eligible(r, strict):
                _o = _orows.get(r.get("id"))
                if _o is not None:
                    _oh = _o.get("hard_nodes") or []
                    if _o.get("state") != "OPEN":
                        print("SKIP %s: origin state=%s (local queue stale)" % (r.get("id"), _o.get("state")))
                        continue
                    if _oh and node not in _oh:
                        print("SKIP %s: origin hard_nodes=%s (local queue stale)" % (r.get("id"), _oh))
                        continue
                pick = r
                if not strict:
                    pick["fallback_from"] = r.get("nodes")
                    pick["fallback_why"] = "pinned lane silent >%ds; any capable lane may take it" % GRACE_S
                break
        if pick:
            break
    if not pick:
        # 2026-11-04 CEO 令「机队没活就赶紧找主控要」：没活不能静默闲着——写显式
        # NEED-WORK 状态件（走代理自己的 state 推送腿，全队 git 可见=可审计的「要活」），
        # 主控据此优先派单；一旦接活立即撤标。
        _need_work_flag(root, node, True,
                        "no master dispatch and no eligible backlog row on this box")
        return None
    _need_work_flag(root, node, False)
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
            _ec = res.get("error_class")
            # 2026-11-05 实测：缺输入的卡反复被挑、反复失败，把唯一活着的机器的槽位
            # 全吃掉，后面的活永远轮不到——这就是"状态等待"。缺料卡转 BLOCKED，
            # 不再参与挑选，等输入到位再由 unlock/prep 解开。
            x["state"] = "DONE" if ok else ("BLOCKED" if _ec == "E-INPUT" else "FAILED")
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
                # 2026-11-05 R9-6：回执已按 fc.error_class 定性，但写回队列时丢了 → 01:07-01:33
                # 实测 10+ 张 FAILED 卡 error_class 全空，solver 无定性可依只会原样重试。
                # 判据沿用 flux_contracts 单源，不在此另立规则。
                x["error_class"] = res.get("error_class") or fc.error_class(res.get("rc"))
            x["created_by"] = (x.get("created_by") or "") + "+lane-self"
            fl.merge_jsonl(qpath, [x])
            break
    return res



def self_acquire_missing(root):
    """空槽自驱：给缺料的卡自取输入（只走确定性通道，取不到不伪造）。"""
    try:
        import json as _json
        import subprocess as _sp
        out = _sp.run(["git", "show", "origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl"],
                      cwd=root, capture_output=True, text=True, timeout=60).stdout
        sa = os.path.join(root, "Tools", "fleet", "self_acquire.py")
        if not os.path.exists(sa):
            return False
        for ln in (out or "").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = _json.loads(ln)
            except Exception:
                continue
            if r.get("state") not in ("OPEN", "BLOCKED"):
                continue
            for need in (r.get("requires") or []):
                ns = str(need)
                if ns.startswith("store/") and len(ns) > 30:
                    if _sp.run([sys.executable, sa, "--vault", os.path.basename(ns),
                                "--dest", "media/inbox/acquired/" + os.path.basename(ns)],
                               cwd=root, capture_output=True, text=True, timeout=900).returncode == 0:
                        print("LANE-ACQUIRE %s :: %s" % (r.get("id"), ns))
                        return True
            url = r.get("source_url")
            if url:
                if _sp.run([sys.executable, sa, "--net", url, "--allow-net",
                            "--dest", "media/inbox/acquired/" + os.path.basename(url)],
                           cwd=root, capture_output=True, text=True, timeout=1800).returncode == 0:
                    print("LANE-ACQUIRE %s :: net" % r.get("id"))
                    return True
    except Exception as e:
        print("W-SELF-ACQUIRE %s" % str(e)[:80])
    return False

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
        if not dry and self_acquire_missing(root):
            return True
        reason = payload.get("idle_reason") or "NO-ASSIGNMENT"
        publish(node, "IDLE", {"reason": reason}, hub, port)
        write_last(root, node, "IDLE", note=reason)
        print("LANE-IDLE %s :: %s" % (node, reason))
# NO-JOBS (2026-11-07): an empty lane file plus nothing self-dispatchable used to
# return True, so queue_claim exited here and the shared PRODUCTION-QUEUE was never
# read again - real OPEN jobs sat unclaimable for days. The lane is empty, not
# sovereign: tell the caller so it may take a global OPEN job.
        return "NO-JOBS"

    # 选卡（2026-11-05 全链路实测修）：原来只认 jobs[0]，而主控车道第一张常年是
    # 重卡或已关的卡——车道被一张跑不动的卡永久占住，队列有活却一动不动，后面
    # 的卡永远轮不到。改成跳过"本机跑不了/已关"的，取第一张能跑的。
    def _runnable(x):
        if already_closed(root, x.get("id")):
            return False
        if node == "bm-m" and (x.get("needs") == "gpu" or x.get("heavy")
                               or int(x.get("minutes") or 0) > 3):
            return False
        if x.get("heavy") and not fl.heavy_allowed(node) and not allow_gpu_workhours:
            return False
        return True

    _cand = [x for x in jobs if _runnable(x)]
    if not _cand:
        _id = (jobs[0] or {}).get("id")
        publish(node, "DEFERRED", {"job": _id, "reason": "NO-RUNNABLE-ASSIGNMENT"}, hub, port)
        write_last(root, node, "DEFERRED", job=_id, note="NO-RUNNABLE-ASSIGNMENT")
        print("LANE-DEFER %s :: nothing in this assignment is runnable here" % _id)
        return True
    # 并发槽位（2026-11-05）：一台机能同时跑几张卡，由配置决定；GPU 同一时刻只跑一张。
    try:
        with open(os.path.join(root, "cph4", "fleet", "AUTONOMY-CONFIG.json"),
                  encoding="utf-8") as _f:
            _slots = int((((json.load(_f).get("supply") or {}).get("slots_per_node") or {})
                          .get(node, 1)) or 1)
    except Exception:
        _slots = 1
    def _run_one_job(_j, _root, _node, _hub, _port, _gpu_ok, _max_s, _dry):
        """单卡执行（并行槽位用）。步序与单卡路径一致：RUNNING -> run_job -> RESULT。
        2026-11-08：定义曾被 checkout 顶掉、只剩调用点 -> NameError，卡认领后
        永久 RUNNING、机器空转（实测堆积 18 张）。定义与调用点必须同一提交（RG-30）。"""
        _jid = _j.get("id")
        if already_closed(_root, _jid):
            return None
        if _j.get("heavy") and not fl.heavy_allowed(_node) and not _gpu_ok:
            publish(_node, "DEFERRED", {"job": _jid, "reason": "HEAVY-YIELD (parallel)"},
                    _hub, _port)
            return None
        _need_work_flag(_root, _node, False)
        write_last(_root, _node, "RUNNING", job=_jid)
        _res = run_job(_j, _root, _node, _hub, _port, _gpu_ok, _max_s)
        write_last(_root, _node, "RESULT", job=_res.get("id"),
                   note=_res.get("note") or "", rc=_res.get("rc"))
        return _res

    if _slots > 1:
        _picked, _gpu_taken = [], False
        for _j in _cand:
            if len(_picked) >= _slots:
                break
            if _j.get("needs") == "gpu":
                if _gpu_taken:
                    continue
                _gpu_taken = True
            _picked.append(_j)
        if len(_picked) > 1:
            from concurrent.futures import ThreadPoolExecutor
            print("LANE-SLOTS %s :: %d job(s): %s" % (node, len(_picked),
                  ",".join(str(_x.get("id")) for _x in _picked)))
            with ThreadPoolExecutor(max_workers=len(_picked)) as _ex:
                list(_ex.map(lambda _x: _run_one_job(_x, root, node, hub, port,
                                                     allow_gpu_workhours, max_seconds, dry),
                             _picked))
            return True
    job = _cand[0]
    _need_work_flag(root, node, False)   # 主控派到了单：撤「要活」标
    if already_closed(root, job.get("id")):
        # Finished on the shared surface: never replay it. Idle is the honest answer.
        publish(node, "IDLE", {"reason": "ALREADY-CLOSED %s" % job.get("id")}, hub, port)
        write_last(root, node, "IDLE", note="ALREADY-CLOSED")
        print("LANE-SKIP %s :: already closed in queue" % job.get("id"))
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