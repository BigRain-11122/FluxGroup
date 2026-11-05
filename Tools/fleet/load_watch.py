#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""load_watch.py - 满负荷巡检（60 秒一次，只读+告警，不写任何账本）。

高压线（CEO 2026-11-05）：「没有满负荷或者空转」。
  满负荷 = 每台在线机的槽位都被可跑的真卡占住；
  空转   = 机器在线却没卡可跑，或 RUNNING 卡没有进展。

为什么独立于主控脉：主控脉 180 秒一轮、还做很多重活；空转是分钟级问题，
需要一条更快的只读眼睛。它不写队列（避免多写者），只产出告警件，
由主控脉在下一轮据此补料。

判定（全部可核）：
  U1 机器在线 且 无 RUNNING 卡 且 队列里有本机可跑的 OPEN 卡 → UNDER-DISPATCH
  U2 机器在线 且 无 RUNNING 卡 且 队列里无本机可跑的 OPEN 卡 → SUPPLY-DRY
  U3 RUNNING 卡 progress_ts 超过 stall_after_s → STALLED
  U4 ACTIVE 线不在 LINE-NEXT-STEPS 里，且队列里没有它的活 → LINE-IDLE

用法：python3 Tools/fleet/load_watch.py [--json]
Exit: 0 全满；1 有缺口（告警，不是故障）
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "state", "load-watch.json")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def runnable_here(card, node):
    if card.get("state") != "OPEN":
        return False
    nodes = card.get("nodes") or []
    if nodes and node not in nodes:
        return False
    if node == "bm-m" and (card.get("needs") == "gpu" or card.get("heavy")
                           or int(card.get("minutes") or 0) > 3):
        return False
    dl = card.get("deliverable")
    if dl:
        p = dl if os.path.isabs(dl) else os.path.join(ROOT, dl)
        if os.path.exists(p):
            return False
    return True


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    cfg = jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}
    stall_s = int(((cfg.get("progress") or {}).get("stall_after_s")) or 1800)
    slots = (cfg.get("supply") or {}).get("slots_per_node") or {}

    ms = jload(os.path.join(F, "dispatcher", "MASTER-STATE.json"), {}) or {}
    lanes = ms.get("lanes") or {}
    queue = rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
    running = [r for r in queue if r.get("state") == "RUNNING"]
    openc = [r for r in queue if r.get("state") == "OPEN"]

    gaps = []
    now = datetime.now()
    nodes = []
    for node, v in lanes.items():
        online = bool(v.get("online"))
        if not online:
            continue
        n_run = len([r for r in running if r.get("owner") == node or node in (r.get("nodes") or [])])
        n_can = len([r for r in openc if runnable_here(r, node)])
        cap = int(slots.get(node, 1) or 1)
        nodes.append({"node": node, "running": n_run, "runnable": n_can, "slots": cap})
        if n_run == 0 and n_can > 0:
            gaps.append({"node": node, "kind": "UNDER-DISPATCH",
                         "why": "有 %d 张本机可跑的卡却没开工" % n_can})
        elif n_run == 0 and n_can == 0:
            gaps.append({"node": node, "kind": "SUPPLY-DRY",
                         "why": "在线但无卡可跑：需要补料"})
        elif n_run < cap and n_can > 0:
            gaps.append({"node": node, "kind": "PARTIAL",
                         "why": "槽位 %d 只用了 %d，还有 %d 张可跑" % (cap, n_run, n_can)})

    stalled = []
    for r in running:
        try:
            idle = (now - datetime.fromisoformat(str(r.get("progress_ts")))).total_seconds()
        except Exception:
            continue
        if idle > stall_s:
            stalled.append({"id": r.get("id"), "idle_s": int(idle)})
    for s in stalled:
        gaps.append({"kind": "STALLED", "why": "%s 无进展 %ds" % (s["id"], s["idle_s"])})

    # 4) ACTIVE 线不许静默搁置
    truth = (jload(os.path.join(F, "state", "lines.json"), {}) or {})
    declared = jload(os.path.join(F, "LINE-NEXT-STEPS.json"), {}) or {}
    have_steps = set((declared.get("lines") or {}).keys())
    line_busy = {(r.get("line") or "") for r in queue if r.get("state") in ("OPEN", "RUNNING")}
    blocked = (cfg.get("capacity") or {}).get("blocked_active") or {}
    idle_lines = []
    blocked_lines = []
    for l in truth.get("lines") or []:
        lid = l.get("id")
        if str(l.get("declared")) != "ACTIVE":
            continue
        if lid in blocked:
            blocked_lines.append({"line": lid, "waiting_on": blocked[lid]})
            continue
        if lid in have_steps or lid in line_busy:
            continue
        idle_lines.append(lid)
        gaps.append({"line": lid, "kind": "LINE-IDLE",
                     "why": "ACTIVE 但没有下一步声明、队列里也没有它的活"})

    out = {"ts": now.isoformat(timespec="seconds"), "nodes": nodes,
           "gaps": gaps, "gap_count": len(gaps),
           "stalled": stalled, "idle_lines": idle_lines, "blocked_lines": blocked_lines,
           "verdict": "FULL" if not gaps else "GAPS"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[load-watch] %s gaps=%d" % (out["verdict"], len(gaps)))
        for g in gaps[:8]:
            print("  - %s %s: %s" % (g.get("kind"), g.get("node") or g.get("line") or "", g["why"]))
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))