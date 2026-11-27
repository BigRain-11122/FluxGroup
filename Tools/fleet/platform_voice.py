#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""platform_voice.py — 从真实语料里挖"平台人味"，按人群段分开。

CEO 2026-11-21「要有平台相关用户的人味」：同一个意思，B 站的人会带 [doge]、会说
「好家伙」「这不比…」，而我们的模型一条都不带。实测（20,000 行真实评论 vs 我们生成）：
  真实评论 **29% 带表情码**（[笑哭]1043 / [doge]943 / [大哭]500 / [打call]412），
  memer 段 **76% 带表情**、shallow 31%、craft_learner 15%；
  我们生成（基座 20 条、shallow 旧件 30 条）**0%**。
差距不在"会不会写字"，在提示词从没要求"像这个平台的人"。

产出（机读，供提示词/指标用）：
  cph4/fleet/social/PLATFORM-VOICE-v1.json
    segments.<seg>: emoji_top / meme_top / opener_top / particles / emoji_rate / len
    global: 同上（不分段）
  cph4/fleet/social/PLATFORM-VOICE.md（人读）

只统计、不生成；词条只取"高频且有平台特征"的，短于 2 字的、纯标点的不要，
已被 AI 腔表判定为坏句的样本不进统计（否则会把"干货/三连"当成平台人味）。

用法：
  python3 Tools/fleet/platform_voice.py
  python3 Tools/fleet/platform_voice.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
BAKED = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
OUT = os.path.join(SOCIAL, "PLATFORM-VOICE-v1.json")
MD = os.path.join(SOCIAL, "PLATFORM-VOICE.md")
sys.path.insert(0, HERE)

IMG = re.compile(r"\[[^\[\]]{1,10}\]")
# 平台口癖候选：不做词表猜，直接按语料高频 2-3 字抓，再用下面这张"无意义词"黑名单过掉
STOP = set("""这个 那个 什么 怎么 就是 可以 我们 你们 他们 自己 时候 一个 没有 不是
真的 还是 因为 所以 但是 如果 已经 现在 知道 觉得 感觉 应该 可能 这样 那样 一直
直接 一下 一点 一次 起来 出来 过来 上来 下来 东西 事情 问题 视频 评论 弹幕 支持""".split())


def mine(texts, keep=12):
    texts = [t for t in texts if t]
    n = len(texts) or 1
    emoji = Counter(m for t in texts for m in IMG.findall(t))
    emoji_rate = round(sum(1 for t in texts if IMG.search(t)) / n, 3)
    # 口癖：剥掉表情与标点后的 2-3 字高频（排除黑名单）
    grams = Counter()
    for t in texts:
        s = re.sub(r"[^\u4e00-\u9fff]", "", IMG.sub("", t))
        for L in (2, 3):
            for i in range(len(s) - L + 1):
                g = s[i:i + L]
                if g in STOP:
                    continue
                grams[g] += 1
    meme_top = [(g, c) for g, c in grams.most_common(60)
                if c >= max(3, n * 0.004)][:keep]
    opener = Counter(re.sub(r"[^\u4e00-\u9fff]", "", IMG.sub("", t))[:2]
                     for t in texts if re.sub(r"[^\u4e00-\u9fff]", "", IMG.sub("", t)))
    lens = sorted(len(IMG.sub("", t)) for t in texts)
    return {
        "n": len(texts),
        "emoji_rate": emoji_rate,
        "emoji_top": emoji.most_common(10),
        "meme_top": meme_top,
        "opener_top": opener.most_common(8),
        "len_p25": lens[len(lens) // 4] if lens else 0,
        "len_p50": lens[len(lens) // 2] if lens else 0,
        "len_p75": lens[len(lens) * 3 // 4] if lens else 0,
    }


def self_test():
    """负控：带表情的样本 emoji_rate 必须算出来；坏句样本不许进统计。"""
    import train_build as tb
    ok_img = mine(["好家伙[doge]", "这个真的[doge][笑哭]", "没有表情的一句"])["emoji_rate"]
    bad = "教程太干货了，必须三连支持！"
    dropped = bool(tb.ai_smell(bad))
    ok = abs(ok_img - 0.6667) < 0.01 and dropped
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "表情率": ok_img,
                      "坏句应被剔": dropped}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    import train_build as tb
    rows = []
    for line in open(BAKED, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        t = r.get("text") or ""
        if not t or r.get("dup_of") or tb.ai_smell(t):
            continue
        rows.append(r)
    if a.limit:
        rows = rows[:a.limit]
    byseg = {}
    for r in rows:
        byseg.setdefault(r.get("seg") or "generic", []).append(r.get("text") or "")
    segs = {}
    for s, texts in byseg.items():
        if len(texts) < 100:        # 样本太少的分段不统计，免得把个例当规律
            continue
        segs[s] = mine(texts)
    d = {"version": "v1-20261121",
         "_why": "按段统计的平台语汇与表情率；供 llm_client.platform_block 与 ai_rate 用",
         "source": "corpus/human/BAKED-v1.jsonl（已剔除 AI 腔行、去重行）",
         "global": mine([r.get("text") or "" for r in rows]),
         "segments": dict(sorted(segs.items(), key=lambda kv: -kv[1]["n"]))}
    json.dump(d, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# 平台人味（真实 B 站语料实测）", "",
          "| 段 | 样本 | 带表情 | 常用表情 | 常见口癖 | 字长 p25/50/75 |",
          "|---|---|---|---|---|---|"]
    for s, v in list(d["segments"].items())[:10]:
        md.append("| %s | %d | %.0f%% | %s | %s | %d/%d/%d |" % (
            s, v["n"], v["emoji_rate"] * 100,
            " ".join(e for e, _ in v["emoji_top"][:3]),
            "、".join(g for g, _ in v["meme_top"][:5]),
            v["len_p25"], v["len_p50"], v["len_p75"]))
    g = d["global"]
    md += ["", "## 全局", "",
           "带表情 %.0f%%｜常用 %s｜口癖 %s｜字长 %d/%d/%d" % (
               g["emoji_rate"] * 100, " ".join(e for e, _ in g["emoji_top"][:4]),
               "、".join(x for x, _ in g["meme_top"][:6]),
               g["len_p25"], g["len_p50"], g["len_p75"])]
    open(MD, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(json.dumps({"rows": len(rows), "segments": len(segs),
                      "global_emoji_rate": g["emoji_rate"],
                      "out": [os.path.relpath(OUT, ROOT), os.path.relpath(MD, ROOT)]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
