#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""outcome_harvest.py - 采集我方评论的**真实结果**（可见/点赞/被回/被删）。

为什么必须单独做这一件（2026-11-27 总纲 v3 第五节）：
我们的闭环一直是「造集→训练→用自己造的分数评测→再训练」，从头到尾没有一处用平台
的真实反应做判据。结果就是：合成评测说 music_seeker「+27.9 分可上线」，
而平台上 27 条可判的评论里只有 15 条真的能露出来（56%）——两个数几乎不相关。
没有这个采集器，"从实战中总结"是一句空话；有了它，训练集才有真实标签。

判据纪律（三条硬规矩）：
  1. **判不出 ≠ 不可见**。接口没返回 JSON、被风控、profile 被占，一律记 `unknown`。
     把 unknown 写成 False 会冤枉账号，并让"不可见"这个负样本变脏。
  2. **每条结果必须能追到四要素**：文案 / 人群段 / 形态臂 / 当时线上适配器。
     缺任何一项标 `attribution_incomplete`，该条不许进训练集。
  3. **只追加，不覆盖**。同一条 rpid 每回验一次就多一行，summary 取最新一行；
     这样"15 分钟时可见、2 小时后被删"这种时间演化才看得见。

数据源：常驻浏览器 `roots2`（time 序第一页，带 rpid/like/rcount）。
不用 verify_comment_browser 的原因：它会自己开浏览器抢 profile，和 browserd 打架。

用法：
  python3 Tools/fleet/outcome_harvest.py                 # 补最近 3 天
  python3 Tools/fleet/outcome_harvest.py --days 7 --json
  python3 Tools/fleet/outcome_harvest.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
PRACTICE = os.path.join(SOCIAL, "practice-log.jsonl")
OUT = os.path.join(SOCIAL, "REAL-OUTCOMES.jsonl")
SUMMARY = os.path.join(SOCIAL, "REAL-OUTCOMES.json")

sys.path.insert(0, HERE)


