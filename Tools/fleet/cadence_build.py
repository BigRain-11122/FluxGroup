# -*- coding: utf-8 -*-
"""cadence_build.py - 从主控脉的 STAGES 生成细分节奏表（v3）。

为什么生成而不是手写：脉里 86 个阶段在跑，手写的表只登记了 32 条，剩下 54 条的
周期/判据没人管——"节奏表"就成了部分真相。这台机器负责把两边对齐：
  * STAGES 有的、表里没有 -> 补条目（周期取代码，域按规则分类，相位自动错峰）
  * 表里有、STAGES 没有    -> 标 orphan（说明是纸面任务，必须接线或删）
  * 已有手工条目           -> 保留其 accept/on_fail/deps（人手写的更准）

Usage: cadence_build.py [--out cph4/fleet/COMMAND-CADENCE-v3.json]
"""
import argparse
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
PULSE = os.path.join(ROOT, "Tools", "fleet", "master_pulse.py")
OLD = os.path.join(FLEET, "COMMAND-CADENCE-v2.json")

# 域分类：先按显式名单，再按关键词兜底。每条必须落一个域。
DOMAIN = {
    "值守": ["hb", "qcheck", "executor_guard", "card_contract_check", "deadline",
             "verify_done", "canary", "backup", "state_push", "submit_ledger"],
    "派单": ["supply_target", "night_plan", "night_fill", "bank_autofill", "workgen",
             "master", "inventory", "squeeze", "wait_map", "ceo_queue", "next_actions",
             "decision_router", "decision_close"],
    "执行": ["lane", "lane_agents", "closer", "autowork", "solver", "local_tasks",
             "mac_farm", "artifact_push", "asr_subs"],
    "线": ["census", "line_plan", "canon", "city", "ri", "checkups", "market", "quality",
           "done_audit", "contingency", "skills", "skill_promote", "radar", "forecast",
           "gate", "gate_rigor", "vault", "asset_reach", "asset_prompts", "biz",
           "review_proxy", "inference_audit", "modelradar", "ossradar"],
    "一屏": ["commander", "digest", "judge", "brain", "bulletin", "handoff", "supervisor",
             "metrics", "eventlog", "health", "chief", "surface", "showcase", "orgs",
             "mem", "decide", "warm", "social", "memory_nightly"],
    "方向": ["ceo_pilot", "ceo_three", "demand_audit", "fact_check", "model_plan",
             "fork_close", "self_improve", "tool_watch", "useful_load"],
}
DEFAULT_ACCEPT = {
    "值守": "rc 在 ok_rc 内且产出落在指定路径",
    "派单": "队列/车道有可见变化，或明确报「无活可派」",
    "执行": "回执含 rc、耗时、产出字节；无产物即判假完成",
    "线": "产出落盘且年龄可算；rc=2 视为告警不是故障",
    "一屏": "文件 mtime 前进且内容非空",
    "方向": "结论带证据指针，否则视为未出结论",
}
DEFAULT_FAIL = {
    "值守": "连续 3 轮失败 → 告警并停该阶段",
    "派单": "连续 2 轮无变化 → 报 E-SUPPLY-STUCK",
    "执行": "同卡 3 次未成 → E-ROOTCAUSE-3X 停线",
    "线": "同线 3 次告警未处理 → 交 CEO 待办",
    "一屏": "未更新 → 视为阶段未执行，报 E-STAGE-SILENT",
    "方向": "无候选时须写明「没有需要你做的事」，不许空文件",
}


def stages():
    src = open(PULSE, encoding="utf-8").read()
    tree = ast.parse(src)
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "STAGES" for t in node.targets):
            for e in node.value.elts:
                if isinstance(e, (ast.Tuple, ast.List)) and len(e.elts) >= 3:
                    n = e.elts[0].value if isinstance(e.elts[0], ast.Constant) else None
                    ev = e.elts[2].value if isinstance(e.elts[2], ast.Constant) else None
                    if n and n not in out:
                        out[n] = int(ev or 60)
    return out


def argv_map():
    """Extract each stage's argv so产出路径 can be inferred instead of invented."""
    src = open(PULSE, encoding="utf-8").read()
    tree = ast.parse(src)
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "STAGES" for t in node.targets):
            for e in node.value.elts:
                if isinstance(e, (ast.Tuple, ast.List)) and len(e.elts) >= 2:
                    n = e.elts[0].value if isinstance(e.elts[0], ast.Constant) else None
                    if not n or n in out:
                        continue
                    parts = []
                    if isinstance(e.elts[1], (ast.List, ast.Tuple)):
                        for x in e.elts[1].elts:
                            if isinstance(x, ast.Constant):
                                parts.append(str(x.value))
                    out[n] = parts
    return out


