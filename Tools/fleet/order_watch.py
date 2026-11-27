#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""order_watch.py - 主控读令：CEO 在任何机器上发的令，主控必须当轮看见并重排。

为什么（CEO 2026-11-05：他有时会在 bm-a 等机器直接下令主控不能不知道）：
  令总线 fleet_order_bus.py 已经能把一条令分发到各车道、写 docs/orders.md 台账，
  但**没有任何一环去消费它**：令发出去、机器各自执行，主控仍按旧计划派卡，
  两边一旦冲突就是"主控在派一件已经被令停掉的事"。

它做三件：
  1. 扫 order-bus/receipts/*.json 里上次之后新增的令（按 mtime 与已见 marker）；
  2. 落 state/orders-new.json（机读）：新令清单 + 未 ack 的节点；
  3. 让 master_loop 一屏顶行显示"新令 N 条待落地"，并把它们当成最高优先决策项。

注意：这一站只读不写业务账本——派单仍由主控脉的既有权。

用法：python3 Tools/fleet/order_watch.py [--json]
Exit: 0 有新令或没有新令都算正常；rc=2 表示令总线目录缺失（结构问题）。
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
BUS = os.path.join(F, "order-bus", "receipts")
STATE = os.path.join(F, "state", "order-watch.json")
OUT = os.path.join(F, "state", "orders-new.json")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.isdir(BUS):
        print("[order-watch] FATAL: order-bus/receipts missing")
        return 2

    first_run = not os.path.exists(STATE)
    prev = jload(STATE, {}) or {}
    seen = set(prev.get("seen") or [])
    newest_ts = float(prev.get("newest_mtime") or 0)

    files = sorted(glob.glob(os.path.join(BUS, "OB-*.json")),
                   key=lambda p: os.path.getmtime(p))
    fresh = []
    for p in files:
        oid = os.path.basename(p)[:-5]
        if oid in seen:
            continue
        o = jload(p, {}) or {}
        if not o:
            continue
        acks = o.get("acks") or {}
        fresh.append({
            "id": oid,
            "ts": o.get("ts"),
            "text": (o.get("text") or "")[:300],
            "lanes": o.get("lanes") or [],
            "nodes": o.get("nodes") or [],
            "unacked": [n for n, v in acks.items() if str(v).lower() in ("no-ack", "", "none")],
        })
        newest_ts = max(newest_ts, os.path.getmtime(p))

    if first_run:
        # 首次运行只建基线：把存量令全部记为已见，避免把历史令报成"今天新增 N 条"。
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds"),
                       "seen": [os.path.basename(p)[:-5] for p in files],
                       "newest_mtime": newest_ts, "baseline": True}, f,
                      ensure_ascii=False, indent=1)
        print("[order-watch] baseline: %d existing order(s) recorded as seen" % len(files))
        return 0
    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "new_count": len(fresh),
           "unacked_total": sum(len(x["unacked"]) for x in fresh),
           "orders": fresh,
           "note": "新令=最高优先：主控必须当轮重排，冲突任务停飞并记被令覆盖"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"ts": out["ts"], "seen": sorted(seen | {x["id"] for x in fresh}),
                   "newest_mtime": newest_ts}, f, ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[order-watch] new=%d unacked=%d" % (len(fresh), out["unacked_total"]))
        for x in fresh[:5]:
            print("  + %s lanes=%s :: %s" % (x["id"], ",".join(x["lanes"]), x["text"][:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))