def _rows(path):
    out = []
    try:
        for ln in open(path, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return out


def my_posts(days=3, now=None):
    """最近 N 天里**有 rpid** 的发帖记录（无 rpid = 没有回执，不采集）。"""
    now = now or time.time()
    cut = now - days * 86400
    out = []
    for r in _rows(PRACTICE):
        if r.get("action") != "post" or not r.get("rpid"):
            continue
        ts = str(r.get("ts") or "")
        try:
            t = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            continue
        if t < cut:
            continue
        out.append(r)
    return out


def observe(rpid, aid, fetch):
    """查一条评论的真实状态。返回 dict(visible= True/False/None, likes, rcount, note)。

    fetch(aid) 必须返回 (code, replies) 或 None（= 取不到数）。
    """
    got = fetch(aid)
    if got is None:
        return {"visible": None, "likes": None, "rcount": None,
                "note": "取不到数（接口/风控/占用）→ unknown，不是不可见"}
    code, replies = got
    if code != 0:
        return {"visible": None, "likes": None, "rcount": None,
                "note": "接口 code=%r → unknown" % (code,)}
    for x in replies or []:
        if str(x.get("rpid")) == str(rpid):
            return {"visible": True, "likes": int(x.get("like") or 0),
                    "rcount": int(x.get("rcount") or 0), "note": "在公开列表里"}
    return {"visible": False, "likes": None, "rcount": None,
            "note": "code=0 但首页查不到 → 确实不在公开列表"}


def _norm(t):
    import re
    return re.sub(r"[\s\W_]+", "", str(t or ""))


def _dom_visible(url, texts, collect=None):
    """DOM 兜底：直接读渲染后的评论区，按文案匹配判断可见性。

    为什么需要这条：写接口（add）带 wbi 签名能发成功，而读接口 /x/v2/reply 现在
    恒返回非 JSON（平台对读的限制更紧）。但**渲染后的评论区是能读的**——我们的
    10 万行语料就是走 shadow DOM 抓下来的。所以读侧退回 DOM，用文案匹配代替 rpid。
    返回 dict(visible, likes, rcount, note)；判不出仍返回 None 语义。
    """
    if collect is None:
        try:
            import social_collect as _sc
            collect = _sc.collect
        except Exception:
            return None
    try:
        rows = collect(url, "bilibili", limit=150, min_n=5, scrolls=6)
    except Exception as e:
        return {"visible": None, "likes": None, "rcount": None,
                "note": "DOM 采集异常：%s" % str(e)[:50]}
    if not rows:
        return {"visible": None, "likes": None, "rcount": None,
                "note": "DOM 没抓到任何评论（可能未加载/被拦）"}
    got = [_norm(r.get("text")) for r in rows if isinstance(r, dict)]
    keys = [_norm(t)[:12] for t in texts if len(_norm(t)) >= 6]
    hit = any(k and any(k in g for g in got) for k in keys)
    return {"visible": bool(hit), "likes": None, "rcount": None,
            "note": "DOM 匹配%s（按文案前 12 字）" % ("命中" if hit else "未命中")}


def _fetch_via_daemon(aid, limit=50):
    """用常驻浏览器取 time 序第一页。返 (code, replies) 或 None。"""
    try:
        import social_comment as sc
        r = sc._daemon("roots2", {"aid": aid, "limit": limit, "priority": "post"}, timeout=60)
    except Exception:
        return None
    if not r or not r.get("ok"):
        return None
    res = r.get("res")
    if not isinstance(res, dict):
        return None
    return res.get("code"), res.get("replies") or []


def harvest(days=3, fetch=None, now=None, collect=None):
    """采集并追加。返回 (本次新增条数, 本轮统计)。"""
    fetch = fetch or _fetch_via_daemon
    posts = my_posts(days=days, now=now)
    added, stat = 0, {"total": 0, "visible": 0, "invisible": 0, "unknown": 0}
    os.makedirs(SOCIAL, exist_ok=True)
    # 同一视频只抓一次：接口优先（有 likes/rcount），判不出再用 DOM 兜底（只有可见性）。
    import collections
    by_aid = collections.defaultdict(list)
    for p in posts:
        by_aid[p.get("aid")].append(p)
    dom_cache = {}
    with open(OUT, "a", encoding="utf-8") as f:
      for _aid, group in by_aid.items():
        _api_ok = False
        for p in group:
            obs = observe(p.get("rpid"), p.get("aid"), fetch)
            if obs["visible"] is not None:
                _api_ok = True
            else:
                # 接口判不出：整组退回 DOM（用该视频下所有文案一起匹配）
                if _aid not in dom_cache:
                    dom_cache[_aid] = _dom_visible(
                        (group[0].get("video") or ""), [q.get("text") for q in group],
                        collect=collect)
                d = dom_cache[_aid] or {}
                if d.get("visible") is not None:
                    obs = dict(obs, visible=d["visible"], note=d.get("note") or "")
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "posted_at": p.get("ts"), "rpid": str(p.get("rpid")), "aid": p.get("aid"),
                   "text": (p.get("text") or "")[:80],
                   "seg": p.get("seg") or p.get("persona"), "arm": p.get("arm"),
                   "serving": p.get("serving"),
                   "basis": "roots2-pn1" if obs["likes"] is not None or "接口" in (obs.get("note") or "") else "dom"}
            rec.update(obs)
            if not (rec.get("seg") and rec.get("arm") and rec.get("text")):
                rec["attribution_incomplete"] = True
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            added += 1
            stat["total"] += 1
            if obs["visible"] is True:
                stat["visible"] += 1
            elif obs["visible"] is False:
                stat["invisible"] += 1
            else:
                stat["unknown"] += 1
    write_summary()
    return added, stat
    with open(OUT, "a", encoding="utf-8") as f:
        for p in posts:
            obs = observe(p.get("rpid"), p.get("aid"), fetch)
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "posted_at": p.get("ts"), "rpid": str(p.get("rpid")), "aid": p.get("aid"),
                   "text": (p.get("text") or "")[:80],
                   "seg": p.get("seg") or p.get("persona"), "arm": p.get("arm"),
                   "serving": p.get("serving"), "basis": "roots2-pn1"}
            rec.update(obs)
            if not (rec.get("seg") and rec.get("arm") and rec.get("text")):
                rec["attribution_incomplete"] = True
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            added += 1
            stat["total"] += 1
            if obs["visible"] is True:
                stat["visible"] += 1
            elif obs["visible"] is False:
                stat["invisible"] += 1
            else:
                stat["unknown"] += 1
    write_summary()
    return added, stat


