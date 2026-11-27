#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前瞻：每条线的剩余弹药（runway）与卡点，提前发现"明天没活"。

CEO 2026-11-03：主控要大量调研与预备任务卡，不许等机队没活了。

判据（全部可机器复核，不估不猜）：
  runway_days = (OPEN+READY 卡数) / 近三日日均完成数
    - 无历史完成数 → 记 rate=0，runway=∞ 但要标 NO-HISTORY（别把"没跑过"当"弹药充足"）
    - runway < 2 天 → ALERT（明天可能断粮）
  blocker = 工序表里第一段"上一段已交、本段未交"的段，以及它缺什么
    - 段被 BLOCKED 回执卡住时，写明 error_class 与 gaps 首条
  no_table = 线在 registry 里 ACTIVE 却没有工序表 → 只能收自检卡，永远没有真任务

用法：
  python3 Tools/fleet/forecast.py            # 打印 + 写 cph4/fleet/FORECAST-<date>.json/.md
  python3 Tools/fleet/forecast.py --alert    # 仅当有 ALERT 时 rc=2（可接进慢批告警）
"""

import argparse
import glob
import json
import os
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
ALERT_DAYS = 2.0


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
    q = rows(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    b = rows(os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl"))
    reg = json.load(open(os.path.join(FLEET, "LINE-REGISTRY.json"), encoding="utf-8"))
    lines = reg.get("lines") or []
    tables = {}
    for p in glob.glob(os.path.join(FLEET, "ri", "*", "lines", "*.json")):
        try:
            t = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        tables[t.get("line")] = t

    stock = Counter()
    for r in q:
        if r.get("state") in ("OPEN", "RUNNING"):
            stock[r.get("line") or "none"] += 1
    for r in b:
        if r.get("state") == "READY":
            stock[r.get("line") or "none"] += 1

    today = time.strftime("%Y-%m-%d")
    days = []
    for i in (1, 2, 3):
        days.append(time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400 * i)))
    done = Counter()
    for r in q:
        if r.get("state") == "DONE" and str(r.get("finished_at") or "")[:10] in days:
            done[r.get("line") or "none"] += 1
    rate = {k: round(v / 3.0, 2) for k, v in done.items()}

    # 卡点：找每张工序表里"上一段产物在、本段产物不在"的第一段
    def stage_state(t):
        stages = t.get("stages") or []
        out = []
        for s in stages:
            dv = s.get("deliverable") or ""
            dv = dv.format(date=today.replace("-", "")) if dv else ""
            present = bool(dv) and os.path.exists(os.path.join(ROOT, dv))
            out.append({"id": s.get("id"), "ok": present, "deliverable": dv,
                        "needs": s.get("needs"), "hard_nodes": s.get("hard_nodes") or []})
        return out

    recs = []
    for l in lines:
        lid, status, prio = l.get("id"), l.get("status"), l.get("priority")
        r = rate.get(lid, 0)
        s = stock.get(lid, 0)
        runway = round(s / r, 1) if r else None
        t = tables.get(lid)
        item = {"line": lid, "status": status, "prio": prio, "stock": s,
                "rate_per_day": r, "runway_days": runway,
                "has_table": bool(t), "blocker": None, "flags": []}
        if not t:
            item["flags"].append("NO-TABLE")
        else:
            ss = stage_state(t)
            for st in ss:
                if not st["ok"]:
                    item["blocker"] = {"stage": st["id"], "deliverable": st["deliverable"],
                                       "needs": st["needs"], "hard_nodes": st["hard_nodes"]}
                    break
        if str(status).upper() in ("PARKED", "PAUSED"):
            item["flags"].append("INACTIVE")
        else:
            if runway is None and r == 0:
                item["flags"].append("NO-HISTORY")
            elif runway is not None and runway < ALERT_DAYS:
                item["flags"].append("ALERT")
        recs.append(item)

    recs.sort(key=lambda x: (x["prio"] or "P9", -x["stock"]))
    alerts = [x for x in recs if "ALERT" in x["flags"]]
    no_table = [x for x in recs if "NO-TABLE" in x["flags"] and "INACTIVE" not in x["flags"]]
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "alert_days": ALERT_DAYS,
           "lines": recs, "alerts": len(alerts), "no_table": len(no_table)}
    p = os.path.join(FLEET, "FORECAST-%s.json" % time.strftime("%Y%m%d"))
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# 前瞻：线的弹药与卡点（%s）" % out["ts"], "",
          "| 线 | 优先 | 状态 | 库存 | 日均 | 剩余天 | 卡点 |", "|---|---|---|---|---|---|---|"]
    for x in recs:
        md.append("| %s | %s | %s | %d | %s | %s | %s |" % (
            x["line"], x["prio"] or "-", x["status"] or "-", x["stock"],
            x["rate_per_day"] if x["rate_per_day"] else "0",
            ("%.1f" % x["runway_days"]) if x["runway_days"] is not None else "—",
            (x["blocker"]["stage"] if x["blocker"] else "—") +
            (" ⚠" + ",".join(x["flags"]) if x["flags"] else "")))
    open(os.path.join(FLEET, "FORECAST.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")

    print("lines=%d alert=%d no_table=%d -> cph4/fleet/FORECAST.md" % (len(recs), len(alerts), len(no_table)))
    for x in recs:
        if x["flags"]:
            mark = "!" if "ALERT" in x["flags"] else " "
            print(" %s %-20s stock=%d rate=%s runway=%s 卡点=%s %s" % (
                mark, x["line"], x["stock"], x["rate_per_day"],
                ("%.1f" % x["runway_days"]) if x["runway_days"] is not None else "—",
                (x["blocker"] or {}).get("stage", "-"), ",".join(x["flags"])))
    return 2 if (a.alert and alerts) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))