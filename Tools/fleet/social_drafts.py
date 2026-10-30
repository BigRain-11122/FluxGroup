#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_drafts.py - turn B站/抖音 comments into review-ready reply drafts.

Hard boundary (deliberate, not a limitation to work around):
  * this tool NEVER posts. The group has no platform account authorization yet
    (docs/orders.md: 11 平台账号 = CEO 物理件), and the standing rule is no main-account
    cookies on headless paths. Output is a draft queue a human sends.
  * every row carries needs_human; complaints/legal/flame get NO generated text, only a
    routing note - a wrong public answer costs more than a slow one.

Input  : cph4/fleet/social/inbox.jsonl   {id, comment, author?, video?}
Output : cph4/fleet/social/drafts.jsonl  {id, kind, priority, draft, needs_human, model}
         cph4/fleet/social/DIGEST.md     one screen for the CEO

Usage:
  python3 Tools/fleet/social_drafts.py --demo     # seed 5 sample comments, then run
  python3 Tools/fleet/social_drafts.py            # run on the real inbox
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIR = os.path.join(ROOT, "cph4", "fleet", "social")
INBOX = os.path.join(DIR, "inbox.jsonl")
DRAFTS = os.path.join(DIR, "drafts.jsonl")
DIGEST = os.path.join(DIR, "DIGEST.md")
MODEL = "qwen3:4b-instruct"

# Anything with public/legal risk is never auto-drafted: route, don't answer.
ESCALATE = ("complaint", "legal", "flame")

# Deterministic veto rules. Measured failure 2026-10-31: asked "这个画面是AI做的吗",
# the 4B wrote "画面是手绘风格，不是AI做的" - a flat lie about our own work, and the
# prompt had invited it by saying "don't mention AI". A model must never be asked to
# deny what we did; those questions go to the CEO because the disclosure wording is his.
AI_WORDS = ("ai", "AI", "人工智能", "生成", "合成")
DENIALS = ("不是ai", "不是 AI", "不是AI", "纯手绘", "手绘", "真人拍摄", "实拍", "不是生成")
IDENTITY = ("学考古", "考古专业", "科班", "我是学", "本人就是", "我们团队学")

DEMO = [
    {"id": "d1", "author": "夜航船", "comment": "这个画面是AI做的吗？看着有点恐怖谷"},
    {"id": "d2", "author": "老猫", "comment": "考古生那段太真实了，你是学考古的吗"},
    {"id": "d3", "author": "xx", "comment": "这不就是抄某某MV吗，一模一样"},
    {"id": "d4", "author": "阿岚", "comment": "求bgm名字！"},
    {"id": "d5", "author": "推广号", "comment": "加V看更多精彩内容"},
]


def post(payload, timeout=180):
    body = json.dumps(payload).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def classify_and_draft(comment):
    prompt = (
        "你在替一个 MV 作品账号筛评论。只依据评论本身判断，不要编造事实。\n"
        "把评论分成五类之一：question/praise/complaint/legal/flame/spam。\n"
        "如果是 question 或 praise：写一条 <=40 字的回复草稿，口吻是创作者本人，"
        "能答就答（只答评论里问的），不能答就说明会确认；不要许诺、不要透露未公开信息。\n"
        "授权边界（违反即无效）：不得声称创作者的专业身份或学历经历；"
        "被问是不是 AI 制作时，既不承认也不否认，草稿留空，等人工处理。\n"
        "如果是 complaint/legal/flame/spam：草稿留空。\n"
        "只输出一行 JSON：{\"kind\":\"...\",\"draft\":\"...\"}\n"
        "评论：" + comment
    )
    d = post({"model": MODEL, "prompt": prompt, "stream": False, "think": False,
              "keep_alive": "5m", "options": {"num_ctx": 8192, "temperature": 0.2}})
    text = (d.get("response") or "").strip()
    start, end = text.find("{"), text.rfind("}")
    kind, draft = "question", ""
    if start >= 0 and end > start:
        try:
            o = json.loads(text[start:end + 1])
            kind = str(o.get("kind") or "question").lower()
            draft = str(o.get("draft") or "").strip()[:200]
        except Exception:
            draft = text[:120]
    if kind in ESCALATE or kind == "spam":
        draft = ""
    kind, draft, needs_human, note = vet(comment, kind, draft)
    return kind, draft, needs_human, note


def vet(comment, kind, draft):
    """Deterministic veto after generation. Returns (kind, draft, needs_human, note)."""
    low = (draft or "").lower()
    asks_ai = any(w in comment for w in AI_WORDS)
    denies = any(w.lower() in low for w in DENIALS)
    if asks_ai:
        return "question_ai", "", True, "被问 AI 制作：披露口径归 CEO，不代答"
    if denies:
        return "claim_veto", "", True, "草稿否认/虚构了制作方式，已否决"
    if any(w in (draft or "") for w in IDENTITY):
        return "identity_veto", "", True, "草稿编造了创作者身份经历，已否决"
    if kind in ESCALATE or kind == "spam":
        return kind, "", True, ""
    if not draft:
        return kind, "", True, "模型未给出草稿"
    return kind, draft, False, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()

    os.makedirs(DIR, exist_ok=True)
    if a.demo:
        with open(INBOX, "w", encoding="utf-8") as f:
            for r in DEMO:
                f.write(json.dumps(dict(r, ts=datetime.now().isoformat(timespec="seconds")),
                                   ensure_ascii=False) + "\n")
    if not os.path.exists(INBOX):
        print("[social] no inbox at %s" % INBOX)
        return 0

    rows = [json.loads(l) for l in open(INBOX, encoding="utf-8") if l.strip()][:a.limit]
    done = set()
    if os.path.exists(DRAFTS):
        for l in open(DRAFTS, encoding="utf-8"):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass

    out, n = [], 0
    for r in rows:
        if r.get("id") in done:
            continue
        kind, draft, needs_human, note = classify_and_draft(r.get("comment", ""))
        out.append({"id": r.get("id"), "author": r.get("author"), "comment": r.get("comment"),
                    "kind": kind, "draft": draft, "note": note,
                    "needs_human": needs_human,
                    "model": MODEL, "ts": datetime.now().isoformat(timespec="seconds"),
                    "state": "PENDING_REVIEW"})
        n += 1

    if out:
        with open(DRAFTS, "a", encoding="utf-8") as f:
            for r in out:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    all_rows = []
    if os.path.exists(DRAFTS):
        all_rows = [json.loads(l) for l in open(DRAFTS, encoding="utf-8") if l.strip()]
    pend = [r for r in all_rows if r.get("state") == "PENDING_REVIEW"]
    esc = [r for r in pend if r.get("needs_human")]
    lines = ["# 评论草稿箱 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
             "",
             "- 本轮新生成 %d 条，累计待审 %d 条，其中需人工判断 %d 条" % (n, len(pend), len(esc)),
             "- 铁律：本工具不发送任何内容；账号与发言权在 CEO（orders.md 平台账号物理件）",
             ""]
    for r in pend[:12]:
        tag = "需人工" if r.get("needs_human") else "可直接发"
        lines.append("- [%s] %s：%s" % (tag, r.get("author") or r.get("id"),
                                        (r.get("draft") or "（不代答：%s）" % r.get("kind"))[:80]))
    with open(DIGEST, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("[social] new=%d pending=%d escalate=%d -> %s" % (n, len(pend), len(esc), DIGEST))
    return 0


if __name__ == "__main__":
    sys.exit(main())