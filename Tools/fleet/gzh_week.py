#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_week.py — 「这周写什么」的唯一机器面。

CEO 2026-11-27 令：「每周要有一个主题，围绕主题去写」。
季（4-6 周）是主干，周是执行单位：一周一个主题，篇目从这个主题里长出来。

为什么要有这支工具：以前选题散在 TOPICS / 季池 / 热点三处，写之前没人能回答
"本周主题是什么"，于是写出来的东西互相不认识。周主题一旦成文件，
"跑题"就从感觉变成了可判的事。

用法：
  python3 Tools/fleet/gzh_week.py                  # 本周
  python3 Tools/fleet/gzh_week.py --date 2026-12-10
  python3 Tools/fleet/gzh_week.py --plan 4         # 往后看 4 周
  python3 Tools/fleet/gzh_week.py --json
  python3 Tools/fleet/gzh_week.py --self-test
退出码：0 正常 / 1 今天不在任何一周（季外）/ 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "THEME-SEASONS-v1.json")


def _spec():
    # 内容已迁 BigLoom，本仓留软链；软链断了就没有唯一事实，必须说出来
    if not os.path.exists(SPEC):
        raise SystemExit("缺 THEME-SEASONS-v1.json（%s）——周主题没有正身，不许凭记忆写" % SPEC)
    return json.load(open(SPEC, encoding="utf-8"))


def weeks(spec=None):
    spec = spec or _spec()
    return spec.get("weeks") or []


def for_date(day, spec=None):
    """返回该日期所属周。不在任何一周返回 None（季外不硬编）。"""
    d = day.isoformat() if isinstance(day, date) else str(day)
    for w in weeks(spec):
        if w["from"] <= d <= w["to"]:
            return w
    return None


def season_of(week, spec=None):
    spec = spec or _spec()
    for s in spec.get("seasons") or []:
        if s["id"] == week.get("season"):
            return s
    return None


def check_continuity(spec=None):
    """周与周之间不许有空档或重叠——这是唯一能证明"每周都有主题"的判据。"""
    ws = sorted(weeks(spec), key=lambda w: w["from"])
    bad = []
    for a, b in zip(ws, ws[1:]):
        nxt = (date.fromisoformat(a["to"]) + timedelta(days=1)).isoformat()
        if b["from"] != nxt:
            bad.append("%s→%s 与 %s 之间有%s" % (
                a["week"], a["to"], b["week"],
                "空档" if b["from"] > nxt else "重叠"))
    for w in ws:
        if not (w.get("主题") or "").strip():
            bad.append("%s 没有主题" % w.get("week"))
        if not w.get("篇"):
            bad.append("%s 没有篇目（等于这周没说要写什么）" % w.get("week"))
        for p in w.get("篇") or []:
            if not (p.get("topic") or "").strip() or not (p.get("quadrant") or "").strip():
                bad.append("%s 有篇目缺 quadrant 或 topic" % w.get("week"))
    return bad


def render(w, spec=None):
    s = season_of(w, spec)
    lines = [
        "本周 %s｜%s" % (w["week"], w["主题"]),
        "  %s → %s%s" % (w["from"], w["to"],
                        "｜季 %s「%s」" % (s["id"], s["主题"]) if s else "｜季外"),
        "  为什么这周写这个：%s" % (w.get("为什么这周写这个") or "（未写）"),
        "  关键词：%s" % "、".join(w.get("关键词") or []),
        "  本周要写：",
    ]
    for p in w.get("篇") or []:
        lines.append("    · [%s] %s" % (p["quadrant"], p["topic"]))
    return "\n".join(lines)


def self_test():
    spec = _spec()
    fails = []

    # 1 连续性：无空档、无重叠
    bad = check_continuity(spec)
    if bad:
        fails.append("周结构有问题：" + "；".join(bad[:4]))

    # 2 周主题不重复（同一个主题写两周＝没分周）
    seen = {}
    for w in weeks(spec):
        t = w.get("主题")
        if t in seen:
            fails.append("周主题重复：%s 与 %s 都是「%s」" % (seen[t], w["week"], t))
        seen[t] = w["week"]

    # 3 每周能解析回一个真实日期（不留死周）
    for w in weeks(spec):
        mid = date.fromisoformat(w["from"]) + (date.fromisoformat(w["to"]) -
                                               date.fromisoformat(w["from"])) / 2
        got = for_date(mid, spec)
        if not got or got["week"] != w["week"]:
            fails.append("%s 的中段日期解析不到自己（%s）" % (w["week"], got))

    # 4 负控：把一周的主题抠掉，连续性检查必须能红
    import copy
    broken = copy.deepcopy(spec)
    broken["weeks"][0]["主题"] = "  "
    if not check_continuity(broken):
        fails.append("负控失效：主题抠空仍然判过——这说明这道闸不会红")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 4/4（连续性/主题不重复/日期可解析/负控能红）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--plan", type=int, default=0, help="往后看 N 周")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    spec = _spec()
    if a.plan:
        ws = sorted(weeks(spec), key=lambda w: w["from"])
        start = for_date(date.fromisoformat(a.date) if a.date else date.today(), spec)
        idx = next((i for i, w in enumerate(ws) if start and w["week"] == start["week"]), 0)
        for w in ws[idx:idx + a.plan]:
            print(render(w, spec))
            print()
        return 0

    day = date.fromisoformat(a.date) if a.date else date.today()
    w = for_date(day, spec)
    if not w:
        print("%s 不在任何一周里（季外/换季空档）——先排周，不许凭感觉写。" % day)
        return 1
    if a.json:
        print(json.dumps(w, ensure_ascii=False, indent=1))
    else:
        print(render(w, spec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
