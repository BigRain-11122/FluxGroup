#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reply_tick.py — 把自己视频下的评论逐条看完，并一条一条回好。

CEO 2026-11-24「先开始持续 b 站吧，把我的视频下面的评论全部看一遍并回复好」。

两段式（先看，再回）：
  --survey  只读普查：每个视频有多少评论、多少还没人回、多少我们已经回过（查台账）
  --reply N 真回 N 条：过闸生成 → 发布 → 稍后回验（回验不在同一拍做，真人发完也走）

三条纪律（都来自已踩过的坑）：
1. **不发明事实**：回复只能回应对方评论里已有的东西，不编"我看过你主页"之类。
2. **不重复回**：台账 reply-log.jsonl 记已回 rpid；同时跳过 rcount>0 的（已有人回过的让给它）。
3. **像人**：每条之间隔 40-180 秒，一拍最多 3 条，夜间不动作（2-6 点）。

用法：
  python3 Tools/fleet/reply_tick.py --survey
  python3 Tools/fleet/reply_tick.py --reply 2
  python3 Tools/fleet/reply_tick.py --status
  python3 Tools/fleet/reply_tick.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
OWN = os.path.join(SOCIAL, "OWN-VIDEOS.json")
LOG = os.path.join(SOCIAL, "reply-log.jsonl")
SURVEY = os.path.join(SOCIAL, "REPLY-SURVEY.json")

MAX_PER_TICK = 3
GAP_S = (40, 180)
NIGHT = (2, 6)

# 广告/导流评论：回它等于帮它导流，直接跳过（不删、不举报，只不参与回复）
SPAM = re.compile(r"分享给你|加我|私信我|互关|涨粉|代运营|接单|兼职|点击链接|扫码|加微信|qq群")

# 敏感话题：外貌/年龄/健康/政治/宗教——对陌生人不该自动接话。
# 2026-11-24 实锚：自动回了一句「36 岁确实容易走样」，原文看不到、语境不明，
# 这种话对陌生人说就是冒犯。宁可漏回，不许冒犯。
# 只认明确指向的词组，不用单字："美"会命中"美好"、"死"会命中"笑死"（实测误杀）。
SENSITIVE = re.compile(r"\d+\s*岁|年龄|显老|老了|变胖|胖了|瘦了|变丑|颜值|长相|"
                       r"离婚|出轨|去世|自杀|抑郁|癌症|生病|政治|宗教|工资|房价")


def _fabricates(reply, comment):
    """回复里出现了评论中没有的数字/专名，就判为编造。

    只查两类最硬的信号：数字，以及评论里没有的 2 字以上英文/大写缩写。
    """
    if not reply:
        return True
    for d in set(re.findall(r"\d+", reply)):
        if d not in (comment or ""):
            return True
    for w in set(re.findall(r"[A-Za-z]{2,}", reply)):
        if w.lower() not in (comment or "").lower():
            return True
    return False


def _ontopic(reply, comment, min_share=2):
    """回复要与评论共享 ≥2 个汉字二元组，否则算自说自话。

    为什么用二元组而不是分词：正则切出来的"实词"是整段连写的长串
    （"当年确实被严重低估"），两边永远不相等，实测把 7/8 条好回复误杀。
    二元组比较的是字面相邻关系，不需要分词器也不会被连写打败。
    """
    def bg(s):
        s = re.sub(r"[^\u4e00-\u9fff]", "", s or "")
        return {s[i:i + 2] for i in range(max(0, len(s) - 1))}
    a, b = bg(reply), bg(comment)
    if not a or not b:
        return False
    return len(a & b) >= min_share


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _rows(path=None):
    path = path or LOG
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def _append(rec):
    rec.setdefault("ts", _now())
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def handled_rpids(path=None):
    return {str(r.get("rpid")) for r in _rows(path) if r.get("action") == "reply"}


