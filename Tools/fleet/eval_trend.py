#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eval_trend.py — 训练评测的趋势账（只报不改，不参与任何切换决策）。

为什么要有它：
SEGMENT-EVAL-HISTORY.jsonl 已经有 80+ 条记录，但没人读——于是"某个段上
adapter 比基座低 12 分"这种事实埋在 jsonl 里，看起来训练一直在跑就等于在变好。
本器把它摊开成：每段最近一次的 Δ、历史最好、以及是否持续退步。

口径（照实说，不做推断）：
  Δ = lora 均分 − base 均分（同一次评测内比较，所以不受基座缓存影响）
  base 侧标 cached=true 是正常的：基座没变，复用是对的；lora 侧一律现测。
  "持续退步" = 该段最近 ≥2 次评测的 Δ 都为负，且平均 ≤ -5。

用法：
  python3 Tools/fleet/eval_trend.py            # 每段最近一次 + 退步清单
  python3 Tools/fleet/eval_trend.py --json
  python3 Tools/fleet/eval_trend.py --self-test
退出码：0 无持续退步 / 1 有持续退步（只提示，不阻断任何流程）
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HIST = os.path.join(ROOT, "cph4", "fleet", "social", "train", "SEGMENT-EVAL-HISTORY.jsonl")

REGRESS_MIN_RUNS = 2      # 至少连续几次为负才算"持续"
REGRESS_MIN_DROP = 5.0    # 平均丢分阈值


def _mean(rows):
    if not isinstance(rows, list) or not rows:
        return None
    vals = [float(r.get("avg") or 0) for r in rows if isinstance(r, dict)]
    return st.mean(vals) if vals else None


def load(path=None):
    out = []
    try:
        for line in open(path or HIST, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return out


def analyze(rows):
    """返回 {seg: {latest_delta, n, deltas, streak_neg, avg_recent, regressing}}。"""
    per = {}
    for r in rows:
        b, lo = _mean(r.get("base")), _mean(r.get("lora"))
        if b is None or lo is None:
            continue
        seg = ""
        if isinstance(r.get("lora"), list) and r["lora"]:
            seg = r["lora"][0].get("seg") or ""
        seg = seg or "unknown"
        per.setdefault(seg, []).append({"ts": r.get("ts"), "delta": round(lo - b, 1),
                                        "base": round(b, 1), "lora": round(lo, 1)})
    out = {}
    for seg, items in per.items():
        items.sort(key=lambda x: str(x["ts"]))
        deltas = [x["delta"] for x in items]
        tail = deltas[-REGRESS_MIN_RUNS:] if len(deltas) >= REGRESS_MIN_RUNS else deltas
        streak_neg = len(tail) >= REGRESS_MIN_RUNS and all(d < 0 for d in tail)
        avg_recent = round(st.mean(tail), 1) if tail else None
        out[seg] = {"n": len(items), "latest_delta": deltas[-1], "avg_recent": avg_recent,
                    "best": max(deltas), "worst": min(deltas),
                    "regressing": bool(streak_neg and avg_recent is not None
                                       and avg_recent <= -REGRESS_MIN_DROP),
                    "last_ts": items[-1]["ts"]}
    return out


def report(as_json=False):
    per = analyze(load())
    if as_json:
        print(json.dumps(per, ensure_ascii=False, indent=1))
        return 0 if not any(v["regressing"] for v in per.values()) else 1
    if not per:
        print("还没有评测记录")
        return 0
    print("%-16s %6s %8s %8s %8s %s" % ("人群段", "次数", "最近Δ", "近均Δ", "最好Δ", "状态"))
    for seg in sorted(per, key=lambda s: per[s]["avg_recent"] or 0):
        v = per[seg]
        print("%-16s %6d %+8.1f %+8.1f %+8.1f %s"
              % (seg, v["n"], v["latest_delta"], v["avg_recent"] or 0, v["best"],
                 "退步" if v["regressing"] else ""))
    bad = [s for s, v in per.items() if v["regressing"]]
    if bad:
        print("\n⚠ 持续退步（近 %d 次均为负且均 Δ ≤ %.0f）：%s"
              % (REGRESS_MIN_RUNS, REGRESS_MIN_DROP, "、".join(bad)))
        print("  处置说明：本器只报不改。切换判据仍是 val_loss 最优，是否加质量闸是训练策略决定。")
        return 1
    print("\n没有持续退步的段")
    return 0


def self_test():
    """负控：持续退步必须被点名；单次波动不得误报；缺字段不得崩。"""
    cases = []
    # 造：A 段连续两次 -12/-13（应判退步）；B 段 +20/-1（不该判）；C 段 +5/+6（不算）
    def row(seg, base, lora, ts):
        return {"ts": ts, "base": [{"avg": base, "seg": seg}],
                "lora": [{"avg": lora, "seg": seg}], "samples": 10}
    rows = [
        row("A", 85.5, 73.0, "2026-11-23T17:15"),
        row("A", 85.5, 72.0, "2026-11-23T22:32"),
        row("B", 38.0, 58.0, "2026-11-23T19:53"),
        row("B", 56.5, 55.8, "2026-11-23T20:52"),
        row("C", 20.0, 25.0, "2026-11-23T21:00"),
        row("C", 20.0, 26.0, "2026-11-23T21:30"),
    ]
    per = analyze(rows)
    cases.append(("A 段连续负 → 判退步", per["A"]["regressing"] is True))
    cases.append(("B 段一正一负 → 不判退步", per["B"]["regressing"] is False))
    cases.append(("C 段全正 → 不判退步", per["C"]["regressing"] is False))
    cases.append(("Δ 计算正确（85.5→73.0 = -12.5）", per["A"]["latest_delta"] == -13.0 or
                  per["A"]["best"] == -12.5))
    # 缺 lora/base 的行必须被跳过而不是当成 0 分
    per2 = analyze([{"ts": "x", "base": [], "lora": []}])
    cases.append(("空评测行被跳过（不按 0 分算）", per2 == {}))
    # 只有一次负分不算"持续"
    per3 = analyze([row("D", 50.0, 40.0, "2026-11-23T10:00")])
    cases.append(("只有一次负分 → 不判持续退步", per3["D"]["regressing"] is False))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return report(a.json)


if __name__ == "__main__":
    sys.exit(main())
