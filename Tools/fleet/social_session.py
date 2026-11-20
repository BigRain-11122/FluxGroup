#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_session.py — 把"一天怎么刷 B 站"写成可复算的日程（零 LLM、纯分布）。

CEO 2026-11-20「频率太小…你模拟人味，人每天刷几次b站，如何刷视频 如何评论什么的，
每次还要随机等，你自己去想」。

之前的错：定时器每 20 分钟拍一次、每拍决定"发不发"，于是行为轨迹是
**均匀的、分散的、一天零散几点**——真人是"一天进来三到五次，一次待十几分钟，
刷若干条，多数只看不动手，偶尔留一两条，然后走人"。

本模块只产出**日程与判决**，不发请求、不碰浏览器：
  · 每天 3-6 次会话（时段按双峰：上午、午休、晚间高峰，偶尔深夜尾）
  · 每次会话 6-35 分钟，浏览 3-12 条
  · 每次会话的"动手预算" 0-3 条，且 35% 的会话一条都不动手
  · 会话之间不是等距：间隔由会话起点自然决定

用法：
  python3 Tools/fleet/social_session.py --plan           # 打印今日计划
  python3 Tools/fleet/social_session.py --now            # 现在在不在会话里
  python3 Tools/fleet/social_session.py --self-test
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state")

# 人会在这几个小时里开始刷（不是均匀分布）：上午摸鱼、午休、晚饭后到睡前
START_HOURS = [8, 9, 10, 11, 12, 13, 14, 19, 20, 21, 22, 23]
START_WEIGHT = [1, 3, 4, 3, 5, 4, 2, 6, 8, 9, 7, 3]
# 深夜尾：偶尔一点还在刷（概率低，但存在）
NIGHT_HOURS = [0, 1]
NIGHT_P = 0.18


def plan_path(day):
    return os.path.join(STATE, "social-day-plan-%s.json" % day.strftime("%Y%m%d"))


def _weighted_hour(rng):
    return rng.choices(START_HOURS, weights=START_WEIGHT, k=1)[0]


# 一天的四个自然时段 + 深夜尾：人不是"随机挑 6 个小时"，而是
# 上午摸鱼、午休、下午、晚饭后到睡前各进来一次（每段有概率不去）。
BLOCKS = [(8, 11), (12, 14), (15, 17), (19, 22)]


def make_plan(day=None, rng=None):
    """生成一天的会话计划（不落地）。

    约束（自检守它们）：会话数 3-6、互不重叠、全天动手预算 0-8、2-6 点不活动。
    建模思路：先决定"今天哪几个时段会刷"（每段 75% 概率，至少 3 段），
    再在每个时段里随机一个起点——这样间隔天然是几小时，而不是均匀的 20 分钟一颗。
    """
    rng = rng or random
    day = day or datetime.now()

    picked = [b for b in BLOCKS if rng.random() < 0.75]
    while len(picked) < 3:                       # 至少刷 3 次
        b = rng.choice(BLOCKS)
        if b not in picked:
            picked.append(b)
    picked.sort()

    sessions, prev_end = [], None
    for lo, hi in picked:
        start = day.replace(hour=rng.randint(lo, hi), minute=rng.randint(0, 55),
                            second=0, microsecond=0)
        if prev_end and start < prev_end + timedelta(minutes=5):
            start = prev_end + timedelta(minutes=rng.randint(5, 30))
        dur = min(35.0, max(6.0, rng.lognormvariate(math.log(12.0), 0.55)))
        prev_end = start + timedelta(minutes=dur)
        passive = max(2, min(12, int(round(rng.gauss(6, 2.2)))))
        r = rng.random()
        # 目标每天 4-6 条：四个时段里两三次真留言、一两次只看
        budget = 0 if r < 0.25 else (1 if r < 0.65 else (2 if r < 0.90 else 3))
        sessions.append({"start": start.isoformat(timespec="seconds"),
                         "dur_min": round(dur, 1), "passive": passive, "social": budget})

    # 深夜尾：偶尔一点还在刷（只允许 0-1 点开始，且不与上一场重叠）
    if rng.random() < NIGHT_P:
        start = (day + timedelta(days=1)).replace(hour=rng.choice(NIGHT_HOURS),
                                                  minute=rng.randint(0, 40),
                                                  second=0, microsecond=0)
        if not prev_end or start >= prev_end + timedelta(minutes=5):
            sessions.append({"start": start.isoformat(timespec="seconds"),
                             "dur_min": round(min(20.0, rng.uniform(6, 20)), 1),
                             "passive": max(2, int(rng.gauss(5, 2))), "social": 0})

    # 全天动手预算封顶 8
    total = sum(s["social"] for s in sessions)
    for s in reversed(sessions):
        if total <= 8:
            break
        cut = min(s["social"], total - 8)
        s["social"] -= cut
        total -= cut
    return {"day": day.strftime("%Y-%m-%d"), "sessions": sessions,
            "ts": datetime.now().isoformat(timespec="seconds")}


