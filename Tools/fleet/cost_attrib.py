#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cost_attrib.py — 按线/席位归集机器时间成本，出"最贵 TOP5"。

为什么要有它（`CAPABILITY-DIMENSIONS-v1.md` 落地计划第 4 项）：
本地机时看着"免费"，于是重活无成本地堆着跑；计价才会收敛。

数据源（都是盘上事实，不估）：
  · `cph4/fleet/agent-runs/<date>.jsonl` 的 `ms` → 席位模型调用耗时
  · `cph4/fleet/queue-receipts/*.json` 的 `seconds` → 卡执行耗时（按 node 归集）
计价参数取 `SERVICE-LEVEL-v1.json` 的 `cost.local_cny_per_min`（当前 0.02 元/分），
本器不自己定价。

诚实边界：
  · 没有 `seconds`/`ms` 的记录不计入（不按时长猜）；
  · 只算"机器时间"，不含云端 token 费用（云端账还没接，明说而不是填 0）；
  · 窗口默认 7 天，与 SLO 同窗，避免两套口径。

用法：
  python3 Tools/fleet/cost_attrib.py              # 出表
  python3 Tools/fleet/cost_attrib.py --days 30
  python3 Tools/fleet/cost_attrib.py --self-test
退出码：0 正常 / 2 无数据 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
SPEC = os.path.join(FLEET, "SERVICE-LEVEL-v1.json")
RUNS = os.path.join(FLEET, "agent-runs")
RECEIPTS = os.path.join(FLEET, "queue-receipts")


