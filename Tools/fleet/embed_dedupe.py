#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""embed_dedupe.py - 用本机向量模型给在办卡做语义判重。

为什么（2026-11-09 CEO「用本地算力赋能机队」）：队列 1600+ 张，历史上同题卡反复出现；
字符串判重挡不住"换个说法"。本机 qwen3-embedding 1024 维、0.08s/对，正好干这个。
只打标不自动取消：命中写 duplicate_of + note，由派单侧决定。

用法：
  python3 Tools/fleet/embed_dedupe.py            # 只报告
  python3 Tools/fleet/embed_dedupe.py --apply    # 写回 duplicate_of
"""
import argparse
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
EMBED = os.environ.get("EMBED_URL", "http://127.0.0.1:11434") + "/api/embed"
MODEL = "qwen3-embedding:0.6b"
ACTIVE = ("OPEN", "RUNNING", "READY")


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        pass
    return out


def embed(texts):
    req = urllib.request.Request(EMBED, data=json.dumps({"model": MODEL, "input": texts}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["embeddings"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.93)
    a = ap.parse_args()

    seen_ids, cards = set(), []
    for r in rows(QUEUE) + rows(BACKLOG):
        if r.get("state") in ACTIVE and r.get("id") and r["id"] not in seen_ids:
            seen_ids.add(r["id"])
            cards.append(r)
    if len(cards) < 2:
        print("active cards < 2")
        return 0
    texts = [(r.get("title") or "") + " " + (r.get("prompt") or "")[:200] for r in cards]
    vecs = embed(texts[:64])  # 单批上限，活跃卡通常 <64
    import math
    pairs = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            dot = sum(x * y for x, y in zip(vecs[i], vecs[j]))
            ni = math.sqrt(sum(x * x for x in vecs[i])) or 1
            nj = math.sqrt(sum(x * x for x in vecs[j])) or 1
            sim = dot / (ni * nj)
            if sim >= a.threshold:
                pairs.append((round(sim, 3), cards[i]["id"], cards[j]["id"]))
    pairs.sort(reverse=True)
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "active": len(cards),
               "pairs": len(pairs)},
              open(os.path.join(ROOT, "cph4", "fleet", "state", "embed-dedupe.json"), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)
    # 用完即卸：向量模型占 4.8GB，不常驻
    try:
        req = urllib.request.Request(EMBED.replace("/api/embed", "/api/generate"),
            data=json.dumps({"model": MODEL, "keep_alive": 0}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=30).read()
    except Exception:
        pass
    print("active=%d pairs>=%.2f: %d" % (len(cards), a.threshold, len(pairs)))
    for s, i, j in pairs[:12]:
        print("%.3f  %s  <->  %s" % (s, i, j))
    if a.apply and pairs:
        sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
        import fleet_lane as fl
        upd = []
        seen = set()
        for s, i, j in pairs:
            if j in seen:
                continue
            seen.add(j)
            for r in cards:
                if r["id"] == j:
                    r["duplicate_of"] = i
                    r["duplicate_sim"] = s
                    r["note"] = "semantic-duplicate of %s (%.3f)" % (i, s)
                    upd.append(r)
        if upd:
            fl.merge_jsonl(QUEUE, [u for u in upd if u in rows(QUEUE)], mirror=False)
            fl.merge_jsonl(BACKLOG, [u for u in upd if u in rows(BACKLOG)], mirror=False)
        print("tagged", len(upd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
