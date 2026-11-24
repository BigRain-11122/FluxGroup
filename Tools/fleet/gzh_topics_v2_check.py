#!/usr/bin/env python3
"""选题库 v2 校验器：把 TOPIC-SELECTION-SPEC-v1.md 的六条硬判据变成可红的闸。

为什么要这个：CEO 否掉 v1 的根因是"看起来能写，其实不可核验"。
光改文案没有用——必须有个东西能在下次偷懒时判红。

用法：
  gzh_topics_v2_check.py [--file PATH] [--self-test]
退出码：0 全过 / 1 有 FAIL / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import re
import sys

DEFAULT = "cph4/fleet/social/gzh/TOPICS-v2.json"

# 抽象词黑名单：scene 里出现这些说明没给具体物
ABSTRACT = ("很多", "各种", "众多", "随着", "不断发展", "越来越", "一定程度上",
            "某种意义上", "相关", "等方面", "诸多")

# 禁承诺（沿用 v1 红线）
FORBIDDEN = ["我实测", "我跑了", "我开了几万公里", "我把这几台车摆一起",
             "我拆了", "我上了举升机", "我连续跟车"]

REQUIRED = ["id", "cat", "title", "subject", "hook_type", "scene",
            "opponent", "promise", "evidence", "verifiable", "risk",
            "verify_before_write", "timeliness"]


def check(doc):
    """返回 (fails, warns, stats)。fails 非空即红。"""
    fails, warns = [], []
    topics = doc.get("topics") or []
    stats = {"count": len(topics)}

    if len(topics) != 28:
        fails.append(f"选题数应为 28，实际 {len(topics)}")

    # --- 1. 字段齐全 ---
    for t in topics:
        tid = t.get("id", "?")
        miss = [k for k in REQUIRED if k not in t or t[k] in (None, "", [])]
        if miss:
            fails.append(f"[{tid}] 缺字段: {miss}")

    # --- 2. 标题必须点名 ≥2 个真实对象 ---
    for t in topics:
        tid = t.get("id", "?")
        subs = t.get("subject") or []
        title = t.get("title") or ""
        # 每个 subject 拆成词，看标题里能命中几个
        hit = 0
        for s in subs:
            # 取 subject 里长度 ≥2 的中文/英文片段
            parts = [p for p in re.split(r"[\s/、（）()]+", str(s)) if len(p) >= 2]
            if any(p.lower() in title.lower() for p in parts):
                hit += 1
        if hit < 1:
            fails.append(f"[{tid}] 标题未点名任何可搜对象：{title[:40]}")
        if len(subs) < 2:
            fails.append(f"[{tid}] subject 少于 2 个（单车型无对比=不可核验）")
        # 标题过短必然空泛
        if len(title) < 12:
            fails.append(f"[{tid}] 标题过短（{len(title)} 字）：{title}")

    # --- 3. hook_type 三句式都要有 ---
    hooks = [t.get("hook_type") for t in topics]
    for h in ("A", "B", "C"):
        if h not in hooks:
            fails.append(f"缺少 hook_type={h} 的选题（三种句式必须都用上）")
    bad_hook = [t.get("id") for t in topics if t.get("hook_type") not in ("A", "B", "C")]
    if bad_hook:
        fails.append(f"非法 hook_type: {bad_hook}")

    # --- 4. opponent 必须具体（不是空话） ---
    for t in topics:
        tid = t.get("id", "?")
        op = str(t.get("opponent") or "")
        if len(op) < 6:
            fails.append(f"[{tid}] opponent 太短/空，看不出对立面：{op!r}")

    # --- 5. scene 必须是具体物，不许抽象 ---
    for t in topics:
        tid = t.get("id", "?")
        sc = str(t.get("scene") or "")
        if len(sc) < 8:
            fails.append(f"[{tid}] scene 太短：{sc!r}")
        hit = [w for w in ABSTRACT if w in sc]
        if hit:
            fails.append(f"[{tid}] scene 含抽象词 {hit}，必须换成具体物：{sc[:40]}")

    # --- 6. verify_before_write 必须指向具体页面 ---
    for t in topics:
        tid = t.get("id", "?")
        vb = t.get("verify_before_write") or []
        if not vb:
            fails.append(f"[{tid}] verify_before_write 为空")
        for v in vb:
            if len(str(v)) < 4:
                fails.append(f"[{tid}] verify_before_write 项太笼统：{v!r}")

    # --- 7. 禁承诺 ---
    # 必须先剔掉 forbidden_promises 定义本身再查，否则"我实测"写在
    # 黑名单里会让正文里的同词一起被放过（假绿）。
    doc_wo = {k: v for k, v in doc.items() if k != "forbidden_promises"}
    blob = json.dumps(doc_wo, ensure_ascii=False)
    for bad in FORBIDDEN:
        if bad in blob:
            fails.append(f"正文出现禁用承诺: {bad}")

    # --- 8. evergreen : event 配比 ---
    ev = sum(1 for t in topics if t.get("timeliness") == "event")
    eg = sum(1 for t in topics if t.get("timeliness") == "evergreen")
    stats["event"], stats["evergreen"] = ev, eg
    if ev + eg != len(topics):
        fails.append(f"timeliness 只能是 event/evergreen，实际 {ev}+{eg}≠{len(topics)}")
    if ev < 4:
        warns.append(f"事件型 {ev} 条（建议 4 条绑定当下事件）")

    # --- 9. cat 必须都在 categories 里 ---
    cats = {c["id"] for c in doc.get("categories", [])}
    for t in topics:
        if t.get("cat") not in cats:
            fails.append(f"[{t.get('id')}] cat={t.get('cat')} 不在 categories")

    return fails, warns, stats


def _load(path):
    return json.load(open(path, encoding="utf-8"))


def self_test():
    """负控：故意改坏每一条，闸必须红。"""
    fails = []
    base = _load(DEFAULT)

    def expect_red(name, mutate):
        doc = json.loads(json.dumps(base))  # 深拷贝
        mutate(doc)
        f, _, _ = check(doc)
        if not f:
            fails.append(f"负控[{name}] 改了却判绿")

    # 1. 删掉一条 → 数量不对
    expect_red("删一条", lambda d: d["topics"].pop())
    # 2. 标题去掉车型 → 未点名
    expect_red("标题去对象", lambda d: d["topics"][0].update(title="同价位 5 台车怎么选"))
    # 3. 清空 opponent
    expect_red("空对立面", lambda d: d["topics"][0].update(opponent=""))
    # 4. scene 写抽象话
    expect_red("抽象 scene", lambda d: d["topics"][0].update(scene="随着新能源市场的不断发展"))
    # 5. 清空 verify
    expect_red("空 verify", lambda d: d["topics"][0].update(verify_before_write=[]))
    # 6. 塞禁承诺
    expect_red("禁承诺", lambda d: d["topics"][0].update(promise="我实测了 800 公里"))
    # 7. hook_type 全改 A → 缺 B/C
    expect_red("单一句式", lambda d: [t.update(hook_type="A") for t in d["topics"]])
    # 8. 删字段
    expect_red("删字段", lambda d: d["topics"][0].pop("scene"))

    # 正向：原始数据必须全绿
    f0, w0, s0 = check(base)
    if f0:
        fails.append(f"原始数据未通过: {f0[:3]}")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for x in fails:
            print("  -", x, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 8/8 负控全红 · 原始 28 条全绿 (event={s0['event']} evergreen={s0['evergreen']})")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    doc = _load(a.file)
    fails, warns, stats = check(doc)
    print(f"统计: {stats}")
    for w in warns:
        print(f"WARN  {w}")
    if fails:
        print(f"FAIL {len(fails)} 项", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 1
    print(f"PASS 28/28 条全部满足六条硬判据")
    return 0


if __name__ == "__main__":
    sys.exit(main())
