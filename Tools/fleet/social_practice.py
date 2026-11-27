#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_practice.py - 实战闭环：发一条真评论 → 回验 → 留或撤 → 记账。

CEO 2026-11-18 授权（原话「我允许你少了的（少量）开始真实的回复和评论，实战，并根据情况
撤回或者留下，不断迭代」）。所以这个工具只做一件事，但每一步都要有证据：

  1 PICK   从 comment-queue.jsonl 里挑一条**未用过**的，优先同领域（剪辑/教程/MV）视频
  2 GUARD  风控闸（节律/配额）+ 当日上限（默认 2）+ 间隔（默认 90 分钟）
  3 POST   官方接口 /x/v2/reply/add（root=0 即顶级评论），同源 cookie + wbi + csrf
  4 VERIFY 发后必验：列表里能查到=公开可见；查不到=待审核，**不许宣称成功**
  5 JUDGE  可见且内容合规 → 留；15 分钟仍不可见 → 判待审核并停止后续（不重复发）
  6 LOG    落 comments-sent.jsonl：rpid / aid / 文案 / 判定 / 时间 / 撤销命令

撤回：`python3 Tools/fleet/social_practice.py --withdraw <rpid> --aid <aid>`

用法：
  .venv-housing/bin/python Tools/fleet/social_practice.py --pick        # 只挑不发，看会发什么
  .venv-housing/bin/python Tools/fleet/social_practice.py --send 1      # 真发 1 条
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
QUEUE = os.path.join(SOCIAL, "comment-queue.jsonl")
SENT = os.path.join(SOCIAL, "practice-log.jsonl")

sys.path.insert(0, HERE)

# 同领域优先：在这些词命中的视频下留评论，才是"同行/学习者"的自然行为
NICHE = ("剪辑", "教程", "MV", "mv", "转场", "调色", "分镜", "短片", "拍摄", "剪映", "运镜")
# 标题滑窗取词时要排除的通用词：它们出现在任何句子里都不代表"在说这条视频"。
TITLE_STOP = {"这个", "那个", "我们", "你们", "他们", "什么", "怎么", "真的", "可以",
              "就是", "不过", "时候", "一个", "没有", "不是", "这些", "那些", "自己"}
def _policy():
    """频率上限来自 freq_policy（可见率驱动），工具里不再写死。"""
    try:
        import freq_policy as fp
        p = fp.load_policy()
        return int(p.get("max_per_day", 2)), int(p.get("min_gap_min", 90))
    except Exception:
        return 2, 90


MAX_PER_DAY, MIN_GAP_MIN = _policy()


import re

# 编造闸（2026-11-18 实锚：队列第一条就编了"老寒这教程"，标题里根本没有这个名字；
# 还编了"坐等 2026 版本上线"。编事实/编人名是红线，宁可这条不发）。
FAKE_PAT = (
    (re.compile(r"(坐等|等到|还没|尚未|预计).{0,8}(上线|发布|更新)"), "编造发布计划"),
    (re.compile(r"第[0-9一二三四五六七八九十]+(集|期|部|弹)"), "编造集数"),
    (re.compile(r"[0-9]+\s*(万|千|百)\s*(播放|粉丝|点赞|赞)"), "编造数据"),
    # 没看过就不能说自己看过：编造观看经历与我们"不许编"的纪律同类
    (re.compile(r"(看完|看了|跟着练|学完|试了|上手了)"), "编造观看经历"),
)
ADDRESS_PAT = re.compile(r"([\u4e00-\u9fff]{2,3})这(教程|期|集|视频|波|手)")


