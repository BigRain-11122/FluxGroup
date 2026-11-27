#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quant_positions_bridge.py - 把回测 JSON 的 live_picks 补成下游可消费的 positions。

为什么（2026-11-04 R6 事件班）：
  `Tools/fleet/quant_signal.py` 的输入契约要求顶层 positions/holdings/weights，
  而 `quant/bigmoney/scripts/etf_nobond_vt.py` 只输出 live_picks（symbol/score/class），
  于是"唯一可卖的产物"（下月持仓 CSV）永远 BLOCKED，回执 rc=3 写明缺持仓字段。

为什么不直接改回测脚本：`quant/bigmoney` 是 BigMoney 独立仓（双公司各自治理，
互不写对方仓库）。所以在本仓做桥，不动对方源码。

诚实边界（不许造假活）：
  * 权重不是拍脑袋——`etf_robust_pf.open_to_open_equity` 的**发布默认**就是
    "plain equal weighting of the selected names (the published 1/n_hold)"，
    选择规则也是 plain top-n。本桥只是把这条已有规则显式化。
  * 原回测 JSON 原样保留，不覆盖；补出的文件单独落 queue-receipts，带 derivation 字段。
  * 波动目标叠加（vol_target）在执行侧按当期 book vol 缩放，不改相对权重；
    本文件输出的是叠加前的账本，CSV 的 factor_note 会写明这一点。

用法：
  python Tools/fleet/quant_positions_bridge.py --in quant/bigmoney/results/etf_nobond_vt.json \
      --out cph4/fleet/queue-receipts/etf_nobond_vt_with_positions.json
"""
import argparse
import json
import os
import sys
import time


def enrich(src):
    d = json.load(open(src, encoding="utf-8"))
    # 已有持仓字段 = 生产者自己交付了，原样放行，绝不改写。
    for k in ("positions", "holdings", "weights"):
        if isinstance(d.get(k), list) and d.get(k):
            return d, "passthrough:" + k

    lp = d.get("live_picks") or {}
    picks = lp.get("picks") or []
    if not picks:
        return None, "no-live-picks"

    n = len(picks)
    w = round(1.0 / n, 4)
    d["positions"] = [
        {"code": p.get("symbol") or p.get("code") or "",
         "weight": w,
         "factors": {"score": p.get("score"), "class": p.get("class")}}
        for p in picks
    ]
    d["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    d["derivation"] = {
        "bridge": "Tools/fleet/quant_positions_bridge.py",
        "reason": "producer emits live_picks only; quant_signal needs positions",
        "weight_rule": "equal weight 1/n_hold (the published default of "
                       "etf_robust_pf.open_to_open_equity, not a new policy)",
        "selection_rule": "plain top-n by score (same published default)",
        "sizing": "vol_target overlay is applied at execution; weights here are the "
                  "pre-overlay book and relative weights are unaffected",
        "as_of": lp.get("as_of"),
        "source": src,
    }
    return d, "bridged:%d" % n


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if not os.path.exists(a.inp):
        print(json.dumps({"verdict": "BLOCKED", "reason": "input missing"}, ensure_ascii=False))
        return 3
    d, how = enrich(a.inp)
    if d is None:
        print(json.dumps({"verdict": "BLOCKED", "reason": how}, ensure_ascii=False))
        return 3
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(d, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": "OK", "how": how, "out": a.out,
                      "positions": len(d.get("positions") or [])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))