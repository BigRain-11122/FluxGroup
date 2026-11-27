# -*- coding: utf-8 -*-
"""m-p3-bonds · 关系与相助 v0.1

从事件流回放，把「帮」记成账：帮一次记一次，欠与还分开记。

口径（写死在代码里，改口径＝改契约，须走总控）：
  * 帮助类事件 = help / teach / repair，且 actors 至少有两人
  * actors[0] = 出手的人（给），actors[1] = 受助的人（收）
  * 一对人只出一条账；两个方向各记各的次数，不互相抵消
  * net_creditor = 净给出更多的一方；两边一样多时为 null（平账）

输出：modules/m-p3-bonds/data/bonds.json
运行：python modules/m-p3-bonds/bonds.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
TIME = os.path.join(ROOT, "modules", "m-w2-clock", "data", "time.json")
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")
BONDS = os.path.join(DATA, "bonds.json")

HELP_TYPES = ("help", "teach", "repair")


def read_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def iter_events(path):
    """逐行容错：坏行只计数不整跑崩（与 settle.py 同口径）。"""
    bad = 0
    if not os.path.exists(path):
        return bad
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                bad += 1
                continue
            if not isinstance(ev, dict):
                bad += 1
                continue
            yield ev
    return bad


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    day = read_json(TIME, {"day": 0}).get("day", 0)
    known = {p.get("id") for p in read_json(PEOPLE, {"people": []}).get("people", [])}

    pairs = {}          # (a, b) a<b  -> 记录
    given = {}          # pid -> 给出次数
    received = {}       # pid -> 收到次数
    used = 0            # 计入账的事件数
    skipped_unknown = 0
    bad = 0

    for ev in iter_events(EVENTS):
        if ev.get("type") not in HELP_TYPES:
            continue
        actors = ev.get("actors") or []
        if len(actors) < 2:
            continue
        giver, taker = actors[0], actors[1]
        if giver == taker:
            continue
        if known and (giver not in known or taker not in known):
            skipped_unknown += 1
            continue
        a, b = sorted((giver, taker))
        rec = pairs.setdefault((a, b), {"help": {a: 0, b: 0}, "last_day": 0, "events": []})
        rec["help"][giver] = rec["help"].get(giver, 0) + 1
        rec["last_day"] = max(rec["last_day"], int(ev.get("day") or 0))
        if len(rec["events"]) < 20:      # 只留指针样本，账本不复制事件全文
            rec["events"].append(ev.get("id"))
        given[giver] = given.get(giver, 0) + 1
        received[taker] = received.get(taker, 0) + 1
        used += 1

    out_pairs = []
    for (a, b), rec in sorted(pairs.items()):
        ga, gb = rec["help"].get(a, 0), rec["help"].get(b, 0)
        creditor = a if ga > gb else (b if gb > ga else None)
        out_pairs.append({
            "pair": [a, b],
            "help": {a: ga, b: gb},
            "net": abs(ga - gb),
            "net_creditor": creditor,
            "repaid": bool(ga and gb),
            "last_day": rec["last_day"],
            "events": rec["events"],
        })

    people_stats = []
    for pid in sorted(set(list(given) + list(received))):
        people_stats.append({"id": pid,
                             "given": given.get(pid, 0),
                             "received": received.get(pid, 0)})

    out = {
        "version": "1.0",
        "day": day,
        "rule": "help/teach/repair, actors[0] 给 actors[1]；欠与还分开记，不互相抵消",
        "summary": {
            "help_events": used,
            "pairs": len(out_pairs),
            "repaid_pairs": sum(1 for x in out_pairs if x["repaid"]),
            "one_way_pairs": sum(1 for x in out_pairs if not x["repaid"]),
            "people_involved": len(people_stats),
            "skipped_unknown_actor": skipped_unknown,
        },
        "pairs": out_pairs,
        "people": people_stats,
    }
    write_atomic(BONDS, out)

    s = out["summary"]
    print(f"第 {day} 天 · 相助记账：{s['help_events']} 次出手 · {s['pairs']} 对关系"
          f"（还过 {s['repaid_pairs']} / 单向 {s['one_way_pairs']}）")
    top = sorted(people_stats, key=lambda x: (-x["given"], x["id"]))[:3]
    for x in top:
        print(f"  常出手 {x['id']} · 给 {x['given']} · 收 {x['received']}")
    if bad:
        print(f"  跳过坏行 {bad}")


if __name__ == "__main__":
    sys.exit(main() or 0)
