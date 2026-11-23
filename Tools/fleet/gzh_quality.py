#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_quality.py — 判断"像不像真正的汽车自媒体团队出品"。

核心判断（本文件存在的理由）：
  单篇像可以模仿（换几个词就像）；**一批稿的分布像，才说明学到了团队工艺**。
  所以判据不是"这篇好不好"，而是"我们 30 篇的形态分布，与真稿 30 篇差多少"。

六个可算维度：
  1 标题长度中位      2 标题含数字率      3 标题问句率
  4 开篇首句长度中位  5 正文小标题密度    6 段落长度中位
另加两道独立闸：AI 腔命中（客服/公文/空承诺）与 与真稿的重合度（防洗稿）。

只用规则，不调模型——判据必须可复算，且能在没有语料时用构造样本自检。
用法：
  python3 Tools/fleet/gzh_quality.py --ours ours.jsonl --ref ref.jsonl
  python3 Tools/fleet/gzh_quality.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")

NUM = re.compile(r"\d")
Q = re.compile(r"[？?]|吗|到底|是不是|能不能|该不该|为何|为什么|怎么")
# AI 腔：命中即扣，不解释（2026-11-11 4B 实测的四类句式）
AI_PAT = [
    r"作为(一个|一名)?(AI|人工智能|语言模型)",
    r"首先[，,].{0,30}其次[，,]",
    r"总而言之|综上所述",
    r"希望对(你|您)有帮助|如需(进一步|更多)",
    r"值得注意的(是|一点)",
    r"在这个(信息爆炸|快节奏)的时代",
    r"不难(发现|看出)|显而易见",
    r"让我们一起|下面(我们)?将(介绍|探讨)",
]


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