def _j(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:                                   # noqa: BLE001
        return d


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def price_per_min(spec=None):
    spec = spec or _j(SPEC, {}) or {}
    return float((spec.get("cost") or {}).get("local_cny_per_min") or 0.02)


def _in_window(ts, days):
    try:
        return datetime.fromisoformat(str(ts)[:19]) >= datetime.now() - timedelta(days=days)
    except ValueError:
        return True


def collect(days=7, runs_dir=None, receipts_dir=None):
    """返回 (by_key, totals)。key = ("seat"|"node", 名称)。"""
    runs_dir = runs_dir or RUNS
    receipts_dir = receipts_dir or RECEIPTS
    sec = {}
    n_rec = 0

    if os.path.isdir(runs_dir):
        for fn in sorted(os.listdir(runs_dir)):
            if not fn.endswith(".jsonl"):
                continue
            for r in _rows(os.path.join(runs_dir, fn)):
                if not _in_window(r.get("ts"), days):
                    continue
                ms = r.get("ms")
                if not isinstance(ms, (int, float)) or ms <= 0:
                    continue                    # 没有时长的不计时
                k = ("seat", r.get("seat") or "?")
                sec[k] = sec.get(k, 0.0) + ms / 1000.0
                n_rec += 1

    if os.path.isdir(receipts_dir):
        for fn in sorted(os.listdir(receipts_dir)):
            if not fn.endswith(".json"):
                continue
            d = _j(os.path.join(receipts_dir, fn), {}) or {}
            if not isinstance(d, dict):
                continue        # 实测：回执目录里混着 list 形状的 JSON，直接 .get 会崩
            s = d.get("seconds")
            if not isinstance(s, (int, float)) or s <= 0:
                continue
            if not _in_window(d.get("ts"), days):
                continue
            k = ("node", d.get("node") or "?")
            sec[k] = sec.get(k, 0.0) + float(s)
            n_rec += 1

    return sec, {"records": n_rec, "total_seconds": round(sum(sec.values()), 1)}


def report(days=7):
    spec = _j(SPEC, {}) or {}
    rate = price_per_min(spec)
    sec, meta = collect(days)
    rows = []
    for (kind, name), s in sec.items():
        rows.append({"kind": kind, "name": name, "minutes": round(s / 60.0, 1),
                     "cny": round(s / 60.0 * rate, 3)})
    rows.sort(key=lambda x: -x["cny"])
    return {"ts": datetime.now().isoformat(timespec="seconds"), "days": days,
            "rate_cny_per_min": rate, "meta": meta,
            "total_cny": round(sum(x["cny"] for x in rows), 3),
            "top": rows[:5], "all": rows,
            "note": "只算机器时间；云端 token 费用尚未接入，未计入。"}


def render(r):
    L = ["# 成本归集（机器时间）", "",
         "> 由 `Tools/fleet/cost_attrib.py` 生成；单价取 `SERVICE-LEVEL-v1.json` 的 "
         "`cost.local_cny_per_min` = %s 元/分。" % r["rate_cny_per_min"],
         "> " + r["note"], "",
         "- 时间：%s｜窗口：%d 天｜计入记录：%d 条｜合计 %s 元"
         % (r["ts"], r["days"], r["meta"]["records"], r["total_cny"]), ""]
    if not r["top"]:
        L.append("**没有可计时的记录**（不是零成本，是没有时长的数据）。")
        return "\n".join(L)
    L += ["## 最贵 TOP5", "", "| # | 类型 | 名称 | 分钟 | 元 |", "|---|---|---|---|---|"]
    for i, x in enumerate(r["top"], 1):
        L.append("| %d | %s | %s | %s | %s |" % (i, x["kind"], x["name"], x["minutes"], x["cny"]))
    L += ["", "## 全部", "", "| 类型 | 名称 | 分钟 | 元 |", "|---|---|---|---|"]
    for x in r["all"]:
        L.append("| %s | %s | %s | %s |" % (x["kind"], x["name"], x["minutes"], x["cny"]))
    return "\n".join(L)


def self_test():
    import shutil
    import tempfile
    cases = []
    d = tempfile.mkdtemp(prefix="cost-")
    try:
        runs = os.path.join(d, "runs")
        rc = os.path.join(d, "rc")
        os.makedirs(runs)
        os.makedirs(rc)
        now = datetime.now().isoformat(timespec="seconds")
        old = "2020-01-01T00:00:00"
        with open(os.path.join(runs, "x.jsonl"), "w") as f:
            f.write(json.dumps({"seat": "S1", "ms": 60000, "ts": now}) + "\n")
            f.write(json.dumps({"seat": "S1", "ms": 60000, "ts": now}) + "\n")
            f.write(json.dumps({"seat": "S2", "ms": 30000, "ts": now}) + "\n")
            f.write(json.dumps({"seat": "S3", "ms": 999000, "ts": old}) + "\n")  # 窗口外
            f.write(json.dumps({"seat": "S4", "ts": now}) + "\n")                 # 无 ms
        json.dump({"node": "n1", "seconds": 120, "ts": now},
                  open(os.path.join(rc, "a.json"), "w"))
        json.dump({"node": "n2", "ts": now}, open(os.path.join(rc, "b.json"), "w"))  # 无 seconds
        json.dump([{"node": "n3", "seconds": 999}], open(os.path.join(rc, "c.json"), "w"))  # list 形状

        spec = {"cost": {"local_cny_per_min": 0.5}}
        rate = price_per_min(spec)
        cases.append(("单价取配置", rate == 0.5))
        sec, meta = collect(7, runs, rc)
        cases.append(("S1 累计 120 秒", sec.get(("seat", "S1")) == 120.0))
        cases.append(("S2 30 秒", sec.get(("seat", "S2")) == 30.0))
        cases.append(("负控[窗口外] 不计入", ("seat", "S3") not in sec))
        cases.append(("负控[无 ms] 不计入", ("seat", "S4") not in sec))
        cases.append(("回执按 node 归集 120 秒", sec.get(("node", "n1")) == 120.0))
        cases.append(("负控[无 seconds] 不计入", ("node", "n2") not in sec))
        cases.append(("负控[list 形状回执] 不崩且不计入", ("node", "n3") not in sec))
        cases.append(("计入记录数=4（2+1+1）", meta["records"] == 4))

        # 换窗口：把 days 设成 0 天，全部过期 → 空
        sec0, meta0 = collect(0, runs, rc)
        cases.append(("负控[窗口 0 天] 无记录", meta0["records"] == 0))
    finally:
        shutil.rmtree(d, ignore_errors=True)

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    r = report(a.days)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(render(r))
    return 0 if r["top"] else 2


if __name__ == "__main__":
    sys.exit(main())
