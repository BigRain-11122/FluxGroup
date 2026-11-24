#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_review.py — 用本地小模型做"人工评审"该做的事：像不像人、属于哪种原型、哪里别扭。

为何这么分工（2026-11-22 CEO「尽量利用好本地的大模型能力去做任务循环」）：
- **数字一律由规则算**（长度、重复、具体词、AI 腔命中）——4B 的算术与计数不可靠，
  这条是硬教训，不让模型碰数字结论。
- **判断交模型**：这条评论像不像真人在说话、属于 7 种原型里的哪一种、最别扭的是哪一点。
  这正是正则判不准的地方（正则把 67% 的稿都归成 "plain"）。

严格性：模型只许输出一行 JSON，字段与取值都要过白名单；解析失败重试一次，
再失败就作废（不落账、不猜），绝不把半截输出当结论。

用法：
  python3 Tools/fleet/local_review.py            # 评审最近未评审的 5 条
  python3 Tools/fleet/local_review.py --n 8
  python3 Tools/fleet/local_review.py --json
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
LOG = os.path.join(SOCIAL, "practice-log.jsonl")
OUT = os.path.join(STATE, "LOCAL-REVIEW.json")
SEEN = os.path.join(STATE, "LOCAL-REVIEW-SEEN.json")
LEDGER = os.path.join(STATE, "LOCAL-REVIEW.jsonl")

ARCHS = ["reaction", "praise", "critique", "meme", "resonance", "ask", "plain"]

PROMPT = """你是 B 站评论区老手。给你一条真实发出过的评论，只回一行 JSON，不要解释。

评论：{text}

判三件事：
1. human：0-10，像不像真人随手写的（10 完全像人，0 像模板/文案）
2. archetype：只能选一个——reaction(纯反应) praise(夸) critique(挑刺) meme(玩梗) resonance(共鸣/讲自己) ask(追问) plain(平铺直叙)
3. issue：最别扭的一点，不超过 15 字；没问题写空字符串

只回这个格式：{{"human": 7, "archetype": "praise", "issue": ""}}"""


def _load(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d if d is not None else {}


def _rows(path):
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def _parse(raw):
    """从模型输出里取第一个 JSON；字段与取值全过白名单，不合格返回 None。"""
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except Exception:
        return None
    try:
        human = int(d.get("human"))
    except Exception:
        return None
    arch = str(d.get("archetype") or "").strip()
    issue = str(d.get("issue") or "").strip()[:30]
    if not (0 <= human <= 10) or arch not in ARCHS:
        return None
    return {"human": human, "archetype": arch, "issue": issue}


def review_one(text, cls="triage"):
    """一次评审；解析失败重试一次，两次都不合格就返回 None（作废，不猜）。"""
    import llm_client as lc
    for _ in range(2):
        r = lc.generate(PROMPT.format(text=(text or "")[:120]), cls=cls,
                        timeout=60, num_predict=120, think=False)
        if not r.get("ok"):
            return None
        got = _parse(r.get("text"))
        if got:
            return got
    return None


def _model_ready(cls="triage"):
    # 训练独占时连"探一下"都不要做：探针会触发一次模型装载，被 guard 立刻卸下，
    # 一晚上能来回折腾几十次（日志里那些"卸下 qwen3.5:2b"就是这么来的）。
    if os.path.exists(os.path.join(STATE, "TRAIN-EXCLUSIVE")):
        return False, 5, "训练独占中（哨兵在），不触发模型装载"
    """先探一下模型能不能用：训练独占时不要逐条去打（会把 5 条都记成"作废"，污染台账，
    而真实原因是 GPU 被训练占着，不是稿子有问题）。"""
    try:
        import llm_client as lc
        r = lc.generate("好", cls=cls, timeout=20, num_predict=1, think=False)
        return bool(r.get("ok")), r.get("rc"), (r.get("why") or "")[:60]
    except Exception as e:
        return False, 1, "%s: %s" % (type(e).__name__, str(e)[:50])


def run(n=5, cls="triage"):
    ok_model, rc, why = _model_ready(cls)
    if not ok_model:
        return {"n": 0, "why": "本地模型暂不可用（rc=%s %s），评审排队到下一个窗口" % (rc, why), "rc": rc}
    posts = [r for r in _rows(LOG) if r.get("action") == "post" and (r.get("text") or "").strip()]
    posts = posts[-40:]
    seen = set(_load(SEEN, []) or [])
    todo = [p for p in posts if str(p.get("rpid") or "") not in seen][-max(1, n):]
    if not todo:
        return {"n": 0, "why": "没有新的待评审稿件"}
    results = []
    for p in todo:
        got = review_one(p.get("text"), cls=cls)
        rec = {"ts": p.get("ts"), "rpid": p.get("rpid"),
               "text": (p.get("text") or "")[:80], "ok": bool(got)}
        if got:
            rec.update(got)
        results.append(rec)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        seen.add(str(p.get("rpid") or ""))
        json.dump(sorted(seen), open(SEEN, "w", encoding="utf-8"), ensure_ascii=False)
    ok = [r for r in results if r.get("ok")]
    agg = {
        "ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "n": len(results), "n_ok": len(ok),
        "human_median": round(st.median([r["human"] for r in ok]), 1) if ok else None,
        "archetypes": dict(collections.Counter(r["archetype"] for r in ok).most_common()),
        "issues": [r["issue"] for r in ok if r.get("issue")],
        "items": results,
    }
    json.dump(agg, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return agg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--cls", default="triage", help="座位：triage(2b)/resident(4b)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    agg = run(a.n, a.cls)
    if a.json:
        print(json.dumps(agg, ensure_ascii=False))
    else:
        if not agg.get("n"):
            print("[review] %s" % agg.get("why"))
            return 0
        print("[review] 评 %d 条，成功 %d 条；模型人味中位 %s"
              % (agg["n"], agg["n_ok"], agg["human_median"]))
        print("[review] 模型原型分布 %s" % agg["archetypes"])
        for r in agg["items"]:
            if r.get("ok"):
                print("   %d/10 %-9s %s%s" % (r["human"], r["archetype"], r["text"][:34],
                                             ("  ← " + r["issue"]) if r.get("issue") else ""))
            else:
                print("   作废（模型输出不合格）%s" % r["text"][:34])
    return 0


if __name__ == "__main__":
    sys.exit(main())