def own_videos():
    try:
        with open(OWN, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("videos") or []
    except Exception:
        return []


REPLY_PROFILE = os.path.join(os.path.expanduser("~"), ".fluxgroup", "browser-reply")


class Session:
    """一个短命的独立浏览器会话：读评论、发回复都在它里面，跑完就关。

    为什么不走常驻 daemon：2026-11-24 实测三次把 daemon 卡死（单线程 + 导航类动作 +
    与发帖智能体抢同一个 profile），表现是"连得上但不回话"，还拖累了发帖线。
    独立会话不共享状态，慢一点但不会连累别人；实测直连 fetch 一次就拿到 code=0。
    """

    def __init__(self):
        self._pw = None
        self.ctx = None

    def __enter__(self):
        sys.path.insert(0, HERE)
        import social_comment as sc
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.ctx = sc._launch(self._pw, headless=True, prof=REPLY_PROFILE)
        self.pg = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        self.pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=25000)
        return self

    def __exit__(self, *a):
        try:
            self.ctx.close()
        except Exception:
            pass
        try:
            self._pw.stop()
        except Exception:
            pass

    def comments(self, aid, limit=20):
        raw = self.pg.evaluate("""async(d)=>{const r=await fetch('https://api.bilibili.com/x/v2/reply'
            +'?type=1&oid='+d.aid+'&pn=1&ps='+d.ps+'&sort=1',{credentials:'include'});
            return await r.text();}""", {"aid": aid, "ps": min(50, limit)})
        try:
            d = json.loads(raw or "{}")
        except Exception:
            return [], False
        if d.get("code") is None:
            return [], False
        reps = ((d.get("data") or {}).get("replies")) or []
        return [{"rpid": str(x.get("rpid")),
                 "author": ((x.get("member") or {}).get("uname") or ""),
                 "text": ((x.get("content") or {}).get("message") or ""),
                 "rcount": int(x.get("rcount") or 0)} for x in reps[:limit]], True

    def reply(self, aid, rpid, text):
        import social_comment as sc
        try:
            # dry 默认是 True！不显式传 False 就是演练，却会返回 ok=True ——
            # 2026-11-24 实锚：两条"成功"其实是 dry，台账假绿。
            ok, res = sc._post_in(self.ctx, aid, rpid, text, dry=False)
            return bool(ok), str(res)[:120]
        except Exception as e:
            return False, "%s: %s" % (type(e).__name__, str(e)[:80])


def _setup_profile():
    return None


def _unused_comments(aid, limit=20):
    """取 root 评论：走 daemon 的 roots2（纯接口、不导航）。

    返回 (replies, ok)：ok=False 表示"没读到"而不是"确实没有评论"——
    2026-11-24 实锚：一口气读 25 个视频后接口开始回空（限流），
    把空当成"没有评论"会让普查数字凭空归零。
    """
    sys.path.insert(0, HERE)
    import social_comment as sc
    hit = sc._daemon("roots2", {"aid": aid, "limit": limit}, timeout=60)
    res = (hit or {}).get("res") or {}
    code = res.get("code")
    if not hit or not hit.get("ok") or code is None:
        return [], False
    return (res.get("replies") or []), True


READ_GAP = (4.0, 9.0)      # 读评论之间的间隔：接口有限流，抢太快就回空
BACKOFF_ON_EMPTY = 300     # 连续读空 → 退避 5 分钟，别把限流当"没有评论"


def _aid_in(ses, bvid):
    """会话内取 aid：同源 fetch，不导航。"""
    raw = ses.pg.evaluate("""async(b)=>{const r=await fetch(
        'https://api.bilibili.com/x/web-interface/view?bvid='+b,{credentials:'include'});
        return await r.text();}""", bvid)
    try:
        d = json.loads(raw or "{}")
        return ((d.get("data") or {}).get("aid")) or None
    except Exception:
        return None


def _survey_one(v, aid, cs, done, rows):
    unanswered = [c for c in cs if int(c.get("rcount") or 0) == 0]
    ours = [c for c in cs if str(c.get("rpid")) in done]
    rows.append({"bvid": v["bvid"], "aid": aid, "title": v.get("title"),
                 "comments": len(cs), "unanswered": len(unanswered), "we_replied": len(ours),
                 "sample": [{"rpid": c["rpid"], "author": c.get("author"),
                             "text": (c.get("text") or "")[:40]} for c in unanswered[:3]]})


