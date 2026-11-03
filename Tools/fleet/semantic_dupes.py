#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""semantic_dupes.py - 用向量相似度找"同一件事被派了两张卡"。

为什么不用大模型（2026-11-03 本机实测，同一批 20 对真卡）：
    qwen3:4b-instruct   召回 2/10 · 特异 10/10 · 0.45s/对
    qwen3.5:4b          召回 4/10 · 特异 10/10 · 0.70s/对
    nomic-embed-text    召回 9/10 · 特异 10/10 · 0.08s/对
小模型在这类"是不是同一件事"的判断上倾向一律答"不同"，召回崩掉；
向量法又快又准，所以语义去重交给 embedding，不交给生成模型。

用法：
    python3 Tools/fleet/semantic_dupes.py            # 扫队列，打印相似组
    python3 Tools/fleet/semantic_dupes.py --th 0.70  # 提高阈值（更保守）
退出码：0 = 扫完（有无重复都算成功），1 = 连不上 embedding 服务
"""
import argparse
import re
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
QUEUE = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
DEFAULT_TH = 0.64          # 实测最佳：召回 9/10、特异 10/10


def embed(text):
    body = json.dumps({"model": MODEL, "prompt": text[:800]}).encode()
    req = urllib.request.Request(URL + "/api/embeddings", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["embedding"]


def cos(a, b):
    s = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return s / (na * nb) if na and nb else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--th", type=float, default=DEFAULT_TH)
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    rows = []
    if os.path.exists(QUEUE):
        for ln in open(QUEUE, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("title"):
                rows.append(r)
    if len(rows) < 2:
        print("SEMANTIC-DUPES rows=%d groups=0" % len(rows))
        return 0

    try:
        vecs, meta = [], []
        for r in rows:
            try:
                # 工序化标题带 "[线名（工序链）] " 前缀，模板化文本会把不同线的卡拉到
                # 同一个相似簇（实测 0.64 阈值下把配音质检和回测并成一堆）。先剥前缀。
                t = re.sub(r"^\s*\[[^\]]*\]\s*", "", r["title"])
                vecs.append(embed(t))
                meta.append(r)
            except Exception as e:
                print("skip %s (%s)" % (r.get("id"), str(e)[:60]))
    except Exception as e:
        print("FAIL embedding service: %s" % e)
        return 1

    # 只比较状态未了结的卡，避免把"历史重复"当成本轮问题
    live = [i for i, r in enumerate(meta) if r.get("state") in ("OPEN", "RUNNING", "READY")]
    groups, seen = [], set()
    for i in live:
        g = [i]
        for j in live:
            if j <= i or j in seen:
                continue
            if cos(vecs[i], vecs[j]) >= a.th:
                g.append(j)
        if len(g) > 1:
            for k in g:
                seen.add(k)
            groups.append(g)

    print("SEMANTIC-DUPES rows=%d live=%d groups=%d th=%.2f"
          % (len(rows), len(live), len(groups), a.th))
    out = []
    for g in groups:
        print("- 可能同一件事（%d 张）：" % len(g))
        for k in g:
            r = meta[k]
            print("    %-34s %-9s %s" % (r.get("id"), r.get("state"), (r.get("title") or "")[:52]))
            out.append({"id": r.get("id"), "title": r.get("title"), "state": r.get("state")})
    if a.json:
        json.dump({"groups": [[meta[k]["id"] for k in g] for g in groups]},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())