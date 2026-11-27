#!/usr/bin/env python3
"""排期器：把频率、四类配比、深稿位、热点机动位排成真实日历，并自查冲突。

为什么要它：现在有四份文档各说一段频率（ANNUAL-PLAN 每周2篇 / HOT-FIRST 每天1篇 /
CONTENT-OPS 四类配比 / THEME-SEASONS 每季8-12篇），谁的数都对不上。
**排期必须是一个能算出来的东西，不是几段文字。**

调配规则（写死在这里，改就改这一处）：
  · 周一到周五 5 个固定位，周六 1 个机动位（热点专用，非必须），周日空
  · 周一固定 = 深稿（long，2000-3500 字）；其余固定位 = 快评（short，600-1800 字）
  · 深稿只承接「硬核」，硬核配额超出深稿位时顺延给「科技」
  · 每季四类按 实操3:大众3:科技2:硬核2 等比缩放，缩放误差 ≤1 篇
  · 机动位只在热点属 A/B 类时使用；用了就等于当周多一篇，不用不补

用法：
  gzh_schedule.py --weeks 4         # 排未来 4 周
  gzh_schedule.py --season S1       # 排某一季全季
  gzh_schedule.py --check            # 只做冲突自查
  gzh_schedule.py --self-test
退出码：0 排期成立 / 1 冲突 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SPEC = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "THEME-SEASONS-v1.json")

FIXED_PER_WEEK = 5      # 周一~周五
MOTION_DAY = 5          # 周六：机动/热点位（0=周一）
LONG_DAY = 0            # 周一：深稿位
PUBLISH_AT = "07:30"    # 群发时刻（抢通勤时段）
MAX_PER_DAY = 1         # 订阅号每天只能群发 1 次
DEEP_QUADRANTS = ("硬核", "科技")   # 能承接深稿的类型，按优先级


def load(path=None):
    return json.load(open(path or SPEC, encoding="utf-8"))


def season_quota(spec, season, weeks):
    """按季长算四类目标篇数（固定位口径，不含机动位）。"""
    ratio = spec["season_shape"]["四类配比"]
    total = FIXED_PER_WEEK * weeks
    base = sum(ratio.values())
    quota = {k: max(1, round(v / base * total)) for k, v in ratio.items()}
    # 修：四舍五入会让总和对不上，把差额压到最大项上
    diff = total - sum(quota.values())
    if diff:
        k = max(quota, key=lambda x: quota[x])
        quota[k] = max(1, quota[k] + diff)
    return quota, total


def plan_weeks(spec, season, start, weeks):
    """排出 weeks 周。返回 [{date, weekday, slot, quadrant, kind, season}]。"""
    quota, total = season_quota(spec, season, weeks)
    rem = dict(quota)
    long_left = weeks                      # 深稿位 = 每周 1 个
    rows = []
    pools = season.get("选题池") or {}
    fallback = list(season.get("可写") or [])
    if not pools:
        print(f"⚠ {season['id']} 没有按类分池（选题池），只能从「可写」轮流取题——"
              f"容易出现「硬核深稿配大众题」，需人工改。", file=sys.stderr)
    ti = {k: 0 for k in ("硬核", "实操", "大众", "科技")}
    fi = 0

    # 先定深稿：硬核优先，不够就科技
    hard_cap = min(rem.get("硬核", 0), long_left)
    rem["硬核"] = rem.get("硬核", 0) - hard_cap
    tech_long = long_left - hard_cap
    rem["科技"] = max(0, rem.get("科技", 0) - tech_long)

    for w in range(weeks):
        base = start + timedelta(days=7 * w)
        for d in range(7):
            day = base + timedelta(days=d)
            if day > date.fromisoformat(season["to"]):
                break
            if d == 6:                      # 周日空
                rows.append({"date": day.isoformat(), "weekday": "日", "slot": "空",
                             "quadrant": "", "kind": "", "season": season["id"]})
                continue
            if d == MOTION_DAY:
                rows.append({"date": day.isoformat(), "weekday": "六", "slot": "机动",
                             "quadrant": "热点", "kind": "short|long", "season": season["id"],
                             "note": "仅 A/B 类热点可用；不用不补"})
                continue
            if d == LONG_DAY and w < long_left:
                q = "硬核" if w < hard_cap else "科技"
                kind = "long"
            else:
                # 固定位（快评）：按剩余配额从多到少取，硬核不放快评位（篇幅不符）
                cand = {k: v for k, v in rem.items() if k != "硬核" and v > 0}
                if not cand:
                    cand = {"大众": 1}
                q = max(cand, key=lambda k: cand[k])
                rem[q] = rem.get(q, 0) - 1
                kind = "short"
            if pools.get(q):
                lst = pools[q]
                topic = lst[ti[q] % len(lst)]
                ti[q] += 1
            elif fallback:
                topic = fallback[fi % len(fallback)]
                fi += 1
            else:
                topic = ""
            rows.append({"date": day.isoformat(), "weekday": "一二三四五六日"[d],
                         "slot": "固定", "quadrant": q, "kind": kind,
                         "season": season["id"], "topic": topic})
    # 季回顾必须压轴（该季最后一篇）。它豁免「深稿必须在周一」这条——
    # 季收口比固定节拍重要，这是唯一允许的例外，其余深稿仍在周一。
    fixed = [r for r in rows if r["slot"] == "固定"]
    rev = [r for r in fixed if "回顾" in (r.get("topic") or "")]
    if rev and fixed:
        last = fixed[-1]
        if last is not rev[0]:
            rev[0]["topic"], last["topic"] = last["topic"], rev[0]["topic"]
        last["quadrant"], last["kind"] = "硬核", "long"
        rev[0]["quadrant"], rev[0]["kind"] = "科技", "short"

    return rows, quota, total


def check(rows, spec, season, weeks):
    """冲突自查。返回 (fails, stats)。"""
    fails = []
    by_day = {}
    for r in rows:
        by_day.setdefault(r["date"], []).append(r)
    for d, rs in by_day.items():
        fixed = [x for x in rs if x["slot"] == "固定"]
        if len(fixed) > MAX_PER_DAY:
            fails.append(f"{d} 有 {len(fixed)} 篇群发，超过每天 {MAX_PER_DAY} 次上限")

    longs = [x for x in rows if x["kind"] == "long"]
    if len(longs) != weeks:
        fails.append(f"深稿 {len(longs)} 篇，应为每周 1 篇共 {weeks} 篇")
    for r in longs:
        if r["weekday"] != "一" and "回顾" not in (r.get("topic") or ""):
            fails.append(f"{r['date']} 深稿不在周一（会打乱固定节拍）")
    fixed_all = [x for x in rows if x["slot"] == "固定"]
    if fixed_all and "回顾" in (fixed_all[-1].get("topic") or ""):
        pass
    elif any("回顾" in (x.get("topic") or "") for x in fixed_all):
        fails.append("季回顾没有压轴（该季最后一篇必须是回顾）")

    # 四类配额误差 ≤1
    quota, total = season_quota(spec, season, weeks)
    got = {}
    for r in rows:
        if r["slot"] == "固定":
            got[r["quadrant"]] = got.get(r["quadrant"], 0) + 1
    for k in quota:
        if abs(got.get(k, 0) - quota[k]) > 1:
            fails.append(f"{k} 实际 {got.get(k,0)} 篇，目标 {quota[k]}，偏差 >1")

    if not any(x["slot"] == "机动" for x in rows):
        fails.append("没有机动位（热点无处插入）")

    stats = {"fixed": sum(1 for x in rows if x["slot"] == "固定"),
             "long": len(longs), "motion": sum(1 for x in rows if x["slot"] == "机动"),
             "by_quadrant": got, "quota": quota, "weeks": weeks}
    return fails, stats


def render(rows, stats, season):
    print(f"{season['id']}「{season['主题']}」  {season['from']} → {season['to']}"
          f"  固定 {stats['fixed']} 篇（含深稿 {stats['long']}）+ 机动 {stats['motion']} 位")
    print(f"发布时刻 {PUBLISH_AT} · 每天最多 {MAX_PER_DAY} 次群发\n")
    print(f"{'日期':11}{'星期':4}{'位':5}{'类型':6}{'篇幅':6}选题建议")
    for r in rows:
        if r["slot"] == "空":
            continue
        kind = {"long": "深稿", "short": "快评", "short|long": "待定"}.get(r["kind"], r["kind"])
        print(f"{r['date']:11}{r['weekday']:4}{r['slot']:5}{r['quadrant']:6}{kind:6}"
              f"{(r.get('topic') or r.get('note') or '')[:30]}")
    print(f"\n四类：实际 {stats['by_quadrant']}  目标 {stats['quota']}")


def self_test():
    fails = []
    spec = load()
    s1 = spec["seasons"][0]
    start = date.fromisoformat(s1["from"])
    # 首季从 12-01 起算，取 4 周做样本
    weeks = 4
    rows, quota, total = plan_weeks(spec, s1, start, weeks)

    f, st = check(rows, spec, s1, weeks)
    if f:
        fails.append(f"正控[4 周排期] 自带冲突：{f[:2]}")

    # 1 每天最多 1 篇
    if any(len([x for x in rows if x["date"] == d and x["slot"] == "固定"]) > 1
           for d in {x["date"] for x in rows}):
        fails.append("负控[单日多篇] 未检出")

    # 2 深稿必须正好每周 1 篇且在周一
    if st["long"] != weeks:
        fails.append(f"深稿数 {st['long']} != {weeks}")

    # 3 硬核不许放进快评位（篇幅契约：硬核 2000-3500 > 快评上限 1800）
    bad = [r for r in rows if r["quadrant"] == "硬核" and r["kind"] == "short"]
    if bad:
        fails.append(f"硬核被排进快评位 {len(bad)} 处")

    # 4 机动位必须存在
    if st["motion"] == 0:
        fails.append("无机动位")

    # 5 负控：故意把两篇塞同一天，check 必须报
    broken = [dict(rows[1])] + [dict(rows[1], quadrant="大众")] + rows[2:]
    fb, _ = check(broken, spec, s1, weeks)
    if not any("上限" in x for x in fb):
        fails.append("负控[同日双发] check 未报")

    # 6 负控：把深稿挪到周二，check 必须报
    broken2 = []
    for r in rows:
        r = dict(r)
        if r["kind"] == "long" and r["weekday"] == "一":
            r["weekday"] = "二"
        broken2.append(r)
    fb2, _ = check(broken2, spec, s1, weeks)
    if not any("深稿不在周一" in x for x in fb2):
        fails.append("负控[深稿错日] check 未报")

    # 6b 季回顾必须落在最后一个固定位
    fixed_rows = [r for r in rows if r["slot"] == "固定"]
    if any("回顾" in (r.get("topic") or "") for r in fixed_rows):
        if "回顾" not in (fixed_rows[-1].get("topic") or ""):
            fails.append("负控[季回顾] 未被排到最后一位")

    # 7 配额总和 = 周数×5（固定位）
    if sum(quota.values()) != weeks * FIXED_PER_WEEK:
        fails.append(f"配额总和 {sum(quota.values())} != {weeks*FIXED_PER_WEEK}")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for x in fails:
            print("  -", x, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 7/7  (4 周 {st['fixed']} 篇/深稿 {st['long']}/机动 {st['motion']} 位)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=int, default=4)
    ap.add_argument("--season", default=None)
    ap.add_argument("--from", dest="start", default=None, help="起始日（默认季首日或今天）")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    spec = load()
    if a.season:
        found = [s for s in spec["seasons"] if s["id"] == a.season]
        if not found:
            print(f"没有 {a.season}", file=sys.stderr)
            return 1
        season = found[0]
    else:
        today = date.today()
        season = next((s for s in spec["seasons"]
                       if date.fromisoformat(s["from"]) <= today <= date.fromisoformat(s["to"])),
                      spec["seasons"][0])

    if a.start:
        start = date.fromisoformat(a.start)
    elif date.fromisoformat(season["from"]) <= date.today() <= date.fromisoformat(season["to"]):
        start = date.today()
    else:
        start = date.fromisoformat(season["from"])

    rows, quota, total = plan_weeks(spec, season, start, a.weeks)
    fails, stats = check(rows, spec, season, a.weeks)

    if a.json:
        print(json.dumps({"season": season["id"], "rows": rows, "stats": stats,
                          "fails": fails}, ensure_ascii=False, indent=1))
        return 0 if not fails else 1

    render(rows, stats, season)
    if fails:
        print(f"\nFAIL {len(fails)} 项冲突", file=sys.stderr)
        for x in fails:
            print("  -", x, file=sys.stderr)
        return 1
    print("\nPASS 排期无冲突")
    return 0


if __name__ == "__main__":
    sys.exit(main())