def safe_to_send(text, title="", topics=()):
    """返回 (ok, 原因)。只放行"不编人、不编事、且与本视频相关"的评论。
    2026-11-21 修：原来领域判据是写死的剪辑/MV 词表（NICHE），可出稿早已跨段
    （tech_nerd/shallow/情感…），于是「用蒙版遮掉侧面杂音再叠加歌词」这种明明在讲
    这条视频的话也被判"与本视频领域无关"——闸太窄把好话挡在门外。
    正解是拿**这条视频自己的话题词**当依据（topics 来自该视频真实评论），
    而不是全领域一张表；没有 topics 时仍用 NICHE 兜底（arm_probe 的负控靠这条）。
    """
    txt = (text or "").strip()
    if len(txt) < 8:
        return False, "太短"
    # 元话术（2026-11-27 实锚）：模型会把提示词当内容复述——实际发出过
    # 「标题里那个"抽卡"环节剪辑得真带感啊」。真人不说"标题里"，这是指令泄漏，
    # 既露馅又不像人话，发送前直接拦（提示词那侧也做了修改，两边都守）。
    for w in ("标题里", "标题中", "标题上", "视频里说", "这条视频里", "视频标题"):
        if w in txt:
            return False, "元话术「%s」（指令泄漏）" % w
    for pat, why in FAKE_PAT:
        if pat.search(txt):
            return False, why
    m = ADDRESS_PAT.search(txt)
    if m and m.group(1) not in (title or ""):
        return False, "编造称呼「%s」（标题里没有）" % m.group(1)
    # 任何 2-3 字人名式称呼（老X/小X/阿X）必须出现在标题里
    for cand in re.findall(r"[老小阿][\u4e00-\u9fff]{1,2}", txt):
        if cand not in (title or ""):
            return False, "编造称呼「%s」" % cand
    # 引流硬拒：CEO 2026-11-21「目前不做引流」。2026-11-22 压测实锚：
    # 「你直接进主页看教程吧」从发送闸漏了出去——DRAIN 只在生成侧用过，发送侧没接。
    try:
        import comment_taste as _ct
        hit = [w for w in getattr(_ct, "DRAIN", ()) if w in txt]
        if hit:
            return False, "引流词（%s）" % "/".join(hit[:2])
    except Exception:
        pass
    pool = list(NICHE) + [str(t) for t in (topics or ()) if t and len(str(t)) >= 2]
    # 标题词回填：扩池后大量新视频没有采集过评论 → topics 为空 → 任何句子都被这条闸拒，
    # 出稿直接归零（2026-11-22 实锚：17:44 连续 3 条"与本视频无关"、当天 8 小时没发出）。
    # 视频自己的标题就是最直接的"这条在讲什么"，用它兜底才对得上"与本视频相关"的本意。
    #
    # 2026-11-27 修：原来用 r"[\u4e00-\u9fff]{2,6}" 取标题词，那是**最长匹配**——
    # 「剪辑教程：游戏击杀卡点氛围感效果」只产出 剪辑教程 / 游戏击杀卡点 / 氛围感效果 三个词，
    # 等于要求评论照抄 4-6 字的整段短语。实时实测：12 条候选里 6 条全死在
    # 「与本视频无关（不含该视频话题词/标题词）」，而模型写的"游戏卡点挺带感"明明是贴题的。
    # 正解是按 2-4 字滑窗取词，让 剪辑/教程/游戏/击杀/卡点/氛围 都能命中；
    # 这不是放宽判据，是把"标题说了什么"算对。
    for run in re.findall(r"[\u4e00-\u9fff]{2,}", title or ""):
        for n in (2, 3, 4):
            for i in range(0, max(0, len(run) - n + 1)):
                w = run[i:i + n]
                if w in TITLE_STOP or w in pool:
                    continue
                pool.append(w)
    if not any(w in txt for w in pool):
        return False, "与本视频无关（不含该视频话题词/标题词）"
    return True, ""


