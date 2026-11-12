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
# 2026-11-08：同上，读策略单源，不写死对照档
import local_model as _lm
import voice_gate as vg
MODEL = ((_lm._duties().get("resident") or {}).get("model") or "qwen3.5:4b-mlx")

# Anything with public/legal risk is never auto-drafted: route, don't answer.
# complaint 不在此列：挑刺是关系机会，给一句承认的草稿，但必须人工确认后再发。
ESCALATE = ("legal", "flame")

# Deterministic veto rules. Measured failure 2026-10-31: asked "这个画面是AI做的吗",
# the 4B wrote "画面是手绘风格，不是AI做的" - a flat lie about our own work, and the
# prompt had invited it by saying "don't mention AI". A model must never be asked to
# deny what we did; those questions go to the CEO because the disclosure wording is his.
# 2026-11-11 补：真人/本人 也是同一类问题（"女主是真人吗"曾被当成普通夸奖作答）。
AI_WORDS = ("ai", "AI", "人工智能", "生成", "合成", "真人", "本人", "是不是真的",
            "真的假的", "AI做", "ai做")
DENIALS = ("不是ai", "不是 AI", "不是AI", "纯手绘", "手绘", "真人拍摄", "实拍", "不是生成")
IDENTITY = ("学考古", "考古专业", "科班", "我是学", "本人就是", "我们团队学")
# 评论侧问身份：答案涉及披露口径，归 CEO，不许模型自答
IDENTITY_ASK = ("你是学", "你学的是", "科班", "你是做", "你是哪个", "团队几",
                "本人是", "你是本人", "学过", "什么专业", "干这行")

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


VOICE_CORPUS = os.path.join(ROOT, "cph4", "fleet", "voice", "corpus.jsonl")


