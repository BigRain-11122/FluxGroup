#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seg_policy.py — 按人群段决定用哪条车道出稿（lora 还是基座）。

来由（2026-11-24 实测，不是推断）：
评测历史 82 条摊开后，7 个段里 3 个**持续退步**：
  shallow −17.9（12 次）｜craft_learner −12.5（9 次）｜feeler −7.8（10 次）
另外 4 个明显变好：music_seeker +25.4｜tech_nerd +13.6｜memer +7.1｜peer_pro +1.9
一段适配器全段通用，等于在这些退步的人群上把评论写得比基座还差。
所以按段选车道：退步段先走基座，改善段先走 lora。

三条保守纪律（防这个策略自己变成坏闸）：
  1. 样本 <3 次评测的段一律保持默认（lora 优先）——不拿一两次波动改产线。
  2. 只有"连续 ≥2 次为负且均 Δ ≤ -5"才判退步，与 eval_trend 同一判据，不另立标准。
  3. 基座车道失败时仍会回落 lora（lane 阶梯本来就有兜底），不会因此断产。

用法：
  python3 Tools/fleet/seg_policy.py --write    # 由评测历史生成策略文件
  python3 Tools/fleet/seg_policy.py --show
  python3 Tools/fleet/seg_policy.py --lanes craft_learner   # 打印该段的尝试顺序
  python3 Tools/fleet/seg_policy.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "cph4", "fleet", "social", "train", "SEG-POLICY.json")
DEFAULT_LANES = ["lora", "4b"]      # 现状：先 lora，失败退基座
FALLBACK_LANES = ["4b", "lora"]     # 退步段：先基座，失败退 lora
MIN_EVALS = 3                        # 少于此数不改行为


def compute(hist=None):
    """由评测记录算出每段该用哪条车道。返回 (policy_dict, meta)。"""
    sys.path.insert(0, HERE)
    import eval_trend
    rows = hist if hist is not None else eval_trend.load()
    per = eval_trend.analyze(rows)
    lanes = {}
    for seg, v in per.items():
        if v["n"] < MIN_EVALS:
            lanes[seg] = {"lanes": DEFAULT_LANES, "why": "评测仅 %d 次（<%d），保持默认" % (v["n"], MIN_EVALS)}
        elif v["regressing"]:
            lanes[seg] = {"lanes": FALLBACK_LANES,
                          "why": "持续退步：近次均 Δ %+.1f（%d 次评测）" % (v["avg_recent"], v["n"])}
        else:
            lanes[seg] = {"lanes": DEFAULT_LANES,
                          "why": "未判退步：近次均 Δ %+.1f（%d 次评测）" % (v["avg_recent"], v["n"])}
    return lanes, {"n_segs": len(per), "min_evals": MIN_EVALS}


def lanes_for(seg, policy=None):
    """生产侧入口：给段名，返回尝试顺序。未知名段一律默认顺序（不猜）。"""
    policy = policy if policy is not None else load()
    item = (policy.get("segments") or {}).get(seg or "")
    return list(item["lanes"]) if item else list(DEFAULT_LANES)


def load():
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"segments": {}}


def write():
    lanes, meta = compute()
    doc = {"version": "SEG-POLICY-v1", "generated_by": "Tools/fleet/seg_policy.py",
           "rule": "退步段先走基座；样本<%d 不改行为；连续≥2次为负且均Δ≤-5 才算退步" % MIN_EVALS,
           "segments": lanes}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("已写 %s（%d 段，其中 %d 段改走基座优先）"
          % (os.path.relpath(OUT, ROOT), meta["n_segs"],
             sum(1 for v in lanes.values() if v["lanes"] == FALLBACK_LANES)))
    return 0


def show():
    d = load()
    segs = d.get("segments") or {}
    if not segs:
        print("还没有策略文件，先跑 --write")
        return 0
    for seg in sorted(segs):
        v = segs[seg]
        print("%-16s → %-14s %s" % (seg, ">".join(v["lanes"]), v["why"]))
    return 0


def self_test():
    """负控：退步段必须改道；样本不足必须不改；改善段必须保持；空历史不许崩。"""
    cases = []
    def row(seg, base, lora, ts):
        return {"ts": ts, "base": [{"avg": base, "seg": seg}],
                "lora": [{"avg": lora, "seg": seg}], "samples": 10}
    hist = [
        row("bad", 85, 73, "2026-11-23T10:00"),
        row("bad", 85, 72, "2026-11-23T11:00"),
        row("bad", 85, 71, "2026-11-23T12:00"),
        row("good", 38, 58, "2026-11-23T10:00"),
        row("good", 38, 60, "2026-11-23T11:00"),
        row("good", 38, 62, "2026-11-23T12:00"),
        row("thin", 50, 40, "2026-11-23T10:00"),
        row("thin", 50, 41, "2026-11-23T11:00"),
    ]
    lanes, _ = compute(hist)
    cases.append(("退步段 → 基座优先", lanes["bad"]["lanes"] == FALLBACK_LANES))
    cases.append(("改善段 → lora 优先", lanes["good"]["lanes"] == DEFAULT_LANES))
    cases.append(("只有 2 次评测的段 → 保持默认", lanes["thin"]["lanes"] == DEFAULT_LANES))
    # 未知段不猜
    cases.append(("未知名段 → 默认顺序", lanes_for("nope", {"segments": lanes}) == DEFAULT_LANES))
    # 空历史不许崩，且不得产出弃用策略
    lanes2, _ = compute([])
    cases.append(("空历史 → 空策略、不报错", lanes2 == {}))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--lanes", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.lanes:
        print(">".join(lanes_for(a.lanes)))
        return 0
    if a.write:
        return write()
    return show()


if __name__ == "__main__":
    sys.exit(main())
