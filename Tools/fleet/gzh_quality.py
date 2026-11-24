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
    r"总结一下|简单来说|总的来说",
    r"在(数字化|智能化|新能源)?浪潮下",
    r"赋能|助力(行业|用户)",
    # 2026-11-23 工艺席实测：公文腔 3/3 全漏，而规格里公文腔是一票否决
    r"为(贯彻|落实|深入)(贯彻|落实)?",
    r"现将(有关|相关)?(事项|情况|要求)",
    r"致力于(打造|成为|提供)",
    r"闭环|抓手|高质量发展|持续推进",
    r"一站式(解决方案|服务)|全链路",
    r"进一(步|加强)|着力|切实",
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
    """真中位数。2026-11-23 判据席实测：原实现取 xs[n//2]，n=4 时等于第 3 小值，
    把 heads 维度从 17.5 抬到 24（+37%），等于把闸放松并把中心挪歪。"""
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


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
    heads = [len(set(a.get("heads") or [])) for a in arts]
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
N_MIN = 30      # 比例维度在 n=30 前不可估计；不到就只报数，禁止出"过/不过"

# 2026-11-23 内容工艺席实测：现有语料是 4 篇机构通稿，不是对标对象本人，故这四维
# 全部失真——title_q_pct 方向甚至相反（真稿 0%，而文档写"问句占比最高"）。
# 换成语料=对标对象本人并重标定之前，这四维**只报数、不判生死**。
SUSPENDED = {"title_len_med", "title_num_pct", "title_q_pct", "heads_med"}
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
    if (o.get("n") or 0) < N_MIN or (r.get("n") or 0) < N_MIN:
        # 不下结论：这是本文件最重要的一条纪律，避免用随机噪声当判据
        return None, {"ours": o, "ref": r, "rows": [], "bad": [],
                      "note": "样本不足（ours=%d ref=%d，需各 ≥%d）：只报数，不判过/不过"
                              % (o.get("n") or 0, r.get("n") or 0, N_MIN)}
    rows, bad = [], []
    for k, tol in TOL.items():
        a, b = o.get(k), r.get(k)
        if a is None or b is None:
            rows.append((k, a, b, None, "跳过（一侧为空）"))
            continue
        if k in SUSPENDED:
            rows.append((k, a, b, None, "停用（语料未换成对标对象，需重标定）"))
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
    """AI 腔命中：只要命中就列出来，不扣分算总分——它是"一票否决"，不是权重项。

    2026-11-24：本文件原有的 AI_PAT 是 2026-11-11 从 4B 实测里归纳的十来条句式；
    现在叠加去 AI 感闸的 104 条分级词库（deai_check，判据源在 vendor 的 md 里）。
    两套并行会各说各话，所以分工是：AI_PAT 管**整句结构**，deai_check 管**词与体裁**，
    结果合并进同一份 hits，调用方只读这一份。
    """
    hits = []
    try:
        import deai_check as _dz
        _vocab = _dz.load_vocab()
    except Exception:
        _dz, _vocab = None, None
    for a in arts:
        t = (a.get("text") or "") + "\n" + (a.get("title") or "")
        for pat in AI_PAT:
            m = re.search(pat, t)
            if m:
                hits.append({"title": (a.get("title") or "")[:30], "pat": pat, "hit": m.group(0)[:20]})
        if _dz is not None:
            v = _dz.check(t, _vocab)
            if v["verdict"] == "reject":
                hits.append({"title": (a.get("title") or "")[:30], "pat": "deai",
                             "hit": "、".join(h["term"] for h in v["hits"][:3])[:40]})
    return hits


def _grams(s, n=6):
    s = re.sub(r"\s+", "", s or "")
    return {s[i:i + n] for i in range(0, max(0, len(s) - n + 1))}