def _fewshot(face="comment", k=4):
    """取语料里的好样本当 few-shot。语感靠样本传，不靠形容词。"""
    rows = []
    try:
        for line in open(VOICE_CORPUS, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    except Exception:
        return "", ""
    good = [r for r in rows if r.get("face") == face and r.get("label") == "good"]
    bad = [r for r in rows if r.get("face") == face and r.get("label") == "bad"]
    g = "\n".join("评论：%s → %s" % (r.get("ctx") or "（无）", r.get("text")) for r in good[:k])
    b = "\n".join("「%s」（%s）" % (r.get("text"), r.get("why") or "") for r in bad[:3])
    return g, b


def classify_and_draft(comment, _retry_hits=None, _prev=""):
    good, bad = _fewshot("comment")
    prompt = (
        "你在替一个 MV / 漫剧账号回评论。你是创作者本人，不是客服。\n"
        "只输出一行 JSON：{\"kind\":\"...\",\"draft\":\"...\"}\n\n"
        "分类（五选一）：praise 夸奖 / question 提问 / complaint 挑刺 / "
        "legal 抄袭侵权指控 / flame 骂人 / spam 广告。\n\n"
        "写草稿的铁律：\n"
        "1. 像人说话：短句、口语，10-25 字，最多两句；可用「哈哈」「谢啦」「对」开头。\n"
        "2. 禁用词：感谢喜爱、感谢支持、欢迎查阅、请您、如有疑问、进一步确认、"
        "准确信息、相关信息、我们将、我们会尽快、持续关注、一键三连。\n"
        "3. 不许反问对方，不许用感叹号。\n"
        "4. 不许编事实：不要提置顶、简介、主页、下期、明天、下周这些你不知道的内容。\n"
        "5. 被问具体事实（歌名/用什么软件/什么时候更/是不是真人/谁做的）不要给答案，"
        "写「这个我得翻一下」这类延后话；涉及是否 AI 制作、是否真人，草稿留空。\n"
        "6. complaint 只回一句承认或一个具体回应，不解释不辩解。\n"
        "7. legal/flame/spam：草稿留空字符串。\n\n"
        "照这个语感写（好例子）：\n" + good + "\n\n"
        "不要写成这样（坏例子）：\n" + bad + "\n\n"
        "评论：" + comment
    )
    if _retry_hits:
        prompt += ("\n\n上一次写成「%s」被判不合格，问题：%s。重写一版，只输出 JSON。"
                   % (_prev[:60], "、".join(_retry_hits[:3])))
    d = post({"model": MODEL, "prompt": prompt, "stream": False, "think": False,
              "keep_alive": "5m", "options": {"num_ctx": 8192, "temperature": 0.6}})
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
    kind, draft, human, note = vet(comment, kind, draft)
    if not draft:
        return kind, draft, human, note
    # 语感闸：不过就带着命中项重写一次，仍不过则留空给人
    res = vg.check(draft, "comment", comment)
    if res["verdict"] == "BLOCK":
        k2, d2, h2, n2 = _draft_once(comment, res["hits"], draft)
        if h2 or not d2:
            return k2, d2, True, "语感闸未过(%s) 且重写失败" % ",".join(res["hits"][:2])
        res2 = vg.check(d2, "comment", comment)
        if res2["verdict"] == "BLOCK":
            return "voice_block", "", True, "语感闸两次未过:%s" % ",".join(res2["hits"][:3])
        return k2, d2, human, "重写后过闸 score=%d" % res2["score"]
    tag = "voice=%s/%d" % (res["verdict"], res["score"])
    return kind, draft, human, (note + " | " + tag).strip(" |")


def _draft_once(comment, hits, prev):
    kind, draft, human, note = classify_and_draft(comment, _retry_hits=hits, _prev=prev)
    return kind, draft, human, note


def vet(comment, kind, draft):
    """Deterministic veto after generation. Returns (kind, draft, needs_human, note)."""
    low = (draft or "").lower()
    asks_ai = any(w in comment for w in AI_WORDS)
    denies = any(w.lower() in low for w in DENIALS)
    if asks_ai:
        return "question_ai", "", True, "被问 AI 制作：披露口径归 CEO，不代答"
    if any(w in comment for w in IDENTITY_ASK):
        return "question_identity", "", True, "被问创作者身份/经历：披露口径归 CEO，不代答"
    if denies:
        return "claim_veto", "", True, "草稿否认/虚构了制作方式，已否决"
    if any(w in (draft or "") for w in IDENTITY):
        return "identity_veto", "", True, "草稿编造了创作者身份经历，已否决"
    if kind in ESCALATE or kind == "spam":
        return kind, "", True, ""
    if not draft:
        return kind, "", True, "模型未给出草稿"
    if kind == "complaint":
        return kind, draft, True, "挑刺：草稿供参考，发送前人工确认"
    return kind, draft, False, ""


def _shared_run(a, b, minlen=6):
    """最长公共子串，>= minlen 返回该串，否则返回 ""。"""
    if len(a) < minlen or len(b) < minlen:
        return ""
    best, prev = 0, [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best, end = cur[j], i
        prev = cur
    return a[end - best:end] if best >= minlen else ""


def main():
    global DIR, INBOX, DRAFTS, DIGEST
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    # 2026-11-12：加 --dir。路径原本写死 cph4/fleet/social，导致自驱无法在隔离
    # 沙箱里端到端验证它（一跑就写真实草稿队列），这也是"写死路径"类的通病。
    ap.add_argument("--dir", default=None, help="工作目录（默认 cph4/fleet/social）")
    a = ap.parse_args()
    if a.dir:
        DIR = os.path.abspath(a.dir)
        INBOX = os.path.join(DIR, "inbox.jsonl")
        DRAFTS = os.path.join(DIR, "drafts.jsonl")
        DIGEST = os.path.join(DIR, "DIGEST.md")

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

    # 同批模板感：两条草稿共用 6 字以上同一句尾 = 模板，违反"每条独写无模板"
    for i in range(len(out)):
        for j in range(i + 1, len(out)):
            a, b = out[i].get("draft") or "", out[j].get("draft") or ""
            if not a or not b:
                continue
            hit = _shared_run(a, b, 6)
            if hit:
                for k in (i, j):
                    out[k]["needs_human"] = True
                    out[k]["note"] = (out[k].get("note") or "") + " | 模板感:重复「%s」" % hit
                    out[k]["template_hit"] = hit

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