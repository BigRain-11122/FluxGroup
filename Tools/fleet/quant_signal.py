#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quant_signal.py - 把回测结果变成"下个月买什么"的清单（唯一可卖的产物）。

为什么（2026-11-03 梳理）：客户买的不是回测曲线，是下月持仓；而这条线此前从未产出过
任何一份信号清单，所以"能不能卖"永远无法回答。本工具只做一件事：
从回测 JSON 里取出当期持仓，写成带指纹的 CSV；取不到就写 BLOCKED 并写明缺哪个字段
（rc=3），不许编一份看起来像信号的清单。

输入契约（回测脚本必须给）：results JSON 里含下列之一——
  positions / holdings / weights: [{"code": "510300", "weight": 0.2, "factors": {...}}]
再加上（有就写进指纹）：generated_at / params / universe

用法：
  python3 Tools/fleet/quant_signal.py --in quant/bigmoney/results/etf_nobond_vt.json \
      --out cph4/fleet/queue-receipts/quant-signal-20261103.csv
Exit: 0 = 有持仓或明确空仓（都算成功）；3 = 缺输入/缺字段（BLOCKED，不算失败）
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time


def sha_of(obj):
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def find_positions(d):
    for k in ("positions", "holdings", "weights", "current"):
        v = d.get(k)
        if isinstance(v, list) and (v or k in ("positions", "holdings", "weights")):
            return k, v
    # 兼容 {code: weight} 映射
    for k in ("positions", "holdings", "weights"):
        v = d.get(k)
        if isinstance(v, dict):
            return k, [{"code": c, "weight": w} for c, w in v.items()]
    return None, None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    month = time.strftime("%Y-%m")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    def blocked(why):
        # 拦截回执不能写到交付物路径上（2026-11-03）：这份 CSV 是卖给客户的"下月持仓"，
        # 写成 BLOCKED 既会被收口逻辑当成"产物已在盘"，也会被误发出去。
        # 改道 <名>-blocked-<日期>.csv，并保证 --out 一定不被创建。
        d, b = os.path.split(a.out)
        stem, ext = os.path.splitext(b)
        bpath = os.path.join(d, "%s-blocked-%s%s" % (stem, time.strftime("%Y%m%d"), ext or ".csv"))
        with open(bpath, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["status", "reason", "generated_at", "month"])
            w.writerow(["BLOCKED", why, ts, month])
        print(json.dumps({"verdict": "BLOCKED", "reason": why, "out": bpath,
                          "receipt_is_not_deliverable": True}, ensure_ascii=False))
        return 3

    if not os.path.exists(a.inp):
        return blocked("输入不存在：%s（回测段没跑或路径不对）" % a.inp)
    try:
        d = json.load(open(a.inp, encoding="utf-8"))
    except Exception as e:
        return blocked("输入不是合法 JSON：%s" % str(e)[:60])

    key, rows = find_positions(d)
    if key is None:
        return blocked("缺持仓字段：需要 positions/holdings/weights（回测脚本要输出当期持仓）")

    # 指纹=输入关键参数 + 持仓，任何人可据此复算
    fp = sha_of({k: d.get(k) for k in ("params", "universe", "generated_at") if k in d}
                or {"positions": rows})
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "weight", "factor_note", "month", "generated_at", "input_fp", "source_key"])
        if not rows:
            w.writerow(["", "0", "空仓（策略当期全防御）", month, ts, fp, key])
        for r in rows:
            code = r.get("code") or r.get("symbol") or r.get("etf") or ""
            wt = r.get("weight")
            fac = r.get("factors") if isinstance(r.get("factors"), dict) else None
            note = ",".join("%s=%s" % (k, round(v, 3) if isinstance(v, (int, float)) else v)
                            for k, v in (fac or {}).items())[:200]
            w.writerow([code, wt, note, month, ts, fp, key])
    print(json.dumps({"verdict": "OK", "positions": len(rows), "empty": not rows,
                      "input_fp": fp, "out": a.out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))