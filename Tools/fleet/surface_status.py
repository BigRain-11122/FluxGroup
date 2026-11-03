#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""surface_status.py - 全域优化面日报：哪个域还有几项未决，最该先看哪一条。

为什么（CEO 2026-11-03「你要考虑的比我全面和科学，不是我说哪里弄哪里」）：
  我连续三次只修被点名的那一处。根因不是理解错，是没有一张"面"的账。
  这张账= cph4/fleet/OPTIMIZATION-SURFACE-v1.json，本工具只做三件事：
  数（每域 done/partial/open）、挑（open 里按影响排序的头三条）、提示（缺测量项的域）。

用法：
  python3 Tools/fleet/surface_status.py            # 一屏
  python3 Tools/fleet/surface_status.py --json     # 机读（落 state/surface.json）
Exit: 0 总是（这是日报，不是闸；有未决项不等于故障）
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SURFACE = os.path.join(ROOT, "cph4", "fleet", "OPTIMIZATION-SURFACE-v1.json")
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "surface.json")

# 未决项的"影响权重"：先看会持续偷走算力/token 的，再看会造假的，再看要人拍板的
WEIGHT = {"me-size": 10, "ex-receipt-lag": 9, "st-cold": 7, "inf-remote": 8,
          "dis-bank": 8, "dis-no-receipt": 8, "sy-conflict": 6, "sk-slogan": 5,
          "inf-wired": 3, "inf-kvq": 3, "ex-bm-d": 4, "sp-license": 6,
          "me-dup": 4, "me-budget-gate": 6, "st-git-state": 5, "sy-pulse-race": 5,
          "sk-activation": 3, "st-artifact": 5, "ob-canary": 4}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    d = json.load(open(SURFACE, encoding="utf-8"))
    doms = d.get("domains") or {}
    rows, todo = [], []
    for key, dom in doms.items():
        items = dom.get("items") or []
        c = {"done": 0, "partial": 0, "open": 0}
        for it in items:
            st = it.get("status") or "open"
            c[st] = c.get(st, 0) + 1
            if st in ("open", "partial"):
                todo.append({"id": it.get("id"), "domain": key, "what": it.get("what"),
                             "now": it.get("now"), "trigger": it.get("trigger"),
                             "status": st, "w": WEIGHT.get(it.get("id"), 1)})
        rows.append({"domain": key, "label": dom.get("label"), "total": len(items), **c,
                     "pct": round(100.0 * c["done"] / len(items)) if items else 0})
    todo.sort(key=lambda x: -x["w"])
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "domains": rows,
           "todo": todo, "open_total": len([t for t in todo if t["status"] == "open"]),
           "partial_total": len([t for t in todo if t["status"] == "partial"])}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    print("SURFACE %d 域 / %d 项 · 完成 %d · 部分 %d · 未决 %d"
          % (len(rows), sum(r["total"] for r in rows),
             sum(r["done"] for r in rows), out["partial_total"], out["open_total"]))
    for r in sorted(rows, key=lambda x: x["pct"]):
        print("  %-10s %-12s 完成 %3d%%  (done %d / partial %d / open %d)"
              % (r["domain"], r["label"], r["pct"], r["done"], r.get("partial", 0), r.get("open", 0)))
    print("  先看这 %d 条：" % min(3, len(todo)))
    for t in todo[:3]:
        print("    - [%s] %s —— %s（触发：%s）"
              % (t["domain"], t["what"], t["now"], t.get("trigger") or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))