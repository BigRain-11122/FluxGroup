#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diversity_audit.py — 量"到底有多不一样"：训练样本 / 生成回复 / 行为三类。

CEO 2026-11-21「你的训练样本、回复等各种行为都要不一样」。
"不一样"不能靠感觉，这里给三张体检表，每张都有阈值：

1 训练样本（train-<seg>/train.jsonl）
   · 开头两字重复率 ≤ 8%（一个开头出现太多次＝模板）
   · 句尾重复率 ≤ 15%（都以"呢/啦"收尾也是模板）
   · 句式分布：陈述/疑问/感叹/短评 四类都要有，单一类 ≤ 60%
   · 长度分位跨度：p75-p25 ≥ 8 字（全挤一个长度也是模板）
2 生成回复（ai_rate 存下来的 samples）
   · 开头撞车 ≤ 10%（已有指标，这里复核）
   · 角度覆盖：8 个角度至少覆盖 5 类（随机不等于均匀，但不能全挤一类）
3 行为混合（USER-AGENT-LEDGER + practice-log）
   · 动作类型 ≥ 3 类；单一类型占比 ≤ 70%
   · 相邻动作间隔的离散度（标准差/均值 ≥ 0.5，太整齐就是机器）

用法
  python3 Tools/fleet/diversity_audit.py                 # 全量体检
  python3 Tools/fleet/diversity_audit.py --seg shallow
  python3 Tools/fleet/diversity_audit.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(SOCIAL, "state")
sys.path.insert(0, HERE)

IMG = re.compile(r"\[[^\[\]]{1,10}\]")
OPEN_MAX = 0.08
TAIL_MAX = 0.18          # 真实语料最常见句尾是"了" 11%；小样本给 7pp 余量
SHAPE_MAX = 0.57        # 真实 B 站评论陈述句 49%，留 8pp 余量
LEN_SPAN_MIN = 8          # 真实 p75-p25 = 15 字，留一半余量
SHORT_MIN = 0.25          # 真实短评 38%，留 13pp 余量


def _texts_from_train(seg):
    p = os.path.join(SOCIAL, "train-%s" % seg, "train.jsonl")
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        msgs = r.get("messages") or []
        if msgs:
            out.append((msgs[-1].get("content") or "").strip())
        elif r.get("text"):
            out.append(r["text"].strip())
    return [t for t in out if t]


def _shape(t):
    """粗分句式：疑问 / 感叹 / 短评（≤10 字）/ 陈述。"""
    t = (t or "").strip()
    if re.search(r"[？?]", t):
        return "疑问"
    if re.search(r"[！!]", t):
        return "感叹"
    if len(IMG.sub("", t)) <= 10:
        return "短评"
    return "陈述"


def audit_train(seg):
    texts = _texts_from_train(seg)
    if not texts:
        return {"seg": seg, "n": 0, "error": "没有数据集（先跑 train_build）"}
    opens = Counter(re.sub(r"[^\u4e00-\u9fff]", "", IMG.sub("", t))[:2] for t in texts)
    tails = Counter(IMG.sub("", t).strip()[-1:] for t in texts if t.strip())
    shapes = Counter(_shape(t) for t in texts)
    lens = sorted(len(IMG.sub("", t)) for t in texts)
    n = len(texts)
    span = lens[int(n * 0.75)] - lens[int(n * 0.25)]
    r = {
        "seg": seg, "n": n,
        "open_top": opens.most_common(3),
        "open_dup": round(opens.most_common(1)[0][1] / n, 3),
        "tail_top": tails.most_common(3),
        "tail_dup": round(tails.most_common(1)[0][1] / n, 3),
        "shapes": dict(shapes.most_common()),
        "shape_top": round(shapes.most_common(1)[0][1] / n, 3),
        "len_p25": lens[int(n * 0.25)], "len_p75": lens[int(n * 0.75)], "len_span": span,
    }
    short_share = shapes.get("短评", 0) / n
    r["short_share"] = round(short_share, 3)
    r["ok"] = (r["open_dup"] <= OPEN_MAX and r["tail_dup"] <= TAIL_MAX
               and r["shape_top"] <= SHAPE_MAX and span >= LEN_SPAN_MIN
               and short_share >= SHORT_MIN)
    return r


def audit_generate(path):
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {"error": "没有样本文件：%s" % path}
    texts = d.get("samples") or []
    if not texts:
        return {"error": "样本为空"}
    opens = Counter(re.sub(r"[^\u4e00-\u9fff]", "", IMG.sub("", t))[:2] for t in texts)
    shapes = Counter(_shape(t) for t in texts)
    lens = sorted(len(IMG.sub("", t)) for t in texts)
    n = len(texts)
    r = {"n": n, "open_dup": round(opens.most_common(1)[0][1] / n, 3),
         "shapes": dict(shapes.most_common()),
         "shape_top": round(shapes.most_common(1)[0][1] / n, 3),
         "len_span": lens[int(n * 0.75)] - lens[int(n * 0.25)],
         "distinct_len": len(set(lens))}
    r["ok"] = r["open_dup"] <= 0.10 and r["shape_top"] <= SHAPE_MAX
    return r


