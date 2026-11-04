#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decision_close.py - 主控的裁决收敛环：ESCALATED 不许无声挂着。

为什么（2026-11-04 实测抓到的结构洞）：
  local_judge.autodecide 只收敛 state=="OPEN" 的行；4B 判不了的题被判成 ESCALATED 之后，
  **再没有任何一段代码处理它**——没有 SLA、没有到期默认、没有 owner。实测 5 件从 2026-11-03
  挂到 11-04（4 件 LINE-LATE 36h、1 件 CAPACITY 19.5h），而 brain_brief 每轮都在说
  "先清 5 件 ESCALATED"。等一个永远不来的"云端席位"，就是 CEO 明令禁止的"因为等而停工"。

它做的不是让模型再猜一次，而是**用盘上的事实按题型结案**：
  LINE-LATE / LINE-STALE  查 BUSINESS-MAP：有 blocker_type=CEO/EXTERNAL → 转待裁件（带默认方案与
                          到期时间）；否则查队列有没有卡在跑/待提 → 有则判定作废（证据过期），
                          没有则给出"派给谁、下一件产物是什么"。
  LINE-BLOCKED            按卡点类型换车道。
  CAPACITY                读实测内存：够用就判误报；不够就"暂停重活等夜窗，不杀进程"；
                          证据缺失就降级成体检，绝不凭 null 出杀进程指令。
  RETRY                   已重排 2 次的卡不放行第 3 次，按 error_class 归因（工具/输入/车道）。

写法约束：
  * 只写 JUDGMENT-QUEUE，且走 fleet_lane.merge_jsonl（唯一写入口，不整表覆盖）。
  * 结案一律带依据字段（verdict/evidence_used/model=policy:decision-close），可复核。
  * 待裁件保留 ESCALATED 状态，但必须带 due_at / default_if_silent；到期且不属"对外"门
    就按默认继续（CEO 最高规则：不许因为等 CEO 停工）。

用法：
  python3 Tools/fleet/decision_close.py            # 收敛一轮，写 DECISION-CLOSE.md + state
  python3 Tools/fleet/decision_close.py --json
  python3 Tools/fleet/decision_close.py --dry      # 只看会怎么判，不落盘
Exit: 0 全部收敛；2 仍有待 CEO 裁决项（可见的欠账，不是工具坏）
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

FLEET = os.path.join(ROOT, "cph4", "fleet")
JQ = os.path.join(FLEET, "dispatcher", "JUDGMENT-QUEUE.jsonl")
BM = os.path.join(FLEET, "BUSINESS-MAP-v1.json")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
MD = os.path.join(FLEET, "DECISION-CLOSE.md")
OUT = os.path.join(FLEET, "state", "decision-close.json")

SLA_H = 24            # 判定到期时限（与 local_judge 同口径）
CEO_DUE_H = 24        # 待裁件给 CEO 的答复时限
LIVE = ("RUNNING", "CLAIMED", "OPEN", "READY")


def rows(p):
    return fl.read_jsonl(p) if os.path.exists(p) else []


def age_h(ts):
    try:
        t = datetime.fromisoformat(str(ts)[:19])
        return (datetime.now() - t).total_seconds() / 3600.0
    except Exception:
        return None


def live_card(line_id):
    for r in rows(QUEUE):
        if r.get("line") == line_id and str(r.get("state")).upper() in LIVE:
            return r
    for r in rows(BACKLOG):
        if r.get("line") == line_id and str(r.get("state")).upper() == "READY":
            return r
    return None


def has_line_plan(line_id):
    d = os.path.join(FLEET, "ri")
    if not os.path.isdir(d):
        return False
    for base, _dirs, files in os.walk(d):
        if os.path.basename(base) != "lines":
            continue
        for f in files:
            if line_id.replace("-", "") in f.replace("-", "").replace("_", "") or \
                    line_id in f:
                return True
    return False