def infer_output(name, parts):
    """Return (path, inferred). Prefer an explicit --out/--json arg, else a convention.

    A convention is marked inferred=True so nobody mistakes it for a verified contract.
    """
    for i, tok in enumerate(parts):
        if tok in ("--out", "--json", "--outfile") and i + 1 < len(parts):
            cand = parts[i + 1]
            if cand and not cand.startswith("-"):
                return cand, False
    tool = ""
    for t in parts:
        if t.endswith(".py"):
            tool = os.path.basename(t)[:-3]
            break
    if tool:
        return "cph4/fleet/state/%s.json" % tool, True
    return "(该阶段无固定产物，以 stdout 为准)", True


def domain_of(name):
    for d, names in DOMAIN.items():
        if name in names:
            return d
    for kw, d in (("asset", "线"), ("model", "线"), ("gate", "线"), ("line", "线"),
                  ("supply", "派单"), ("night", "派单"), ("work", "派单"),
                  ("ceo", "方向"), ("audit", "方向")):
        if kw in name:
            return d
    return "一屏"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(FLEET, "COMMAND-CADENCE-v3.json"))
    a = ap.parse_args()

    live = stages()
    argvs = argv_map()
    old = {}
    id2stage = {}
    try:
        with open(OLD, encoding="utf-8") as f:
            for t in (json.load(f).get("tasks") or []):
                st = t.get("stage")
                if st:
                    old[st] = t
                if t.get("id") and st:
                    id2stage[t["id"]] = st   # v2 用 T## 作 id，v3 用 S-<stage>
    except Exception:
        pass

    # 按周期分组自动错峰：同周期内均匀铺相位，避免撞车
    by_period = {}
    for n, p in live.items():
        by_period.setdefault(p, []).append(n)

    tasks, orphans = [], []
    for p, names in sorted(by_period.items()):
        names.sort()
        k = len(names)
        for i, n in enumerate(names):
            eff = max(45, p)
            phase = (i * max(1, eff // k)) % eff
            prev = old.get(n, {})
            d = prev.get("domain") or domain_of(n)
            _out = infer_output(n, argvs.get(n) or [])
            tasks.append({
                "id": "S-%s" % n,
                "domain": d,
                "stage": n,
                "period_s": max(45, p),
                "phase_s": phase,
                "actor": prev.get("actor") or "rule",
                "action": prev.get("action") or ("执行 %s 阶段" % n),
                "input": prev.get("input") or [],
                "output": prev.get("output") or _out[0],
                "output_inferred": (False if prev.get("output") else _out[1]),
                "accept": prev.get("accept") or DEFAULT_ACCEPT[d],
                "on_fail": prev.get("on_fail") or DEFAULT_FAIL[d],
                **({"depends_on": [("S-" + id2stage[d]) if d in id2stage else d
                                   for d in prev["depends_on"]]} if prev.get("depends_on") else {}),
                **({"backoff": prev["backoff"]} if prev.get("backoff") else {}),
                **({"budget": prev["budget"]} if prev.get("budget") else {}),
            })
    for st, t in old.items():
        if st not in live:
            orphans.append(st)

    doc = {
        "_comment": "指挥节奏表 v3（2026-11-07）：由 cadence_build.py 从 master_pulse.STAGES 生成，"
                    "覆盖脉里每一个在跑的细分阶段；手工条目保留其判据。改周期只改脉，再重跑生成器。",
        "version": "v3-20261107",
        "base_tick_s": 45,
        "scope": {"covers": "脉里全部 %d 个阶段（值守/派单/执行/线/一屏/方向）" % len(live),
                  "excludes": "各产品线自己的业务流程（不进脉，不进本表）"},
        "law": [
            "数字一律规则算，不交 4B",
            "产出必须落盘且度量不得引用自己写的文件",
            "模型只做归类/摘要/打分/抽取，结论可被规则复核；模型不可用一律降级为规则",
            "只留三类人工闸：不可逆、对外发布、花钱超限",
            "写同一个文件的任务必须由 depends_on 串起来",
            "闲置而有活=流程缺陷，当场改流程",
        ],
        "actors": {"rule": {"cost": "0 token"}, "model": {"model": "qwen3.5:4b-mlx"},
                   "embed": {"model": "qwen3-embedding:0.6b"}},
        "tasks": tasks,
        "generated": {"from": "Tools/fleet/master_pulse.py:STAGES",
                      "stages": len(live), "orphans": orphans},
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(json.dumps({"out": os.path.relpath(a.out, ROOT), "tasks": len(tasks),
                      "periods": len(by_period), "orphans": orphans,
                      "domains": {d: sum(1 for t in tasks if t["domain"] == d)
                                  for d in DOMAIN}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())