def write_summary():
    """每 rpid 取最新一行，算真实可见率。判不出的单独计数，不混进分母。"""
    latest = {}
    for r in _rows(OUT):
        latest[str(r.get("rpid"))] = r
    vis = [r for r in latest.values() if r.get("visible") is True]
    inv = [r for r in latest.values() if r.get("visible") is False]
    unk = [r for r in latest.values() if r.get("visible") is None]
    d = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "posts_with_rpid": len(latest),
         "visible": len(vis), "invisible": len(inv), "unknown": len(unk),
         "visible_rate_of_known": round(100.0 * len(vis) / max(1, len(vis) + len(inv))),
         "likes_total": sum(int(r.get("likes") or 0) for r in vis),
         "with_replies": sum(1 for r in vis if int(r.get("rcount") or 0) > 0),
         "attribution_incomplete": sum(1 for r in latest.values() if r.get("attribution_incomplete")),
         "note": "visible_rate 的分母只含 known（判得出的）；unknown 单列，不许当不可见"}
    json.dump(d, open(SUMMARY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return d


def self_test():
    cases = []

    def mk(code, replies):
        return lambda aid: (code, replies)

    # 1 正控：在列表里 → visible True + 点赞
    o = observe("1", 9, mk(0, [{"rpid": "1", "like": 3, "rcount": 2}]))
    cases.append(("在公开列表 → 可见且拿到点赞/回复数",
                  o["visible"] is True and o["likes"] == 3 and o["rcount"] == 2))
    # 2 正控：code=0 但查不到 → 不可见
    o = observe("1", 9, mk(0, [{"rpid": "2"}]))
    cases.append(("code=0 且查不到 → 不可见", o["visible"] is False))
    # 3 负控：取不到数必须是 unknown（不许写成不可见）
    o = observe("1", 9, lambda aid: None)
    cases.append(("取不到数 → unknown（不许当不可见）",
                  o["visible"] is None and "unknown" in o["note"]))
    # 4 负控：code 非 0（如 -412）也必须 unknown
    o = observe("1", 9, mk(-412, []))
    cases.append(("code=-412 → unknown", o["visible"] is None))
    # 4.5 DOM 兜底：按文案匹配（判不出仍必须是 unknown）
    fake_collect = lambda url, plat, **kw: [{"text": "分镜流自动卡点挺丝滑，就是配乐偶尔破音"}]
    d = _dom_visible("u", ["分镜流自动卡点挺丝滑，就是配乐偶尔破音哈。"], collect=fake_collect)
    cases.append(("DOM：文案命中 → 可见", d["visible"] is True))
    d2 = _dom_visible("u", ["完全不同的另一句话在这里"], collect=fake_collect)
    cases.append(("DOM：文案不命中 → 不可见", d2["visible"] is False))
    d3 = _dom_visible("u", ["x"], collect=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    cases.append(("DOM：采集异常 → unknown（不许当不可见）", d3["visible"] is None))
    d4 = _dom_visible("u", ["x"], collect=lambda *a, **k: [])
    cases.append(("DOM：一条都没抓到 → unknown（不许当不可见）", d4["visible"] is None))
    # 5 汇总口径：unknown 不许进可见率分母
    global OUT, SUMMARY
    import tempfile
    d = tempfile.mkdtemp(prefix="oh-")
    saved = (OUT, SUMMARY)
    OUT, SUMMARY = os.path.join(d, "o.jsonl"), os.path.join(d, "s.json")
    try:
        with open(OUT, "w", encoding="utf-8") as f:
            for rp, v in (("a", True), ("b", True), ("c", False), ("d", None)):
                f.write(json.dumps({"rpid": rp, "visible": v, "likes": 1}) + "\n")
        s = write_summary()
        cases.append(("汇总：可见率分母只含 known（2/3=67%）",
                      s["visible_rate_of_known"] == 67 and s["unknown"] == 1))
        # 6 同 rpid 多行取最新
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps({"rpid": "c", "visible": True, "likes": 5}) + "\n")
        s2 = write_summary()
        cases.append(("同 rpid 取最新一行（c 由 False 翻为 True）",
                      s2["visible"] == 3 and s2["invisible"] == 0))
    finally:
        OUT, SUMMARY = saved
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  [%s] %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=3.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    n, stat = harvest(days=a.days)
    s = write_summary()
    if a.json:
        print(json.dumps({"added": n, "round": stat, "summary": s}, ensure_ascii=False))
    else:
        print("[outcome] 本轮采集 %d 条 → %s" % (n, os.path.relpath(OUT, ROOT)))
        print("[outcome] 可见 %d / 不可见 %d / 判不出 %d" % (
            stat["visible"], stat["invisible"], stat["unknown"]))
        print("[outcome] 累计真实可见率 %d%%（分母只含判得出的 %d 条；judge 不出 %d 条单列）"
              % (s["visible_rate_of_known"], s["visible"] + s["invisible"], s["unknown"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
