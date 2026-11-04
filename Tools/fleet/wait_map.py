#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wait_map.py - 跨机依赖表：谁在等谁的产物（SYNC-BOARD 缺的那一列）。

为什么（2026-11-04 主控职责面 mc-sync）：
  互报只说了「各机产出了什么」，没说「谁卡在等谁」。跨机依赖因此变成不可派的死结：
  一台机的卡 OPEN 着，其实在等另一台机上一张卡的交付物，双方账上都"正常"，
  只有把边画出来才知道该催谁、该改谁。

做法（全用盘上事实，不猜）：
  * 待办卡（OPEN/READY/RUNNING/CLAIMED）的 requires 里每条路径取 basename；
  * 用全队列（含 DONE）的 deliverable 建 basename → 产卡/机 的索引；
  * 逐条判断：产物在不在盘、产卡什么状态、是否跨机 → 画成"谁等谁"的边；
  * 成环（A 等 B、B 等 A）单独报警——环永远解不开，必须改卡。

用法：
  python3 Tools/fleet/wait_map.py            # 一屏 + state/wait-map.json
  python3 Tools/fleet/wait_map.py --json
Exit: 0 无环；2 出现等待环（结构病，必须改卡）
"""
import argparse
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

FLEET = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
MD = os.path.join(FLEET, "WAIT-MAP.md")
OUT = os.path.join(FLEET, "state", "wait-map.json")

LIVE = ("OPEN", "READY", "RUNNING", "CLAIMED")


def norm(p):
    return os.path.basename(str(p).replace("\\", "/")).strip()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    q = fl.read_jsonl(QUEUE) if os.path.exists(QUEUE) else []
    b = fl.read_jsonl(BACKLOG) if os.path.exists(BACKLOG) else []
    allrows = q + b

    # producer index: deliverable basename -> (card id, owner, state)
    prod = {}
    for r in allrows:
        d = r.get("deliverable")
        if d:
            prod.setdefault(norm(d), []).append(
                {"id": r.get("id"), "owner": r.get("owner"), "state": r.get("state")})

    edges, unknown, cycles = [], [], []
    waits = defaultdict(lambda: defaultdict(list))     # owner -> producer_owner -> [card ids]
    for r in allrows:
        if str(r.get("state")).upper() not in LIVE:
            continue
        reqs = r.get("requires") or []
        if isinstance(reqs, str):
            reqs = [reqs]
        for p in reqs:
            base = norm(p)
            if not base:
                continue
            here = os.path.exists(p) or os.path.exists(os.path.join(ROOT, base))
            if here:
                continue                      # 输入就在盘上：不算"在等"
            cand = prod.get(base) or []
            if not cand:
                kind = ("cross-machine" if (":" in str(p) or str(p).startswith("\\\\")
                                           or str(p).startswith("/Volumes"))
                        else "no-producer")
                unknown.append({"card": r.get("id"), "owner": r.get("owner"), "needs": base,
                                "path": str(p)[:80], "kind": kind})
                continue
            for c in cand:
                if c["id"] == r.get("id"):
                    continue
                if here:
                    continue
                edges.append({"waiter": r.get("id"), "waiter_owner": r.get("owner"),
                              "producer": c["id"], "producer_owner": c["owner"],
                              "producer_state": c["state"], "artifact": base,
                              "cross_machine": (r.get("owner") or "") != (c["owner"] or "")})
                if c["owner"]:
                    waits[r.get("owner") or "?"][c["owner"]].append(r.get("id"))

    # 环检测：owner 级别的等待图
    def has_cycle(g):
        color = {}

        def dfs(u):
            color[u] = 1
            for v in g.get(u, ()):
                if color.get(v) == 1:
                    return True
                if color.get(v) is None and dfs(v):
                    return True
            color[u] = 2
            return False

        return any(color.get(n) is None and dfs(n) for n in list(g))

    if has_cycle({k: list(v) for k, v in waits.items()}):
        cycles = sorted(k for k, v in waits.items() if k in v)

    state = {"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
             "live_cards": len([r for r in allrows if str(r.get("state")).upper() in LIVE]),
             "edges": edges, "unknown_inputs": unknown, "owner_cycles": cycles,
             "matrix": {k: {kk: sorted(set(vv)) for kk, vv in v.items()} for k, v in waits.items()}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)

    lines = ["# 谁在等谁的产物（wait-map）%s" % state["ts"][:16], "",
             "在办卡 %d · 依赖边 %d · 未知输入 %d · 等待环 %d" %
             (state["live_cards"], len(edges), len(unknown), len(cycles)), ""]
    for owner, deps in sorted(waits.items()):
        for po, cards in sorted(deps.items()):
            tag = "同机" if owner == po else "跨机"
            lines.append("- %s 等 %s（%s）：%s" % (owner, po, tag, "、".join(sorted(set(cards))[:6])))
    for u in unknown[:12]:
        why = ("另一台机上的产物，本机看不见" if u["kind"] == "cross-machine"
               else "没有任何卡的 deliverable 对应它")
        lines.append("- [等输入] %s 需要 %s —— %s" % (u["card"], u["needs"], why))
    for c in cycles:
        lines.append("- [环] %s 与下游互相等待，必须改卡（拆小或补输入）" % c)
    if not edges and not unknown:
        lines.append("- 无跨卡依赖：当前在办卡都不靠别人的产物")
    with open(MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(state, ensure_ascii=False))
    else:
        print("[wait-map] live=%d edges=%d unknown=%d cycles=%d"
              % (state["live_cards"], len(edges), len(unknown), len(cycles)))
        for owner, deps in sorted(waits.items()):
            for po, cards in sorted(deps.items()):
                print("  %s 等 %s：%d 张卡" % (owner, po, len(set(cards))))
    return 2 if cycles else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))