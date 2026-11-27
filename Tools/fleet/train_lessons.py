#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_lessons.py — 从训练台账里提炼经验（不是写总结，是出可复算的断言）。

CEO 2026-11-23：「你边训练也要边总结经验」。
所以这里不产出"本次训练效果良好"这种话，只产出**能被台账推翻的断言**，每条带：
  rule（规则号）／claim（一句话结论）／n（样本）／stats（算出来的数）／evidence（run id）

硬纪律：
- 样本不足（n < MIN_N）一律写 INSUFFICIENT，**不下结论**（判词功率 n≥30 的同一条理）；
- 结论按 rule+claim 指纹去重，重复跑不会堆垃圾；
- 每条规则都必须能被合成数据推翻（见 --self-test 的负控）。

用法：
  train_lessons.py --summary        # 打印分析
  train_lessons.py --write          # 追加到 TRAIN-LESSONS.jsonl（幂等）
  train_lessons.py --self-test      # 负控：假数据下规则该红的红、该哑的哑
Exit: 0 正常；1 自检失败
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TRAIN = os.path.join(ROOT, "cph4", "fleet", "social", "train")
LEDGER = os.path.join(TRAIN, "TRAIN-LOOP-LEDGER.jsonl")
OUT = os.path.join(TRAIN, "TRAIN-LESSONS.jsonl")

MIN_N = 5          # 单条规则至少要几行样本才允许下结论


def load_rows(path=LEDGER):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _num(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _lesson(rule, claim, n, stats, runs, verdict="LESSON"):
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "rule": rule, "claim": claim,
            "n": n, "stats": stats, "evidence": runs[:5], "verdict": verdict}


def analyse(rows):
    """四条规则，逐条都返回 lesson（样本不足则 verdict=INSUFFICIENT）。"""
    out = []
    scored = [r for r in rows if r.get("verdict") in ("KEEP", "REJECT") and _num(r.get("val_min")) is not None]

    # R1：val_min 到底能不能区分"采用/拒绝"？
    keep_v = [_num(r["val_min"]) for r in scored if r["verdict"] == "KEEP"]
    rej_v = [_num(r["val_min"]) for r in scored if r["verdict"] == "REJECT"]
    if len(keep_v) >= MIN_N and len(rej_v) >= MIN_N:
        mk, mr = statistics.mean(keep_v), statistics.mean(rej_v)
        gap = abs(mk - mr)
        stats = {"mean_val_keep": round(mk, 3), "mean_val_reject": round(mr, 3), "gap": round(gap, 3)}
        if gap < 0.15:
            out.append(_lesson("R1-val-not-predictive",
                               "val_min 不区分采用/拒绝（均值差 %.3f<0.15）：它只反映拟合，选段不能拿它当判据" % gap,
                               len(keep_v) + len(rej_v), stats,
                               [r.get("run") for r in scored if r.get("verdict") == "KEEP"]))
        else:
            out.append(_lesson("R1-val-separates",
                               "val_min 与采用有区分（均值差 %.3f）：可作为辅助信号，但仍不能单用" % gap,
                               len(keep_v) + len(rej_v), stats, [r.get("run") for r in scored]))
    else:
        out.append(_lesson("R1-val-not-predictive", "样本不足，val 与采用的关系不下结论",
                           len(keep_v) + len(rej_v), {"keep_n": len(keep_v), "reject_n": len(rej_v)},
                           [], "INSUFFICIENT"))

    # R2：烘焙损耗（rows → built），选段该按哪个数
    ratios = []
    for r in rows:
        a, b = _num(r.get("rows"), 0), _num(r.get("built"), 0)
        if a and a > 0 and b and b > 0:
            ratios.append(b / a)
    if len(ratios) >= MIN_N:
        mean_ratio = statistics.mean(ratios)
        stats = {"mean_built_over_rows": round(mean_ratio, 3), "n": len(ratios),
                 "min": round(min(ratios), 3)}
        claim = ("烘焙后只剩 %.0f%%：选段要按 built 排，按 rows 排会高估可用语料" % (mean_ratio * 100)
                 if mean_ratio < 0.85 else
                 "烘焙损耗小（%.0f%% 保留），rows 与 built 可近似互换" % (mean_ratio * 100))
        out.append(_lesson("R2-bake-loss", claim, len(ratios), stats,
                           [r.get("run") for r in rows if r.get("built")]))
    else:
        out.append(_lesson("R2-bake-loss", "样本不足，烘焙损耗不下结论", len(ratios), {}, [], "INSUFFICIENT"))

    # R3：人味方向——整体是在拉高还是拉低
    hd = [_num(r.get("human_delta")) for r in scored if _num(r.get("human_delta")) is not None]
    if len(hd) >= MIN_N:
        neg = sum(1 for x in hd if x < 0) / len(hd)
        mean_hd = statistics.mean(hd)
        stats = {"neg_ratio": round(neg, 3), "mean_human_delta": round(mean_hd, 2), "n": len(hd)}
        if neg >= 0.7 and mean_hd <= -1:
            out.append(_lesson("R3-human-dropping",
                               "%.0f%% 的训练把人味分拉低（均值 %.2f）：AI 腔在回归，先补语料再训" % (neg * 100, mean_hd),
                               len(hd), stats, [r.get("run") for r in scored if (_num(r.get("human_delta")) or 0) < 0]))
        else:
            out.append(_lesson("R3-human-stable",
                               "人味没有系统性下滑（负向 %.0f%%，均值 %.2f）" % (neg * 100, mean_hd),
                               len(hd), stats, [r.get("run") for r in scored]))
    else:
        out.append(_lesson("R3-human-dropping", "样本不足，人味趋势不下结论", len(hd), {}, [], "INSUFFICIENT"))

    # R4：门槛与现实的距离（采用率 0 时，差多少）
    avgs = [(_num(r.get("lora_avg"), 0) - _num(r.get("base_avg"), 0)) for r in scored]
    avgs = [a for a in avgs if a is not None]
    if len(avgs) >= MIN_N:
        keep_n = sum(1 for r in scored if r["verdict"] == "KEEP")
        rate = keep_n / len(scored)
        best = max(avgs)
        stats = {"adopt_rate": round(rate, 3), "best_avg_delta": round(best, 1), "n": len(avgs)}
        if keep_n == 0 and best < 5.0:
            out.append(_lesson("R4-gate-far",
                               "采用率 0，历史最好也只 %.1f 分（门槛 5.0）：差 %.1f，先补语料或按证据改判据" % (best, 5.0 - best),
                               len(avgs), stats, [r.get("run") for r in scored]))
        else:
            out.append(_lesson("R4-gate-reachable",
                               "采用率 %.0f%%，最好差 %.1f 分（门槛 5.0）" % (rate * 100, best),
                               len(avgs), stats, [r.get("run") for r in scored]))
    else:
        out.append(_lesson("R4-gate-far", "样本不足，门槛距离不下结论", len(avgs), {}, [], "INSUFFICIENT"))
    return out


