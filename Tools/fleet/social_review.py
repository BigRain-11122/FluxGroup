#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_review.py - 人工批审台：把"人怎么改的"变成训练数据（养号线）。

Why（2026-11-17）：养号线已有草稿（social_drafts）、风险（social_risk）、选题
（social_topics）三件，唯独缺"人审完就丢了"这一环——模型永远不知道哪句真能用。
本地 4B/9B 不改权重也能学，靠的是好/坏样本进下一轮 prompt（few-shot 是小模型上
唯一被实测有效的"训练"），所以每次 approve / edit / reject 都必须固化：
  * approve → voice/corpus.jsonl 加一条 good 样本（face=通道名）
  * edit    → 人工改写版进 good，模型原稿进 rejections（带"为什么改成这样"）
  * reject  → rejections.jsonl 加一条 bad 样本（必须写 why）

边界（与另三件一致，不放宽）：
  * 本工具不发送任何内容：平台账号与发言权在 CEO（orders.md 平台账号物理件）。
  * 不碰平台接口、不读 cookie；只改本地队列与本地语料。
  * why 必填：没有理由的否决对下一轮毫无价值（"不好"不是判据）。

Input  : cph4/fleet/social/drafts.jsonl        草稿队列（state=PENDING_REVIEW）
Output : 同上（行内 state 改 APPROVED/EDITED/REJECTED + reviewed_by/review_ts）
         cph4/fleet/voice/corpus.jsonl         好样本（few-shot 正例）
         cph4/fleet/social/rejections.jsonl    坏样本（few-shot 反例 + why）

Usage:
  python3 Tools/fleet/social_review.py --list
  python3 Tools/fleet/social_review.py --approve d4
  python3 Tools/fleet/social_review.py --edit d5 --text "加V这种我不接，抱歉" --why "广告号不回复内容"
  python3 Tools/fleet/social_review.py --reject d3 --why "反问观众，且承认了抄袭指控"
  python3 Tools/fleet/social_review.py --stats
  python3 Tools/fleet/social_review.py --self-test
  # 沙箱：--dir <临时目录>（不写生产队列，用于回归）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIR = os.path.join(ROOT, "cph4", "fleet", "social")
CORPUS = os.path.join(ROOT, "cph4", "fleet", "voice", "corpus.jsonl")

PREFIX = {"comment": "C", "danmaku": "D", "dm": "M", "fan": "F"}


def _paths(d):
    return (os.path.join(d, "drafts.jsonl"),
            os.path.join(d, "rejections.jsonl"))


