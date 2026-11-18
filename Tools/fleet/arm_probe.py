#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arm_probe.py — 4 臂形态对照实验的发帖执行体（严格限量，闸不放宽）。

为什么要有这个工具：social_practice.py 只会发**顶级评论**（root=0），而对照实验里
A/B/D 三臂都是**子回复**（要挂到别人的 root 评论下）。同时"今日额度"必须按
**已发出的帖子数**算，而不是按台账行数算——practice-log.jsonl 每条帖子会落
post + verify 两行，按行数算会把 1 条帖子记成 2 条，等于把上限砍半（反过来
按行数算也不许加额度，这一点写死在 policy 里，本工具只读不写）。

四臂（形态是唯一自变量）：
  A 短句子回复：<15 字、无专有名词
  B 短句子回复：同 A 的字数带，换一个视频（排除"这条视频本身好发"的偶然）
  C 短句顶级评论：<15 字、无专有名词、不带子回复层级
  D 长句子回复：>=25 字且含具体内容（画面/剪辑/转场等具体对象）

每个动作都留证据：两道闸的返回值、提交返回码、回验结果，全部落 practice-log.jsonl。

用法：
  .venv-housing/bin/python Tools/fleet/arm_probe.py --status
  .venv-housing/bin/python Tools/fleet/arm_probe.py --arm A --video <url> --text "这个转场太顺了吧" --dry
  .venv-housing/bin/python Tools/fleet/arm_probe.py --arm A --video <url> --text "..." --root auto
  .venv-housing/bin/python Tools/fleet/arm_probe.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
LOG = os.path.join(SOCIAL, "practice-log.jsonl")
SENT2 = os.path.join(SOCIAL, "comments-sent.jsonl")
sys.path.insert(0, HERE)

ARMS = {
    "A": {"kind": "reply", "max_len": 14, "min_len": 8, "why": "短句子回复"},
    "B": {"kind": "reply", "max_len": 14, "min_len": 8, "why": "短句子回复（换视频）"},
    "C": {"kind": "top", "max_len": 14, "min_len": 8, "why": "短句顶级评论"},
    "D": {"kind": "reply", "max_len": 90, "min_len": 25, "why": "长句子回复（带具体内容）"},
}
CONCRETE = ("画面", "剪辑", "镜头", "结尾", "开头", "配乐", "转场", "调色", "教程",
            "素材", "分镜", "节奏", "字幕", "光影", "构图", "音效", "前奏", "副歌")


def _rows(path):
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def posts_today(day=None, log=LOG, sent2=SENT2):
    """今日真实发出的**帖子**数（按 action=post 计，按 rpid 去重跨两个台账）。"""
    day = day or datetime.now().strftime("%Y-%m-%d")
    seen, n = set(), 0
    for p in (log, sent2):
        for r in _rows(p):
            if r.get("action") != "post" or r.get("ok") is False:
                continue
            if not str(r.get("ts", "")).startswith(day):
                continue
            key = str(r.get("rpid") or "") or ("%s|%s" % (r.get("aid"), r.get("text")))
            if key in seen:
                continue
            seen.add(key)
            n += 1
    return n


def last_post_ts(log=LOG, sent2=SENT2):
    ts = ""
    for p in (log, sent2):
        for r in _rows(p):
            if r.get("action") == "post":
                ts = max(ts, str(r.get("ts") or ""))
    return ts


def cap_check(now=None, log=LOG, sent2=SENT2, policy=None):
    """返回 (ok, 原因)。上限与间隔只从 FREQ-POLICY.json 读，工具里不写死、不许改。"""
    import freq_policy as fp
    pol = policy or fp.load_policy()
    mx, gap_min = int(pol.get("max_per_day", 2)), int(pol.get("min_gap_min", 90))
    now = now or datetime.now()
    n = posts_today(now.strftime("%Y-%m-%d"), log, sent2)
    if n >= mx:
        return False, "今日已发 %d 条（上限 %d，FREQ-POLICY stage=%s）" % (
            n, mx, pol.get("stage"))
    lts = last_post_ts(log, sent2)
    if lts:
        try:
            gap = (now - datetime.fromisoformat(lts)).total_seconds() / 60
            if gap < gap_min:
                return False, "距上帖仅 %.0f 分钟（下限 %d）" % (gap, gap_min)
        except Exception:
            pass
    return True, "今日 %d/%d 条，间隔 OK" % (n, mx)


