#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_topics.py - 从真实评论里提炼下一条内容的选题候选（养号线「选题」工序）。

Why（2026-11-12）：PROD-ACCOUNT-GROWTH 的「选题」长期 TOOL-PENDING，导致养号线
五道工序少一环、自驱每轮算出"该建卡"却不敢建。选题的原料其实已经有了：观众
在评论区反复问什么，就是下一条内容该回答什么。

三条硬边界（不造活）：
  * 只用真实出现过的评论，不编造观众声音；每条候选必须挂 evidence（评论 id）。
  * 样本不足就明说 LOW 置信度，绝不假装"数据支持"。
  * 只产出候选与钩子，选题定稿是人判（judge=panel），机器不自评通过。

Input  : cph4/fleet/social/inbox.jsonl    {id, comment, author?, video?}
         cph4/fleet/social/drafts.jsonl   （可选，带 kind 分类，优先用它）
Output : cph4/fleet/out/account/topics.json

Usage:
  python3 Tools/fleet/social_topics.py
  python3 Tools/fleet/social_topics.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIR = os.path.join(ROOT, "cph4", "fleet", "social")
INBOX = os.path.join(DIR, "inbox.jsonl")
DRAFTS = os.path.join(DIR, "drafts.jsonl")
OUT = os.path.join(ROOT, "cph4", "fleet", "out", "account", "topics.json")

# 观众问什么 -> 下一条内容做什么。只映射真实存在的评论类别，不做通用模板。
ANGLE = {
    "question_ai": ("回应「是不是 AI 做的」", "把制作流程摊开讲：哪些镜头是生成、哪些是实拍、改了几版", "披露口径需 CEO 确认"),
    "question_identity": ("回应创作者身份/经历", "讲这一集为什么这么写：真实经历与虚构的比例", "身份披露口径归 CEO"),
    "legal": ("正面回应原创性质疑", "把参考来源、素材授权、创作过程逐项列出", "涉法务，必须先过合规"),
    "question": ("回答观众最常问的一个问题", "挑一条问得最多的，用 30 秒讲透", "无"),
    "spam": ("（不产出选题）", "广告/导流不构成内容需求", "—"),
    "praise": ("放大被认可的那一点", "把观众说「太真实」的段落单独做成加长版", "无"),
}
DEFAULT_ANGLE = ("未分类评论", "人工判断这条评论在问什么", "需要人看")


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


def build(inbox, drafts, now=None):
    """纯函数：评论 -> 选题候选。drafts 有 kind 就用它，否则按文本关键字兜底。"""
    kind_of = {str(d.get("id")): str(d.get("kind") or "") for d in drafts if d.get("id")}
    buckets = {}
    unclassified = 0
    for c in inbox:
        cid = str(c.get("id") or "")
        if not cid:
            continue
        k = kind_of.get(cid) or ""
        if not k:
            txt = str(c.get("comment") or "")
            if "AI" in txt or "ai" in txt:
                k = "question_ai"
            elif "抄" in txt:
                k = "legal"
            elif "V" in txt or "微信" in txt:
                k = "spam"
            else:
                k = "unknown"
        if k == "unknown":
            unclassified += 1
        buckets.setdefault(k, []).append(cid)
    topics = []
    for k, ids in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        if k == "spam":
            continue
        title, hook, risk = ANGLE.get(k, DEFAULT_ANGLE)
        if k == "unknown":
            title = "未分类评论 %d 条（需人工归类）" % len(ids)
        topics.append({"topic": title, "hook": hook, "from_kind": k,
                       "evidence": ids, "count": len(ids), "risk": risk,
                       "needs_human": True})
    n = sum(len(v) for v in buckets.values())
    # 置信度只由样本量决定，不由"看起来像不像"决定。
    conf = "LOW" if n < 20 else ("MED" if n < 100 else "HIGH")
    return {"ts": (now or datetime.now()).isoformat(timespec="seconds"),
            "sample_size": n,
            "confidence": conf,
            "confidence_rule": "LOW<20 条, MED<100 条, HIGH>=100 条（样本来自真实评论）",
            "unclassified": unclassified,
            "topics": topics,
            "note": ("样本不足时这些只是方向候选，不能当作「数据支持」；定稿是人判（panel）。"
                     if conf == "LOW" else "候选需人判定稿（panel）。")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", default=INBOX)
    ap.add_argument("--drafts", default=DRAFTS)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    inbox = _rows(a.inbox)
    if not inbox:
        print("缺输入：%s 里没有评论（先有真实评论再谈选题）" % a.inbox)
        return 3
    rep = build(inbox, _rows(a.drafts))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    print("选题候选 -> %s｜样本 %d 条｜置信 %s｜候选 %d 个"
          % (a.out, rep["sample_size"], rep["confidence"], len(rep["topics"])))
    return 0


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    inbox = [{"id": "1", "comment": "这是AI做的吗"},
             {"id": "2", "comment": "你是不是学考古的"},
             {"id": "3", "comment": "抄某某MV"},
             {"id": "4", "comment": "加V看更多"}]
    drafts = [{"id": "1", "kind": "question_ai"}, {"id": "2", "kind": "question_identity"},
              {"id": "3", "kind": "legal"}, {"id": "4", "kind": "spam"}]
    r = build(inbox, drafts)
    chk("按 kind 归并，spam 不出选题",
        all(t["from_kind"] != "spam" for t in r["topics"]) and len(r["topics"]) == 3, r["topics"])
    chk("每条候选都挂 evidence（不编造观众声音）",
        all(t["evidence"] for t in r["topics"]))
    chk("样本 4 条 -> LOW 置信", r["confidence"] == "LOW", r["confidence"])
    chk("样本 >=20 -> 不再是 LOW", build([{"id": str(i), "comment": "x"} for i in range(20)], [])["confidence"] != "LOW")
    chk("全部候选标 needs_human（定稿是人判）",
        all(t["needs_human"] for t in r["topics"]))
    chk("无 drafts 时按文本兜底分类（AI/抄/V）",
        {t["from_kind"] for t in build(inbox, [])["topics"]} >= {"question_ai", "legal"})
    chk("空输入 -> 样本 0 且无候选", build([], [])["sample_size"] == 0 and build([], [])["topics"] == [])
    # 幂等
    a1 = {k: v for k, v in build(inbox, drafts).items() if k != "ts"}
    a2 = {k: v for k, v in build(inbox, drafts).items() if k != "ts"}
    chk("同输入两次结论一致（可复算）", a1 == a2)
    print("\n[social_topics] %d/%d" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
