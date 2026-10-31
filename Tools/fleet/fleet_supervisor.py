#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_supervisor.py - the resident supervisor's one-screen verdict.

The pulse already schedules and dispatches; this answers the only question the CEO asks:
"现在谁在堵，下一步谁该动". Deterministic rules only - no model, no invention, so the
same input always gives the same verdict.

Reads : MASTER-STATE.json (lanes/queue), PRODUCTION-QUEUE.jsonl, PULSE.json, LINE registry
Writes: cph4/fleet/dispatcher/SUPERVISOR.md  (<= 20 lines, overwritten each slow cycle)
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
D = os.path.join(ROOT, "cph4", "fleet", "dispatcher")
OUT = os.path.join(D, "SUPERVISOR.md")
OFFLINE_S = 900
STUCK_S = 3 * 3600


def load(p, default):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def main() -> int:
    ms = load(os.path.join(D, "MASTER-STATE.json"), {})
    pulse = load(os.path.join(D, "PULSE.json"), {})
    lanes = ms.get("lanes") or {}
    q = ms.get("queue") or {}

    rows = []
    qp = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    if os.path.exists(qp):
        for ln in open(qp, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass

    now = time.time()
    acts = []

    for n, v in lanes.items():
        if not v.get("online"):
            acts.append("%s 离线：等它自己上报（禁 poke 轰炸），或人工开机" % n)
            continue
        if v.get("idle_confirmed") and not v.get("job"):
            reason = (v.get("idle_reason") or "")[:40]
            if reason.startswith("SELF-DISPATCH"):
                acts.append("%s 自扫积压中；持续 >2 轮=该机无已声明活，需生产席补卡" % n)
            elif reason.startswith("CAPACITY"):
                acts.append("%s 容量不足：%s" % (n, reason))
            elif reason.startswith("DAY"):
                acts.append("%s 白天让路（合规，不计闲置）" % n)

    for r in rows:
        if r.get("state") != "RUNNING":
            continue
        ts = str(r.get("claimed_at") or r.get("started_at") or "")
        try:
            age = now - datetime.fromisoformat(ts).timestamp()
        except Exception:
            age = -1
        if age > STUCK_S:
            acts.append("作业 %s 运行 %.1fh 无回执：主控按租约重排/判 FAILED"
                        % (r.get("id"), age / 3600))

    # 心跳新鲜但从不回执行结果 = 执行器没在跑。这是整夜"派了没人接"的真因，
    # 与"机器坏了"完全不同：心跳由 fleet_hb 一个任务发，车道由 lane_agent 另一个任务跑。
    for n, v in lanes.items():
        if not v.get("online"):
            continue
        lr = v.get("last_result") or {}
        lag = None
        try:
            lag = (now - datetime.fromisoformat(lr.get("ts")).timestamp()) / 60
        except Exception:
            pass
        if v.get("job") and (lag is None or lag > 15):
            acts.append("%s 有派单但 %s 分钟无执行回执：执行器(lane_agent/HQ-ProductionClaim)没跑"
                        "——本机执行 `%s`"
                        % (n, "?" if lag is None else int(lag),
                           "python Tools/fleet/lane_agent.py --node %s" % n))

    failed = [r.get("id") for r in rows if r.get("state") == "FAILED"]
    if failed:
        acts.append("失败件 %d 个：%s —— 要么重派要么改卡，不能挂着" %
                    (len(failed), ",".join(str(x) for x in failed[:4])))

    dry = (q.get("open", 0) + q.get("running", 0)) == 0
    if dry:
        acts.append("队列抽干：主控不造活，生产席需按 NEED-SUPPLY 补真卡")

    pulse_age = time.time() - os.path.getmtime(os.path.join(D, "PULSE.json")) \
        if os.path.exists(os.path.join(D, "PULSE.json")) else 1e9
    if pulse_age > 300:
        acts.append("总控脉 %.0f 分钟未更新：看门狗应 kickstart com.fluxgroup.pulse" % (pulse_age / 60))

    online = sum(1 for v in lanes.values() if v.get("online"))
    head = [
        "# 机队监督摘要 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",
        "- 在线 %d/%d · 队列 open=%s running=%s failed=%s · 主控脉 %.0fs 前 · 本轮 %ss"
        % (online, len(lanes) or 5, q.get("open"), q.get("running"), q.get("failed"),
           pulse_age, pulse.get("sec")),
        "- 主控脉搏判定：%s%s" % ("正常" if (pulse.get("ok") and pulse_age < 300) else "异常",
                                "" if pulse.get("ok") else " · " + ",".join(pulse.get("blockers") or [])),
        "",
        "## 下一步（按优先级）",
    ]
    body = ["- " + a for a in acts[:10]] or ["- 无异常：各机按车道自领，主控只等回执"]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(head + body) + "\n")
    print("[supervisor] online=%d/%d actions=%d" % (online, len(lanes) or 5, len(acts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())