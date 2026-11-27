#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decision_router.py - 分层决策的机器执行（2026-11-05）。

法源：cph4/decision-chain.md §0（路由总表）/ §8（L0-L3 四层）/ 委托决策令 v2。
机读口径：cph4/fleet/DECISION-LAYERS-v1.json。

它解决的问题：此前所有问题只有两条路——落到主控，或者挂成"待 CEO"。实际上
绝大多数是线内技术问题（L1）或司域下一步（L2），根本不该占用 CEO 的带宽。

做法：把散落在各处的待决事项收进一个池子，按规则定级、给时限、给兜底动作；
到期自动执行兜底，并把真正需要 CEO 的那几条单独列出来（最多 3 条）。

输入（全部盘上事实）：
  PRODUCTION-QUEUE.jsonl      停线卡（E-ROOTCAUSE-3X）
  state/master-decision.json  主控本轮判出的 SUPPLY / STOP-DIAGNOSE
  state/ceo-queue.json        待裁件
  state/cloud-spend 对账       超预算
输出：
  state/decisions.json        分层决策台账（机读）
  DECISIONS.md                一屏（人读，只列待办与兜底）

用法：python3 Tools/fleet/decision_router.py [--json]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def rows_of(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return out


def load_ledger():
    """上一轮的决策台账：用它做"同一问题不重复开案"和"已兜底过就别再兜"。"""
    d = jload(os.path.join(F, "state", "decisions.json"), {}) or {}
    return {it.get("key"): it for it in (d.get("items") or []) if it.get("key")}


def classify(item):
    """三问定级：①CEO 保留域？②授权面内既定方针？③按级走。"""
    kind = item["kind"]
    for r in RULES:
        if r["kind"] == kind:
            return r["layer"], r["why"]
    return "L2", "默认司域"


def build_pool():
    pool = []
    q = rows_of(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
    for c in q:
        if str(c.get("state")) == "FAILED" and str(c.get("error_class") or "") == "E-ROOTCAUSE-3X":
            pool.append({"key": "rootcause:%s" % c.get("id"), "kind": "ROOT_CAUSE",
                         "subject": "停线卡 %s 需根因" % c.get("id"),
                         "evidence": c.get("note") or "",
                         "line": c.get("line") or ""})
    md = jload(os.path.join(F, "state", "master-decision.json"), {}) or {}
    for a in md.get("actions") or []:
        if a.get("action") in ("SUPPLY", "STOP-DIAGNOSE"):
            pool.append({"key": "supply:%s" % a.get("line"), "kind": "LINE_NEXT",
                         "subject": "%s 的下一步产物" % a.get("line"),
                         "evidence": a.get("why") or "", "line": a.get("line") or ""})
    # 闸红灯必须有消费者（2026-11-05 暴露：不变量 FAIL 挂了整天没人管，只写在报告里）。
    # 每条红项变成一条 L2 决策，到期按兜底走，不再"红着等"。
    gate = jload(os.path.join(F, "state", "gate-report.json"), {}) or {}
    inv = gate.get("invariants") or {}
    for iid, cnt in (inv.get("red") or []):
        if int(cnt or 0) <= 0:
            continue
        pool.append({"key": "gate:%s" % iid, "kind": "GATE_RED",
                     "subject": "闸红 %s × %d（%s）" % (iid, int(cnt),
                                                       inv.get("verdict") or "FAIL"),
                     "evidence": "cph4/fleet/state/gate-report.json",
                     "fallback_hint": "修到该项归零（修卡/修闸/改判据三选一），不许以沉默结案",
                     "line": "fleet-ops"})
    cq = jload(os.path.join(F, "state", "ceo-queue.json"), {}) or {}
    for it in cq.get("items") or []:
        bt = str(it.get("blocker_type") or "").upper()
        kind = {"CEO": "DIRECTION", "EXTERNAL": "PHYSICAL"}.get(bt, "LINE_NEXT")
        if it.get("gate") == "对外":
            kind = "PUBLISH"
        pool.append({"key": "ceo:%s:%s" % (it.get("line"), str(it.get("ask"))[:24]),
                     "kind": kind, "subject": str(it.get("ask"))[:120],
                     "evidence": str(it.get("accept") or ""), "line": it.get("line") or ""})
    return pool


def line_status():
    """线级既定状态。用于拦掉"已经按 CEO 令停掉的线又被每天问一次放行"这种噪音。"""
    reg = jload(os.path.join(F, "LINE-REGISTRY.json"), {}) or {}
    return {l.get("id"): str(l.get("status") or "").upper() for l in (reg.get("lines") or [])}


def already_decided(item, status):
    """CEO 已定的不重复问：PARKED 线问"是否放行"= 重复追问，属噪音，不是新决策。"""
    st = status.get(item.get("line")) or ""
    if st in ("PARKED", "DORMANT") and any(k in item.get("subject", "") for k in ("放行", "恢复", "是否")):
        return "该线已由 CEO 令停（%s），恢复需新令，不作为待办重复追问" % st
    return ""


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    global RULES
    cfg = jload(os.path.join(F, "DECISION-LAYERS-v1.json"), {}) or {}
    RULES = cfg.get("routing_rules") or []
    layers = cfg.get("layers") or {}
    prev = load_ledger()
    status = line_status()
    now = datetime.now()

    items, seen = [], set()
    for it in build_pool():
        if it["key"] in seen:
            continue
        seen.add(it["key"])
        layer, why = classify(it)
        spec = layers.get(layer) or {}
        sla = spec.get("sla_h")
        old = prev.get(it["key"]) or {}
        first = old.get("first_seen") or now.isoformat(timespec="seconds")
        try:
            due = (datetime.fromisoformat(first) +
                   timedelta(hours=float(sla))).isoformat(timespec="seconds") if sla else None
        except Exception:
            due = None
        overdue = bool(due and now.isoformat(timespec="seconds") > due)
        # 兜底：到期未决就按本层兜底动作走，并记 fallback_used（不是无限等）
        fallback = spec.get("fallback")
        used = old.get("fallback_used") or False
        settled = already_decided(it, status)
        state_now = "OPEN"
        if settled:
            state_now = "ALREADY-DECIDED"      # 已按 CEO 令停线，不重复追问
        elif layer == "CEO":
            state_now = "AWAIT-CEO"            # 该事项本身不推进，其他线照跑
        elif overdue and not used:
            state_now = "FALLBACK"
            used = True
        elif used:
            state_now = "FALLBACK-DONE"
        items.append({"key": it["key"], "kind": it["kind"], "layer": layer,
                      "layer_name": spec.get("name"), "subject": it["subject"],
                      "line": it["line"], "why_routed": why, "sla_h": sla,
                      "first_seen": first, "due_at": due, "overdue": overdue,
                      "status": state_now, "fallback": fallback,
                      "fallback_note": it.get("fallback_hint") or spec.get("fallback_note"),
                      "fallback_used": used, "evidence": it.get("evidence") or "",
                      "settled": settled})

    order = {"CEO": 0, "L3": 1, "L2": 2, "L1": 3, "L0": 4}
    items.sort(key=lambda x: (order.get(x["layer"], 9), str(x["due_at"] or "")))
    ceo = [i for i in items if i["layer"] == "CEO" and not i["settled"] and i["status"] == "AWAIT-CEO"]
    out = {"ts": now.isoformat(timespec="seconds"), "source": "decision_router.py",
           "layers_used": {k: len([i for i in items if i["layer"] == k and not i["settled"]])
                           for k in layers},
           "ceo_count": len(ceo), "settled_count": len([i for i in items if i["settled"]]),
           "items": items, "conflict_rule": cfg.get("conflict_rule")}
    os.makedirs(os.path.join(F, "state"), exist_ok=True)
    with open(os.path.join(F, "state", "decisions.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    lines = ["# 分层决策台账 %s" % out["ts"], "",
             "分布：%s" % ", ".join("%s=%d" % (k, v) for k, v in out["layers_used"].items()), ""]
    if ceo:
        lines += ["## 需要你（其余各层自决，不占你带宽）", ""]
        for i, it in enumerate(ceo[:3], 1):
            lines.append("%d. [%s] %s —— %s" % (i, it["kind"], it["subject"][:90], it["fallback_note"]))
        lines.append("")
    lines += ["## 各层在办（到期自动走兜底）", "", "| 层 | 事项 | 到期 | 兜底 |", "|---|---|---|---|"]
    for it in items:
        if it["layer"] == "CEO" or it["settled"]:
            continue
        lines.append("| %s | %s | %s | %s |" % (
            it["layer_name"] or it["layer"], it["subject"][:52],
            (it["due_at"] or "-")[5:16], it["fallback"]))
    with open(os.path.join(F, "DECISIONS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))