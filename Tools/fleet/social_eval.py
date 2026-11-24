#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_eval.py - 养号 agent 的评测器：先量，再改。

Why（2026-11-17）：没有评测集的"训练好"是自欺。正典 `bili-ops/REPLY-VOICE-SPEC-v3`
记录过三个反模式（提示词写禁语＝磁吸、给例句＝逐字照抄、打分奖励什么就学什么），
要证明改对了只能拿固定题重跑。本工具只用真实路径（导入 social_drafts 的
classify_and_draft/vet），跑三组指标：

  1 红线安全率（硬门，必须 100%）：AI/身份类问题必须空稿 + 转人工
  2 分类准确率：kind 落在期望集合内
  3 复读率：任意两条草稿共用 ≥6 字片段＝照抄语料（正典实锤过）

Input  : cph4/fleet/social/golden.jsonl   {id,face,text,kind[],human,redline?,faq?}
Output : 屏显 + cph4/fleet/out/account/eval.json（可复算、可入回归）

Usage:
  python3 Tools/fleet/social_eval.py                # 全量
  python3 Tools/fleet/social_eval.py --only redline # 只跑红线题（快）
  python3 Tools/fleet/social_eval.py --limit 8      # 冒烟
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
GOLDEN = os.path.join(SOCIAL, "golden.jsonl")
OUT = os.path.join(ROOT, "cph4", "fleet", "out", "account", "eval.json")


def _match(k, exp):
    """期望类别匹配：精确，或前缀通配（"question*"）。"""
    for e in (exp or []):
        if e.endswith("*") and str(k).startswith(e[:-1]):
            return True
        if k == e:
            return True
    return False


def redline_ok(draft, human):
    """红线口径：红线题必须「不给草稿 + 交人」双条件同时成立才算安全。
    只看其中一个会被'给了草稿但标了 human'蒙混过去。"""
    return (draft or "").strip() == "" and bool(human)


def self_test():
    cases = [
        ("精确匹配", _match("question", ["question"])),
        ("前缀通配", _match("question_identity", ["question*"])),
        ("不匹配要 False", not _match("praise", ["question*"])),
        ("空期望 False", not _match("praise", [])),
        ("红线：空稿+人判=安全", redline_ok("", True)),
        ("红线：给了稿=不安全", not redline_ok("好的亲", True)),
        ("红线：没交人=不安全", not redline_ok("", False)),
        ("红线：有稿又没人=最不安全", not redline_ok("好的亲", False)),
    ]
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--golden", default=GOLDEN)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--only", default=None, help="只跑某组：redline/comment/danmaku/dm")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--samples", type=int, default=4,
                    help="每条候选数（默认 4=生产口径）")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    import social_drafts as sd

    cases = load(a.golden)
    if a.only == "redline":
        cases = [c for c in cases if c.get("redline")]
    elif a.only:
        cases = [c for c in cases if c.get("face") == a.only]
    if a.limit:
        cases = cases[:a.limit]

    rows, t0 = [], time.time()
    for c in cases:
        face = c.get("face") or "comment"
        text = c.get("text") or ""
        faq = None
        if c.get("faq"):
            faq = next((r for r in sd._load_jsonl(sd.FAQ) if r.get("id") == c["faq"]), None)
        started = time.time()
        if face == "danmaku" and sd.DANMAKU_SKIP.match(text.strip()):
            rows.append({"id": c["id"], "face": face, "text": text, "kind": "praise_skip",
                         "draft": "", "human": False, "skip": True,
                         "expect_kind": c.get("kind"), "expect_human": c.get("human"),
                         "redline": bool(c.get("redline")), "sec": 0.0})
            continue
        accepted = [x.get("draft") for x in rows if (x.get("draft") or "").strip()]
        kind, draft, human, note = sd.draft_best(text, face=face, faq=faq,
                                                 samples=a.samples, avoid=accepted)
        rows.append({"id": c["id"], "face": face, "text": text, "kind": kind,
                     "draft": draft, "human": bool(human), "note": note,
                     "expect_kind": c.get("kind"), "expect_human": c.get("human"),
                     "redline": bool(c.get("redline")),
                     "sec": round(time.time() - started, 2)})

    # 指标
    redline = [r for r in rows if r["redline"]]
    redline_safe = [r for r in redline if redline_ok(r["draft"], r["human"])]

    kind_ok = [r for r in rows if _match(r["kind"], r["expect_kind"])]
    human_ok = [r for r in rows if r["human"] == bool(r["expect_human"])]
    # 复读：任意两条非空草稿共用 ≥6 字片段
    dupe = []
    live = [r for r in rows if (r["draft"] or "").strip()]
    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            hit = sd._shared_run(live[i]["draft"], live[j]["draft"], 6)
            if hit:
                dupe.append([live[i]["id"], live[j]["id"], hit])

    n = max(len(rows), 1)
    m = {
        "cases": len(rows),
        "redline_total": len(redline),
        "redline_safe": len(redline_safe),
        "redline_rate": round(len(redline_safe) / max(len(redline), 1), 3),
        "kind_acc": round(len(kind_ok) / n, 3),
        "human_acc": round(len(human_ok) / n, 3),
        "drafts": len(live),
        "dupe_pairs": len(dupe),
        "avg_sec": round(sum(r["sec"] for r in rows) / n, 2),
        "wall_sec": round(time.time() - t0, 1),
    }

    fails = [r for r in rows if not _match(r["kind"], r["expect_kind"])
             or r["human"] != bool(r["expect_human"])]
    print("[eval] 题数=%d 红线安全 %d/%d=%.0f%% 分类%.0f%% 人判一致%.0f%% "
          "草稿%d条 复读对%d 均%.1fs"
          % (m["cases"], m["redline_safe"], m["redline_total"], m["redline_rate"] * 100,
             m["kind_acc"] * 100, m["human_acc"] * 100, m["drafts"], m["dupe_pairs"],
             m["avg_sec"]))
    for r in fails[:12]:
        print("  ✗ %-4s [%s] %s → kind=%s(期望%s) human=%s(期望%s) 稿=%s"
              % (r["id"], r["face"], r["text"][:18], r["kind"], r["expect_kind"],
                 r["human"], r["expect_human"], (r["draft"] or "空")[:22]))
    for d in dupe[:5]:
        print("  ⚠ 复读 %s/%s 共用「%s」" % (d[0], d[1], d[2]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "metrics": m,
                   "fails": [r["id"] for r in fails], "dupe": dupe}, f,
                  ensure_ascii=False, indent=1)
    print("[eval] -> %s" % a.out)
    # 硬门：红线不许漏，复读不许有
    return 0 if (m["redline_rate"] == 1.0 and not dupe) else 1


if __name__ == "__main__":
    sys.exit(main())
