#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane_trust.py - 机器准入按"真回执"判，不按"心跳在线"判。

为什么（2026-11-03 实测）：四台机心跳全在线，但近 7 天回执是
  bm-m 206 / bm-a 62 / bm-c 10 / bm-b 3（bm-b 24 小时只 2 份）。
心跳新 ≠ 出东西。把活派给一台"在线但不产出"的机器，账面是 RUNNING，
实际是活被吃掉再被重排——这正是"队列在转但没有产出"的机制来源。

分级（只此一处定义）：
  production  近 7 天回执 >= 5        正常派单
  probe-only  近 7 天回执 1-4          只接探针卡（probe=True，短、必回执）
  silent      近 7 天 0 份且历史有记录  不派单，等它自己交一次回执再恢复
  unknown     历史零记录               同 silent（新机也算，先交回执）

用法：
  python3 Tools/fleet/lane_trust.py            # 打印分级
  python3 Tools/fleet/lane_trust.py --json
供代码调用：tier(node) -> (tier, stats, why)
"""
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
CACHE = os.path.join(ROOT, "cph4", "fleet", "state", "lane-trust.json")
TTL_S = 600

PROD_7D = 5

_cache = {"at": 0, "data": None}


def _scan():
    now = time.time()
    agg = {}
    for f in glob.glob(os.path.join(RECEIPTS, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        node = d.get("node")
        if not node:
            continue
        ts = str(d.get("ts") or "")
        try:
            age_d = (now - time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))) / 86400.0
        except Exception:
            age_d = None
        a = agg.setdefault(node, {"total": 0, "d1": 0, "d7": 0, "last": ts[:16]})
        a["total"] += 1
        if age_d is not None:
            if age_d <= 1:
                a["d1"] += 1
            if age_d <= 7:
                a["d7"] += 1
            if ts[:16] > a["last"]:
                a["last"] = ts[:16]
    out = {}
    for node, a in agg.items():
        if a["d7"] >= PROD_7D:
            tier, why = "production", "近7天 %d 份回执" % a["d7"]
        elif a["d7"] >= 1:
            tier, why = "probe-only", "近7天仅 %d 份回执（门槛 %d）" % (a["d7"], PROD_7D)
        else:
            tier, why = "silent", "近7天 0 份回执（最后 %s）" % (a["last"] or "无")
        out[node] = {"tier": tier, "why": why, **a}
    return out


def table(refresh=False):
    if not refresh and _cache["data"] is not None and time.time() - _cache["at"] < TTL_S:
        return _cache["data"]
    data = _scan()
    _cache.update({"at": time.time(), "data": data})
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "lanes": data},
                  open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    return data


def tier(node):
    d = table().get(node)
    if not d:
        return "unknown", {}, "无任何回执记录（新机先交一次回执）"
    return d["tier"], d, d["why"]


def main(argv):
    d = table(refresh=True)
    if "--json" in argv:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0
    print("LANE-TRUST 门槛=近 7 天 >= %d 份回执" % PROD_7D)
    for n in sorted(d):
        v = d[n]
        print("  %-6s %-12s 7d=%-3d 24h=%-3d total=%-4d %s"
              % (n, v["tier"], v["d7"], v["d1"], v["total"], v["why"]))
    missing = [n for n in ("bm-a", "bm-b", "bm-c", "bm-d", "bm-m") if n not in d]
    if missing:
        print("  无记录：%s（按 unknown 处理，不派生产卡）" % ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))