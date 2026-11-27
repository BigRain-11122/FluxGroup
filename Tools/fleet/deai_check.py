#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deai_check.py — 去 AI 感闸（判据来自 vendor 进仓的词库，不另编一套）。

为什么有这个闸：
2026-11-24 CEO「去找最新最好的 github 上面去 AI 感的 skill 并加载好，把评论啊回复弄好」。
skill 本身（`cph4/fleet/social/deai/` 两份 + 已装到 ~/.codely-cli/skills/）管的是**改写**，
但改写要靠模型；而我们出评是本地 4B、每条都要过。所以这里只做**判定**：
模型写完 → 本闸判 → 命中就带命中项重写一次 → 还命中就不发（宁缺不脏）。

判据来源（逐条可回溯）：
  词库 = cph4/fleet/social/deai/cn-humanizer/references/cn-ai-vocabulary.md（MIT，100+ 条，分级）
  体裁 = cph4/fleet/social/deai/qu-ai-wei/references/platform-patterns.md「B 站 AI 味」一节
本文件不硬编码词表——词表在上游 md 里，改词表不用改代码；md 读不到就报错，不许静默降级成"没命中"。

分级口径（照搬上游）：
  一级（铁证）：出现即红。上游原话"单独出现就可疑，密集出现几乎可以确认"。
  二级（密集才可疑）：一段里命中 ≥3 个才红，1-2 个只记不判。
  其余分类（宣传腔/拔高/开头/收尾/客服/连接/伪深度）：出现即记，≥1 即红（它们本来就是套话清单）。

用法：
  python3 Tools/fleet/deai_check.py --text "这句话赋能了闭环"      # 判一句
  python3 Tools/fleet/deai_check.py --stdin                       # 管道进来
  python3 Tools/fleet/deai_check.py --audit --n 30                # 审最近 30 条已发评论
  python3 Tools/fleet/deai_check.py --self-test
退出码：0 干净 / 1 命中（该改或该丢） / 2 词库不可用
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
VOCAB = os.path.join(SOCIAL, "deai", "cn-humanizer", "references", "cn-ai-vocabulary.md")
LOG = os.path.join(SOCIAL, "practice-log.jsonl")

# 段名 → 等级。段名取自上游 md 的二级标题原文，改上游就要同步改这里（不一致会报错而不是静默漏词）。
SECTIONS = {
    "一级高频词": "L1",
    "二级高频词": "L2",
    "宣传腔词汇": "propaganda",
    "意义拔高短语": "inflate",
    "万能开头套话": "opening",
    "万能收尾套话": "ending",
    "客服/机器人短语": "service",
    "过度连接词": "connector",
    "伪深度词汇": "pseudo",
}
# 硬判（出现即红）与软判（要够密才红）。依据上游口径：
# 一级=单独出现可疑；二级=一段 3 个以上可疑；开头/连接词属语气词，人也会用
# （"作为一个车主""近年来"都正常），所以按密度判，不按单点判。
SOFT = ("L2", "opening", "connector")
SOFT_MIN = {"L2": 3, "opening": 2, "connector": 2}

# 否定语境：这些词出现在命中词之前 6 字内，说明是在说"不/别/没有"，不算 AI 腔
NEG_PREFIX = ("不", "无", "没", "禁", "别", "免", "杜绝", "避免", "零")