def _load(path):
    rows = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _save(path, rows):
    """原子写：先写同目录临时文件再 replace，避免半截队列。"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def _next_corpus_id(face, existing):
    """语料 id 按 face 分前缀递增，绝不覆盖历史样本。"""
    p = PREFIX.get(face, "X")
    nums = []
    for r in existing:
        rid = str(r.get("id") or "")
        if rid.startswith(p + "-"):
            try:
                nums.append(int(rid.split("-", 1)[1]))
            except ValueError:
                pass
    return "%s-%03d" % (p, (max(nums) + 1) if nums else 1)


def _add_good(ctx, text, face, why, source, corpus_path):
    corpus = _load(corpus_path)
    text = (text or "").strip()
    if not text:
        return None
    # 同一 ctx+text 已经在库＝不重复写（车同一条评论审两次）
    for r in corpus:
        if (r.get("ctx") or "").strip() == (ctx or "").strip() \
                and (r.get("text") or "").strip() == text:
            return None
    row = {"id": _next_corpus_id(face, corpus), "face": face, "label": "good",
           "ctx": (ctx or "").strip()[:120], "text": text[:200],
           "why": why or "人工确认可用", "source": source}
    corpus.append(row)
    _save(corpus_path, corpus)
    return row


def _add_bad(row, why, drafts_path_dir, source):
    path = os.path.join(drafts_path_dir, "rejections.jsonl")
    bad = _load(path)
    text = (row.get("draft") or "").strip()
    if not text:
        return None            # 本来就没给草稿（转人工项）＝没有可学的坏样本
    bad.append({"id": row.get("id"), "face": row.get("face") or "comment",
                "ctx": (row.get("comment") or "")[:120], "bad_text": text[:200],
                "why": why, "source": source,
                "ts": datetime.now().isoformat(timespec="seconds")})
    _save(path, bad)
    return bad[-1]


def _mark(rows, rid, state, extra=None):
    hit = 0
    for r in rows:
        if str(r.get("id")) == str(rid):
            r["state"] = state
            r["reviewed_by"] = os.environ.get("USER") or "human"
            r["review_ts"] = datetime.now().isoformat(timespec="seconds")
            if extra:
                r.update(extra)
            hit += 1
    return hit


def _pending(rows, face=None):
    out = [r for r in rows if r.get("state") == "PENDING_REVIEW"]
    if face:
        out = [r for r in out if (r.get("face") or "comment") == face]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None, help="工作目录（默认 cph4/fleet/social）")
    ap.add_argument("--corpus", default=None,
                    help="语料路径（默认 cph4/fleet/voice/corpus.jsonl；沙箱必改，不许写生产语料）")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--approve")
    ap.add_argument("--edit")
    ap.add_argument("--text")
    ap.add_argument("--reject")
    ap.add_argument("--why")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--face", default=None, help="只列某通道 comment/danmaku/dm/fan")
    a = ap.parse_args()

    global CORPUS
    d = os.path.abspath(a.dir) if a.dir else DIR
    if a.corpus:
        CORPUS = os.path.abspath(a.corpus)
    drafts_path, _ = _paths(d)
    if a.self_test:
        return self_test()

    rows = _load(drafts_path)
    if not rows and not (a.approve or a.edit or a.reject):
        print("[review] 队列为空：%s" % drafts_path)
        return 0

    acted = False
    if a.approve:
        n = _mark(rows, a.approve, "APPROVED")
        row = next((r for r in rows if str(r.get("id")) == str(a.approve)), None)
        if n and row:
            g = _add_good(row.get("comment"), row.get("draft"),
                          row.get("face") or "comment", "人工审核通过，可照此语感写",
                          "social_review %s approve" % datetime.now().date(),
                          CORPUS)
            print("[review] %s 通过%s" % (a.approve, "（+1 好样本 %s）" % g["id"] if g else "（语料已有，不重复）"))
        elif not n:
            print("[review] 没有 id=%s" % a.approve)
            return 2
        acted = True

    if a.edit:
        if not (a.text or "").strip():
            print("[review] --edit 必须带 --text（人工改写版）")
            return 2
        n = _mark(rows, a.edit, "EDITED", {"final": a.text.strip()[:200],
                                           "edit_reason": (a.why or "").strip()})
        row = next((r for r in rows if str(r.get("id")) == str(a.edit)), None)
        if n and row:
            _add_good(row.get("comment"), a.text.strip(), row.get("face") or "comment",
                      (a.why or "人工改写后可用").strip(),
                      "social_review %s edit" % datetime.now().date(), CORPUS)
            _add_bad(row, (a.why or "人工改写").strip(), d,
                     "social_review %s edit" % datetime.now().date())
            print("[review] %s 已改写并采用（好样本+1，模型原稿记为坏样本）" % a.edit)
        elif not n:
            print("[review] 没有 id=%s" % a.edit)
            return 2
        acted = True

    if a.reject:
        if not (a.why or "").strip():
            print("[review] --reject 必须带 --why：没有理由的否决对下一轮没有价值")
            return 2
        n = _mark(rows, a.reject, "REJECTED", {"reject_reason": a.why.strip()})
        row = next((r for r in rows if str(r.get("id")) == str(a.reject)), None)
        if n and row:
            b = _add_bad(row, a.why.strip(), d,
                         "social_review %s reject" % datetime.now().date())
            print("[review] %s 已否决%s" % (a.reject, "（+1 坏样本）" if b else "（无草稿，仅改状态）"))
        elif not n:
            print("[review] 没有 id=%s" % a.reject)
            return 2
        acted = True

    if acted:
        _save(drafts_path, rows)

    pend = _pending(rows, a.face)
    if a.list or acted or a.stats:
        if a.stats:
            from collections import Counter
            c = Counter(r.get("state") or "?" for r in rows)
            fc = Counter(r.get("face") or "comment" for r in rows)
            print("[review] 状态 %s" % dict(c))
            print("[review] 通道 %s" % dict(fc))
            print("[review] 语料 %d 条 · 坏样本 %d 条" % (len(_load(CORPUS)),
                                                         len(_load(os.path.join(d, "rejections.jsonl")))))
        if a.list or acted:
            print("[review] 待审 %d 条：" % len(pend))
            for r in pend[:20]:
                flag = "需人工" if r.get("needs_human") else "可直发"
                print("  - %-6s [%s/%s] %s → %s" % (
                    r.get("id"), r.get("face") or "comment", flag,
                    (r.get("comment") or "")[:34],
                    (r.get("draft") or "（不代答：%s）" % r.get("kind"))[:40]))
    return 0


def self_test():
    """沙箱自检：approve/edit/reject 三条路都要真落盘，坏样本必须带 why。"""
    ok = 0
    total = 0
    global CORPUS
    tmp = tempfile.mkdtemp(prefix="social-review-")
    # 测试绝不许写生产路径：语料也搬进沙箱（2026-11-12 铁律，R-11 实锚）
    CORPUS = os.path.join(tmp, "corpus.jsonl")
    drafts_path, rej_path = _paths(tmp)
    seed = [
        {"id": "t1", "comment": "这段剪辑太顺了", "draft": "谢啦，剪了好几遍", "kind": "praise",
         "face": "comment", "state": "PENDING_REVIEW"},
        {"id": "t2", "comment": "求bgm名字", "draft": "这首我得翻一下工程文件", "kind": "question",
         "face": "comment", "state": "PENDING_REVIEW"},
        {"id": "t3", "comment": "这不是抄xx吗", "draft": "没有抄，你别乱说", "kind": "legal",
         "face": "comment", "state": "PENDING_REVIEW"},
        {"id": "t4", "comment": "主播唱歌好听", "draft": "谢谢", "kind": "praise",
         "face": "danmaku", "state": "PENDING_REVIEW"},
    ]
    _save(drafts_path, seed)
    corpus_before = len(_load(CORPUS))

    def run(argv):
        sys.argv = ["social_review.py", "--dir", tmp] + argv
        return main()

    total += 1
    if run(["--approve", "t1"]) == 0:
        ok += 1
    rows = _load(drafts_path)
    total += 1
    if next(r for r in rows if r["id"] == "t1")["state"] == "APPROVED":
        ok += 1
    total += 1
    if len(_load(CORPUS)) == corpus_before + 1:      # 好样本落库
        ok += 1
    total += 1
    if run(["--approve", "t1"]) == 0 and len(_load(CORPUS)) == corpus_before + 1:
        ok += 1                                        # 重复 approve 不重复写
    total += 1
    if run(["--reject", "t3"]) == 2:                   # 无 why 必须拒
        ok += 1
    total += 1
    if run(["--reject", "t3", "--why", "替观众否认指控，等于对赌"]) == 0:
        ok += 1
    total += 1
    if _load(rej_path) and _load(rej_path)[-1]["why"]:
        ok += 1
    total += 1
    if run(["--edit", "t2", "--text", "这首是 xx（已核实）", "--why", "事实包已核实"]) == 0:
        ok += 1
    rows = _load(drafts_path)
    total += 1
    if next(r for r in rows if r["id"] == "t2").get("final") == "这首是 xx（已核实）":
        ok += 1
    total += 1
    if next(r for r in rows if r["id"] == "t4")["state"] == "PENDING_REVIEW":   # 未审的不能动
        ok += 1
    print("[self-test] %d/%d %s" % (ok, total, "PASS" if ok == total else "FAIL"))
    print("[self-test] 沙箱=%s" % tmp)
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
