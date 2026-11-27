#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""station_status.py - 五工位分片的只读汇总视图。

Why（2026-11-11）：队列分片后，任何"看一眼谁有活"的动作都不该再读那份 2500 行的
旧队列。本工具只读：本地分片 + origin 分片（git show，不动工作树），输出一屏。

用法：
    python3 Tools/fleet/station_status.py            # 五工位摘要
    python3 Tools/fleet/station_status.py --json     # 机器可读
    python3 Tools/fleet/station_status.py --remote   # 只读 origin 快照
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
PRODUCTS = os.path.join(ROOT, "cph4", "fleet", "PRODUCTS.json")
STATIONS = os.path.join(ROOT, "cph4", "fleet", "STATIONS.json")

LIVE = ("OPEN", "RUNNING", "BLOCKED", "UNVERIFIED")


def load_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}


def summary(remote=False):
    prod = {p["id"]: p for p in load_json(PRODUCTS).get("products", [])}
    st = {s["id"]: s for s in load_json(STATIONS).get("stations", [])}
    out = {}
    for sid in ss.STATIONS:
        rows = ss.read_remote_queue(sid) if remote else (ss.read_queue(sid) or [])
        if remote and not rows:
            rows = ss.read_queue(sid)
        live = [r for r in rows if str(r.get("state")).upper() in LIVE]
        by_state = collections.Counter(str(r.get("state")) for r in rows)
        prods = collections.Counter(r.get("product_id") or "-" for r in live)
        out[sid] = {
            "name": (st.get(sid) or {}).get("name", sid),
            "machine": (st.get(sid) or {}).get("machine", "?"),
            "status": (st.get(sid) or {}).get("status", "unknown"),
            "rows": len(rows),
            "live": len(live),
            "by_state": dict(by_state),
            "products": {k: v for k, v in prods.items() if k != "-"},
            "next": [{"id": r.get("id"), "state": r.get("state"),
                      "product": r.get("product_id")} for r in live[:5]],
        }
    return out, prod


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--remote", action="store_true")
    a = ap.parse_args(argv)
    data, prod = summary(remote=a.remote)
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return 0
    print("== 五工位 ==")
    for sid, d in data.items():
        print("%-9s %-8s %-20s rows=%-3d live=%-2d %s"
              % (sid, d["status"], d["machine"], d["rows"], d["live"], d["by_state"]))
        for n in d["next"]:
            p = prod.get(n["product"], {}).get("name", n["product"] or "-")
            print("    · %-42s %-9s %s" % (str(n["id"])[:42], n["state"], p))
    total_live = sum(d["live"] for d in data.values())
    print("== 合计可执行/待核 %d 张 ==" % total_live)
    return 0


if __name__ == "__main__":
    sys.exit(main())
