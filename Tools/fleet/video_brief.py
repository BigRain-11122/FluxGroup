#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""video_brief.py — 给每条视频造一份"内容简报"，让评论能落在具体内容上。

CEO 2026-11-21「尤其是要看视频内容什么的」：现在的评论只看标题就写，
于是满屏"画面真好看""希望他们打好"——没有一句是指着这条片子说的。
素材其实一直都在：每条视频下面我们已经采了几百上千条真实评论，
从里面能看出观众到底在聊什么（蒙版/字幕/转场/鼓点…）。

做法（纯统计，不调模型）：
  1 取该视频全部真实评论（BAKED，已剔 AI 腔与重复）；
  2 算 2-4 字词频，去掉平台口水词（哈哈/来了/谢谢/好看…）与纯标点；
  3 留 top 6 个"内容词" + 官方简介前 100 字 → 一份简报。
  4 落盘 VIDEO-BRIEFS.json（按 url 索引，可增量刷新）。

用法
  python3 Tools/fleet/video_brief.py --build          # 全量重建
  python3 Tools/fleet/video_brief.py --url https://... # 看一条
  python3 Tools/fleet/video_brief.py --self-test
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
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
OUT = os.path.join(SOCIAL, "VIDEO-BRIEFS.json")
sys.path.insert(0, HERE)

IMG = re.compile(r"\[[^\[\]]{1,10}\]")
# 平台口水词：出现在几乎每条视频下，对"这条片子讲了什么"零信息量
WATER = set("""哈哈 哈哈哈 来了 谢谢 好看 支持 喜欢 感谢 分享 真的 什么 这个 那个 这么
就是 可以 不是 没有 感觉 觉得 应该 还是 一直 直接 已经 现在 可能 因为 所以 但是
哈哈 哈哈哈哈 三连 收藏 视频 怎么 一 二 三 我 你 他 她 它 我们 你们 他们 一 下 点 个 次 说 看 听 想""".split())


def brief_from(texts, desc="", keep=6):
    """从一组真实评论里抽"观众在聊什么"。"""
    grams = Counter()
    for t in texts:
        s = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", IMG.sub("", t or ""))
        for L in (2, 3, 4):
            for i in range(len(s) - L + 1):
                g = s[i:i + L]
                if L == 2 and g in WATER:
                    continue
                if g in WATER:
                    continue
                grams[g] += 1
    # 拉丁词必须整词出现：2026-11-21 实测「BLG」会派生「LG」「BL」、「video」派生「eo」，
    # 这些在中文语境里不是词。判据=该拉丁串在原文里两侧不能紧邻字母。
    def _latin_whole(g, texts):
        if not re.fullmatch(r"[A-Za-z0-9]+", g):
            return True
        pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(g) + r"(?![A-Za-z0-9])")
        return any(pat.search(t or "") for t in texts[:2000])

    # 去掉"滑窗碎片"：2026-11-21 实测 naive 分数会吐出「版转/场好/好丝」这类
    # 只存在于「蒙版转场好丝滑」中间的片段。判据=若存在更长的候选把 g 夹在**中间**
    # （既不是前缀也不是后缀），g 就是碎片；而「蒙版」「转场」是前缀/后缀，保留。
    # 频次门槛跟着样本量走：真实视频几百条评论用 5，小样本（自检）降到 2，
    # 否则"评论太少"会被误判成"没有内容词"。
    min_freq = max(2, min(5, len(texts) // 10))
    cand = [(g, c) for g, c in grams.most_common(200)
            if c >= min_freq and 2 <= len(g) <= 4 and _latin_whole(g, texts)]
    frag = set()
    for g, c in cand:
        for g2, c2 in cand:
            if len(g2) <= len(g) or g not in g2:
                continue
            # ①中间片段（版转/场好）：只要被更长词夹在中间就不是词
            if c2 >= c * 0.6 and not (g2.startswith(g) or g2.endswith(g)):
                frag.add(g)
                break
            # ②冗余短词（工作流 出现 100 次时，"作流/求工"几乎同频 → 它只是切片）
            if c2 >= c * 0.8:
                frag.add(g)
                break
    top = []
    for g, c in cand:
        if g in frag:
            continue
        top.append((g, c))
        if len(top) >= keep:
            break
    # 简介只留第一句前 60 字：往期列表/联系方式对"这条讲了什么"没信息量，
    # 而且截断在句中是噪音（实测提示词里挂了一串"往期剪映教程…av"）。
    d = re.split(r"[\n。！？]", (desc or "").strip())[0][:60]
    return {
        "topics": [g for g, _ in top],
        "desc": d.strip(),
        "n": len(texts),
    }


def build(limit_videos=0):
    import train_build as tb
    try:
        tv = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        tv = {}
    by = {}
    for line in open(BAKED, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        u = (r.get("thread") or "").strip()
        if not u:
            continue
        t = r.get("text") or ""
        if not t or r.get("dup_of") or tb.ai_smell(t):
            continue
        by.setdefault(u, []).append(t)
    out = {}
    urls = [u for u in by if len(by[u]) >= 20]
    if limit_videos:
        urls = urls[:limit_videos]
    for u in urls:
        meta = tv.get(u) or {}
        b = brief_from(by[u], meta.get("desc") or "", keep=6)
        b["title"] = (meta.get("title") or "")[:60]
        b["has_title"] = bool(meta.get("title"))
        out[u] = b
    json.dump({"version": "v1-20261121", "briefs": out}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    no_title = sum(1 for v in out.values() if not v["has_title"])
    return {"videos": len(out), "no_title": no_title,
            "avg_topics": round(sum(len(v["topics"]) for v in out.values()) / max(1, len(out)), 1),
            "file": os.path.relpath(OUT, ROOT)}


def get(url, d=None):
    d = d or json.load(open(OUT, encoding="utf-8"))
    return (d.get("briefs") or {}).get((url or "").strip())


def block(url, d=None):
    """提示词用的一句话简报。"""
    b = get(url, d)
    if not b:
        return ""
    bits = []
    if b.get("desc"):
        bits.append("简介：" + b["desc"])
    if b.get("topics"):
        bits.append("观众在聊：" + "、".join(b["topics"][:4]))
    return ("\n这条视频的内容——" + "；".join(bits) + "。评论要指着具体内容说，别泛泛夸。") if bits else ""


def self_test():
    """负控：口水词必须被滤掉；具体内容词必须留下。"""
    texts = ["蒙版转场好丝滑啊", "这个蒙版怎么做的", "字幕也跟上了", "哈哈哈哈"]
    b = brief_from(texts)
    ok1 = any("蒙版" in t for t in b["topics"])
    ok2 = not any(t in WATER for t in b["topics"])
    ok = ok1 and ok2
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "留下内容词": ok1,
                      "滤掉口水词": ok2, "topics": b["topics"]}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--url", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.build:
        print(json.dumps(build(), ensure_ascii=False, indent=1))
        return 0
    if a.url:
        print(json.dumps(get(a.url), ensure_ascii=False, indent=1))
        return 0
    print("用法：--build / --url <视频地址> / --self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
