#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""corpus_bake.py - 用多核把全量语料"烤"一遍：品味五维 + 段位 + 近重复。

为什么要有它（CEO 2026-11-19「cpu 和 gpu 都利用到位了吗」）：
实测 CPU 只忙 17-33%，而语料侧有一件一直没人干的活——47,968 行只被"过闸筛选"过，
没有逐行打分、没有段位标注、也没做近重复。这三件都是纯 CPU、可并行、且直接决定
训练集质量（去近重复能减少模型背句子，段位标注决定按段取料）。

输出：
  cph4/fleet/social/corpus/human/BAKED-v1.jsonl   每行带 seg/taste/verdict/dup_of
  cph4/fleet/social/corpus/human/BAKED-stats.json 分布与去重统计

自检（负控）：
  - 一字不差的重复必须被抓到；只差标点的也必须抓到
  - 内容不同的句子不许被误判成重复
  - 段位标注必须与 segments.classify 一致（同一套 spec，不另立口径）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
CORPUS = os.path.join(SOCIAL, "corpus", "human", "own_collected.jsonl")
# 2026-11-20 闭环：实战写出去、过完所有闸的稿子也是语料——而且是最贴我们目标的分布。
PRACTICE = os.path.join(SOCIAL, "corpus", "human", "own_practice.jsonl")
SOURCES = [CORPUS, PRACTICE]
OUT = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
STATS = os.path.join(SOCIAL, "corpus", "human", "BAKED-stats.json")

sys.path.insert(0, HERE)
_NORM = re.compile(r"[\s\W_]+", re.U)


def shingles(text, k=6):
    """字符 k-gram 集合：中文按字切，比词切更抗同义替换（无分词器依赖）。"""
    t = _NORM.sub("", text or "")
    if len(t) < k:
        return {t} if t else set()
    return {t[i:i + k] for i in range(len(t) - k + 1)}


def near_dup(a, b, jaccard=0.82):
    """近重复：k-gram 集合 Jaccard 阈值。标点/空格差异会被归一化吃掉。"""
    sa, sb = shingles(a), shingles(b)
    if not sa or not sb:
        return False
    inter = len(sa & sb)
    return inter / float(len(sa | sb)) >= jaccard


_CT = None
_SG = None
_SPEC = None


def _warm():
    """每个 worker 只加载一次打分器与段位 spec。

    2026-11-19 实锚：初版在 bake_one 里逐行 `import` + `load_spec()`（每行读一次 JSON），
    结果父进程 100% 卡在序列化、只有 1 个 worker 干活，整机 CPU 才 23%——
    "写了 Pool" 不等于并行。
    """
    global _CT, _SG, _SPEC
    sys.path.insert(0, HERE)
    import comment_taste as ct
    import segments as sg
    _CT, _SG, _SPEC = ct, sg, sg.load_spec()


def bake_one(text):
    """单行加工：只收文本、只回小元组（别把整行 dict 塞进 IPC）。"""
    t = text or ""
    seg = _SG.classify(t, _SPEC)
    s = _CT.score(t, seg=seg["primary"])
    return (seg["primary"], s.get("total"), s.get("verdict"),
            s.get("human"), s.get("voice"))


def _feed_practice():
    """烘焙前先把实战稿导回语料（闭环：实战→训练）。失败不影响烘焙。"""
    try:
        import practice_feed
        practice_feed.main()
    except Exception as e:
        print("[bake] 实战稿导流失败（跳过）：%s" % e)


def run(workers, limit=0):
    _feed_practice()
    rows, seen = [], set()
    for src in SOURCES:
        if not os.path.exists(src):
            continue
        for line in open(src, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            h = r.get("h") or (r.get("text") or "")[:40]
            if h in seen:
                continue
            seen.add(h)
            rows.append(r)
    if limit:
        rows = rows[:limit]
    t0 = time.time()
    texts = [(r.get("text") or "") for r in rows]
    with Pool(processes=workers, initializer=_warm) as pool:
        raw = pool.map(bake_one, texts, chunksize=400)
    meta = [{"seg": x[0], "taste": x[1], "verdict": x[2], "human": x[3], "voice": x[4]}
            for x in raw]
    bake_s = time.time() - t0

    # 近重复：按段分桶后再比（全量两两比是 O(n²)，分桶后每桶内按长度邻域比）
    # 分桶要"足够窄"：初版只按 (段, 长度//8) 分，generic 一桶上千行 → 两两比是
    # 单核 O(n²)，把并行收获全吃掉（实测跑了 2 分钟没出结果）。加"首 6 字"后
    # 每桶通常个位数，比较量降三个数量级。
    buckets = {}
    for i, m in enumerate(meta):
        t = _NORM.sub("", rows[i].get("text") or "")
        buckets.setdefault((m["seg"], len(t) // 8, t[:6]), []).append(i)
    dup_of = {}
    for _, idxs in buckets.items():
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                i, j = idxs[a], idxs[b]
                if i in dup_of or j in dup_of:
                    continue
                if near_dup(rows[i].get("text"), rows[j].get("text")):
                    dup_of[j] = rows[i].get("text", "")[:20]

    with open(OUT, "w", encoding="utf-8") as f:
        for i, r in enumerate(rows):
            rec = dict(r)
            rec.update(meta[i])
            if i in dup_of:
                rec["dup_of"] = dup_of[i]
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    segs = Counter(m["seg"] for m in meta)
    verd = Counter(m["verdict"] for m in meta)
    st = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "rows": len(rows), "workers": workers,
          "bake_sec": round(bake_s, 1), "rows_per_sec": round(len(rows) / max(bake_s, 1e-6), 1),
          "near_dup": len(dup_of), "segments": dict(segs.most_common()),
          "verdicts": dict(verd)}
    json.dump(st, open(STATS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return st


def self_test():
    ok, bad = [], []

    def chk(n, c):
        (ok if c else bad).append(n)

    a = "这个转场太丝滑了，学废了"
    chk("一字不差判重复", near_dup(a, a))
    chk("只差标点也判重复", near_dup(a, "这个转场太丝滑了，学废了！！"))
    chk("不同内容不误判", not near_dup(a, "求BGM名字，找了半天没找到"))
    chk("完全不同不误判", not near_dup("这段调色很稳", "第三集什么时候更"))
    _warm()
    r = bake_one("老师这个转场怎么做的，我零基础看不懂")
    r = {"seg": r[0], "taste": r[1]}
    chk("段位与分类器一致", r["seg"] == "beginner")
    chk("品味分有值", isinstance(r["taste"], int))
    for n in ok:
        print("  PASS", n)
    for n in bad:
        print("  FAIL", n)
    print("[bake] self-test %d/%d" % (len(ok), len(ok) + len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 1))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    st = run(a.workers, a.limit)
    print("[bake] %d 行 / %d workers / %.1fs（%.0f 行/秒）｜ 近重复 %d 条"
          % (st["rows"], st["workers"], st["bake_sec"], st["rows_per_sec"], st["near_dup"]))
    print("[bake] 段位 Top5 %s" % list(st["segments"].items())[:5])
    print("[bake] 判词 %s" % st["verdicts"])