def verdict(row, biz):
    """按题型给结论。返回 dict(mode, answer, action, gate) —— 只读事实，不猜。"""
    kind = (row.get("kind") or "").upper()
    subj = row.get("subject") or ""
    ev = row.get("evidence") or {}

    if kind in ("LINE-LATE", "LINE-STALE", "LINE-LATE-ENGINE"):
        b = biz.get(subj)
        if not b:
            return {"mode": "ANSWER", "gate": None,
                    "answer": "业务总账里没有 %s 这条线 → 判定作废，改为补登记（BUSINESS-MAP）" % subj,
                    "action": {"kind": "REGISTER", "owner": "bm-m"}}
        bt = (b.get("blocker_type") or "").upper()
        if bt in ("CEO", "EXTERNAL"):
            return {"mode": "CEO", "gate": ("对外" if bt == "EXTERNAL" else "方向"),
                    "answer": "线迟到不是故障，是卡在 %s 级卡点：%s" % (bt, b.get("blocker") or b.get("next_product")),
                    "action": {"kind": "ASK-CEO", "owner": "ceo",
                               "ask": "「%s」下一步=%s，是否放行？" % (b.get("name"), b.get("next_product")),
                               "default": "机队继续做不依赖该决定的部分：%s（不对外、不花钱）"
                                          % (b.get("next_product") or "备料与预研")}}
        c = live_card(subj)
        if c:
            return {"mode": "ANSWER", "gate": None,
                    "answer": "证据已过期：队列里有 %s(%s) 在跑，本判定作废" % (c.get("id"), c.get("state")),
                    "action": {"kind": "NOOP", "card": c.get("id")}}
        plan = has_line_plan(subj)
        return {"mode": "ANSWER", "gate": None,
                "answer": "无线级卡点且无卡在跑 → 派「%s」，承办 %s（%s）"
                          % (b.get("next_product"), b.get("owner"),
                             "按工序表出卡" if plan else "该线无工序表，先补表"),
                "action": {"kind": "DISPATCH" if plan else "PLAN", "owner": b.get("owner")}}

    if kind == "LINE-BLOCKED":
        b = biz.get(subj) or {}
        return {"mode": "ANSWER", "gate": None,
                "answer": "卡点=%s（%s）→ 换车道：按 LANES 能力表改派；无车道可跑就拆小或降级"
                          % (b.get("blocker_type"), (b.get("blocker") or "")[:60]),
                "action": {"kind": "RELANE", "owner": b.get("owner")}}

    if kind == "CAPACITY":
        ram = ev.get("ram_free_gb")
        gpu = ev.get("gpu_util_pct")
        if ram is None:
            return {"mode": "ANSWER", "gate": None,
                    "answer": "证据缺失（ram_free_gb=null）→ 不碰进程，降级为一次资源体检",
                    "action": {"kind": "INSTRUMENT", "owner": subj or "bm-m"}}
        if float(ram) >= 8:
            return {"mode": "ANSWER", "gate": None,
                    "answer": "误报：实测空闲 %.1fGB ≥ 8GB，不动作（盲杀会打断生产）" % float(ram),
                    "action": {"kind": "NOOP"}}
        if float(ram) < 2:
            return {"mode": "ANSWER", "gate": None,
                    "answer": "实测空闲 %.1fGB < 2GB → 暂停该机重活等夜窗，不杀进程" % float(ram),
                    "action": {"kind": "PAUSE-HEAVY", "owner": subj}}
        return {"mode": "ANSWER", "gate": None,
                "answer": "空闲 %.1fGB 处黄区：GPU=%s → 只降并发，不释放进程" % (float(ram), gpu),
                "action": {"kind": "THROTTLE", "owner": subj}}

    if kind == "RETRY":
        note = str(ev.get("note") or "")
        if "attempt 2" in note or "2 次" in note:
            return {"mode": "ANSWER", "gate": None,
                    "answer": "已重排 2 次 → 不放行第 3 次；先按 receipt_attrib 归因"
                              "（TOOL 修工具 / INPUT 补输入 / LANE 换机），改卡后再入队",
                    "action": {"kind": "ATTRIBUTE", "owner": "bm-m"}}
        return {"mode": "ANSWER", "gate": None,
                "answer": "首次失败 → 允许重试一次，并带原因回执",
                "action": {"kind": "RETRY", "owner": "bm-m"}}

    return {"mode": "UNKNOWN", "gate": None,
            "answer": "题型 %s 没有规则 → 记规则缺口，不动作（不拿猜的结论结案）" % (kind or "?"),
            "action": {"kind": "RULE-GAP"}}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)

    jq = rows(JQ)
    bm = json.load(open(BM, encoding="utf-8")).get("businesses") or []
    biz = {b.get("id"): b for b in bm}

    closed, ceo, unknown, unchanged = [], [], [], 0
    now = datetime.now()
    patch = []
    for r in jq:
        st = (r.get("state") or "").upper()
        if st not in ("ESCALATED", "OPEN"):
            continue
        h = age_h(r.get("ts"))
        if h is None or h < SLA_H:
            continue                      # 未到期：留给 local_judge 正常流程
        v = verdict(r, biz)
        row = dict(r)
        row["verdict"] = v["answer"]
        row["model"] = "policy:decision-close"
        row["answered_at"] = now.isoformat(timespec="seconds")
        row["age_h"] = round(h, 1)
        row["next_action"] = v["action"]
        if v["mode"] == "ANSWER":
            row["state"] = "ANSWERED"
            row["answer"] = "【规则裁决·超%dh】%s" % (SLA_H, v["answer"])
            closed.append(row)
        elif v["mode"] == "CEO":
            due = datetime.fromisoformat(str(r.get("ts"))[:19]) + timedelta(hours=CEO_DUE_H)
            row["escalate_to"] = "ceo"
            row["gate"] = v["gate"]
            row["ceo_ask"] = v["action"].get("ask")
            row["default_if_silent"] = v["action"].get("default")
            row["due_at"] = due.isoformat(timespec="seconds")
            overdue = now > due
            row["overdue"] = overdue
            if overdue and v["gate"] != "对外":
                # CEO 最高规则：不许因为等而停工。方向类到期即按默认继续，事后复核。
                row["state"] = "ANSWERED"
                row["answer"] = ("【超期未裁·按默认继续】%s｜默认=%s"
                                 % (v["answer"], row["default_if_silent"]))
                row["default_activated"] = True
                closed.append(row)
            else:
                if overdue:
                    row["default_activated"] = True   # 对外门：草稿照做，签名仍归 CEO
                ceo.append(row)
        else:
            unknown.append(row)
        patch.append(row)

    if patch and not a.dry:
        fl.merge_jsonl(JQ, patch, key="key")

    state = {"ts": now.isoformat(timespec="seconds"), "scanned": len(jq),
             "closed": len(closed), "to_ceo": len(ceo), "rule_gap": len(unknown),
             "items": [{"key": x.get("key"), "kind": x.get("kind"), "age_h": x.get("age_h"),
                        "state": x.get("state"), "verdict": x.get("verdict"),
                        "next": x.get("next_action"), "gate": x.get("gate"),
                        "due_at": x.get("due_at")}
                       for x in closed + ceo + unknown]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)

    if not a.dry:
        lines = ["# 裁决收敛（decision-close）%s" % now.strftime("%Y-%m-%d %H:%M"), "",
                 "扫描 %d 件判定：结案 %d / 待 CEO %d / 规则缺口 %d" %
                 (len(jq), len(closed), len(ceo), len(unknown)), ""]
        for x in closed:
            lines.append("- [结案] %s（%sh）%s → %s" %
                         (x.get("key"), x.get("age_h"), x.get("verdict"),
                          json.dumps(x.get("next_action"), ensure_ascii=False)))
        for x in ceo:
            lines.append("- [待裁] %s（%sh·%s）问：%s｜默认：%s｜到期：%s" %
                         (x.get("key"), x.get("age_h"), x.get("gate"), x.get("ceo_ask"),
                          x.get("default_if_silent"), x.get("due_at")))
        for x in unknown:
            lines.append("- [缺口] %s 题型 %s 无规则" % (x.get("key"), x.get("kind")))
        with open(MD, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(state, ensure_ascii=False))
    else:
        print("[decision-close] 扫描 %d 结案 %d 转CEO %d 缺口 %d%s"
              % (len(jq), len(closed), len(ceo), len(unknown), " (dry)" if a.dry else ""))
        for x in closed:
            print("  [结案] %-40s %s" % (x.get("key"), (x.get("verdict") or "")[:70]))
        for x in ceo:
            print("  [待裁] %-40s %s 到期 %s" % (x.get("key"), x.get("gate"), x.get("due_at")))
    return 2 if (ceo or unknown) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))