def load_vocab(path=None):
    """解析词库 md → {grade: [term]}。读不到或一段都没解析出来就抛错（不许静默降级）。"""
    path = path or VOCAB
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    out, cur = {}, None
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("## "):
            title = s[3:].strip()
            # 上游标题带括号后缀（"一级高频词（铁证）"），精确匹配会整段漏词，
            # 而漏词的表现是"闸判定更宽松"——不报错的假绿。故按前缀匹配，多命中即取最长的那个。
            base = re.sub(r"[（(].*?[）)]", "", title).strip()
            cur = None
            for key in sorted(SECTIONS, key=len, reverse=True):
                if base == key or title.startswith(key):
                    cur = SECTIONS[key]
                    break
            if cur:
                out.setdefault(cur, [])
            continue
        if not cur:
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not cells or cells[0] in ("词", "词/短语", "过度使用", "----", "") or set(cells[0]) <= {"-"}:
                continue
            term = cells[0].strip('"“” ')
            if term and not term.startswith("("):
                out[cur].append(term)
        elif s.startswith("- "):
            term = s[2:].strip()
            term = re.sub(r"[（(][^）)]*[）)]", "", term)   # 括号里是编辑注释，不是词
            term = term.split("→")[0].strip().strip('"“” ')
            term = term.rstrip("，。,")
            if term and len(term) >= 2:
                out[cur].append(term)
    # 归一化：上游词条带占位符（"此外，..."、"具有里程碑式的意义"、"以下是关于...的介绍"），
    # 字面匹配永远打不中。取 ... 之前的部分做标记，并去掉尾部标点。
    for grade, terms in out.items():
        norm = []
        for term in terms:
            base = term.split("...")[0].rstrip("，。,.、 ")
            base = base.strip('"“” ')
            if len(base) >= 2:
                norm.append(base)
        out[grade] = sorted(set(norm))

    total = sum(len(v) for v in out.values())
    if total < 60:
        raise RuntimeError("词库解析异常：只解析到 %d 条（预期 60+），检查 %s" % (total, path))
    if "L1" not in out or len(out["L1"]) < 10:
        raise RuntimeError("一级高频词解析不足，拒绝以不完整词库判定")
    return out


def _negated(text, idx):
    head = text[max(0, idx - 6):idx]
    return any(n in head for n in NEG_PREFIX)


def check(text, vocab=None):
    """判一段中文。返回 {verdict, score, hits, why}。纯函数，自检直接注入。"""
    vocab = vocab or load_vocab()
    t = (text or "").strip()
    if not t:
        return {"verdict": "empty", "score": 0, "hits": [], "why": "空文本"}
    hits = []
    soft_cnt = {}
    for grade in ("L1", "propaganda", "inflate", "opening", "ending", "service", "connector", "pseudo"):
        for term in vocab.get(grade) or []:
            start = 0
            while True:
                i = t.find(term, start)
                if i < 0:
                    break
                if not _negated(t, i):
                    if grade in SOFT:
                        soft_cnt[grade] = soft_cnt.get(grade, 0) + 1
                    else:
                        hits.append({"grade": grade, "term": term, "at": i})
                start = i + len(term)
    l2 = [term for term in (vocab.get("L2") or []) if term in t and not _negated(t, t.find(term))]
    if len(l2) >= 3:
        hits += [{"grade": "L2", "term": x, "at": t.find(x)} for x in l2]
    for g, n in soft_cnt.items():
        if g != "L2" and n >= SOFT_MIN.get(g, 3):
            hits.append({"grade": g, "term": "%s×%d" % (g, n), "at": 0})

    # B 站体裁专节（qu-ai-wei platform-patterns.md）：假装看过、时间轴、机械玩梗、固定升华
    if re.search(r"\d{1,2}:\d{2}", t):
        hits.append({"grade": "bili-timeline", "term": "时间轴", "at": 0})
    if re.search(r"第\s*\d+\s*(秒|分钟|集|p)", t):
        hits.append({"grade": "bili-pretend", "term": "假装看过", "at": 0})
    for w in ("yyds", "绝绝子", "笑不活了", "狠狠地", "谁懂啊家人们"):
        if w in t:
            hits.append({"grade": "bili-meme", "term": w, "at": t.find(w)})

    hard = [h for h in hits if h["grade"] not in ("L2",)]
    verdict = "reject" if hard else ("warn" if l2 else "clean")
    return {"verdict": verdict, "score": len(hard) + (len(l2) if len(l2) >= 3 else 0),
            "hits": hits, "l2_count": len(l2),
            "why": ("命中 %d 处：%s" % (len(hard), "、".join("%s(%s)" % (h["term"], h["grade"])
                                                       for h in hard[:4])) if hard
                    else ("二级词 %d 个（<3 不判）" % len(l2) if l2 else "干净"))}


