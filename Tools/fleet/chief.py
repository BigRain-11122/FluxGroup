#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chief.py - 总管环：每 2 分钟读事实、做处置、留痕、写早报。

设计（2026-11-02 CEO 定）：有限权的总管。
  * 只做四件：盯盘子、做处置、收异常、写早报；
  * 动作白名单，越界即拒；执行一律走脚本与队列，不许自己跑任意命令；
  * 90% 确定性规则，模型只在"归因写一句话"时用；
  * 分四阶段放权：1 只读 / 2 给建议 / 3 可自处置 / 4 可停线扩权。

事实源：队列、断言、通信、计分、发布台账、车道文件。
产物：chief/BRIEF-<日期>.md（早报）+ chief/LEDGER.jsonl（决定台账）+ chief/STATE.json。

用法：python3 chief.py [--json] [--dry]
"""
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
CHIEF = os.path.join(FLEET, "chief")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
MODE = os.path.join(CHIEF, "MODE.json")
LEDGER = os.path.join(CHIEF, "LEDGER.jsonl")

sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

ACTIONS = {"report", "requeue", "promote", "flag", "stop-line", "night-pack", "escalate"}


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def mode():
    m = jload(MODE, {}) or {}
    return int(m.get("stage") or 1), m


def log(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def act(kind, payload, stage, allowed_min, dry):
    """动作闸：白名单 + 阶段闸。返回 (done, note)。"""
    if kind not in ACTIONS:
        return False, "action-not-whitelisted"
    if stage < allowed_min:
        return False, "stage-%d-cannot-%s" % (stage, kind)
    if dry:
        return False, "dry-run"
    return True, "ok"


def main(argv):
    dry = "--dry" in argv
    os.makedirs(CHIEF, exist_ok=True)
    stage, mcfg = mode()
    q = fl.read_jsonl(QUEUE)
    bl = fl.read_jsonl(BACKLOG)
    inv = jload(os.path.join(STATE, "invariants.json"), {}) or {}
    com = jload(os.path.join(STATE, "comms.json"), {}) or {}
    met = jload(os.path.join(STATE, "metrics.json"), {}) or {}
    ck = jload(os.path.join(STATE, "checkups.json"), {}) or {}
    now = datetime.now()

    running = [r for r in q if r.get("state") == "RUNNING"]
    opens = [r for r in q if r.get("state") == "OPEN"]
    red = [(c.get("id"), c.get("count"), (c.get("samples") or [])[:2])
           for c in (inv.get("checks") or []) if c.get("count")]
    bad_nodes = [n for n in (com.get("nodes") or []) if n.get("flags")]
    ready = [r for r in bl if r.get("state") == "READY" and r.get("cmd")]

    decisions, applied = [], []
    # 规则 1：机器空着且有匹配活 → 让出（派单器下一轮会接，这里只记）
    idle = [n for n in (com.get("nodes") or []) if "IDLE-WITH-QUEUE" in (n.get("flags") or [])]
    if idle:
        decisions.append({"kind": "flag", "why": "%d 台机空转且有活" % len(idle),
                          "target": [n["node"] for n in idle], "min_stage": 1})

    # 规则 2：卡在 RUNNING 但机器很久没回执 → 退回重排（可逆）
    stuck = [r for r in running
             if any(n.get("node") == r.get("owner") and "NO-RECEIPT-1H" in (n.get("flags") or [])
                    for n in (com.get("nodes") or []))]
    if stuck:
        decisions.append({"kind": "requeue", "why": "%d 张卡在跑但 1 小时无回执" % len(stuck),
                          "target": [r["id"] for r in stuck], "min_stage": 3})

    # 规则 3：队列空且有候选 → 灌卡（夜间包同理，可逆）
    if len(opens) < 2 and ready:
        decisions.append({"kind": "promote", "why": "队列空，候选 %d 张" % len(ready),
                          "target": [r["id"] for r in ready][:3], "min_stage": 3})

    # 规则 4：P0 线 24h 无产物 → 升级（停线需 stage 4）
    p0_red = [s for i, _n, ss in red if i == "I14" for s in ss]
    if p0_red:
        decisions.append({"kind": "escalate", "why": "P0 线 24h 无产物：%d 条" % len(p0_red),
                          "target": p0_red[:3], "min_stage": 1})

    # 规则 5：供给缺口（队列空、候选空）→ 明说，不造假活
    if not opens and not ready:
        decisions.append({"kind": "escalate", "why": "队列与候选都空：供给缺口，不是调度故障",
                          "target": [], "min_stage": 1})

    # 执行（按阶段放权）
    for d in decisions:
        ok, note = act(d["kind"], d.get("target"), stage, d["min_stage"], dry)
        if ok and d["kind"] == "requeue":
            touched = []
            for r in stuck:
                r["state"] = "OPEN"
                r["owner"] = None
                r["retries"] = int(r.get("retries") or 0) + 1
                r["note"] = "chief-requeue: 1h 无回执"
                touched.append(r)
            fl.merge_jsonl(QUEUE, touched)
            applied.append({"kind": "requeue", "ids": [r["id"] for r in touched]})
        elif ok and d["kind"] == "promote":
            import subprocess
            r = subprocess.run([sys.executable, os.path.join(HERE, "night_fill.py"),
                                "--target", "3"], capture_output=True, text=True, timeout=120)
            applied.append({"kind": "promote", "out": (r.stdout or "").strip()[:120]})
        d["result"] = "applied" if ok else note

    # 阶段 4 的准入：连续 7 天、采纳率 >=80%（采纳=动作被执行且未被撤销）
    adoption = {"days": 0, "applied": 0, "total": 0, "rate": None, "eligible_stage4": False}
    try:
        rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
        applied_n = sum(1 for r in rows if r.get("result") == "applied")
        total_n = sum(1 for r in rows if r.get("action") != "flag")
        days = len({r.get("ts", "")[:10] for r in rows})
        rate = round(100.0 * applied_n / total_n, 1) if total_n else None
        adoption = {"days": days, "applied": applied_n, "total": total_n, "rate": rate,
                    "eligible_stage4": bool(days >= 7 and rate is not None and rate >= 80)}
    except Exception:
        pass

    # 早报（只写 3 件：要你定的、我在处理的、今天最该看的数）
    L = ["# 总管早报 %s（阶段 %d）" % (now.strftime("%Y-%m-%d %H:%M"), stage), ""]
    L.append("## 要你定的（≤3）")
    asks = [d for d in decisions if d["kind"] in ("escalate",)]
    for d in asks[:3]:
        L.append("- %s｜%s" % (d["why"], ", ".join(d.get("target") or []) or "-"))
    if not asks:
        L.append("- 无")
    L.append("")
    L.append("## 我在处理的")
    for d in decisions:
        if d["kind"] not in ("escalate",):
            L.append("- %s（%s）→ %s" % (d["why"], d["kind"], d.get("result")))
    if not any(d["kind"] != "escalate" for d in decisions):
        L.append("- 无")
    L.append("")
    L.append("## 今天的数")
    L.append("- 在产 %d / 待领 %d / 候选 %d" % (len(running), len(opens), len(ready)))
    L.append("- 断言红 %d 项%s" % (len(red), ("：" + ",".join("%s x%s" % (i, n) for i, n, _ in red[:5])) if red else ""))
    bad_ck = [r for r in (ck.get("lines") or []) if r.get("status") == "FAIL"]
    if bad_ck:
        L.append("- 体检不合格 %d 条：%s" % (len(bad_ck), "、".join(r["line"] for r in bad_ck[:4])))
    L.append("- 机器不一致 %d 台%s" % (len(bad_nodes),
                                 ("：" + ",".join("%s(%s)" % (n["node"], "、".join(n["flags"])) for n in bad_nodes[:3])) if bad_nodes else ""))
    if met.get("debt") is not None:
        L.append("- 结构债 %s 条，已降 %s%%" % (met.get("debt"), met.get("debt_drop_pct")))
    L.append("")
    L.append("")
    L.append("## 放权进度")
    L.append("- 阶段 %d｜近 %d 天决定 %s 条，执行 %s 条，采纳率 %s%%｜阶段4 资格：%s" % (
        stage, adoption["days"], adoption["total"], adoption["applied"],
        adoption["rate"], "是" if adoption["eligible_stage4"] else "否"))
    L.append("---")
    L.append("动作白名单：%s｜阶段闸：%s" % (",".join(sorted(ACTIONS)), mcfg.get("note", "")))
    brief = os.path.join(CHIEF, "BRIEF-%s.md" % now.strftime("%Y%m%d"))
    open(brief, "w", encoding="utf-8").write("\n".join(L) + "\n")

    # 台账：每行一个决定，永不删
    with open(LEDGER, "a", encoding="utf-8") as f:
        for d in decisions:
            f.write(json.dumps({"ts": now.isoformat(timespec="seconds"), "stage": stage,
                                "read": {"running": len(running), "open": len(opens),
                                         "ready": len(ready), "red": len(red)},
                                "judged": d["why"], "action": d["kind"],
                                "target": d.get("target"), "result": d.get("result")},
                               ensure_ascii=False) + "\n")

    out = {"ts": now.isoformat(timespec="seconds"), "stage": stage, "adoption": adoption,
           "decisions": decisions, "applied": applied, "brief": brief}
    json.dump(out, open(os.path.join(CHIEF, "STATE.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))