def form_check(arm, text):
    """形态闸：字数带与"具体内容"要求在臂定义里，不达标就没有可比性。"""
    a = ARMS.get(arm)
    if not a:
        return False, "未知臂 %s" % arm
    t = (text or "").strip()
    if not (a["min_len"] <= len(t) <= a["max_len"]):
        return False, "%s 臂字数 %d 不在 %d-%d" % (arm, len(t), a["min_len"], a["max_len"])
    if arm == "D" and not any(w in t for w in CONCRETE):
        return False, "D 臂要求含具体内容（%s 之一）" % "/".join(CONCRETE[:5])
    return True, "形态 OK"


def gates(text, ctx=""):
    """两道闸：social_practice.safe_to_send + social_comment_gen.gate。"""
    import social_practice as sp
    import social_comment_gen as cg
    ok1, w1 = sp.safe_to_send(text, ctx)
    ok2, w2, s = cg.gate(text, ctx=ctx, taken=(), corpus=())
    return (ok1 and ok2), {"safe_to_send": [ok1, w1], "gen_gate": [ok2, w2],
                           "taste": (s or {}).get("total"),
                           "verdict": (s or {}).get("verdict")}


def fetch_roots(aid, limit=20):
    """同源取第一页 root 评论（带 rpid），并滤掉注销号/空内容。"""
    import social_comment as sc
    mod, _ = sc._pw()
    from time import sleep
    with mod.sync_playwright() as p:
        ctx = sc._launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/video/av%s" % aid,
                    wait_until="domcontentloaded", timeout=60000)
            sleep(3)
            raw = pg.evaluate("""async(a)=>{const r=await fetch('https://api.bilibili.com/x/v2/reply?type=1&oid='
                +a+'&pn=1&ps=20&sort=1',{credentials:'include'});return await r.text();}""",
                              aid)
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    d = json.loads(raw or "{}")
    reps = ((d.get("data") or {}).get("replies") or [])[:limit]
    return sc.live_comments([
        {"rpid": str(x.get("rpid")), "author": ((x.get("member") or {}).get("uname") or ""),
         "text": ((x.get("content") or {}).get("message") or "")} for x in reps])


def run(arm, video, text, root="auto", dry=False, wait_s=120):
    import social_comment as sc
    a = ARMS[arm]
    okf, wf = form_check(arm, text)
    if not okf:
        return {"ok": False, "stage": "form", "why": wf}
    okg, g = gates(text, video)
    if not okg:
        return {"ok": False, "stage": "gate", "why": g}
    okc, wc = cap_check()
    if not okc:
        return {"ok": False, "stage": "cap", "why": wc}
    aid = sc.bv_to_aid(video)
    if not aid:
        return {"ok": False, "stage": "aid", "why": "解析 aid 失败"}
    if dry:
        return {"ok": True, "stage": "dry", "arm": arm, "aid": aid, "gates": g, "cap": wc}
    root_rpid = 0
    if a["kind"] == "reply":
        if root == "auto":
            roots = fetch_roots(aid)
            if not roots:
                return {"ok": False, "stage": "root", "why": "第一页没有可用 root 评论"}
            root_rpid = int(roots[0]["rpid"])
        else:
            root_rpid = int(root)
    # 发前先像人一样读一会儿（human_read），否则服务端看到的是一开页就调接口
    okp, res = sc.post_reply(aid, root_rpid, text, dry=False, read_first=True)
    rpid, code, toast = "", None, ""
    try:
        d = json.loads(res.get("text") or "{}")
        code = d.get("code")
        toast = d.get("message") or ""
        rpid = str((d.get("data") or {}).get("rpid") or "")
    except Exception:
        pass
    rec = {"action": "post", "arm": arm, "form": a["why"], "video": video, "aid": aid,
           "root": root_rpid, "text": text, "rpid": rpid, "code": code, "toast": toast,
           "ok": okp, "gates": g, "cap": wc}
    _log(rec)
    if not okp or not rpid:
        return {"ok": False, "stage": "post", "why": rec}
    if root_rpid:
        vis, vwhy = sc.verify_visible(aid, root_rpid, rpid, wait_s=wait_s)
    else:
        vis, vwhy = sc.verify_comment(aid, rpid, wait_s=max(wait_s, 300))
    _log({"action": "verify", "arm": arm, "aid": aid, "rpid": rpid, "root": root_rpid,
          "visible": vis, "why": vwhy,
          "verdict": "公开可见" if vis else "待审核-保留"})
    return {"ok": True, "stage": "posted", "rpid": rpid, "visible": vis, "why": vwhy}


