# -*- coding: utf-8 -*-
"""m-w4-history · 验收闸（纪年）

判据：
  1 首纪从第 1 天开始，末纪到 time.day 结束，中间无缝无重
  2 每个非首纪的起始日，事件流里必须有 blackout 或 breach
  3 各纪事件数之和 == 事件总数
  4 每纪的 dominant_region 是该纪事件最多的区域（同数按 id）
  5 名字里必须含 dominant_region 的区域名；段号与顺序一致
  6 不许有空段（from_day > to_day），不许同名重复

用法：python modules/m-w4-history/check.py [--quiet]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HIST = os.path.join(HERE, "data", "history.json")
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
TIME = os.path.join(ROOT, "modules", "m-w2-clock", "data", "time.json")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")
MARK_TYPES = ("blackout", "breach")


def load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    quiet = "--quiet" in argv
    bad = []
    if not os.path.exists(HIST):
        print("FAIL 缺 history.json（先跑 python modules/m-w4-history/history.py）")
        return 1

    hist = load(HIST)
    day = load(TIME, {"day": 0}).get("day", 0)
    names = {r["id"]: r["name"] for r in load(REGIONS, {"regions": []}).get("regions", [])}
    events = [json.loads(l) for l in open(EVENTS, encoding="utf-8") if l.strip()]
    mark_days = {int(e.get("day") or 0) for e in events if e.get("type") in MARK_TYPES}

    eras = hist.get("eras") or []
    if not eras:
        print("FAIL 没有任何纪元")
        return 1

    if eras[0].get("from_day") != 1:
        bad.append(f"首纪不是从第 1 天开始：{eras[0].get('from_day')}")
    if eras[-1].get("to_day") != day:
        bad.append(f"末纪没到第 {day} 天：{eras[-1].get('to_day')}")

    total = 0
    seen_names = set()
    for i, e in enumerate(eras):
        f, t = e.get("from_day"), e.get("to_day")
        if not isinstance(f, int) or not isinstance(t, int) or f > t:
            bad.append(f"第 {i+1} 纪区间非法：{f}-{t}")
            continue
        if e.get("index") != i + 1:
            bad.append(f"第 {i+1} 纪的 index={e.get('index')} 与顺序不符")
        if i > 0:
            prev = eras[i - 1].get("to_day")
            if f != prev + 1:
                bad.append(f"第 {i+1} 纪起点 {f} 与上一纪结束 {prev} 不连续")
            if f not in mark_days:
                bad.append(f"第 {i+1} 纪起点 {f} 不是大事日（黑屏/失守）")

        seg = [x for x in events if f <= int(x.get("day") or 0) <= t]
        if int(e.get("events", -1)) != len(seg):
            bad.append(f"第 {i+1} 纪事件数 {e.get('events')} 与实算 {len(seg)} 不符")
        total += len(seg)

        per = {}
        for x in seg:
            rid = x.get("region_id")
            per[rid] = per.get(rid, 0) + 1
        dom = sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if per else None
        if e.get("dominant_region") != dom:
            bad.append(f"第 {i+1} 纪 dominant_region 应为 {dom}，实为 {e.get('dominant_region')}")

        nm = e.get("name") or ""
        if dom and names.get(dom) and names[dom] not in nm:
            bad.append(f"第 {i+1} 纪名字里没有区域名「{names.get(dom)}」：{nm}")
        if not nm:
            bad.append(f"第 {i+1} 纪没有名字")
        if nm in seen_names:
            bad.append(f"纪元名重复：{nm}")
        seen_names.add(nm)

    if total != len(events):
        bad.append(f"覆盖不全：各纪合计 {total} 条，事件流 {len(events)} 条")

    if bad:
        print(f"FAIL 纪年校验失败 {len(bad)} 条")
        for m in bad[:20]:
            print("  -", m)
        return 1

    if not quiet:
        print(f"PASS 纪年 · {len(eras)} 纪 · 覆盖 {total}/{len(events)} 事件 · 末纪 {eras[-1]['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
