#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""supply_guard.py - 供给守卫：每台在线机器必须随时有可跑卡，否则当场补料并报警。

为什么（CEO 2026-11-05「如何保障一直能正常供给任务，不仅自己满负荷，机队也满负荷」）：
  造卡器早就存在（workgen / supply_batch / prep_work / backlog_fill），但「什么时候该造」
  没人判——load_watch 报 SUPPLY-DRY 只是个观察，没有任何执行者。
  且监测工具本身被合并删掉过一次（load_watch.py 消失、launchd 还在调它），
  所以守卫必须自己检工具完整性，不能假设上游都在。

水位线：每台在线机器 runnable >= floor（默认 3）。低于就依次尝试：
  1) supply_batch --apply（把盘上真活铺成卡）
  2) 仍不足 → 记 SUPPLY-SHORT，写缺口明细交主控，不造无输入的假卡

判据（都可机器核）：
  - runnable = 队列里 state∈{READY,OPEN} 且 (无 nodes 或 nodes 含本机) 且未超时的卡
  - 在线 = state/comms.json 里 online=true
  - 工具缺失 = MISSING-TOOL，直接判红（这是本次真事故）

用法：
  python3 Tools/fleet/supply_guard.py [--floor 3] [--apply] [--json out.json]
Exit: 0 全部达标；1 有机器低于水位；2 关键工具缺失
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
COMMS = os.path.join(STATE, "comms.json")

CRITICAL_TOOLS = [
    "lane_agent.py", "closer.py", "master_agent.py", "workgen.py",
    "supply_batch.py", "asset_pull.py", "asset_gap_audit.py",
    "soak_watch.py", "fleet_lane.py", "master_pulse.py",
]


def load_rows(path):
    rows = []
    if not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def nodes_of(row):
    n = row.get("nodes") or row.get("hard_nodes") or []
    if isinstance(n, str):
        n = [n]
    return [str(x).strip() for x in n if str(x).strip()]


def runnable_for(node, rows):
    """state∈{READY,OPEN} 且 无 nodes 或 nodes 含本机。"""
    out = []
    for r in rows:
        if str(r.get("state", "")).upper() not in ("READY", "OPEN"):
            continue
        ns = nodes_of(r)
        if ns and node not in ns:
            continue
        out.append(r.get("id"))
    return out


def excluded_nodes():
    """控制节点（role=主控）不按产线卡水位考核：它空转是常态，不是断供。"""
    try:
        cfg=json.load(open(os.path.join(F,"AUTONOMY-CONFIG.json"),encoding="utf-8"))
        return set((cfg.get("supply") or {}).get("exclude_nodes") or [])
    except Exception:
        return set()


def online_nodes():
    """在线判据：优先 comms.json；comms 过期或为空时退回 lanes/*.json 的心跳龄。

    2026-11-05 实测：冻结主控脉后 comms.json 不再刷新，守卫就报「在线 0 台」——
    在线判据不能吊死在单一易失文件上。
    """
    nodes = []
    fresh = False
    if os.path.isfile(COMMS):
        try:
            d = json.load(open(COMMS, encoding="utf-8"))
            ts = str(d.get("ts") or "")
            if ts:
                age = time.time() - time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
                fresh = age < 600
            nodes = [n.get("node") for n in (d.get("nodes") or []) if n.get("online")]
        except Exception:
            nodes, fresh = [], False
    if nodes and fresh:
        return nodes
    lanes = os.path.join(F, "lanes")
    if os.path.isdir(lanes):
        now = time.time()
        out = []
        for fn in os.listdir(lanes):
            if not fn.endswith(".json"):
                continue
            p = os.path.join(lanes, fn)
            try:
                if now - os.path.getmtime(p) < 1800:
                    out.append(fn[:-5])
            except OSError:
                pass
        if out:
            return sorted(set(out))
    return nodes


def tool_check():
    missing = [t for t in CRITICAL_TOOLS if not os.path.isfile(os.path.join(HERE, t))]
    return missing


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", type=int, default=3)
    ap.add_argument("--apply", action="store_true", help="水位不足时真的跑 supply_batch --apply")
    ap.add_argument("--json", default=os.path.join(STATE, "supply-guard.json"))
    a = ap.parse_args(argv)

    missing = tool_check()
    all_nodes = online_nodes()
    _skip = excluded_nodes()
    nodes = [n for n in all_nodes if n not in _skip]
    rows = load_rows(QUEUE) + load_rows(BACKLOG)
    before = {n: runnable_for(n, rows) for n in nodes}
    short = [n for n, ids in before.items() if len(ids) < a.floor]

    acted, errors = [], []
    if short and a.apply:
        sb = os.path.join(HERE, "supply_batch.py")
        if not os.path.isfile(sb):
            errors.append("MISSING-TOOL supply_batch.py，无法补料")
        else:
            try:
                p = subprocess.run([sys.executable, sb, "--apply"], cwd=ROOT,
                                   capture_output=True, text=True, timeout=300)
                acted.append({"tool": "supply_batch", "rc": p.returncode,
                              "tail": (p.stdout or p.stderr)[-300:]})
            except Exception as e:
                errors.append("supply_batch 失败：%s" % str(e)[:120])
        # 2026-11-05 实测：supply_batch 只覆盖软著/提审/资产三类，backlog 跑空后
        # 主控派单会返回 supply=[]。必须再接一个持续需求源，否则"水位"永远补不上。
        dg = os.path.join(HERE, "demand_gen.py")
        if os.path.isfile(dg):
            try:
                p = subprocess.run([sys.executable, dg], cwd=ROOT,
                                   capture_output=True, text=True, timeout=300)
                acted.append({"tool": "demand_gen", "rc": p.returncode,
                              "tail": (p.stdout or p.stderr)[-300:]})
            except Exception as e:
                errors.append("demand_gen 失败：%s" % str(e)[:120])
        else:
            errors.append("MISSING-TOOL demand_gen.py，需求源断供")
        rows = load_rows(QUEUE) + load_rows(BACKLOG)

    after = {n: runnable_for(n, rows) for n in nodes}
    still_short = {n: len(v) for n, v in after.items() if len(v) < a.floor}

    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "floor": a.floor,
        "online_nodes": nodes,
        "runnable_before": {n: len(v) for n, v in before.items()},
        "runnable_after": {n: len(v) for n, v in after.items()},
        "short_before": short,
        "short_after": still_short,
        "acted": acted,
        "errors": errors,
        "missing_tools": missing,
        "verdict": "RED-MISSING-TOOL" if missing else ("GAPS" if still_short else "PASS"),
    }
    os.makedirs(STATE, exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    print("[supply] 在线 %d 台（考核 %d，跳过控制节点 %s），水位 %d" % (len(all_nodes), len(nodes), ",".join(sorted(_skip)) or "-", a.floor))
    for n in nodes:
        flag = "OK " if len(after[n]) >= a.floor else "LOW"
        print("  %s %-8s 可跑 %d -> %d" % (flag, n, len(before[n]), len(after[n])))
    if missing:
        print("[supply] 关键工具缺失：%s" % ", ".join(missing))
    for e in errors:
        print("[supply] %s" % e)
    for x in acted:
        print("[supply] 补料 %s rc=%s" % (x["tool"], x["rc"]))
    if still_short:
        print("[supply] 仍低于水位：%s" % json.dumps(still_short, ensure_ascii=False))
    return 2 if missing else (1 if still_short else 0)


if __name__ == "__main__":
    sys.exit(main())