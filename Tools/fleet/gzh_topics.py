#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_topics.py — 选题库的可兑现性判据。

为什么要有它：
群审判过一条最硬的：原 20 条选题里 7 条承诺了交付不了的事（「我实测 3 万公里」
「我把 5 台车摆一起」）——我们无车、无设备、无场地。承诺写进标题，就是一次公开的
假话；写稿时才发现做不到，等于整条产线白跑。
所以把「能不能兑现」做成机器判据：选题卡里出现做不到的动作 → 红，不许进排期。

判据（四条，全部可机检）：
  A. promise 与 title 里不许出现 forbidden_promises 里的动作（实测/拆车/摆车…）
  B. evidence 必须非空，且每一项都得是 evidence_types 里定义的合法类型
  C. verifiable 必须非空（"读者怎么核"必须写出来，没写＝不可兑现）
  D. risk 必须非空（每条选题都要写明它会踩到什么，否则是空想）

用法：
  python3 Tools/fleet/gzh_topics.py --check
  python3 Tools/fleet/gzh_topics.py --list
  python3 Tools/fleet/gzh_topics.py --self-test
退出码：0 全可兑现 / 1 有不可兑现项 / 2 文件读不到
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOPICS = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "TOPICS-v1.json")


def load(path=None):
    with open(path or TOPICS, encoding="utf-8") as f:
        return json.load(f)


def check(doc):
    """返回 (ok, 问题列表, 统计)。doc 可注入，供自检造坏样本。"""
    bad = []
    types = set((doc.get("evidence_types") or {}).keys())
    forb = doc.get("forbidden_promises") or []
    topics = doc.get("topics") or []
    if not topics:
        return False, ["没有选题"], {}
    cats = {c["id"] for c in (doc.get("categories") or [])}
    per_cat = {}
    for t in topics:
        tid = t.get("id") or "?"
        per_cat[t.get("cat")] = per_cat.get(t.get("cat"), 0) + 1
        blob = (t.get("title") or "") + " " + (t.get("promise") or "")
        hit = [w for w in forb if w in blob]
        if hit:
            bad.append("A: %s 承诺了做不到的事「%s」" % (tid, "、".join(hit)))
        ev = t.get("evidence") or []
        if not ev:
            bad.append("B: %s 没有证据来源" % tid)
        for e in ev:
            if e not in types:
                bad.append("B: %s 证据类型「%s」未定义（不许自造）" % (tid, e))
        if not (t.get("verifiable") or "").strip():
            bad.append("C: %s 没写『读者怎么核』" % tid)
        if not (t.get("risk") or "").strip():
            bad.append("D: %s 没写会踩到什么" % tid)
        if t.get("cat") not in cats:
            bad.append("分类: %s 的 cat=%s 不在 categories 里" % (tid, t.get("cat")))
    return (not bad), bad, {"n": len(topics), "per_cat": per_cat, "cats": sorted(cats)}


def status():
    doc = load()
    ok, bad, st = check(doc)
    print("选题库 %s：%d 条，%d 类｜%s"
          % (doc.get("version"), st["n"], len(st["cats"]), "全部可兑现" if ok else "有不可兑现项"))
    print("  分布：" + "｜".join("%s=%d" % (c, st["per_cat"].get(c, 0)) for c in st["cats"]))
    for b in bad:
        print("  ✗ " + b)
    return 0 if ok else 1


def listing():
    doc = load()
    names = {c["id"]: c["name"] for c in doc.get("categories") or []}
    for t in doc.get("topics") or []:
        print("%-4s %-10s %s" % (t["id"], names.get(t.get("cat"), "?"), t.get("title")))
        print("      证据=%s｜怎么核=%s" % ("、".join(t.get("evidence") or []),
                                       (t.get("verifiable") or "")[:46]))
    return 0


def self_test():
    """负控：造四种坏选题，各自必须判红；真数据必须判绿。"""
    cases = []
    base = {"version": "t", "forbidden_promises": ["我实测"],
            "evidence_types": {"spec": "配置表"},
            "categories": [{"id": "C1", "name": "选购"}],
            "topics": [{"id": "T1", "cat": "C1", "title": "按配置表删车",
                        "promise": "一条排除链", "evidence": ["spec"],
                        "verifiable": "官网页可核", "risk": "不能说自己开过"}]}
    cases.append(("正常选题 → 绿", check(base)[0] is True))

    b1 = json.loads(json.dumps(base))
    b1["topics"][0]["title"] = "我实测 3 万公里后的结论"
    cases.append(("负控1 承诺实测 → 红", any(x.startswith("A:") for x in check(b1)[1])))

    b2 = json.loads(json.dumps(base))
    b2["topics"][0]["evidence"] = []
    cases.append(("负控2 无证据来源 → 红", any(x.startswith("B:") for x in check(b2)[1])))

    b3 = json.loads(json.dumps(base))
    b3["topics"][0]["evidence"] = ["我的感觉"]
    cases.append(("负控3 自造证据类型 → 红", any(x.startswith("B:") for x in check(b3)[1])))

    b4 = json.loads(json.dumps(base))
    b4["topics"][0]["verifiable"] = ""
    cases.append(("负控4 没写怎么核 → 红", any(x.startswith("C:") for x in check(b4)[1])))

    b5 = json.loads(json.dumps(base))
    b5["topics"] = []
    cases.append(("负控5 空选题库 → 红（不许空着算过）", check(b5)[0] is False))

    try:
        ok, bad, _ = check(load())
        cases.append(("真数据可读且全绿", ok is True and not bad))
    except Exception as e:
        cases.append(("真数据可读且全绿", False))

    n = sum(1 for _, v in cases if v)
    for name, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", name))
    print("[self-test] %d/%d %s" % (n, len(cases), "PASS" if n == len(cases) else "FAIL"))
    return 0 if n == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.list:
        return listing()
    return status()


if __name__ == "__main__":
    sys.exit(main())
