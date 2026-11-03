#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主控的一屏：所有业务的最下一步，与磁盘实况合并后生成。

CEO 2026-11-03：主控要对所有业务了如指掌，随时能给出下一步任务。
所以这里不做分析，只做三件确定性的事：
  1. 读 BUSINESS-MAP-v1.json（每条业务的 目标/阶段/下一产物/承办机/判据/卡点）
  2. 与磁盘实况合并：该业务当前是否有卡在跑、是否有 READY 待提、工序表卡在哪段
  3. 生成 NEXT-ACTIONS.md（一屏）+ NEXT-ACTIONS.json（机读）

判据：一条业务只有三种状态，人一眼能分
  RUNNING  有卡在跑 → 显示卡号与机器
  QUEUED   有 READY/OPEN → 显示下一张
  STALLED  无卡在跑也无待办 → 必须显示卡点类型与下一步动作（不许写"待定"）

用法：
  python3 Tools/fleet/next_actions.py            # 生成一屏
  python3 Tools/fleet/next_actions.py --alert    # 有 STALLED 的 ENGINE 卡点时 rc=2
"""

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
MAP = os.path.join(FLEET, "BUSINESS-MAP-v1.json")


def rows(p):
    out = []
    if not os.path.exists(p):
        return out
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--alert", action="store_true")
    a = ap.parse_args(argv)
    bm = json.load(open(MAP, encoding="utf-8"))
    q = rows(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    b = rows(os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl"))

    def live(lid):
        run = [r for r in q if r.get("line") == lid and r.get("state") == "RUNNING"]
        if run:
            return "RUNNING", run[0].get("id"), run[0].get("owner")
        ready = [r for r in q if r.get("line") == lid and r.get("state") == "OPEN"]
        ready += [r for r in b if r.get("line") == lid and r.get("state") == "READY"]
        if ready:
            return "QUEUED", ready[0].get("id"), None
        return "STALLED", None, None

    out, stalled_engine = [], 0
    for x in bm["businesses"]:
        st, cid, owner = live(x["id"])
        if st == "STALLED" and x["blocker_type"] == "ENGINE":
            stalled_engine += 1
        out.append(dict(x, state=st, card=cid, running_on=owner))
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "businesses": out,
           "counts": {k: sum(1 for y in out if y["state"] == k) for k in ("RUNNING", "QUEUED", "STALLED")},
           "stalled_engine": stalled_engine}
    p = os.path.join(FLEET, "NEXT-ACTIONS-%s.json" % time.strftime("%Y%m%d"))
    json.dump(rec, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# 所有业务的下一步（%s）" % rec["ts"], "",
          "运行 %d · 排队 %d · 停滞 %d（其中工程可自解 %d）" % (
              rec["counts"]["RUNNING"], rec["counts"]["QUEUED"],
              rec["counts"]["STALLED"], stalled_engine), "",
          "| 业务 | 优先 | 状态 | 下一个产物 | 承办 | 卡点 |", "|---|---|---|---|---|---|"]
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P9": 9}
    for y in sorted(out, key=lambda z: (order.get(z["prio"], 5), z["state"] != "STALLED")):
        st = y["state"] + ((" · " + str(y["card"])) if y["card"] else "")
        md.append("| %s | %s | %s | %s | %s | %s(%s) |" % (
            y["name"], y["prio"], st, y["next_product"], y["owner"],
            y["blocker_type"], y["blocker"][:60]))
    open(os.path.join(FLEET, "NEXT-ACTIONS.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")

    print("业务=%d RUNNING=%d QUEUED=%d STALLED=%d（ENGINE 停滞 %d）" % (
        len(out), rec["counts"]["RUNNING"], rec["counts"]["QUEUED"],
        rec["counts"]["STALLED"], stalled_engine))
    for y in out:
        if y["state"] == "STALLED":
            print("  [停] %-24s %s: %s" % (y["name"], y["blocker_type"], y["next_product"]))
    print("wrote cph4/fleet/NEXT-ACTIONS.md")
    return 2 if (a.alert and stalled_engine) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))