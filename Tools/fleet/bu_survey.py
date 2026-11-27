#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bu_survey.py - one machine-readable verdict per business line.

Why (2026-11-03, CEO 「其他子公司和业务挨个梳理」): every line looked alive because
the books are full of *self-check* cards. Fifteen lines, and only one had a real
product today; four ACTIVE lines each had exactly one entry - "线级体检与缺口清单".
Counting those as output is how an idle fleet reports green.

So the survey answers four questions per line, from disk facts only:
  1 供给  does it have a process table (line_plan can emit cards) / a next-step?
  2 产物  最近 DONE 是真产物还是自检卡（按卡 id/标题分类，不靠人声明）
  3 状态  registry status + 最近产出年龄 vs 该线阈值
  4 判词  PRODUCTIVE / SELF-CHECK-ONLY / NO-SUPPLY / STALE / PARKED / OFFBOX

Usage: python3 Tools/fleet/bu_survey.py [--json] [--out PATH]
Exit: 0 normal; 1 registry unreadable.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
REGISTRY = os.path.join(FLEET, "LINE-REGISTRY.json")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
NEXT = os.path.join(FLEET, "LINE-NEXT-STEPS.json")
TABLES = os.path.join(FLEET, "ri", "*", "lines", "*.json")
DEFAULT_OUT = os.path.join(FLEET, "BU-SURVEY.json")

# 表名 -> 线 id（表按业务短名建，registry 用全名）
ALIAS = {"asset": "asset-lib", "mv": "bigstream-mv", "drama": "bigstream-drama",
         "duanju": "bigstream-duanju"}

# 自检卡的标志：这些词出现在 id/标题里就说明"这条线在体检自己"，不是产物。
SELFCHECK_WORDS = ("triage", "体检", "扫描", "证据目录", "缺口清单", "盘点", "判定",
                   "plan-", "r-plan", "survey", "index", "library-check", "env-check",
                   "probe", "accept", "gate", "audit")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8-sig"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def is_selfcheck(card):
    hay = ("%s %s" % (card.get("id") or "", card.get("title") or "")).lower()
    return any(w.lower() in hay for w in SELFCHECK_WORDS)


def age_h(ts):
    try:
        return round((datetime.now() - datetime.fromisoformat(str(ts))).total_seconds() / 3600.0, 1)
    except Exception:
        return None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args(argv)

    reg = jload(REGISTRY)
    if not reg:
        print("LINE-REGISTRY.json 读不了：%s" % REGISTRY, file=sys.stderr)
        return 1
    lines = reg.get("lines") or []
    tables = {}
    import glob
    for p in glob.glob(TABLES):
        tables[ALIAS.get(os.path.basename(p)[:-5], os.path.basename(p)[:-5])] = \
            os.path.relpath(p, ROOT)
    nxt = (jload(NEXT, {}) or {}).get("lines") or {}
    q = rows(QUEUE)

    out_lines = []
    for ln in lines:
        lid = ln.get("id")
        mine = [c for c in q if c.get("line") == lid]
        done = [c for c in mine if c.get("state") == "DONE"]
        real = [c for c in done if not is_selfcheck(c)]
        free = sorted([(c.get("finished_at"), c) for c in done if c.get("finished_at")])
        last_done_h = age_h(free[-1][0]) if free else None
        last_real_h = None
        realf = [c for c in done if not is_selfcheck(c) and c.get("finished_at")]
        realf.sort(key=lambda c: c["finished_at"])
        if realf:
            last_real_h = age_h(realf[-1]["finished_at"])
        thr = ln.get("stale_after_h", reg.get("default_stale_after_h", 48))
        status = str(ln.get("status") or "").upper()

        if status in ("PARKED", "PAUSED", "DORMANT"):
            verdict = "OFF-DUTY"
        elif lid == "fleet-ops":
            # 平台线自己就是供给层（派单/收口/体检工具），没有"工序表"是正常的。
            verdict = "PLATFORM"
        elif lid not in tables and lid not in nxt:
            verdict = "NO-SUPPLY"           # 既无工序表也无下一步声明：只能收自检卡
        elif last_real_h is None or last_real_h > thr:
            verdict = "SELF-CHECK-ONLY" if real == [] else "STALE"
        else:
            verdict = "PRODUCTIVE"

        out_lines.append({
            "line": lid, "name": ln.get("name"), "org": ln.get("org"),
            "priority": ln.get("priority"), "status": status,
            "supply": {"process_table": tables.get(lid), "next_step": bool(lid in nxt),
                       "can_emit_cards": bool(lid in tables and status == "ACTIVE")},
            "cards": {"total": len(mine), "done": len(done),
                      "real_product": len(real), "selfcheck": len(done) - len(real),
                      "open": len([c for c in mine if c.get("state") == "OPEN"]),
                      "failed": len([c for c in mine if c.get("state") == "FAILED"])},
            "last_done_h": last_done_h, "last_real_product_h": last_real_h,
            "stale_after_h": thr,
            "verdict": verdict,
            "note": ln.get("pause_reason") or "",
        })

    order = {"PRODUCTIVE": 0, "STALE": 1, "SELF-CHECK-ONLY": 2, "NO-SUPPLY": 3,
             "PLATFORM": 4, "OFF-DUTY": 5}
    out_lines.sort(key=lambda r: (order.get(r["verdict"], 9),
                                 0 if r["priority"] == "P0" else 1))

    counted = {
        "lines": len(out_lines),
        "with_process_table": len([r for r in out_lines if r["supply"]["process_table"]]),
        "with_next_step": len([r for r in out_lines if r["supply"]["next_step"]]),
        "productive": len([r for r in out_lines if r["verdict"] == "PRODUCTIVE"]),
        "selfcheck_only": len([r for r in out_lines if r["verdict"] == "SELF-CHECK-ONLY"]),
        "no_supply": len([r for r in out_lines if r["verdict"] == "NO-SUPPLY"]),
        "off_duty": len([r for r in out_lines if r["verdict"] == "OFF-DUTY"]),
    }
    res = {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "counted": counted,
           "lines": out_lines}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0

    print("%-22s %-9s %-4s %-15s %-6s %-6s %s" %
          ("line", "status", "优先", "判词", "真产物", "自检", "最后真产物"))
    for r in out_lines:
        print("  %-20s %-9s %-4s %-15s %-6d %-6d %s" % (
            r["line"][:20], r["status"], r["priority"] or "-", r["verdict"],
            r["cards"]["real_product"], r["cards"]["selfcheck"],
            ("%.1fh" % r["last_real_product_h"]) if r["last_real_product_h"] is not None else "—"))
    print("合计：%d 条线 / 有工序表 %d / 有下一步 %d / 真产出 %d / 只剩自检 %d / 无供给 %d / 停线 %d"
          % (counted["lines"], counted["with_process_table"], counted["with_next_step"],
             counted["productive"], counted["selfcheck_only"], counted["no_supply"],
             counted["off_duty"]))
    print("-> %s" % os.path.relpath(a.out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))