def _log(rec):
    rec.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def self_test():
    """负控 ≥3 条 + 正向：闸该拒的必须拒，该过的必须过（用临时台账，不碰真账）。"""
    import tempfile
    cases = []
    pol = {"max_per_day": 2, "min_gap_min": 90, "stage": 0}
    tmp = tempfile.mkdtemp()
    p1, p2 = os.path.join(tmp, "a.jsonl"), os.path.join(tmp, "b.jsonl")
    day = "2026-11-18"
    now = datetime(2026, 11, 18, 20, 0, 0)
    # 负控 1：已发满 2 条 → 必须拒
    open(p1, "w").write(
        json.dumps({"action": "post", "ts": day + "T10:00:00", "rpid": "1", "ok": True}) + "\n" +
        json.dumps({"action": "post", "ts": day + "T12:00:00", "rpid": "2", "ok": True}) + "\n" +
        json.dumps({"action": "verify", "ts": day + "T12:02:00", "rpid": "2"}) + "\n")
    ok, why = cap_check(now, p1, p2, pol)
    cases.append(("负控1：发满即停（verify 行不算量）", (not ok) and "已发 2" in why))
    # 负控 2：间隔不足 → 必须拒
    open(p1, "w").write(json.dumps({"action": "post", "ts": "2026-11-18T19:40:00",
                                    "rpid": "3", "ok": True}) + "\n")
    ok, why = cap_check(now, p1, p2, pol)
    cases.append(("负控2：间隔 20<90 分钟拒", (not ok) and "分钟" in why))
    # 正向：0 条且无上帖 → 必须过
    open(p1, "w").write("")
    ok, why = cap_check(now, p1, p2, pol)
    cases.append(("正向：额度内放行", ok))
    # 负控 3：跨台账同 rpid 不许重复计数（否则上限被砍半）
    open(p1, "w").write(json.dumps({"action": "post", "ts": day + "T09:00:00",
                                    "rpid": "9", "ok": True}) + "\n")
    open(p2, "w").write(json.dumps({"action": "post", "ts": day + "T09:00:00",
                                    "rpid": "9", "ok": True}) + "\n")
    cases.append(("负控3：跨台账去重", posts_today(day, p1, p2) == 1))
    # 负控 4：形态闸——A 臂写 20 字必须拒
    cases.append(("负控4：A 臂超字数拒",
                  form_check("A", "这个转场衔接得太顺了我很喜欢这个节奏")[0] is False))
    cases.append(("负控5：D 臂无具体内容拒",
                  form_check("D", "真的很喜欢这个视频希望以后多更新一些内容吧")[0] is False))
    # 负控 6：导流文案必须被两道闸拦下
    okg, g = gates("加微信领剪辑素材包")
    cases.append(("负控6：导流被闸拦", okg is False))
    # 正向：真实短评论过双闸 + 形态
    t = "这个转场太顺了吧"
    okg, g = gates(t, "剪辑教学")
    cases.append(("正向：短句过双闸", okg and form_check("A", t)[0]))
    # 负控 7：无领域词的短句必须被 safe_to_send 拦（防"与本视频无关"）
    okg2, g2 = gates("哈哈哈太好笑了", "剪辑教学")
    cases.append(("负控7：无领域词被拦", okg2 is False))
    n = sum(1 for _, v in cases if v)
    for name, v in cases:
        if not v:
            print("  FAIL %s" % name)
    print("[self-test] %d/%d %s" % (n, len(cases), "PASS" if n == len(cases) else "FAIL"))
    return 0 if n == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--arm", choices=list(ARMS))
    ap.add_argument("--video", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--root", default="auto")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--wait", type=int, default=120)
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.status:
        ok, why = cap_check()
        print(json.dumps({"cap_ok": ok, "why": why,
                          "posts_today": posts_today(),
                          "last_post": last_post_ts()}, ensure_ascii=False, indent=1))
        return 0
    if not (a.arm and a.video and a.text):
        ap.print_help()
        return 2
    r = run(a.arm, a.video, a.text, root=a.root, dry=a.dry, wait_s=a.wait)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
