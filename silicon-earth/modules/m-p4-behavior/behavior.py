# -*- coding: utf-8 -*-
"""m-p4-behavior · 需求与行为（规则版 v0.1）

不接模型，先定规则：每天给每个人一条「今天做什么」，理由必须能从记忆与关系里查出来。

动作四类（不含模型判断，全部可由数据重算）：
  修  ← 有 lost 记忆（记忆断了，先修）
  还  ← 欠账 ≥ 2（收得多、给得少：去还）
  帮  ← 给出比收到多 ≥ 2（有余力：去帮）
  守  ← 以上都不成立（本事：把手上未了的事守着）

输出：modules/m-p4-behavior/data/behavior.json
运行：python modules/m-p4-behavior/behavior.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")
MEMORY = os.path.join(ROOT, "modules", "m-p2-memory", "data", "memory.json")
BONDS = os.path.join(ROOT, "modules", "m-p3-bonds", "data", "bonds.json")
TIME = os.path.join(ROOT, "modules", "m-w2-clock", "data", "time.json")
OUT = os.path.join(DATA, "behavior.json")

DEBT_MIN = 1          # 欠一次就该去还（规则版先不设门槛）
SURPLUS_MIN = 1       # 多给一次就算有余力


def read_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def build_ledger(bonds):
    """pid -> {"given": n, "received": n, "creditors": [(谁给过我, 次数)], "debtors": [(我帮过谁, 次数)]}"""
    led = {}
    for x in bonds.get("pairs") or []:
        a, b = x.get("pair") or [None, None]
        if not a or not b:
            continue
        h = x.get("help") or {}
        ga, gb = int(h.get(a, 0)), int(h.get(b, 0))
        if ga:
            la = led.setdefault(a, {"given": 0, "received": 0, "creditors": [], "debtors": []})
            lb = led.setdefault(b, {"given": 0, "received": 0, "creditors": [], "debtors": []})
            la["given"] += ga
            la["debtors"].append((b, ga))
            lb["received"] += ga
            lb["creditors"].append((a, ga))
        if gb:
            lb = led.setdefault(b, {"given": 0, "received": 0, "creditors": [], "debtors": []})
            la = led.setdefault(a, {"given": 0, "received": 0, "creditors": [], "debtors": []})
            lb["given"] += gb
            lb["debtors"].append((a, gb))
            la["received"] += gb
            la["creditors"].append((b, gb))
    return led


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    day = read_json(TIME, {"day": 0}).get("day", 0)
    people = read_json(PEOPLE, {"people": []}).get("people", [])
    memories = read_json(MEMORY, {"memories": []}).get("memories", [])
    bonds = read_json(BONDS, {"pairs": []})

    lost = {}
    for m in memories:
        if m.get("kind") == "lost":
            lost[m.get("person_id")] = lost.get(m.get("person_id"), 0) + 1

    led = build_ledger(bonds)
    actions = []
    counts = {"修": 0, "还": 0, "帮": 0, "守": 0}

    for p in people:
        pid = p.get("id")
        row = {"id": pid, "region_id": p.get("region_id")}
        if lost.get(pid):
            row.update(action="修", why="有 %d 段记忆断了" % lost[pid], target=None)
        else:
            me = led.get(pid) or {"given": 0, "received": 0, "creditors": [], "debtors": []}
            debt = me["received"] - me["given"]
            if debt >= DEBT_MIN:
                top = sorted(me["creditors"], key=lambda x: (-x[1], x[0]))[0]
                row.update(action="还", why="欠 %d 次未还" % debt, target=top[0])
            elif -debt >= SURPLUS_MIN:
                # 帮回去找「我帮过但没还我」的那个人；没有就随便挑一个我帮过的
                owed_back = [d for d in me["debtors"]]
                top = sorted(owed_back, key=lambda x: (-x[1], x[0]))[0] if owed_back else (None, 0)
                row.update(action="帮", why="多给出 %d 次" % (-debt), target=top[0])
            else:
                row.update(action="守", why=(p.get("unfinished") or "守着未了的事")[:40], target=None)
        counts[row["action"]] += 1
        actions.append(row)

    out = {
        "version": "1.0",
        "day": day,
        "rule": "修(lost)>还(欠%+d)>帮(多给%+d)>守；目标人取自关系账，不凭空生成" % (DEBT_MIN, SURPLUS_MIN),
        "summary": counts,
        "actions": actions,
    }
    write_atomic(OUT, out)

    print(f"第 {day} 天 · 行为：{len(actions)} 人 → 修 {counts['修']} · 还 {counts['还']} · "
          f"帮 {counts['帮']} · 守 {counts['守']}")


if __name__ == "__main__":
    sys.exit(main() or 0)