def fingerprint(l):
    return hashlib.sha1(("%s|%s" % (l["rule"], l["claim"])).encode("utf-8")).hexdigest()[:16]


def write_lessons(lessons, path=OUT):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    seen = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    seen.add(fingerprint(json.loads(line)))
                except Exception:
                    pass
    added = 0
    with open(path, "a", encoding="utf-8") as f:
        for l in lessons:
            fp = fingerprint(l)
            if fp in seen:
                continue
            seen.add(fp)
            l["fp"] = fp
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
            added += 1
    return added


def show(lessons):
    for l in lessons:
        tag = "结论" if l["verdict"] == "LESSON" else "空档"
        print("[%s] %-22s n=%-3d %s" % (tag, l["rule"], l["n"], l["claim"]))
        if l.get("stats"):
            print("        %s" % json.dumps(l["stats"], ensure_ascii=False))


def self_test():
    """负控：每条规则都要能被假数据推翻（该红必须红、该哑必须哑）。"""
    cases = []
    # 1) val 与采用强相关 → R1 不许报"不区分"
    rows = ([{"verdict": "KEEP", "val_min": 1.0, "rows": 100, "built": 95, "human_delta": 1,
              "base_avg": 50, "lora_avg": 60, "run": "k%d" % i} for i in range(6)] +
            [{"verdict": "REJECT", "val_min": 4.0, "rows": 100, "built": 95, "human_delta": 1,
              "base_avg": 50, "lora_avg": 49, "run": "r%d" % i} for i in range(6)])
    L = {l["rule"]: l for l in analyse(rows)}
    cases.append(("val 强相关时不许说'不区分'", L["R1-val-separates"]["verdict"] == "LESSON"))

    # 2) val 完全相同但结论不同 → R1 必须报"不区分"
    rows2 = ([{"verdict": "KEEP", "val_min": 3.0, "rows": 100, "built": 95, "human_delta": 0,
               "base_avg": 50, "lora_avg": 60} for _ in range(6)] +
             [{"verdict": "REJECT", "val_min": 3.0, "rows": 100, "built": 95, "human_delta": 0,
               "base_avg": 50, "lora_avg": 49} for _ in range(6)])
    L2 = {l["rule"]: l for l in analyse(rows2)}
    cases.append(("val 相同必须报'不区分'", L2["R1-val-not-predictive"]["verdict"] == "LESSON"))

    # 3) 人味全跌 → R3 必须报"在回归"
    rows3 = [{"verdict": "REJECT", "val_min": 3.0, "rows": 100, "built": 50,
              "human_delta": -2, "base_avg": 80, "lora_avg": 70} for _ in range(8)]
    L3 = {l["rule"]: l for l in analyse(rows3)}
    cases.append(("人味全跌必须报警", L3["R3-human-dropping"]["claim"].startswith("100%")))

    # 4) 烘焙只剩一半 → R2 必须说按 built 排
    cases.append(("烘焙损耗必须提示", "按 built" in L3["R2-bake-loss"]["claim"]))

    # 5) 空台账 → 全部 INSUFFICIENT，不下结论
    L5 = analyse([])
    cases.append(("空台账一律不下结论", all(l["verdict"] == "INSUFFICIENT" for l in L5)))

    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("  %s %s" % ("PASS" if ok else "FAIL", n))
    print("[self-test] %d/%d %s" % (len(cases) - len(bad), len(cases), "PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--ledger", default=LEDGER)
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rows = load_rows(a.ledger)
    lessons = analyse(rows)
    if a.summary or not a.write:
        print("台账 %s：%d 行（KEEP/REJECT %d 行）\n" % (
            os.path.relpath(a.ledger, ROOT), len(rows),
            sum(1 for r in rows if r.get("verdict") in ("KEEP", "REJECT"))))
        show(lessons)
    if a.write:
        n = write_lessons(lessons)
        print("\n新写入 %d 条 → %s（凭 fingerprint 去重）" % (n, os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
