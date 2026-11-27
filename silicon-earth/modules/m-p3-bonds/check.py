# -*- coding: utf-8 -*-
"""m-p3-bonds · 验收闸

不看"跑没跑过"，只看账与事件流对不对得上。任一条不过就 rc=1。

判据：
  1 每一次帮助类事件（help/teach/repair，两人以上）恰好记进一条账
  2 账里的两个人都在 people.json 里（外键）
  3 账里引用的事件 id 真实存在于 events.jsonl
  4 每个方向的次数与事件流逐条重算一致（不是自说自话）
  5 net / net_creditor / repaid 三个派生字段与计数自洽
  6 同一对人不出现两次；pair[0] < pair[1]；不出现自己帮自己

用法：python modules/m-p3-bonds/check.py [--quiet]
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BONDS = os.path.join(HERE, "data", "bonds.json")
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")
HELP_TYPES = ("help", "teach", "repair")


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    quiet = "--quiet" in argv
    bad = []

    if not os.path.exists(BONDS):
        print("FAIL 缺 bonds.json（先跑 python modules/m-p3-bonds/bonds.py）")
        return 1

    bonds = load_json(BONDS)
    people = {p.get("id") for p in load_json(PEOPLE).get("people", [])}
    events = [json.loads(l) for l in open(EVENTS, encoding="utf-8") if l.strip()]
    eids = {e.get("id") for e in events}

    # 从事件流独立重算（不复用 bonds.py 的实现）
    expect = Counter()
    per_event = {}
    for e in events:
        if e.get("type") not in HELP_TYPES:
            continue
        actors = e.get("actors") or []
        if len(actors) < 2 or actors[0] == actors[1]:
            continue
        g, t = actors[0], actors[1]
        if g not in people or t not in people:
            bad.append(f"事件 {e.get('id')} 的 actor 不在 people.json")
            continue
        a, b = sorted((g, t))
        expect[(a, b, g)] += 1
        per_event[e.get("id")] = (a, b)

    pairs = bonds.get("pairs") or []
    seen = set()
    total_help = 0

    for x in pairs:
        a, b = x.get("pair") or [None, None]
        if a is None or b is None:
            bad.append("有账缺 pair")
            continue
        if a == b:
            bad.append(f"自己帮自己：{a}")
        if a >= b:
            bad.append(f"pair 未按字典序：{[a, b]}")
        key = (a, b)
        if key in seen:
            bad.append(f"同一对出现两条账：{[a, b]}")
        seen.add(key)
        if a not in people or b not in people:
            bad.append(f"账里的外键不存在：{[a, b]}")

        help_counts = x.get("help") or {}
        ga, gb = int(help_counts.get(a, 0)), int(help_counts.get(b, 0))
        total_help += ga + gb
        exp_a, exp_b = expect.get((a, b, a), 0), expect.get((a, b, b), 0)
        if (ga, gb) != (exp_a, exp_b):
            bad.append(f"{[a, b]} 计数与事件流不符：账 {ga}/{gb} vs 重算 {exp_a}/{exp_b}")

        if int(x.get("net", -1)) != abs(ga - gb):
            bad.append(f"{[a, b]} net 与计数不符")
        want = a if ga > gb else (b if gb > ga else None)
        if x.get("net_creditor") != want:
            bad.append(f"{[a, b]} net_creditor 应为 {want}")
        if bool(x.get("repaid")) != bool(ga and gb):
            bad.append(f"{[a, b]} repaid 与计数不符")

        for eid in x.get("events") or []:
            if eid not in eids:
                bad.append(f"{[a, b]} 引用了不存在的事件 {eid}")

    expanded = sum(v for v in expect.values())
    if total_help != expanded:
        bad.append(f"覆盖不全：账里 {total_help} 次 vs 事件流 {expanded} 次")

    # 每个人被记录一次的账必须能在 events 样本里找到 —— 只做提示，不作判据

    if bad:
        print(f"FAIL 关系账校验失败 {len(bad)} 条")
        for m in bad[:20]:
            print("  -", m)
        return 1

    if not quiet:
        s = bonds.get("summary") or {}
        print(f"PASS 关系账 · {s.get('help_events')} 次出手 · {s.get('pairs')} 对 · "
              f"还过 {s.get('repaid_pairs')} · 单向 {s.get('one_way_pairs')} · 覆盖 {expanded}/{expanded}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
