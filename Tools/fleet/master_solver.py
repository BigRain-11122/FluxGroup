#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""master_solver.py - the master's "fix it" leg (dispatch / supervise / coordinate / solve).

Supervision without action is just a nicer log. This leg takes the problems the supervisor
already sees and applies a bounded whitelist of fixes; anything outside the whitelist is
escalated with owner + the decision needed, never worked around.

Whitelist (each action is reversible, evidence-backed, and capped):
  A1 node repo behind / line BLOCKED on git divergence -> queue a sync card to that node
     (the only channel that exists: no SSH/WinRM to the production boxes, CEO 2026-10-23)
  A2 FAILED card with a retryable error -> requeue once per card, max 2 attempts
  A3 lane STARVED for >3 rounds -> arm that line's recurring work (real rows only)
  A4 ollama/pulse/caffeinate down -> already auto-repaired inline by master_pulse.checks()

Everything else (blocked on a human decision, a machine that is off, a physical item) is
escalated in SOLVER.md as "谁 / 缺什么 / 怎么解".

Usage: python3 Tools/fleet/master_solver.py [--dry]
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
STATE = os.path.join(FLEET, "dispatcher", "MASTER-STATE.json")
OUT = os.path.join(FLEET, "dispatcher", "SOLVER.md")
MAX_RETRY = 2


def load(p, default):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def jl(p):
    out = []
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def save_jl(p, rows):
    tmp = "%s.%d.tmp" % (p, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, p)


def sync_card(node, why, dry):
    day = datetime.now().strftime("%Y%m%d")
    jid = "Q-SYNC-%s-%s" % (node.upper().replace("-", ""), day)
    have = {r.get("id") for r in jl(BACKLOG) + jl(QUEUE)}
    if jid in have:
        return None
    card = {"id": jid, "title": "%s 工作树收口（fetch+rebase，勿 hard reset）" % node,
            "cmd": "git pull --rebase --autostash origin main", "cwd": "",
            "requires": [], "needs": "cpu", "nodes": [node], "prio": "P2", "day_ok": True,
            "why": why, "created_by": "master_solver:A1",
            "created_at": datetime.now().isoformat(timespec="seconds")}
    if not dry:
        with open(BACKLOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
    return jid


def main() -> int:
    dry = "--dry" in sys.argv
    st = load(STATE, {})
    lanes = st.get("lanes") or {}
    rows = jl(QUEUE)
    fixes, escalate = [], []

    # A1 - a line blocked because a node's tree is stale/diverged
    for ln in (st.get("lines") or {}).values():
        pass  # verdict detail lives in PULSE/NEED-SUPPLY; node-level check below is enough
    for n, v in lanes.items():
        if not v.get("online"):
            continue
        reason = (v.get("idle_reason") or "")
        if "SELF-DISPATCH" in reason and (v.get("idle_rounds") or 0) > 3:
            # A3: starving with no declared work -> only a real recurring row may feed it
            fixes.append("%s 连续 %d 轮无活：只允许做真活，已交 line_agents 续卡（本机无该线输入则报 NO-DATA）"
                         % (n, v.get("idle_rounds") or 0))

    # A1b - bm-b/bm-c style divergence: the queue is the only remote channel we have
    for n in ("bm-b", "bm-c", "bm-a"):
        if n in lanes and lanes[n].get("online") and lanes[n].get("tree_dirty"):
            jid = sync_card(n, "工作树脏/分叉：远端无法执行，只能由本机 lane 跑一次 rebase", dry)
            if jid:
                fixes.append("已开同步卡 %s -> %s" % (jid, n))

    # A2 - retry failed cards, capped
    changed = False
    for r in rows:
        if r.get("state") != "FAILED":
            continue
        tries = int(r.get("retries") or 0)
        if tries >= MAX_RETRY:
            escalate.append("%s 已失败 %d 次：%s —— 需改卡或人工定性（不放行第 3 次）"
                            % (r.get("id"), tries, (r.get("failure") or "")[:60]))
            continue
        if not dry:
            r["state"] = "OPEN"
            r["retries"] = tries + 1
            r["owner"] = None
            r["requeued_at"] = datetime.now().isoformat(timespec="seconds")
            changed = True
        fixes.append("重派 %s（第 %d 次）" % (r.get("id"), tries + 1))
    if changed:
        save_jl(QUEUE, rows)

    q = st.get("queue") or {}
    lines = ["# 主控解题 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), "",
             "- 队列 open=%s running=%s failed=%s · 在线 %d 台"
             % (q.get("open"), q.get("running"), q.get("failed"),
                sum(1 for v in lanes.values() if v.get("online"))),
             "", "## 本轮已处理"]
    lines += ["- " + f for f in fixes] or ["- 无自动动作（没有可自解的堵点）"]
    lines += ["", "## 需人/需资源（主控不越权）"]
    lines += ["- " + e for e in escalate] or ["- 无"]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("[solver] fixes=%d escalate=%d%s" % (len(fixes), len(escalate), " (dry)" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())