def load_jsonl(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def sent_today():
    """今天"发出去几条"——只数 post，不数 verify。

    2026-11-18 实锚：每条帖在台账里落 post + verify 两行，按行数算日限会把
    1 条记成 2 条，额度直接砍半（今天只剩 1 条却报 2/2）。

    2026-11-27 修（宣称分级）：post 行原来只要有 text 就算发出去，于是一条
    **rpid 为空**的失败记录（00:41:47「标题里那个抽卡环节剪辑得真带感啊…」rpid=）
    被算成"今日已发 1 条"。没有 rpid 就等于没有回执，最多算"已提交待回执"，
    不能计入额度——否则额度被失败记录吃掉，真发的时候反而没配额。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    for r in load_jsonl(SENT):
        if not str(r.get("ts", "")).startswith(today):
            continue
        if r.get("action") == "verify":
            continue
        if r.get("action") in ("post", None):
            if r.get("rpid") or r.get("reply"):
                out.append(r)
    return out


def pick():
    """挑一条没用过、同领域优先的队列项。返回 (row, 理由) 或 (None, 原因)。"""
    done = {(r.get("text") or "").strip() for r in load_jsonl(SENT)}
    cands, rejected = [], []
    for r in load_jsonl(QUEUE):
        if (r.get("text") or "").strip() in done:
            continue
        ok, why = safe_to_send(r.get("text"), r.get("title") or "")
        if ok:
            cands.append(r)
        else:
            rejected.append("%s：%s" % ((r.get("text") or "")[:14], why))
    if not cands:
        return None, "没有过关的条目（被编造闸拦下 %d 条，例：%s）" % (
            len(rejected), "；".join(rejected[:3]))
    def score(r):
        t = (r.get("title") or "")
        niche = sum(1 for w in NICHE if w in t)
        return (-niche, -(r.get("taste") or 0))
    cands.sort(key=score)
    best = cands[0]
    why = "同领域命中 %d 个关键词，品味分 %s" % (
        sum(1 for w in NICHE if w in (best.get("title") or "")), best.get("taste"))
    return best, why


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pick", action="store_true")
    ap.add_argument("--send", type=int, default=0)
    ap.add_argument("--text", default=None, help="指定文案（仍要过两道闸）")
    ap.add_argument("--video", default=None, help="指定视频链接（配 --text 用）")
    ap.add_argument("--withdraw", default=None)
    ap.add_argument("--aid", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()

    import social_comment as sc

    if a.withdraw:
        if not a.aid:
            print("[practice] --withdraw 需要 --aid")
            return 2
        ok, res = sc.delete_reply(a.aid, a.withdraw)
        print("[practice] 撤回 rpid=%s → %s %s"
              % (a.withdraw, "ok" if ok else "fail", json.dumps(res, ensure_ascii=False)[:200]))
        _log({"action": "withdraw", "rpid": a.withdraw, "aid": a.aid, "ok": ok,
              "res": str(res)[:200]})
        return 0 if ok else 1

    if a.text:
        v = a.video or ""
        ok1, w1 = safe_to_send(a.text, v)
        import social_comment_gen as cg
        ok2, w2, _ = cg.gate(a.text, ctx=v, taken=(), corpus=())
        if not (ok1 and ok2):
            print("[practice] 指定文案未过闸：%s%s" % (w1 or "", (" / " + w2) if w2 else ""))
            return 2
        row = {"title": v, "text": a.text, "taste": 0, "video": v}
    else:
        row, why = pick()
        if not row:
            print("[practice] 无可发内容：%s" % why)
            return 2
    print("[practice] 选中：%s\n          文案：%s"
          % ((row.get("title") or "")[:40], row.get("text")))
    if a.pick or a.send <= 0:
        return 0

    today = sent_today()
    if len(today) >= MAX_PER_DAY:
        print("[practice] 今日已发 %d 条（上限 %d），停" % (len(today), MAX_PER_DAY))
        return 0
    if today:
        last = max(str(r.get("ts")) for r in today)
        try:
            gap = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 60
            if gap < MIN_GAP_MIN:
                print("[practice] 距上一条仅 %.0f 分钟（下限 %d），再等等" % (gap, MIN_GAP_MIN))
                return 0
        except Exception:
            pass

    import social_riskguard as guard
    ok, gwhy = guard.check("bilibili")
    if not ok:
        ok, gwhy = guard.wait_turn("bilibili", max_wait=120)
        if not ok:
            print("[practice] 风控闸拒绝：%s" % gwhy)
            return 3

    aid = sc.bv_to_aid(row["video"])
    if not aid:
        print("[practice] 解析 aid 失败：%s" % row["video"])
        return 2
    ok, res = sc.post_reply(aid, 0, row["text"], dry=False)   # root=0 → 顶级评论
    rpid, code, toast = "", None, ""
    try:
        d = json.loads(res.get("text") or "{}")
        code = d.get("code"); toast = d.get("message") or ""
        rpid = str((d.get("data") or {}).get("rpid") or "")
    except Exception:
        rpid = ""
    _log({"action": "post", "video": row["video"], "aid": aid, "text": row["text"],
          "rpid": rpid, "code": code, "toast": toast, "ok": ok,
          "taste": row.get("taste")})
    print("[practice] 提交 → %s rpid=%s" % ("ok" if ok else "fail", rpid or "?"))
    if not ok:
        return 1
    if rpid:
        # 优先按正文回验（接口已被 412，DOM 通道可用），拿不到数再退回 rpid 查
        vis, vwhy = sc.verify_text(aid, row["text"])
        if vis is None:
            _v2, _w2 = sc.verify_comment(aid, rpid, wait_s=120)
            if _v2 is not None:
                vis, vwhy = _v2, _w2
        _log({"action": "verify", "aid": aid, "rpid": rpid, "visible": vis, "why": vwhy})
        print("[practice] 回验：%s（%s）" % ("公开可见" if vis else "不可见", vwhy))
    return 0


def _log(rec):
    rec.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    with open(SENT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def self_test():
    """三条判据必须能红：挑不到、超日限、间隔不足。"""
    done = {"甲": "x"}
    cases = [
        ("幽灵账号过滤", not ("账号已注销" in (__import__("social_comment").live_comments(
            [{"author": "账号已注销", "text": "UP主加油！"}]) or [{}])[0].get("author", "x"))),
        ("同领域优先", ("剪辑" in NICHE)),
        ("日限为正数", MAX_PER_DAY > 0),
    ]
    # 标题贴题判据（2026-11-27）：滑窗取词必须让"贴题的短句"过、让"无关句"拒。
    # 负控的必要性：旧实现用最长匹配取词，等于要求照抄 4-6 字整段短语，
    # 实际把 6/12 条贴题候选全拒了——这条测试就是为了不让它被改回去。
    _t = "剪辑教程：游戏击杀卡点氛围感效果"
    _on, _ = safe_to_send("游戏击杀那下卡点很带感", title=_t, topics=())
    _off, _ = safe_to_send("今天天气不错我出去走走了", title=_t, topics=())
    cases += [("标题滑窗：贴题短句必须放行", _on is True),
              ("标题滑窗：无关句必须仍拒", _off is False)]
    # 元话术必须拦（实锚：真发出过「标题里那个"抽卡"环节剪辑得真带感啊」）
    _meta, _ = safe_to_send(
        "标题里那个抽卡环节剪辑得真带感啊", title="剪辑教程：抽卡", topics=())
    cases.append(("元话术（指令泄漏）必须拦", _meta is False))
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
