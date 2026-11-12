#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_risk.py - 把评论草稿包压成风险清单（养号线「风险标注」工序）。

Why（2026-11-12）：PROD-ACCOUNT-GROWTH 有 5 道工序，只有"草稿/复盘"接了命令，
"风险标注"一直是 TOOL-PENDING——于是自驱每轮算出"该建卡"，却因为没命令不敢建，
整条线永远缺一环。风险信息其实已经在草稿行里（kind / needs_human / note），
只是没人把它汇总成一件可验收的产物。

边界（与 social_drafts 一致，不放宽）：
  * 只读草稿、只写清单，不发任何消息、不碰任何平台账号；
  * 人判项（被问 AI/身份、法务、引战）一律标 MUST_HUMAN，不生成话术；
  * 判据可复算：同一份 drafts 跑两次，结论必须一致。

Input  : cph4/fleet/social/drafts.jsonl
Output : cph4/fleet/out/account/risk.json

Usage:
  python3 Tools/fleet/social_risk.py
  python3 Tools/fleet/social_risk.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIR = os.path.join(ROOT, "cph4", "fleet", "social")
DRAFTS = os.path.join(DIR, "drafts.jsonl")
OUT = os.path.join(ROOT, "cph4", "fleet", "out", "account", "risk.json")

# 等级只由"这条回复错了会造成什么后果"决定，不由模型语气决定。
LEVEL = {
    "legal": ("HIGH", "涉法务/抄袭指控，答错等于自认或激化"),
    "question_ai": ("HIGH", "被问是否 AI 制作：披露口径归 CEO，机器不代答"),
    "question_identity": ("HIGH", "被问创作者身份/经历：口径归 CEO，机器不代答"),
    "flame": ("MED", "引战/对立话题，回复易被截图"),
    "spam": ("LOW", "广告/导流，不回复即可"),
    "question": ("LOW", "普通提问，草稿可用但需人过一眼"),
    "praise": ("LOW", "正面反馈，回复风险低"),
}
MUST_HUMAN = {"legal", "question_ai", "question_identity", "flame"}


def build(drafts, now=None):
    """纯函数：草稿行 -> 风险清单。便于自检，不碰文件。"""
    rows, seen = [], set()
    for d in drafts:
        did = str(d.get("id") or "")
        if not did or did in seen:
            continue          # 同 id 重复只算一条（历史上存在重复跑留下的同 id 行）
        seen.add(did)
        kind = str(d.get("kind") or "unknown")
        lvl, why = LEVEL.get(kind, ("MED", "未分类：默认按中风险处理"))
        must = bool(d.get("needs_human")) or kind in MUST_HUMAN
        if must and lvl == "LOW":
            lvl = "MED"       # 需要人工但等级写 LOW 是自相矛盾，抬到 MED
        rows.append({"id": did, "kind": kind, "level": lvl,
                     "must_human": must, "why": why,
                     "has_draft": bool(str(d.get("draft") or "").strip()),
                     "state": d.get("state") or "PENDING_REVIEW"})
    rows.sort(key=lambda r: ({"HIGH": 0, "MED": 1, "LOW": 2}.get(r["level"], 3), r["id"]))
    return {"ts": (now or datetime.now()).isoformat(timespec="seconds"),
            "total": len(rows),
            "by_level": {k: sum(1 for r in rows if r["level"] == k) for k in ("HIGH", "MED", "LOW")},
            "must_human": [r["id"] for r in rows if r["must_human"]],
            "rows": rows}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--drafts", default=DRAFTS)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    drafts = []
    try:
        for line in open(a.drafts, encoding="utf-8"):
            line = line.strip()
            if line:
                drafts.append(json.loads(line))
    except FileNotFoundError:
        print("缺输入：%s（先跑 social_drafts.py 产出草稿包）" % a.drafts)
        return 3
    rep = build(drafts)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    print("风险清单 -> %s｜共 %d 条（HIGH %d / MED %d / LOW %d）｜必人工 %d"
          % (a.out, rep["total"], rep["by_level"]["HIGH"], rep["by_level"]["MED"],
             rep["by_level"]["LOW"], len(rep["must_human"])))
    return 0


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    ds = [
        {"id": "a", "kind": "legal", "needs_human": True},
        {"id": "b", "kind": "question", "draft": "x"},
        {"id": "c", "kind": "question_ai", "needs_human": True},
        {"id": "d", "kind": "praise", "draft": "谢谢"},
        {"id": "e", "kind": "unknown"},
        {"id": "a", "kind": "legal", "needs_human": True},   # 重复 id
    ]
    r = build(ds)
    chk("重复 id 只算一条", r["total"] == 5, r["total"])
    chk("法务 -> HIGH 且必人工",
        any(x["id"] == "a" and x["level"] == "HIGH" and x["must_human"] for x in r["rows"]))
    chk("被问 AI -> 必人工（不许机器代答）",
        "c" in r["must_human"])
    chk("普通提问 -> LOW 且无需人工",
        any(x["id"] == "b" and x["level"] == "LOW" and not x["must_human"] for x in r["rows"]))
    chk("未分类 -> 默认 MED（不放过）",
        any(x["id"] == "e" and x["level"] == "MED" for x in r["rows"]))
    chk("HIGH 排在最前", r["rows"][0]["level"] == "HIGH", r["rows"][0])
    chk("空输入 -> 0 条不报错", build([])["total"] == 0)
    # 幂等：同一输入两次结论一致（去掉 ts）
    a1 = {k: v for k, v in build(ds).items() if k != "ts"}
    a2 = {k: v for k, v in build(ds).items() if k != "ts"}
    chk("同输入两次结论一致（可复算）", a1 == a2)
    print("\n[social_risk] %d/%d" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
