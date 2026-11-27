#!/usr/bin/env python3
"""大纲工坊：把选题变成带槽位的骨架，并校验大纲有没有塌。

为什么只给骨架不写内容：大纲的价值是**先定死结构再填字**——
章节数、每章要回答什么、依据从哪来、字数怎么分。
这些框定好了，写的时候就不会写着写着跑偏成散文。
内容仍然要人/模型来写（CEO 反复说的：不写模板腔）。

章节从哪来：选题库的 `promise` 字段本身就是用「+」分隔的三段
（例：「两种信息架构的差异 + 各自代价 + 正确层级怎么定」），
天然就是章节结构。不额外发明结构，避免大纲和选题脱节。

用法：
  gzh_outline.py --topic A01              # 出大纲骨架
  gzh_outline.py --topic A01 --out x.md   # 落盘
  gzh_outline.py --check x.md             # 校验已有大纲
  gzh_outline.py --self-test
退出码：0 通过 / 1 不通过 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOPICS = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "TOPICS-v4.json")

TARGET_WORDS = 3600          # 42 号实测正文中位 3610
OPEN_WORDS = 120
CLOSE_WORDS = 150
CHAPTER_RANGE = (2, 5)
WORD_TOL = 0.10              # 字数合计允许 ±10%

# 选题库的 evidence 白名单（大纲里的「依据」必须落在这里面）
EVIDENCE = {
    "spec": "官方参数 / 配置表",
    "price": "官方报价 / 终端价",
    "reg": "工信部公告 / 国标",
    "financial": "财报 / 招股书",
    "owner": "车主公开反馈 / 社区帖",
    "official": "官方界面截图 / 发布会",
}

# 禁承诺：出现在大纲的「依据」里，等于计划编数据
FORBIDDEN = ("我实测", "我跑了", "我拆了", "我上了举升机", "我连续跟车",
             "我把这几台车摆一起", "我开了几万公里")


def _load_topic(tid):
    doc = json.load(open(TOPICS, encoding="utf-8"))
    for t in doc.get("topics") or []:
        if t.get("id") == tid:
            return t
    raise SystemExit(f"选题库里没有 {tid}")


def chapters_of(topic):
    """从 promise 拆章；拆不出来就给三段兜底槽位（并标明是兜底）。"""
    promise = (topic or {}).get("promise") or ""
    parts = [p.strip() for p in re.split(r"[+＋]", promise) if p.strip()]
    if len(parts) >= CHAPTER_RANGE[0]:
        return parts[:CHAPTER_RANGE[1]], False
    return ["这一层要回答的问题", "为什么是这样", "代价是什么"], True


def generate(topic):
    """产出大纲 markdown。槽位写「（待填）」，不预填任何判断，避免变成模板腔。"""
    title = topic.get("title", "")
    cat = topic.get("cat", "")
    ev = topic.get("evidence") or []
    parts, fallback = chapters_of(topic)
    n = len(parts)
    per = max(200, round((TARGET_WORDS - OPEN_WORDS - CLOSE_WORDS) / n))

    ev_txt = " / ".join(f"{e}({EVIDENCE.get(e, e)})" for e in ev) or "（选题未定证据类型，写前必须补）"
    L = [f"# {title}", "",
         f"> 栏目 {cat} · 章节 {n} · 目标 {TARGET_WORDS} 字 · 证据 {ev_txt}",
         ""]
    if fallback:
        L += ["> ⚠ 该选题的 promise 没拆出章节，下面是兜底槽位，必须按实际论点改。", ""]

    L += [f"## 开篇（{OPEN_WORDS} 字）",
          f"- 落点：{topic.get('scene') or '（待填：一个具体物/一个具体动作）'}",
          "- 硬要求：首句落到具体物，禁「随着 / 在当今 / 近年来」",
          "- 禁：先给结论", ""]

    cn = "一二三四五"
    for i, p in enumerate(parts):
        L += [f"## {cn[i]}、{p}（约 {per} 字）",
              "- 论点：（待填：一句可被反驳的判断，删掉主谓宾就立不住的不算）",
              f"- 依据：{ev_txt}",
              f"- 对手：{topic.get('opponent') or '（待填）'}",
              "- 收口：这一章交出一个具体结论，不用「值得关注」收尾", ""]

    L += [f"## 收口（{CLOSE_WORDS} 字）",
          "- 给判断，不给「未来可期 / 拭目以待」",
          "- 呼应开篇那个具体物", ""]
    L += ["---", "",
          "## 写完必过的闸", "",
          "```bash",
          "python3 Tools/fleet/gzh_article_check.py --in 稿子.md   # 结构",
          "python3 Tools/fleet/gzh_fact_check.py    --in 稿子.md   # 数字有源",
          "python3 Tools/fleet/gzh_logic_check.py   --in 稿子.md   # 逻辑",
          "python3 Tools/fleet/deai_check.py        --in 稿子.md   # 去 AI 味",
          "```", ""]
    return "\n".join(L)


def check(md):
    """返回 (fails, warns, stats)。"""
    fails, warns = [], []

    m = re.search(r"^#\s+(.+)$", md, re.M)
    if not m:
        fails.append("缺 H1 标题")
    heads = re.findall(r"^##\s+(.+)$", md, re.M)
    # 章节 = 去掉开篇/收口/闸清单之后的小标题
    body_heads = [h for h in heads if not h.startswith(("开篇", "收口", "写完必过"))]
    stats = {"chapters": len(body_heads), "words": 0}

    lo, hi = CHAPTER_RANGE
    if not (lo <= len(body_heads) <= hi):
        fails.append(f"章节 {len(body_heads)} 个，不在 {lo}-{hi}（42 号实测中位 3）")

    # 小标题不许用问号（42 号实测只有 5% 用疑问句）
    for h in body_heads:
        if re.search(r"[？?]", h):
            fails.append(f"小标题用问句：{h[:24]}（实测 5%，去掉问号还能不能立住？）")

    # 每章必须三行齐全：论点 / 依据 / 收口
    blocks = re.split(r"^##\s+", md, flags=re.M)[1:]
    for b in blocks:
        name = b.split("\n", 1)[0].strip()
        if name.startswith(("开篇", "收口", "写完必过")):
            continue
        for need in ("论点", "依据"):
            if f"- {need}" not in b:
                fails.append(f"章节「{name[:20]}」缺「{need}」行")

    # 依据不能是禁承诺（写进大纲就等于计划编数据）
    for w in FORBIDDEN:
        if w in md:
            fails.append(f"大纲里出现禁承诺「{w}」——依据必须是可查的公开来源")

    # 字数预算：只数小标题里的「约 N 字」，不数开头那行「目标 3600 字」（否则重复计一次）
    heads_all = re.findall(r"^##\s+(.+)$", md, re.M)
    nums = [int(x) for h in heads_all for x in re.findall(r"(?:约\s*)?(\d{2,4})\s*字", h)]
    total = sum(nums)
    stats["words"] = total
    if nums:
        if abs(total - TARGET_WORDS) > TARGET_WORDS * WORD_TOL:
            fails.append(f"字数预算合计 {total}，偏离目标 {TARGET_WORDS} 超过 "
                         f"{int(WORD_TOL * 100)}%")
    else:
        warns.append("没有任何字数预算（写的时候容易跑偏）")

    return fails, warns, stats


GOOD_TOPIC = {
    "id": "T01", "cat": "A",
    "title": "同一块屏，为什么新势力要点三层、传统车企要五层",
    "subject": ["新势力", "传统车企"],
    "scene": "同一个「关闭车道保持」，一台点两下，一台点五下",
    "opponent": "把「功能多」当「设计好」的堆料逻辑",
    "promise": "两种信息架构的差异 + 各自代价 + 正确层级怎么定",
    "evidence": ["spec", "official"],
}


def self_test():
    fails = []
    md = generate(GOOD_TOPIC)

    f, w, st = check(md)
    if f:
        fails.append(f"正控[生成的大纲] 被判不通过: {f[:2]}")
    if st["chapters"] != 3:
        fails.append(f"正控[拆章] 应为 3 章，实际 {st['chapters']}")

    # 负控 1：小标题用问句
    bad_q = md.replace("## 一、两种信息架构的差异（", "## 一、两种信息架构差在哪？（")
    if not any("问句" in x for x in check(bad_q)[0]):
        fails.append("负控[问句小标题] 未判红")

    # 负控 2：缺「依据」行
    bad_ev = re.sub(r"(?m)^- 依据：.*$", "", md)
    if not any("依据" in x for x in check(bad_ev)[0]):
        fails.append("负控[缺依据] 未判红")

    # 负控 3：章节太少（砍掉两章只剩 1 章，落到下限 2 以下）
    bad_cnt = re.sub(r"(?ms)^## [二三]、.*?(?=^## )", "", md)
    if not any("章节" in x for x in check(bad_cnt)[0]):
        fails.append("负控[章节太少] 未判红")

    # 负控 4：字数预算严重偏离
    bad_w = md.replace(f"目标 {TARGET_WORDS} 字", "目标 12000 字")
    bad_w = re.sub(r"约 \d+ 字", "约 4000 字", bad_w)
    if not any("字数预算" in x for x in check(bad_w)[0]):
        fails.append("负控[字数偏离] 未判红")

    # 负控 5：大纲里写禁承诺
    bad_p = md.replace("- 依据：", "- 依据：我实测过，")
    if not any("禁承诺" in x for x in check(bad_p)[0]):
        fails.append("负控[禁承诺] 未判红")

    # 正控：promise 拆不出三章时要给兜底并明说
    fb = generate({**GOOD_TOPIC, "promise": "讲清楚这件事"})
    if "兜底槽位" not in fb:
        fails.append("正控[兜底] 未标明是兜底槽位")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for x in fails:
            print("  -", x, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 7/7  (正控 3 章 {st['words']} 字 / 5 类负控 / 兜底标注)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic")
    ap.add_argument("--out")
    ap.add_argument("--check", dest="chk")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    if a.chk:
        md = open(a.chk, encoding="utf-8").read()
        f, w, st = check(md)
        print(f"统计: {st}")
        for x in f:
            print(f"FAIL {x}")
        for x in w:
            print(f"WARN {x}")
        if f:
            print(f"\nFAIL {len(f)} 项", file=sys.stderr)
            return 1
        print("PASS 大纲结构成立")
        return 0

    if not a.topic:
        ap.print_help()
        return 1

    md = generate(_load_topic(a.topic))
    if a.out:
        open(a.out, "w", encoding="utf-8").write(md)
        print(f"已写 {a.out}（{len(md)} 字符）")
    else:
        print(md)
    f, _, _ = check(md)
    if f:
        print(f"\n注意：生成的大纲自身有 {len(f)} 项问题：{f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
