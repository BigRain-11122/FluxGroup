#!/usr/bin/env python3
"""practice_feed.py — 把实战写出去、过完全部闸的稿子导回语料（闭环的"实战→训练"一段）。

为什么必须做：实战稿是我们自己在这个号、这个人设下真发出去的内容，
它已经过了品味闸/合规闸/长度闸，分布最贴目标；不用它，等于每次训练都从别人的评论重新猜。

规则：
- 只收 `action=post` 且 `ok` 为真（真发出去的）；
- 去重（同文本只收一次）；带上 seg（用 segments 分类）与 thread（视频地址）；
- 被闸拒的稿不进正样本，单独记到 negatives.jsonl 供规则分析（mlx 无 DPO，不能直接做偏好训练）。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
LOG = os.path.join(SOCIAL, "practice-log.jsonl")
OUT = os.path.join(SOCIAL, "corpus", "human", "own_practice.jsonl")
NEG = os.path.join(SOCIAL, "corpus", "human", "negatives.jsonl")
sys.path.insert(0, HERE)


def h_of(t):
    return hashlib.md5((t or "").encode()).hexdigest()[:16]


def main():
    import segments as sg
    spec = sg.load_spec()
    got = neg = 0
    seen = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            if line.strip():
                seen.add(json.loads(line).get("h"))
    rows = []
    for line in open(LOG, encoding="utf-8"):
        if line.strip():
            rows.append(json.loads(line))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as fo, open(NEG, "a", encoding="utf-8") as fn:
        for r in rows:
            t = (r.get("text") or "").strip()
            if not t:
                continue
            ok = str(r.get("ok")).lower() == "true"
            if r.get("action") == "post" and ok:
                h = h_of(t)
                if h in seen:
                    continue
                seen.add(h)
                seg = sg.classify(t, spec)["primary"]
                fo.write(json.dumps({"h": h, "text": t, "src": "own_practice",
                                     "license": "自有账号实际发布（已过全部闸）", "use": "train",
                                     "kind": "其他", "seg": seg,
                                     "thread": r.get("video") or "", "ts": r.get("ts")},
                                    ensure_ascii=False) + "\n")
                got += 1
            elif r.get("action") == "fail" and r.get("why"):
                fn.write(json.dumps({"text": t or "", "why": str(r.get("why"))[:200],
                                     "ts": r.get("ts")}, ensure_ascii=False) + "\n")
                neg += 1
    print("[feed] 实战稿入语料 %d 条 → %s" % (got, OUT))
    print("[feed] 被拒稿记负样本 %d 条 → %s" % (neg, NEG))
    return 0


if __name__ == "__main__":
    sys.exit(main())
