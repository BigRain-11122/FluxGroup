#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cloud_budget.py - 云端算力的日预算闸（CEO 2026-11-05：按日预算放开，硬上限 ¥100/天）。

背景：2026-10-20 的 T0 令是"云道停用"。CEO 11-05 改为按日预算放开，因此云端调用
必须先问这一站，而不是每个脚本各自决定要不要花。

用法：
  python3 Tools/fleet/cloud_budget.py check                 # 今日余额（rc=0 可花，rc=1 超限）
  python3 Tools/fleet/cloud_budget.py spend --cny 3.5 --what "seedance 4 条 5s"
  python3 Tools/fleet/cloud_budget.py report                # 近 7 天明细

阈值唯一来源=cph4/fleet/AUTONOMY-CONFIG.json 的 cloud.daily_cny_cap。
账本=cph4/fleet/token-ledger/SPEND.jsonl（进 git，任何一笔都能追）。
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
CFG_PATH = os.path.join(F, "AUTONOMY-CONFIG.json")


def cfg():
    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def ledger_path():
    rel = (cfg().get("cloud") or {}).get("ledger") or "cph4/fleet/token-ledger/SPEND.jsonl"
    return os.path.join(ROOT, rel)


def rows():
    p = ledger_path()
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
            continue
    return out


def day_of(r):
    return str(r.get("ts") or "")[:10]


def spent_today():
    today = datetime.now().strftime("%Y-%m-%d")
    total = 0.0
    for r in rows():
        if day_of(r) == today:
            try:
                total += float(r.get("cny") or 0)
            except (TypeError, ValueError):
                pass
    return round(total, 2)


def cap():
    return float((cfg().get("cloud") or {}).get("daily_cny_cap") or 0)


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check")
    sp = sub.add_parser("spend")
    sp.add_argument("--cny", type=float, required=True)
    sp.add_argument("--what", default="")
    sp.add_argument("--credits", type=float, default=None)
    sp.add_argument("--node", default="bm-m")
    # 本地优先的凭证（CEO 2026-11-05「优先本地算力互相赋能，其次云端，有必要才用」）：
    # 上云必须先说明本地为什么不行，空口不许花钱。
    sp.add_argument("--local-checked", default="", help="本地已尝试/已排查的证据，如 squeeze.json 结论或排满的卡号")
    sp.add_argument("--why-not-local", default="", help="本地为什么做不了（能力缺失/排队成本）")
    sub.add_parser("report")
    a = ap.parse_args(argv or ["check"])

    c = cap()
    used = spent_today()

    if a.cmd == "spend":
        cny = float(a.cny)
        need_ev = bool((cfg().get("cloud") or {}).get("require_local_evidence"))
        if need_ev and not (a.local_checked and a.why_not_local):
            print(json.dumps({"allowed": False,
                              "why": "cloud is last-resort: pass --local-checked and --why-not-local",
                              "hint": "先看 cph4/fleet/state/squeeze.json 与 PRODUCTION-QUEUE.jsonl：本地有余量就先派本地"},
                             ensure_ascii=False))
            return 2
        if c > 0 and used + cny > c:
            print(json.dumps({"allowed": False, "why": "would exceed daily cap",
                              "spent_cny": used, "request_cny": cny, "cap_cny": c},
                             ensure_ascii=False))
            return 1
        p = ledger_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        rec = {"ts": datetime.now().isoformat(timespec="seconds"), "node": a.node,
               "cny": round(cny, 3), "credits": a.credits, "what": a.what,
               "local_checked": a.local_checked, "why_not_local": a.why_not_local}
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(json.dumps({"allowed": True, "recorded": rec,
                          "spent_cny": round(used + cny, 2), "cap_cny": c},
                         ensure_ascii=False))
        return 0

    if a.cmd == "report":
        since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        for r in rows():
            if day_of(r) >= since:
                print("%s %-8s %7.2f  %s" % (day_of(r), r.get("node") or "-",
                                             float(r.get("cny") or 0), r.get("what") or ""))
        print("今日 %.2f / %.2f CNY" % (used, c))
        return 0

    allowed = (c <= 0) or (used < c)
    # 本机队还有多少可派余量：给调用方一个"本地其实没满"的提示，不是自动放行。
    idle = None
    try:
        sq = json.load(open(os.path.join(F, "state", "squeeze.json"), encoding="utf-8"))
        idle = {"mean_cpu_pct": sq.get("mean_cpu_pct"), "local_gpu_pct": sq.get("local_gpu_pct"),
                "total_idle_slots": sum(int(n.get("idle_slots") or 0)
                                        for n in (sq.get("nodes") or []))}
    except Exception:
        idle = None
    print(json.dumps({"allowed": allowed, "spent_cny": used, "cap_cny": c,
                      "remaining_cny": round(max(0.0, c - used), 2),
                      "mode": (cfg().get("cloud") or {}).get("mode") or "last-resort",
                      "require_local_evidence": bool((cfg().get("cloud") or {}).get("require_local_evidence")),
                      "local_idle": idle,
                      "policy": "本地优先；有余量就派本地，云端只在本地做不了时用"},
                     ensure_ascii=False))
    return 0 if allowed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))