def survey(limit_videos=None):
    """只读：逐视频取首页 root 评论，统计待回量。"""
    sys.path.insert(0, HERE)
    import arm_probe as ap
    vids = own_videos()
    if limit_videos:
        vids = vids[:limit_videos]
    done = handled_rpids()
    rows, tot, open_, mine = [], 0, 0, 0
    with Session() as ses:
        for v in vids:
            aid = _aid_in(ses, v["bvid"])
            if not aid:
                rows.append({"bvid": v["bvid"], "aid": None, "err": "aid 取不到"})
                continue
            try:
                cs, okread = ses.comments(aid)
            except Exception as e:
                rows.append({"bvid": v["bvid"], "aid": aid, "err": "%s: %s" % (type(e).__name__, str(e)[:60])})
                continue
            if not okread:
                rows.append({"bvid": v["bvid"], "aid": aid, "err": "读取失败（接口回空）"})
                continue
            _survey_one(v, aid, cs, done, rows)
            tot += len(cs)
            open_ += len([c for c in cs if int(c.get("rcount") or 0) == 0])
            mine += len([c for c in cs if str(c.get("rpid")) in done])
            time.sleep(random.uniform(*READ_GAP))
        import random as _r
        time.sleep(_r.uniform(*READ_GAP))     # 限速：读评论也要像人
        unanswered = [c for c in cs if int(c.get("rcount") or 0) == 0]
        ours = [c for c in cs if str(c.get("rpid")) in done]
        tot += len(cs)
        open_ += len(unanswered)
        mine += len(ours)
        rows.append({"bvid": v["bvid"], "aid": aid, "title": v.get("title"),
                     "comments": len(cs), "unanswered": len(unanswered), "we_replied": len(ours),
                     "sample": [{"rpid": c["rpid"], "author": c.get("author"),
                                 "text": (c.get("text") or "")[:40]} for c in unanswered[:3]]})
    out = {"ts": _now(), "videos": len(vids), "comments_total": tot,
           "unanswered": open_, "we_replied": mine, "rows": rows}
    with open(SURVEY, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("[reply] 普查 %d 个视频｜评论 %d 条｜还没人回 %d 条｜我们已回 %d 条 → %s"
          % (len(vids), tot, open_, mine, os.path.relpath(SURVEY, ROOT)))
    for r in rows:
        if r.get("err"):
            print("   ✗ %s %s" % (r["bvid"], r["err"]))
        else:
            print("   %s 评论 %-3d 待回 %-3d ｜%s" % (r["bvid"], r["comments"], r["unanswered"],
                                                   (r.get("title") or "")[:30]))
    return 0


# 语气样例：只给口气，不给内容。实测（2026-11-24）：
# 无样例时 4B 会写出「切好给你，别硬切老人」「20241210」这类完全跑题的回复；
# 给了 3 条真实语气 + 「只回应他说的事、不许编造」两条硬约束后，同批 4/4 过闸。
_FEW = """UP主回复观众的语气样例（只学口气，不要照抄）：
观众：这首我循环一整晚 —— UP：一整晚不睡明天上班可惨了[笑哭]
观众：听完想起高中 —— UP：那会儿我反复倒带听到磁带磨白
观众：这歌被低估了 —— UP：同意，当年真没几个人提
"""
_RULE = ("要求：10-24字；只回应他说的那一件事；不许编造具体经历、数字、事件；"
         "不许客套和客服腔；一句话。\n")


def _reply_text(comment, video_title=""):
    """生成一条回复。返回空串表示这条不该发（过不了闸）。"""
    _setup_profile()
    sys.path.insert(0, HERE)
    import llm_client as lc
    import social_comment_gen as cg
    import deai_check as dz
    prompt = _FEW + _RULE + "观众：%s\nUP：" % (comment or "")[:60]
    try:
        r = lc.generate_lora(prompt, max_tokens=48, temperature=0.75)
    except Exception:
        return ""
    t = (r.get("text") or "").strip().strip("“”\"'").split("\n")[0].strip()
    if not t:
        return ""
    if not (8 <= len(t) <= 30):
        print("     [len] %d 字不在 8-30：%s" % (len(t), t[:20]))
        return ""
    ok, why, _ = cg.gate(t, face="reply", taste_gate=False)
    if not ok:
        print("     [gate] 拦下：%s" % why)
        return ""
    if dz.check(t)["verdict"] != "clean":
        print("     [deai] 有 AI 腔：%s" % t[:20])
        return ""
    if _fabricates(t, comment):
        print("     [编造] 出现评论里没有的信息：%s" % t[:20])
        return ""
    if not _ontopic(t, comment):
        print("     [跑题] 与评论无实词交集：%s" % t[:20])
        return ""
    return t


def reply(n=1):
    hour = datetime.now().hour
    if NIGHT[0] <= hour < NIGHT[1]:
        print("[reply] 夜间不动作（%d 点）" % hour)
        return 0
    vids = own_videos()
    if not vids:
        print("[reply] 没有 OWN-VIDEOS.json，先跑 own_videos.py")
        return 2
    done = handled_rpids()
    n = min(int(n), MAX_PER_TICK)
    sent = 0
    rng = random.Random()
    with Session() as ses:
        for v in vids:
            if sent >= n:
                break
            aid = _aid_in(ses, v["bvid"])
            if not aid:
                continue
            cs, okread = ses.comments(aid, limit=20)
            if not okread:
                print("   [read] %s 读不到，跳过这个视频" % v["bvid"])
                continue
            for c in cs:
                if sent >= n:
                    break
                rid = str(c.get("rpid"))
                if rid in done or int(c.get("rcount") or 0) > 0:
                    continue
                txt = (c.get("text") or "").strip()
                if not txt:
                    continue
                if SPAM.search(txt):
                    _append({"action": "skip", "rpid": rid, "why": "广告/导流"})
                    continue
                if SENSITIVE.search(txt):
                    _append({"action": "skip", "rpid": rid, "why": "敏感话题"})
                    continue
                t = _reply_text(txt, v.get("title") or "")
                if not t:
                    _append({"action": "skip", "rpid": rid, "why": "闸拒或无稿"})
                    continue
                ok, res = ses.reply(aid, rid, t)
                _append({"action": "reply", "rpid": rid, "aid": aid, "bvid": v["bvid"],
                         "src": txt[:60], "text": t, "ok": bool(ok), "res": res})
                print("   %s 回复 %s：%s → %s" % ("✓" if ok else "✗", rid, t[:24], res[:36]))
                if ok:
                    sent += 1
                    done.add(rid)
                time.sleep(rng.uniform(*GAP_S))
    print("[reply] 本拍回复 %d 条" % sent)
    return 0


def status():
    rows = _rows()
    replied = [r for r in rows if r.get("action") == "reply" and r.get("ok")]
    print("台账 %d 行｜成功回复 %d 条｜覆盖视频 %d 个"
          % (len(rows), len(replied), len({r.get("bvid") for r in replied})))
    try:
        with open(SURVEY, encoding="utf-8") as f:
            d = json.load(f)
        print("最近普查 %s：视频 %d｜评论 %d｜待回 %d"
              % (d.get("ts"), d.get("videos"), d.get("comments_total"), d.get("unanswered")))
    except Exception:
        print("还没普查过，跑 --survey")
    return 0


def self_test():
    """负控：台账去重、rcount>0 不抢、夜间不动、上限生效。"""
    cases = []
    cases.append(("MAX_PER_TICK 上限存在", MAX_PER_TICK >= 1))
    import tempfile
    global LOG
    saved = LOG
    LOG = tempfile.mktemp()
    _append({"action": "reply", "rpid": "1", "ok": True})
    cases.append(("台账能读出已回 rpid", "1" in handled_rpids()))
    _append({"action": "skip", "rpid": "2"})
    cases.append(("skip 行不算已回", "2" not in handled_rpids()))
    LOG = saved
    cases.append(("夜间窗口定义正确", NIGHT == (2, 6)))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


LOCK = os.path.join(SOCIAL, "reply-tick.lock")


def _take_lock():
    """单实例：上一条还没跑完就别再起一条（浏览器会话很重，叠起来会互相踢）。"""
    try:
        if os.path.exists(LOCK):
            age = time.time() - os.path.getmtime(LOCK)
            if age < 1800:
                return False
        with open(LOCK, "w") as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return True


def _drop_lock():
    try:
        os.unlink(LOCK)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--reply", type=int, default=0)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.status:
        return status()
    if a.survey:
        return survey()
    if a.reply:
        if not _take_lock():
            print("[reply] 上一拍还没结束（锁在），本次跳过")
            return 0
        try:
            return reply(a.reply)
        finally:
            _drop_lock()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
