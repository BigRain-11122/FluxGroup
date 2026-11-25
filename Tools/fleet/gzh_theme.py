#!/usr/bin/env python3
"""主题季调度：现在该写哪个主题、这季四类内容还差几篇、这篇稿子属不属于当季。

为什么要这个：CEO 令「每段时间一个主题」「突发事件不要硬蹭」。
硬蹭热点的可机检特征只有一个——**写完这篇，当季主题没有任何进展**。
所以需要一个能回答「这篇算不算本季」的东西，而不是靠事后回忆。

三个动作：
  --status      看当前季（按日期自动定位）、剩余周数、四类还差几篇
  --check 稿子  判这篇属不属于当季、大概属哪类、缺哪个类型的建议
  --season S3   指定看某一季

判定说明（诚实）：
  · 季节定位按日期，硬边界；
  · 「属不属于本季」= 稿中出现本季关键词 vs 其他季关键词的比例，是**启发式**，
    只用来提示，不是硬闸；
  · 「属哪类」按四类关键词命中数初判，作者可以否。

用法：
  gzh_theme.py --status
  gzh_theme.py --check 稿子.md
  gzh_theme.py --self-test
退出码：0 正常 / 1 不属于当季或判不出 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SPEC = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "THEME-SEASONS-v1.json")


def load(path=None):
    return json.load(open(path or SPEC, encoding="utf-8"))


def season_at(spec, day=None):
    """按日期定位季。返回 (season, 状态) 状态 ∈ in/早于首季/晚于末季。"""
    day = day or date.today()
    seasons = spec["seasons"]
    for s in seasons:
        if date.fromisoformat(s["from"]) <= day <= date.fromisoformat(s["to"]):
            return s, "in"
    if day < date.fromisoformat(seasons[0]["from"]):
        return seasons[0], "早于首季"
    return seasons[-1], "晚于末季"


def days_left(season, day=None):
    day = day or date.today()
    return (date.fromisoformat(season["to"]) - day).days


def counts(spec, season):
    """该季四类目标篇数（按季长等比缩放）。"""
    shape = spec["season_shape"]
    base = sum(shape["四类配比"].values()) if False else None
    ratio = shape["四类配比"]
    base_n = sum(ratio.values())
    weeks = (date.fromisoformat(season["to"]) -
             date.fromisoformat(season["from"])).days / 7
    target_total = round(sum(shape["每季篇数"]) / 2 * (weeks / 5)) or base_n
    per = {k: max(1, round(v / base_n * target_total)) for k, v in ratio.items()}
    return per, target_total


def quadrant_of(spec, text):
    """按关键词命中数初判内容类型。返回 (类型, 命中词, 各类型分数)。"""
    kws = spec["quadrant_detect"]
    scores = {k: sum(text.count(w) for w in v) for k, v in kws.items() if not k.startswith("_")}
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "", [], scores
    hits = [w for w in kws[best] if w in text][:4]
    return best, hits, scores


def season_match(spec, text, season):
    """本季 vs 其他季 的关键词命中对比。返回 (是否属于, 本季命中, 最强对手季)。"""
    def hit(se):
        return sum(text.count(w) for w in se.get("关键词") or [])
    mine = hit(season)
    others = [(hit(s), s["id"]) for s in spec["seasons"] if s["id"] != season["id"]]
    others.sort(reverse=True)
    best_other = others[0] if others else (0, "-")
    return mine >= max(1, best_other[0]), mine, best_other


def check_article(spec, text, day=None):
    season, st = season_at(spec, day)
    ok, mine, other = season_match(spec, text, season)
    quad, hits, scores = quadrant_of(spec, text)
    return {"season": season, "season_state": st, "in_season": ok,
            "mine": mine, "other": other, "quadrant": quad,
            "quadrant_hits": hits, "scores": scores}


BANK_TOPIC = ("同一块屏，为什么新势力要点三层、传统车企要五层。" * 2
              + "同一个关闭车道保持，一台点两下，一台点五下，指尖在屏幕上找了三圈。"
              + "我把两条路径画在白板上，一共十一步，差的是层级不是功能。"
              + "层级定错的代价不只在多点两下，在于用户每次都要重新找一遍。")
SHADOW_TOPIC = "深色模式发灰，不是屏幕问题。用测色仪量面板反射率，8% 到 20% 的灰阶缺失。"


def self_test():
    fails = []
    spec = load()
    seasons = spec["seasons"]

    # 1 季定位必须落在季内（拿每季起始日试）
    for s in seasons:
        got, st = season_at(spec, date.fromisoformat(s["from"]))
        if got["id"] != s["id"] or st != "in":
            fails.append(f"季定位错：{s['id']} 起始日判成 {got['id']}({st})")

    # 2 季首尾边界：末季末日必须落在末季
    last = seasons[-1]
    got, st = season_at(spec, date.fromisoformat(last["to"]))
    if got["id"] != last["id"] or st != "in":
        fails.append("末季末日定位错")

    # 3 早于首季 / 晚于末季
    got, st = season_at(spec, date(2020, 1, 1))
    if st != "早于首季":
        fails.append("2020 年应判「早于首季」")
    got, st = season_at(spec, date(2030, 1, 1))
    if st != "晚于末季":
        fails.append("2030 年应判「晚于末季」")

    # 4 层级类稿子必须判进 S1（且不属于 S2）
    s1 = seasons[0]
    r = check_article(spec, BANK_TOPIC, date.fromisoformat("2026-12-10"))
    if r["season"]["id"] != "S1":
        fails.append("2026-12-10 应属 S1")
    if not r["in_season"]:
        fails.append(f"层级主题稿被判不属于 S1（本季 {r['mine']} vs 对手 {r['other']}）")
    if r["quadrant"] != "硬核":
        fails.append(f"层级稿应判硬核，实际 {r['quadrant']}")

    # 5 负控：色阶稿在 S1 期间应判「不属于当季」（提醒作者这是 S2 的题）
    r2 = check_article(spec, SHADOW_TOPIC, date.fromisoformat("2026-12-10"))
    if r2["in_season"]:
        fails.append("色阶稿在 S1 期间被判属于当季（应提示属 S2）")

    # 6 四类配比必须覆盖四类且每类≥1
    per, total = counts(spec, s1)
    if set(per) != {"实操", "科技", "大众", "硬核"}:
        fails.append(f"四类配比缺项：{per}")
    if min(per.values()) < 1:
        fails.append("存在某类目标篇数为 0（会让壁垒退化）")
    if total < 4:
        fails.append(f"季度目标篇数 {total} 太少")

    # 7 无信号文本不许硬判类型
    if quadrant_of(spec, "今天天气不错")[0] != "":
        fails.append("无信号文本被硬判类型")

    # 8 突发事件规则必须存在三分类且都有时限
    bn = spec.get("breaking_news", {})
    for k in ("A-并进主题", "B-第二落点", "C-不写"):
        if k not in bn.get("三分类", {}):
            fails.append(f"突发事件缺分类 {k}")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 8/8  ({len(seasons)} 季定位/边界/归属/四类配比/无信号/突发事件三分类)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--check", dest="chk")
    ap.add_argument("--season", default=None)
    ap.add_argument("--date", default=None, help="按指定日期定位季（YYYY-MM-DD，调试用）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    spec = load()
    day = date.fromisoformat(a.date) if a.date else date.today()

    if a.chk:
        text = open(a.chk, encoding="utf-8").read()
        r = check_article(spec, text, day)
        s = r["season"]
        print(f"当前季 {s['id']}「{s['主题']}」（{s['from']} → {s['to']}，剩 {days_left(s, day)} 天）")
        print(f"本季关键词命中 {r['mine']}；最强对手季 {r['other'][1]} 命中 {r['other'][0]}")
        if not r["in_season"]:
            print(f"\n⚠ 这篇不像本季的题——更像 {r['other'][1]}（{r['other'][0]} 次 vs 本季 {r['mine']} 次）。")
            print("  要么改成本季角度，要么明确标成「跨季」，别当成当季进度。")
        if r["quadrant"]:
            print(f"\n初判类型：{r['quadrant']}（命中 {r['quadrant_hits']}）")
            print(f"  四类分数：{ {k: v for k, v in r['scores'].items() if v} }")
        else:
            print("\n初判类型：判不出（无类型关键词）——检查是否写成了纯叙述")
        per, total = counts(spec, s)
        print(f"\n本季目标约 {total} 篇，四类配比 {per}")
        return 0 if r["in_season"] else 1

    if a.season:
        s = [x for x in spec["seasons"] if x["id"] == a.season]
        if not s:
            print(f"没有 {a.season}；可选 {[x['id'] for x in spec['seasons']]}", file=sys.stderr)
            return 1
        s = s[0]
    else:
        s, st = season_at(spec, day)
        print(f"（{day} 定位）" + ("" if st == "in" else f" 状态：{st}"))

    per, total = counts(spec, s)
    print(f"\n{s['id']}「{s['主题']}」  {s['from']} → {s['to']}"
          f"（剩 {days_left(s, day)} 天）")
    print(f"为什么现在做：{s['为什么现在做']}")
    print(f"目标 {total} 篇，四类配比 {per}")
    print(f"关键词：{ '、'.join(s.get('关键词') or []) }")
    print("\n可写选题：")
    for t in s.get("可写") or []:
        print(f"  · {t}")
    if day < date.fromisoformat(s["from"]):
        print("\n⚠ 还没到这一季，先把上一季收口（每季最后一篇要做回顾）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