def _med(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None


def _pct(xs, fn):
    xs = list(xs)
    return round(100.0 * sum(1 for x in xs if fn(x)) / len(xs), 1) if xs else None


def profile(arts):
    """把一批稿压成一个"形态指纹"。字段都可由原文直接数出来。"""
    ts = [(a.get("title") or "") for a in arts]
    leads = [(a.get("lead") or "").split("\n")[0] for a in arts]
    bodies = [(a.get("text") or "") for a in arts]
    paras = []
    for b in bodies:
        ps = [x for x in re.split(r"\n+", b) if x.strip()]
        if ps:
            paras.append(_med([len(x) for x in ps]))
    heads = [len(a.get("heads") or []) for a in arts]
    return {
        "n": len(arts),
        "title_len_med": _med([len(t) for t in ts]),
        "title_num_pct": _pct(ts, lambda t: bool(NUM.search(t))),
        "title_q_pct": _pct(ts, lambda t: bool(Q.search(t))),
        "lead_len_med": _med([len(x) for x in leads if x]),
        "heads_med": _med(heads),
        "para_len_med": _med(paras),
    }


# 每维允许的相对偏差（超过才算"不像"）。数值来自对本轮 4 篇真稿的观察，
# 不是拍脑袋的"标准"；语料够了要重标定，标定记录写进 GZH-TRAIN-SPEC。
TOL = {
    "title_len_med": 0.35,
    "title_num_pct": 25.0,     # 百分点
    "title_q_pct": 25.0,
    "lead_len_med": 0.50,
    "heads_med": 0.60,
    "para_len_med": 0.50,
}


def compare(ours, ref):
    """逐维比较。返回 (是否达标, 明细)。分母用真稿，方向不对称是对的：
    我们要像它们，不是它们像我们。"""
    o, r = profile(ours), profile(ref)
    rows, bad = [], []
    for k, tol in TOL.items():
        a, b = o.get(k), r.get(k)
        if a is None or b is None:
            rows.append((k, a, b, None, "跳过（一侧为空）"))
            continue
        if k.endswith("_pct"):
            diff, ok = abs(a - b), abs(a - b) <= tol
        else:
            diff = abs(a - b) / max(b, 1)
            ok = diff <= tol
        rows.append((k, a, b, round(diff, 3), "OK" if ok else "偏离"))
        if not ok:
            bad.append(k)
    return (not bad), {"ours": o, "ref": r, "rows": rows, "bad": bad}


def ai_flavor(arts):
    """AI 腔命中：只要命中就列出来，不扣分算总分——它是"一票否决"，不是权重项。"""
    hits = []
    for a in arts:
        t = (a.get("text") or "") + "\n" + (a.get("title") or "")
        for pat in AI_PAT:
            m = re.search(pat, t)
            if m:
                hits.append({"title": (a.get("title") or "")[:30], "pat": pat, "hit": m.group(0)[:20]})
    return hits


def _grams(s, n=6):
    s = re.sub(r"\s+", "", s or "")
    return {s[i:i + n] for i in range(0, max(0, len(s) - n + 1))}


def overlap(ours, ref, n=6, limit=13):
    """洗稿闸：任一篇与任一篇真稿的最长公共子串长度 > limit 即判红。
    用 6-gram 交集做快速剪枝，不追求学术级最长公共子串。"""
    refs = [(a.get("title") or "") + (a.get("text") or "") for a in ref]
    ref_sets = [_grams(s, n) for s in refs]
    worst = 0
    worst_pair = None
    for a in ours:
        mine = (a.get("title") or "") + (a.get("text") or "")
        gs = _grams(mine, n)
        if not gs:
            continue
        for i, rs in enumerate(ref_sets):
            common = gs & rs
            if not common:
                continue
            # 用命中 gram 数量近似判断：命中块越长越危险
            score = len(common)
            if score > worst:
                worst = score
                worst_pair = ((a.get("title") or "")[:20], (ref[i].get("title") or "")[:20])
    return worst, worst_pair


def self_test():
    """负控：分布完全相同必须过、完全不同必须红、AI 腔必须被抓出。"""
    cases = []
    base = [{"title": "15 万纯电 SUV，5 台只有 1 台敢买", "lead": "先说结论，我把这 5 台按排除法删到只剩一台。" * 3,
             "text": "段落一\n\n" + "正文内容" * 40, "heads": ["a", "b", "c"], "words": 900} for _ in range(6)]
    alt = [{"title": "这是一篇很长很长而且没有任何数字也没有问句的标题用来测试偏离程度到底会不会被抓出来啊啊啊",
            "lead": "短", "text": "一句话。", "heads": [], "words": 20} for _ in range(6)]

    ok1, _ = compare(base, base)
    cases.append(("同分布→达标", ok1 is True))
    ok2, _ = compare(alt, base)
    cases.append(("全偏离→判红", ok2 is False))

    # 单维篡改：只把标题拉长，也必须红（证明逐维真的在读）
    mut = [dict(x, title=x["title"] * 3) for x in base]
    ok3, d3 = compare(mut, base)
    cases.append(("只改标题长度→红", ok3 is False and "title_len_med" in d3["bad"]))

    # AI 腔
    ai = [{"title": "x", "text": "作为一个人工智能，首先，我们应该看到其次，总结一下。"}]
    cases.append(("AI 腔被命中", len(ai_flavor(ai)) >= 2))
    cases.append(("干净稿不误伤", len(ai_flavor(base)) == 0))

    # 洗稿
    w, pair = overlap(base, base)
    cases.append(("同文自比→重合度极高", w > 13))
    cases.append(("无关文本→低重合", overlap(alt, base)[0] <= 13))

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default=os.path.join(GZH, "DRAFTS.jsonl"))
    ap.add_argument("--ref", default=os.path.join(GZH, "ARTICLES.jsonl"))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    ours, ref = _rows(a.ours), _rows(a.ref)
    if not ours or not ref:
        print("[gzh-q] 缺语料：ours=%d ref=%d（不出稿阶段，ref 用于标定；ours 为空属正常）"
              % (len(ours), len(ref)))
        return 0
    ok, d = compare(ours, ref)
    hits = ai_flavor(ours)
    w, pair = overlap(ours, ref)
    if a.json:
        print(json.dumps({"ok": ok, "detail": d, "ai": hits, "overlap": w}, ensure_ascii=False, indent=1))
        return 0
    print("形态对照（分母＝真稿）")
    for k, o, r, diff, verdict in d["rows"]:
        print("  %-16s ours=%-8s ref=%-8s 差=%-7s %s" % (k, o, r, diff, verdict))
    print("AI 腔命中：%d 处" % len(hits))
    for h in hits[:5]:
        print("   · %s ← %s" % (h["hit"], h["title"]))
    print("与真稿最大重合块：%d gram（>13 视为洗稿）%s" % (w, ("｜%s" % (pair,)) if pair else ""))
    print("结论：%s" % ("过" if ok and not hits and w <= 13 else "不过"))
    return 0 if ok and not hits and w <= 13 else 1


if __name__ == "__main__":
    sys.exit(main())
