# -*- coding: utf-8 -*-
"""m-p4-behavior · 验收闸（规则版）

独立重算一遍，再和 behavior.json 逐人对账。任一条不过 rc=1。

判据：
  1 每个人都恰好有一条行为，不多不少（people.json 全量覆盖）
  2 动作只许四类：修 / 还 / 帮 / 守
  3 「修」的人必须真的有 lost 记忆；没有 lost 的人不许判修
  4 「还」的目标必须真的是给过他的人（方向不能反）
  5 「帮」的目标必须真的是他帮过的人
  6 四类计数与 summary 自洽

用法：python modules/m-p4-behavior/check.py [--quiet]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BEHAVIOR = os.path.join(HERE, "data", "behavior.json")
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")
MEMORY = os.path.join(ROOT, "modules", "m-p2-memory", "data", "memory.json")
BONDS = os.path.join(ROOT, "modules", "m-p3-bonds", "data", "bonds.json")
DEBT_MIN = 1
SURPLUS_MIN = 1
KINDS = ("修", "还", "帮", "守")


def load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    quiet = "--quiet" in argv
    bad = []
    if not os.path.exists(BEHAVIOR):
        print("FAIL 缺 behavior.json（先跑 python modules/m-p4-behavior/behavior.py）")
        return 1

    out = load(BEHAVIOR)
    people = {p.get("id") for p in load(PEOPLE, {"people": []}).get("people", [])}
    lost = {}
    for m in load(MEMORY, {"memories": []}).get("memories", []):
        if m.get("kind") == "lost":
            lost[m.get("person_id")] = lost.get(m.get("person_id"), 0) + 1

    # 独立重算关系方向
    gave, got = {}, {}
    for x in load(BONDS, {"pairs": []}).get("pairs", []):
        a, b = x.get("pair") or [None, None]
        h = x.get("help") or {}
        for giver, taker, n in ((a, b, int(h.get(a, 0))), (b, a, int(h.get(b, 0)))):
            if not n:
                continue
            gave.setdefault((giver, taker), 0)
            gave[(giver, taker)] += n
            got.setdefault(taker, 0)
            got[taker] += n

    # 独立重算「每人该做什么」：规则顺序 修 > 还 > 帮 > 守，ties 按 (-次数, id)
    led = {}
    for x in load(BONDS, {"pairs": []}).get("pairs", []):
        a, b = x.get("pair") or [None, None]
        h = x.get("help") or {}
        for giver, taker, n in ((a, b, int(h.get(a, 0))), (b, a, int(h.get(b, 0)))):
            if not n:
                continue
            led.setdefault(giver, {"given": 0, "received": 0, "creditors": [], "debtors": []})
            led.setdefault(taker, {"given": 0, "received": 0, "creditors": [], "debtors": []})
            led[giver]["given"] += n
            led[giver]["debtors"].append((taker, n))
            led[taker]["received"] += n
            led[taker]["creditors"].append((giver, n))

    expect = {}
    for pid in people:
        if lost.get(pid):
            expect[pid] = ("修", None)
            continue
        me = led.get(pid) or {"given": 0, "received": 0, "creditors": [], "debtors": []}
        debt = me["received"] - me["given"]
        if debt >= DEBT_MIN and me["creditors"]:
            expect[pid] = ("还", sorted(me["creditors"], key=lambda x: (-x[1], x[0]))[0][0])
        elif -debt >= SURPLUS_MIN and me["debtors"]:
            expect[pid] = ("帮", sorted(me["debtors"], key=lambda x: (-x[1], x[0]))[0][0])
        else:
            expect[pid] = ("守", None)

    rows = out.get("actions") or []
    seen = set()
    counts = {k: 0 for k in KINDS}
    for r in rows:
        pid = r.get("id")
        if pid in seen:
            bad.append(f"{pid}: 一天里出现两条行为")
        seen.add(pid)
        if pid not in people:
            bad.append(f"{pid}: 不在 people.json")
        act = r.get("action")
        if act not in KINDS:
            bad.append(f"{pid}: 动作非法 {act}")
            continue
        counts[act] += 1
        if act == "修" and not lost.get(pid):
            bad.append(f"{pid}: 判了修但其实没有 lost 记忆")
        if act != "修" and lost.get(pid):
            bad.append(f"{pid}: 有 lost 记忆却没判修（规则不是这么写的）")
        if act == "还":
            tgt = r.get("target")
            if not tgt:
                bad.append(f"{pid}: 还 缺目标")
            elif gave.get((tgt, pid), 0) <= 0:
                bad.append(f"{pid}: 还 的目标 {tgt} 并没有给过他")
        if act == "帮":
            tgt = r.get("target")
            if not tgt:
                bad.append(f"{pid}: 帮 缺目标")
            elif gave.get((pid, tgt), 0) <= 0:
                bad.append(f"{pid}: 帮 的目标 {tgt} 并不是他帮过的人")
        # 与独立重算逐人比对（动作 + 目标都要一模一样）
        want = expect.get(pid)
        if want and (act, r.get("target")) != want:
            bad.append(f"{pid}: 应为 {want[0]}/{want[1]}，实际 {act}/{r.get('target')}")

    missing = people - seen
    if missing:
        bad.append(f"有 {len(missing)} 人没有任何行为（例：{sorted(missing)[:3]}）")

    summary = out.get("summary") or {}
    for k in KINDS:
        if int(summary.get(k, -1)) != counts[k]:
            bad.append(f"summary[{k}]={summary.get(k)} 与逐行计数 {counts[k]} 不符")

    if bad:
        print(f"FAIL 行为校验失败 {len(bad)} 条")
        for m in bad[:20]:
            print("  -", m)
        return 1

    if not quiet:
        print(f"PASS 行为 · {len(rows)} 人全覆盖 · 修 {counts['修']} · 还 {counts['还']} · "
              f"帮 {counts['帮']} · 守 {counts['守']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
