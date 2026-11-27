# -*- coding: utf-8 -*-
"""一次性迁移：v0.1 数据结构 → v0.2（静态/动态分离、记忆独立成档）"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MOD = os.path.join(ROOT, "modules")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    # 1 区域：去掉动态状态
    rp = os.path.join(MOD, "m-w1-regions", "data", "regions.json")
    regions = load(rp)["regions"]
    baseline = {}
    for r in regions:
        baseline[r["id"]] = r.pop("positivity", 50)
        r.pop("state", None)
    dump(rp, {"version": "1.1", "regions": regions})
    dump(os.path.join(MOD, "m-w3-settle", "data", "baseline.json"),
         {"note": "结算基线，归 m-w3-settle 独占", "baseline": baseline})

    # 2 人：记忆分离
    pp = os.path.join(MOD, "m-p1-census", "data", "people.json")
    people = load(pp)["people"]
    memories = []
    n = 0
    for p in people:
        for m in p.pop("memory", []):
            n += 1
            memories.append({
                "id": "M%04d" % n,
                "person_id": p["id"],
                "day": m.get("day", 1),
                "kind": m.get("kind", "kept"),
                "text": m.get("text", ""),
                "event_id": None,
                "unrecognized": None,
            })
    dump(pp, {"version": "1.1", "people": people})
    dump(os.path.join(MOD, "m-p2-memory", "data", "memory.json"),
         {"version": "1.0", "memories": memories})

    # 3 时间与事件移位
    old_state = os.path.join(MOD, "m-w2-clock", "state.json")
    day = 0
    if os.path.exists(old_state):
        day = load(old_state).get("day", 0)
        os.remove(old_state)
    dump(os.path.join(MOD, "m-w2-clock", "data", "time.json"),
         {"version": "1.0", "day": day, "seq": 0})
    old_events = os.path.join(MOD, "m-w2-clock", "events.jsonl")
    new_events = os.path.join(MOD, "m-w2-clock", "data", "events.jsonl")
    if os.path.exists(old_events) and not os.path.exists(new_events):
        os.makedirs(os.path.dirname(new_events), exist_ok=True)
        os.replace(old_events, new_events)

    print(f"迁移完成：区域 {len(regions)} · 人 {len(people)} · 记忆 {len(memories)} · 旧天数 {day}")


if __name__ == "__main__":
    main()