def overlap(ours, ref, n=6, limit=30):
    """洗稿闸（兜底近似）：任一篇与任一篇真稿的**最长连续相同字符数** > limit 才判红。

    2026-11-23 判据席实测原实现（6-gram 交集个数 >13）有两个硬伤：
      ① 语义错——数的是"共享 6-gram 的个数"，随文档长度单调增长，与"抄了多长"无关；
      ② 误杀——连续 19 字相同就判红，车型清单/官方规程名一律中招。
    现在用 SequenceMatcher 求最长公共块（字符数），阈值 30 字。
    仍会漏"每 5 字改 1 字"的改词洗稿——这是已知局限，不能当唯一防线。"""
    import difflib
    refs = [(a.get("title") or "") + (a.get("text") or "") for a in ref]
    worst, worst_pair = 0, None
    for a in ours:
        mine = (a.get("title") or "") + (a.get("text") or "")
        if len(mine) < 40:
            continue                     # 太短无法判重，不当成"通过"
        for i, rs in enumerate(refs):
            m = difflib.SequenceMatcher(None, mine, rs, autojunk=False).find_longest_match(
                0, len(mine), 0, len(rs))
            if m.size > worst:
                worst = m.size
                worst_pair = ((a.get("title") or "")[:20], (ref[i].get("title") or "")[:20])
    return worst, worst_pair


def self_test():
    """负控：分布完全相同必须过、完全不同必须红、AI 腔必须被抓出。"""
    global N_MIN
    cases = []
    saved_n = N_MIN
    # 先验"样本不足必须不出结论"，再把闸放到 1 去验边界（否则测试自己就被闸拦住）
    small = [{"title": "标题带数字 3 个", "lead": "开篇" * 40, "text": "正文" * 50,
              "heads": ["a"], "words": 200}]
    cases.append(("样本不足→不出结论（ok is None）", compare(small, small)[0] is None))
    N_MIN = 1
    base = [{"title": "15 万纯电 SUV，5 台只有 1 台敢买", "lead": "先说结论，我把这 5 台按排除法删到只剩一台。" * 3,
             "text": "段落一\n\n" + "正文内容" * 40, "heads": ["a", "b", "c"], "words": 900} for _ in range(6)]
    alt = [{"title": "这是一篇很长很长而且没有任何数字也没有问句的标题用来测试偏离程度到底会不会被抓出来啊啊啊",
            "lead": "短", "text": "一句话。", "heads": [], "words": 20} for _ in range(6)]

    ok1, _ = compare(base, base)
    cases.append(("同分布→达标", ok1 is True))
    ok2, _ = compare(alt, base)
    cases.append(("全偏离→判红", ok2 is False))

    # 单维篡改：只把**未停用**的开篇拉长，也必须红（证明判决维真的在读）
    mut = [dict(x, lead="短") for x in base]
    ok3, d3 = compare(mut, base)
    cases.append(("只改开篇长度→红", ok3 is False and "lead_len_med" in d3["bad"]))

    # 停用维度不得影响结论：把停用维度的值改到离谱，结论仍须为"过"
    mut2 = [dict(x, heads=["a"], title=x["title"][:3]) for x in base]
    ok4, _ = compare(mut2, base)
    cases.append(("停用维度不影响结论", ok4 is True))

    # AI 腔
    ai = [{"title": "x", "text": "作为一个人工智能，首先，我们应该看到其次，总结一下。"}]
    cases.append(("AI 腔被命中", len(ai_flavor(ai)) >= 2))
    gongwen = [{"title": "x", "text": "为贯彻落实相关要求，现将有关事项通知如下，我们致力于打造一站式解决方案，赋能行业高质量发展。"}]
    cases.append(("公文腔被命中（原 3/3 全漏）", len(ai_flavor(gongwen)) >= 2))

    # 负控：只用新词库才抓得到的稿子（旧的 AI_PAT 一条都不匹配）——
    # 否则"叠加了 deai"可能只是摆设，实际全靠旧句式规则在干活。
    vocab_only = [{"title": "深耕三年，这款车的底层逻辑", "text": "我们深耕细分市场，多维度打造闭环，全程一站式服务。"}]
    hv = ai_flavor(vocab_only)
    cases.append(("只有新词库能抓的稿 → 被判 deai", any(h["pat"] == "deai" for h in hv)))
    clean = [{"title": "10 万落地，我把 4 台车开了一遍", "text": "试驾那天下了雨，胎噪在 80 码之后才明显。"}]
    cases.append(("正常车评稿不被 deai 误判", not any(h["pat"] == "deai" for h in ai_flavor(clean))))
    cases.append(("干净稿不误伤", len(ai_flavor(base)) == 0))

    # 洗稿
    w, pair = overlap(base, base)
    cases.append(("同文自比→重合度极高", w > 13))
    cases.append(("无关文本→低重合", overlap(alt, base)[0] <= 13))

    N_MIN = saved_n
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