def audit(n=30):
    """审最近 n 条已发评论/回复，给命中率。用于判断这条线现在有多 AI。"""
    rows = []
    try:
        for line in open(LOG, encoding="utf-8"):
            if line.strip():
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("action") == "post" and d.get("text"):
                    rows.append(d)
    except FileNotFoundError:
        print("没有 practice-log")
        return 2
    rows = rows[-n:]
    vocab = load_vocab()
    bad = []
    for r in rows:
        v = check(r.get("text"), vocab)
        if v["verdict"] != "clean":
            bad.append((r.get("ts"), r.get("text"), v))
    print("审 %d 条，命中 %d 条（%.0f%%）" % (len(rows), len(bad), 100.0 * len(bad) / max(1, len(rows))))
    for ts, text, v in bad[:8]:
        print("  ✗ %s %s" % (str(ts)[11:19], text[:40]))
        print("     %s" % v["why"])
    return 0 if not bad else 1


def self_test():
    """负控：AI 腔必须红；人话必须绿；否定语境不许误杀；词库读不到必须炸而不是放行。"""
    cases = []
    v = load_vocab()
    cases.append(("词库解析 ≥60 条", sum(len(x) for x in v.values()) >= 60))
    cases.append(("一级词表 ≥10 条", len(v.get("L1") or []) >= 10))

    r1 = check("我们深耕汽车行业，赋能用户，打造一站式闭环体验。", v)
    cases.append(("负控1 AI 黑话堆砌 → reject", r1["verdict"] == "reject"))

    r2 = check("这段转场我没看懂，2 分半那里是不是剪掉了？", v)
    cases.append(("人话（具体+疑问）→ clean", r2["verdict"] == "clean"))

    r3 = check("不吹不黑，这首歌我循环了一下午。", v)
    cases.append(("否定语境不算 AI 腔", r3["verdict"] == "clean"))

    r4 = check("让我们拭目以待，未来可期。", v)
    cases.append(("万能收尾 → reject", r4["verdict"] == "reject"))

    r5 = check("以下是关于这首歌的介绍，希望以上信息对您有所帮助。", v)
    cases.append(("客服腔 → reject", r5["verdict"] == "reject"))

    r6 = check("此外，值得注意的是，与此同时，毫无疑问这很好。", v)
    cases.append(("连接词串联 ≥3 → 不算干净", r6["verdict"] != "clean"))

    r7 = check("02:15 那句和声真好听", v)
    cases.append(("时间轴（B站假装看过信号）→ 命中", any(h["grade"] == "bili-timeline" for h in r7["hits"])))

    r8 = check("", v)
    cases.append(("空文本 → empty 不算通过", r8["verdict"] == "empty"))

    # 词库缺失必须炸，不能静默返回"干净"
    try:
        load_vocab("/nonexistent/vocab.md")
        cases.append(("负控9 词库缺失必须抛错", False))
    except Exception:
        cases.append(("负控9 词库缺失必须抛错", True))

    ok = sum(1 for _, x in cases if x)
    for name, x in cases:
        print("  %s %s" % ("PASS" if x else "FAIL", name))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=None)
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.audit:
        return audit(a.n)
    if a.stdin:
        text = sys.stdin.read()
    elif a.text is not None:
        text = a.text
    else:
        print(__doc__)
        return 0
    r = check(text)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        print("[deai] %s ｜ %s" % (r["verdict"], r["why"]))
    return 0 if r["verdict"] == "clean" else 1


if __name__ == "__main__":
    sys.exit(main())
