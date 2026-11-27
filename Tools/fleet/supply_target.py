#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""supply_target.py - 把「等输入」变成可执行的供给目标（不是再写一份清单）。

为什么（2026-11-04 主控职责面 mc-supply）：
  wait_map 已经把「谁等谁」画出来了，但等的那一头没有任何人接：卡在等
  full_mv_v721.mp4 / gaming/MiniGame，而全队没有一张卡在生产它们。供给缺口不是
  "库存 11 < 可再吃 38" 这个数字，是**这些具体产物没有归属**。

它对每条等输入回答四个问题（全部用盘上事实，判不了就写判不了）：
  1) 谁该产：按路径前缀映射业务线 + BUSINESS-MAP 的承办机；
  2) 有没有人已经在产：全队列里有没有卡的 deliverable 同名（任何状态）；
  3) 能不能现在产：该线在册工具里有没有产出它的工具（在册=文件在盘）；
  4) 不能产时缺什么：NEEDS-TOOL（无工具）/ NEEDS-CEO（卡在对外或花钱）/ NEEDS-PIN（工具在别的机器）。

产出：SUPPLY-TARGETS.md + state/supply-targets.json。
Exit: 0 无未归属缺口；1 有 needs-producer（供给缺口，告警不阻断）
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
WAIT = os.path.join(FLEET, "state", "wait-map.json")
BM = os.path.join(FLEET, "BUSINESS-MAP-v1.json")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
OUT = os.path.join(FLEET, "state", "supply-targets.json")
MD = os.path.join(FLEET, "SUPPLY-TARGETS.md")

# 路径前缀 → 业务线（只写能判死的；判不了就留空让人看）
PREFIX_LINE = (
    ("gaming/", "biggame"), ("media/drama", "bigstream-drama"), ("media/", "bigstream-mv"),
    ("cph4/fleet/mv0001", "bigstream-mv"), ("quant/", "bigmoney"),
    ("cph4/fleet/asset-lib", "asset-lib"), ("cph4/fleet/car", "car-gaming"),
)


def line_of(path):
    p = str(path).replace("\\", "/")
    for pre, lid in PREFIX_LINE:
        if p.startswith(pre):
            return lid
    return ""


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(WAIT):
        print("[supply-target] 没有 wait-map.json，先跑 wait_map.py")
        return 3
    w = json.load(open(WAIT, encoding="utf-8"))
    biz = {b.get("id"): b for b in json.load(open(BM, encoding="utf-8")).get("businesses") or []}

    cards = []
    for p in (QUEUE, BACKLOG):
        if os.path.exists(p):
            for ln in open(p, encoding="utf-8"):
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    cards.append(json.loads(ln))
                except Exception:
                    pass

    def producer_of(base):
        hits = [c for c in cards if os.path.basename(str(c.get("deliverable") or "")) == base]
        return hits

    rows, seen = [], set()
    for u in w.get("unknown_inputs") or []:
        key = (u.get("card"), u.get("needs"))
        if key in seen:
            continue
        seen.add(key)
        if u.get("kind") != "artifact-missing":
            continue                      # 工具/子仓/跨机类不是"没人产"，另行处理
        base = u["needs"]
        lid = line_of(u.get("path") or base)
        b = biz.get(lid) or {}
        prod = producer_of(base)
        if prod:
            st = "ALREADY-QUEUED" if any(str(x.get("state")).upper() in
                                        ("OPEN", "READY", "RUNNING", "CLAIMED") for x in prod) \
                 else "PRODUCED-ELSEWHERE"
            why = ("已有卡 %s(%s) 在做" % (prod[0].get("id"), prod[0].get("state")))
        else:
            st = "NEEDS-PRODUCER"
            why = ("全队列没有卡的 deliverable 等于 %s" % base)
        rows.append({"artifact": base, "path": u.get("path"),
                     "waited_by": u.get("card"), "line": lid or "UNMAPPED",
                     "owner": b.get("owner"), "status": st, "why": why,
                     "line_blocker": b.get("blocker_type"),
                     "next_product": b.get("next_product")})

    order = {"NEEDS-PRODUCER": 0, "UNMAPPED": 1, "PRODUCED-ELSEWHERE": 2, "ALREADY-QUEUED": 3}
    rows.sort(key=lambda r: order.get(r["status"], 9))
    need = [r for r in rows if r["status"] == "NEEDS-PRODUCER"]

    state = {"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
             "artifact_waits": len(rows), "needs_producer": len(need), "items": rows}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(state, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# 供给目标：谁该产那些没人产的产物（%s）" % state["ts"][:16], "",
          "产物类等输入 %d 条，其中 **%d 条无人生产**" % (len(rows), len(need)), ""]
    for r in rows:
        md.append("- [%s] `%s` ← %s 在等；线=%s 承办=%s；%s"
                  % (r["status"], r["artifact"], r["waited_by"], r["line"], r["owner"], r["why"]))
        if r["status"] == "NEEDS-PRODUCER":
            md.append("    该线下一件产物：%s（卡点 %s）"
                      % (r["next_product"] or "未声明", r["line_blocker"] or "-"))
    open(MD, "w", encoding="utf-8").write("\n".join(md) + "\n")

    if a.json:
        print(json.dumps(state, ensure_ascii=False))
    else:
        print("[supply-target] artifact-waits=%d needs-producer=%d -> SUPPLY-TARGETS.md"
              % (len(rows), len(need)))
        for r in rows[:8]:
            print("  %-18s %-28s line=%-16s owner=%s" %
                  (r["status"], r["artifact"][:28], r["line"], r["owner"]))
    return 1 if need else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))