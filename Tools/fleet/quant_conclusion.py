#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quant_conclusion.py - 把回测输出压成一页"能对外说的话"。

为什么（2026-11-03）：策略线每晚跑体检，但没有一份结论能直接拿去报价/上架。
一份合格的策略结论必须四件齐全，缺一件就等于没有结论：
  样本区间 / 成本假设 / 失效条件 / 输入指纹
本工具只做格式与校验，不重算：拿回测 JSON（或 CSV 摘要）生成 md/json 双份。

用法：
  python quant_conclusion.py --in quant/bigmoney/results/etf_nobond_vt.json \
      --line bigmoney --out cph4/fleet/queue-receipts/quant-conclusion-20260101.md
Exit: 0 合格（四件齐），3 缺件（写出缺什么），1 输入读不了。
"""
import argparse
import hashlib
import json
import os
import sys
import time

KEYS_RANGE = ("sample_from", "sample_to", "start", "end", "date_range", "period")
KEYS_COST = ("cost", "fee", "slippage", "commission", "assumption")
KEYS_KILL = ("kill", "invalid", "fail_condition", "stop_rule")
KEYS_METRIC = ("annual", "cagr", "sharpe", "max_dd", "drawdown", "turnover", "winrate")


def jload(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def pick(obj, keys):
    for k in keys:
        if k in obj:
            return k, obj[k]
    for k, v in obj.items():
        lk = str(k).lower()
        for cand in keys:
            if cand in lk:
                return k, v
    return None, None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--line", default="bigmoney")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if not os.path.exists(a.src):
        print("[quant_conclusion] 输入不在盘：%s" % a.src)
        return 1
    try:
        obj = jload(a.src)
    except Exception as e:
        print("[quant_conclusion] 读不了：%s" % e)
        return 1
    flat = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            flat[str(k).lower()] = v
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    flat.setdefault(str(k2).lower(), v2)
    rk, rv = pick(flat, KEYS_RANGE)
    ck, cv = pick(flat, KEYS_COST)
    kk, kv = pick(flat, KEYS_KILL)
    metrics = sorted(k for k in flat if any(m in k for m in KEYS_METRIC))
    raw = open(a.src, "rb").read()
    fp = hashlib.sha256(raw).hexdigest()[:16]
    missing = [n for n, v in (("样本区间", rv), ("成本假设", cv), ("失效条件", kv)) if v in (None, "", [], {})]
    md = ["# 策略结论 %s" % time.strftime("%Y-%m-%d"), "",
          "- 线：%s" % a.line,
          "- 输入：%s（指纹 %s）" % (a.src, fp),
          "- 样本区间：%s" % (rv if rv is not None else "**缺**"),
          "- 成本假设：%s" % (cv if cv is not None else "**缺**"),
          "- 失效条件：%s" % (kv if kv is not None else "**缺**"),
          "- 指标：%s" % (", ".join("%s=%s" % (k, flat[k]) for k in metrics[:8]) or "**缺**"),
          "", "## 能不能对外说", "",
          "四件不齐不许报价；缺项：" + ("、".join(missing) if missing else "无（可对外）")]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    side = os.path.splitext(a.out)[0] + ".json"
    with open(side, "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "line": a.line, "input": a.src,
                   "input_sha16": fp, "sample": rv, "cost": cv, "kill": kv,
                   "metrics": {k: flat[k] for k in metrics[:12]}, "missing": missing},
                  f, ensure_ascii=False, indent=1)
    print("[quant_conclusion] %s 缺件=%s -> %s" % ("OK" if not missing else "INCOMPLETE",
                                                   ",".join(missing) or "无", a.out))
    return 0 if not missing else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))