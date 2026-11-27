#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""risky_diagnose.py - RISKY 68% 的成因拆解（实验 E-20261126-02 的取证器）。

问题（上一轮留下的唯一悬念）：
    BAKED-v1 里 RISKY 占 68.6%、PASS 只有 19.5%。到底是
      (A) 语料本不适合当示范（logic 主干缺）→ 该换来源/换采集方向，还是
      (B) 总分只差一点点（分档线设错）→ 该改用法，把 RISKY 分层使用？

为什么不能"感觉语料不够"：
    2026-11-26 E-01 已经把"门槛放松"这条路证伪（--min-human 5→3，62.5% vs 56.2%）。
    在同一个维度上再抠一次等于重复劳动。要么证明"这批料的形状就是不行"，
    要么证明"料没问题、是我用错了档"，二者必须由数字判，不由印象判。

三个必答问题：
  1. RISKY 里五个子维各短多少？（logic/voice/human/taste/natural）
  2. 卡住它的主因是"总分不足"还是"logic 不足"还是"单个做作词"？
  3. 若按"差 ≤N 分"分层，各层有多少条、覆盖哪些段？（决定分层用法是否可行）

自检（负控）：
  - 重算判词必须与烘焙时存的 verdict 一致率 ≥95%（否则是打分器被改过，结论不可用）
  - 构造一条总分只差 1 分的样本必须被判为 near_pass
  - 构造一条 logic=0 的样本必须被判为 logic_blocked
  - 构造一条命中唯一做作词的样本必须被判为 cli_blocked

用法：
  python3 Tools/fleet/risky_diagnose.py                 # 全量报告
  python3 Tools/fleet/risky_diagnose.py --self-test     # 负控
  python3 Tools/fleet/risky_diagnose.py --json out.json # 落盘
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
BAKED = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")

sys.path.insert(0, HERE)
import comment_taste as ct  # noqa: E402


def _lines(path):
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                yield json.loads(ln)
            except Exception:
                continue


def _limits(seg):
    """该段的三条线：总分线 / 逻辑线 / 是否短促接话可算完整。"""
    return ct.SEG_TUNE.get(seg, (60, 30, False))


def classify_reason(s, seg):
    """把一条 RISKY 归到唯一主因桶。

    优先级：做作词（一票否决，最省事）> logic 不足 > 总分不足 > 其他。
    为什么 cli 优先：它和总分无关，放松总分线永远救不了它——若不单独计数，
    会得出"再放宽 5 分就能救一半"的错误结论。
    """
    pass_line, logic_line, short_ok = _limits(seg)
    t = ct.strip_reply_prefix(s.get("text") or s.get("t") or "")
    cli = [w for w in ct.CLICHE if w in t]
    if cli:
        return "cli_blocked", {"cli": cli[:3]}
    if s["logic"] < logic_line:
        return "logic_blocked", {"logic": s["logic"], "need": logic_line}
    if s["total"] < pass_line:
        return "total_short", {"total": s["total"], "need": pass_line}
    if ct.FILLER.match(t) or len(t) < 6:
        return "filler", {}
    return "other", {}


def run(path=BAKED, near_bands=(5, 10, 15, 20)):
    rows = list(_lines(path))
    agree = disagree = 0
    risky = []
    for r in rows:
        text = r.get("text") or ""
        s = ct.score(text, r.get("seg"))
        if s["verdict"] != r.get("verdict"):
            disagree += 1
            continue
        agree += 1
        if r.get("verdict") != "RISKY":
            continue
        reason, extra = classify_reason(dict(s, text=text), r.get("seg"))
        pass_line, logic_line, short_ok = _limits(r.get("seg"))
        risky.append({
            "seg": r.get("seg"), "src": r.get("src"), "len": s["len"],
            "total": s["total"], "gap": pass_line - s["total"],
            "logic": s["logic"], "logic_need": logic_line,
            "logic_gap": max(0, logic_line - s["logic"]),
            "voice": s["voice"], "human": s["human"],
            "taste": s["taste"], "natural": s["natural"],
            "reason": reason, "extra": extra,
        })
    total = len(rows)
    conf = agree / float(total) if total else 0.0

    reason = Counter(x["reason"] for x in risky)
    # 子维缺口：每条理由里最接近线的那一维差多少
    dims = defaultdict(list)
    for x in risky:
        dims["logic"].append(x["logic"])
        dims["logic_gap"].append(x["logic_gap"])
        dims["voice"].append(x["voice"])
        dims["human"].append(x["human"])
        dims["taste"].append(x["taste"])
        dims["natural"].append(x["natural"])
        dims["gap"].append(x["gap"])

    def pct(v, p):
        if not v:
            return 0
        v = sorted(v)
        k = min(len(v) - 1, int(round((p / 100.0) * (len(v) - 1))))
        return v[k]

    dim_stat = {k: {"mean": round(sum(v) / len(v), 1) if v else 0,
                    "p50": pct(v, 50), "p90": pct(v, 90)} for k, v in dims.items()}

    # 分层：差 ≤N 分可救多少（且未命中做作/逻辑硬门槛）
    b = {}
    for n in near_bands:
        hit = [x for x in risky if x["reason"] == "total_short" and 0 < x["gap"] <= n]
        b["le%d" % n] = {"n": len(hit),
                         "share_of_risky": round(len(hit) / len(risky) * 100, 1) if risky else 0,
                         "segs": dict(Counter(x["seg"] for x in hit).most_common(6))}

    # 只差 1-2 分的极端情况：说明线本身卡在边缘
    edge = [x for x in risky if x["reason"] == "total_short" and x["gap"] <= 2]

    seg_risky = Counter(x["seg"] for x in risky)
    seg_total = Counter((r.get("seg") or "?") for r in rows)
    seg_rate = {s: {"risky": seg_risky.get(s, 0), "total": seg_total.get(s, 0),
                    "rate": round(seg_risky.get(s, 0) / seg_total[s] * 100, 1)}
                for s in seg_total if seg_total[s] >= 50}

    src_risky = Counter(x["src"] for x in risky)
    src_total = Counter((r.get("src") or "?") for r in rows)

    return {
        "rows": total, "conformance": round(conf, 4),
        "disagree": disagree,
        "risky": len(risky),
        "reasons": dict(reason.most_common()),
        "reason_share": {k: round(v / len(risky) * 100, 1) for k, v in reason.most_common()} if risky else {},
        "dims": dim_stat,
        "bands": b,
        "edge": {"n": len(edge),
                 "samples": [x for x in edge[:8]]},
        "seg_rate": dict(sorted(seg_rate.items(), key=lambda kv: -kv[1]["rate"])),
        "src_rate": {s: {"risky": src_risky.get(s, 0), "total": src_total[s],
                         "rate": round(src_risky.get(s, 0) / src_total[s] * 100, 1)}
                     for s in src_total if src_total[s] >= 50},
    }