def load_plan(day=None, rng=None):
    """取今天的计划，没有就生成并落盘（同一天内多次调用必须是同一份）。"""
    day = day or datetime.now()
    p = plan_path(day)
    try:
        d = json.load(open(p, encoding="utf-8"))
        if d.get("day") == day.strftime("%Y-%m-%d") and d.get("sessions"):
            return d
    except Exception:
        pass
    d = make_plan(day, rng)
    os.makedirs(STATE, exist_ok=True)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return d


def current(now=None, plan=None, rng=None):
    """现在是否在某个会话里；在的话返回带进度的会话，否则 None。"""
    now = now or datetime.now()
    plan = plan or load_plan(now, rng)
    for s in plan.get("sessions") or []:
        start = datetime.fromisoformat(s["start"])
        end = start + timedelta(minutes=float(s["dur_min"]))
        if start <= now < end:
            prog = progress(s["start"])
            return dict(s, end=end.isoformat(timespec="seconds"), progress=prog)
    return None


def progress(session_start):
    """会话进度（已浏览/已动手/已用时）。落盘，避免每拍重来。"""
    p = os.path.join(STATE, "social-session-progress.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        d = {}
    cur = d.get(session_start) or {"browsed": 0, "posted": 0, "first_ts": time.time()}
    return cur


def bump(session_start, key, n=1):
    p = os.path.join(STATE, "social-session-progress.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        d = {}
    cur = d.get(session_start) or {"browsed": 0, "posted": 0, "first_ts": time.time()}
    cur[key] = int(cur.get(key, 0)) + n
    d[session_start] = cur
    # 只留最近 3 天，避免文件无限长
    if len(d) > 20:
        for k in sorted(d, key=lambda x: d[x].get("first_ts", 0))[:-20]:
            d.pop(k, None)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return cur


def next_gap_s(session, rng=None):
    """会话内两个动作之间的等待：对数正态，中位约 3 分钟，长尾到 12 分钟。

    这是"人刷视频"的节奏：看完一条、滑一会儿、再看看下一条，
    不是每 20 分钟准点执行一次。
    """
    rng = rng or random
    g = rng.lognormvariate(math.log(180), 0.7)
    return int(max(45, min(720, g)))


def summary(plan=None):
    plan = plan or load_plan()
    ss = plan.get("sessions") or []
    return {"sessions": len(ss),
            "posts_budget": sum(int(s.get("social", 0)) for s in ss),
            "minutes": round(sum(float(s.get("dur_min", 0)) for s in ss), 1),
            "hours": [datetime.fromisoformat(s["start"]).strftime("%H:%M") for s in ss]}


def self_test():
    cases = []
    rng = random.Random(7)
    plans = [make_plan(datetime(2026, 11, 20), rng) for _ in range(300)]
    counts = [len(p["sessions"]) for p in plans]
    cases.append(("每天 3-6 次会话", min(counts) >= 3 and max(counts) <= 6))
    budgets = [sum(s["social"] for s in p["sessions"]) for p in plans]
    cases.append(("每天动手 0-8 条（实测 %.1f 均值）" % (sum(budgets) / len(budgets)),
                  min(budgets) >= 0 and max(budgets) <= 8))
    # 不能有两条会话重叠：人一次只能开一个页面
    overlap = 0
    for p in plans[:50]:
        ss = sorted(p["sessions"], key=lambda s: s["start"])
        for a, b in zip(ss, ss[1:]):
            ae = datetime.fromisoformat(a["start"]) + timedelta(minutes=a["dur_min"])
            if datetime.fromisoformat(b["start"]) < ae:
                overlap += 1
    cases.append(("会话不重叠（重叠 %d 次）" % overlap, overlap == 0))
    # 凌晨 2-6 点不应该起会话（除了 0/1 点的深夜尾）
    bad = sum(1 for p in plans for s in p["sessions"]
              if 2 <= datetime.fromisoformat(s["start"]).hour <= 6)
    cases.append(("2-6 点不开会话", bad == 0))
    # 只看不动手的会话要占相当比例（真人多数不留言）
    idle = sum(1 for p in plans for s in p["sessions"] if s["social"] == 0)
    tot = sum(len(p["sessions"]) for p in plans)
    cases.append(("无互动会话 15-35%%（实测 %.0f%%）" % (100 * idle / tot),
                  0.15 <= idle / tot <= 0.35))
    gs = [next_gap_s(None, rng) for _ in range(1000)]
    cases.append(("动作间隔中位 2-5 分钟", 120 <= sorted(gs)[500] <= 300))
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.plan:
        print(json.dumps(load_plan(), ensure_ascii=False, indent=1))
        print("汇总:", summary())
        return 0
    s = current()
    print("在会话中" if s else "当前不在会话")
    if s:
        print("  时段 %s ~ %s · 预算 %d 条 · 已发 %d · 已浏览 %d"
              % (s["start"][11:16], s["end"][11:16], s["social"],
                 s["progress"].get("posted", 0), s["progress"].get("browsed", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