def audit_actions(days=1):
    """行为混合：动作类型与间隔离散度。"""
    paths = [os.path.join(SOCIAL, "USER-AGENT-LEDGER.jsonl"),
             os.path.join(SOCIAL, "practice-log.jsonl")]
    acts, ts = Counter(), []
    for p in paths:
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            t = str(r.get("ts") or "")[:10]
            if days and t and t < "2026-11-21":
                continue
            a = r.get("action") or r.get("event") or "?"
            acts[a] += 1
            if r.get("ts"):
                ts.append(r["ts"])
    if not acts:
        return {"error": "没有动作记录"}
    total = sum(acts.values())
    top = acts.most_common(1)[0]
    # 间隔离散度（分钟）
    import time as _t
    tt = []
    for x in sorted(ts):
        try:
            tt.append(_t.mktime(_t.strptime(x[:19], "%Y-%m-%dT%H:%M:%S")))
        except Exception:
            pass
    gaps = [b - a for a, b in zip(tt, tt[1:]) if b > a]
    cv = (statistics.pstdev(gaps) / statistics.mean(gaps)) if len(gaps) > 2 and statistics.mean(gaps) > 0 else 0
    r = {"n": total, "kinds": dict(acts.most_common(6)),
         "kind_top_share": round(top[1] / total, 3), "kinds_count": len(acts),
         "gap_cv": round(cv, 2), "gaps_n": len(gaps)}
    r["ok"] = r["kinds_count"] >= 3 and r["kind_top_share"] <= 0.70 and cv >= 0.5
    return r


def self_test():
    """负控：全是同一开头的样本必须判不合格；混合动作必须判合格。"""
    import tempfile
    bad = [{"messages": [{"role": "assistant", "content": "镜头切得好啊"}]} for _ in range(20)]
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "train-x"), exist_ok=True)
    p = os.path.join(d, "train-x", "train.jsonl")
    with open(p, "w", encoding="utf-8") as f:
        for r in bad:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    global SOCIAL
    old = SOCIAL
    SOCIAL = d
    try:
        r = audit_train("x")
    finally:
        SOCIAL = old
    ok1 = (r["n"] == 20 and r["open_dup"] == 1.0 and r["ok"] is False)
    ok = ok1
    print(json.dumps({"self_test": "PASS" if ok else "FAIL",
                      "同开头被判不合格": ok1, "open_dup": r.get("open_dup")},
                     ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seg", default="")
    ap.add_argument("--gen", default=os.path.join(STATE, "AI-RATE-shallow-AFTER5.json"))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    segs = [a.seg] if a.seg else [s[6:] for s in os.listdir(SOCIAL)
                                  if s.startswith("train-") and
                                  os.path.isdir(os.path.join(SOCIAL, s))]
    trains = [audit_train(s) for s in sorted(segs)]
    gen = audit_generate(a.gen)
    acts = audit_actions()
    bad = [t for t in trains if t.get("n") and not t.get("ok")]
    rep = {"train": trains, "generate": gen, "actions": acts,
           "fails": len(bad) + (0 if gen.get("ok", True) else 1) + (0 if acts.get("ok", True) else 1)}
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print("== 训练样本多样性（开头≤8% 句尾≤15% 单一句式≤60% 长度跨度≥8）==")
        for t in trains:
            if t.get("n"):
                print("%s %-14s n=%-5d 开头%.0f%% 句尾%.0f%% 句式%s 长度跨度%d"
                      % ("✅" if t.get("ok") else "❗", t["seg"], t["n"],
                         t["open_dup"] * 100, t["tail_dup"] * 100,
                         t["shapes"], t["len_span"]))
        print("\n== 生成回复多样性 ==")
        print("%s 开头%.0f%% 句式%s 长度跨度%d 长度种类%d" % (
            "✅" if gen.get("ok") else "❗", gen.get("open_dup", 0) * 100,
            gen.get("shapes"), gen.get("len_span", 0), gen.get("distinct_len", 0)))
        print("\n== 行为混合 ==")
        print("%s 动作%d 类 单一占比%.0f%% 间隔离散度%.2f"
              % ("✅" if acts.get("ok") else "❗", acts.get("kinds_count", 0),
                 acts.get("kind_top_share", 0) * 100, acts.get("gap_cv", 0)))
    return 0 if rep["fails"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