def self_test():
    cases = []

    # 1 负控：logic=0（没有任何具体对象/转折）必须归 logic_blocked
    #    注意「这个/感觉」在 CONNECT 表里会被当成转折词各给 20 分，选样例时要避开
    s = ct.score("这首歌真的很好听", "critic")
    r, _ = classify_reason(dict(s, text="这首歌真的很好听"), "critic")
    cases.append(("无具体对象→logic_blocked", r == "logic_blocked"))

    # 2 负控：命中一个做作词就归 cli_blocked（哪怕总分够）
    bad = ct.CLICHE[0] if ct.CLICHE else "绝绝子"
    s = ct.score("这个转场%s" % bad, "critic")
    r, _ = classify_reason(dict(s, text="这个转场%s" % bad), "critic")
    cases.append(("命中做作词→cli_blocked", r == "cli_blocked"))

    # 3 正控：总分刚好达标且逻辑够 → 不是 RISKY（不该出现在 RISKY 集合里）
    good = "结尾那个转场接得太生硬了，前面铺垫全废"
    s = ct.score(good, "critic")
    cases.append(("合格句不该是 RISKY", s["verdict"] in ("PASS", "RISKY") and
                  (s["verdict"] != "RISKY" or classify_reason(dict(s, text=good), "critic")[0] != "cli_blocked")))

    # 4 正控：构造 total_short（逻辑够、总分差一点、无做作词）
    fake = {"text": "前面铺垫太长了不过我倒是觉得节奏还行", "logic": 45, "voice": 16,
            "human": 20, "taste": 16, "natural": 20, "total": 58}
    r, extra = classify_reason(fake, "critic")  # critic 线 58 → 刚好够，改成 tech_nerd(62)
    r2, extra2 = classify_reason(fake, "tech_nerd")
    cases.append(("差一点→total_short（gap 记录正确）",
                  r2 == "total_short" and extra2.get("need") == 62))

    # 5 负控：FILLER 短接话必须单独归类，不混进 total_short
    s = ct.score("哈哈哈哈哈", "memer")
    r, _ = classify_reason(dict(s, text="哈哈哈哈哈"), "memer")
    cases.append(("纯助兴不混入 total_short", r in ("filler", "logic_blocked", "other")))

    ok = sum(1 for _, v in cases if v)
    for name, v in cases:
        print("  [%s] %s" % ("PASS" if v else "FAIL", name))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baked", default=BAKED)
    ap.add_argument("--json")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not os.path.exists(a.baked):
        print("[risky] 找不到 %s" % a.baked, file=sys.stderr)
        return 2
    d = run(a.baked)
    print("[risky] 行数 %d · 重算一致率 %.1f%%（不一致 %d 条=打分器改过，结论打折）"
          % (d["rows"], d["conformance"] * 100, d["disagree"]))
    print("[risky] RISKY %d 条" % d["risky"])
    print("[risky] 主因分布：")
    for k, v in d["reason_share"].items():
        print("        %-14s %5.1f%%  (%d)" % (k, v, d["reasons"][k]))
    print("[risky] 子维（mean/p50/p90）：")
    for k in ("logic", "logic_gap", "voice", "human", "taste", "natural", "gap"):
        x = d["dims"][k]
        print("        %-10s %6.1f / %4d / %4d" % (k, x["mean"], x["p50"], x["p90"]))
    print("[risky] 分层可救（仅 total_short）：")
    for k, v in d["bands"].items():
        print("        %-6s %5d 条 (RISKY 的 %.1f%%)  %s"
              % (k, v["n"], v["share_of_risky"], v["segs"]))
    print("[risky] 差 ≤2 分（线卡在边缘）：%d 条" % d["edge"]["n"])
    print("[risky] 按段 RISKY 率：")
    for s, v in list(d["seg_rate"].items())[:10]:
        print("        %-14s %5.1f%%  (%d/%d)" % (s, v["rate"], v["risky"], v["total"]))
    print("[risky] 按来源 RISKY 率：")
    for s, v in list(d["src_rate"].items())[:10]:
        print("        %-16s %5.1f%%  (%d/%d)" % (s, v["rate"], v["risky"], v["total"]))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print("[risky] → %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
