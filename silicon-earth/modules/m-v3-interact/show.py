# -*- coding: utf-8 -*-
"""
m-v3-interact · 点开一个人，看他的记忆链

用法：
  python modules/m-v3-interact/show.py P0101
  python modules/m-v3-interact/show.py --list

这是这个世界唯一别人抄不走的东西：一个人被记住了多少、缺了哪段、缺了之后认不出谁。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")
MEMORY = os.path.join(ROOT, "modules", "m-p2-memory", "data", "memory.json")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")

KIND = {"given": "被给予", "taken": "被拿走", "kept": "留下", "lost": "丢失"}


def load(p, key):
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f).get(key, [])


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    people = load(PEOPLE, "people")
    memories = load(MEMORY, "memories")
    regions = {r["id"]: r["name"] for r in load(REGIONS, "regions")}

    if len(sys.argv) >= 2 and sys.argv[1] == "--random":
        import random as _r
        pid = _r.choice(people)["id"]
        sys.argv = [sys.argv[0], pid]

    if len(sys.argv) >= 2 and sys.argv[1] == "--powers":
        import collections as _c
        cnt = _c.Counter((p.get("power", "无主"), p.get("org", "")) for p in people)
        for (pw, org), n in cnt.most_common(15):
            print(f"{pw:<8} {org:<16} {n}")
        return 0

    if len(sys.argv) >= 2 and sys.argv[1] == "--stats":
        import collections as _c
        cnt = _c.Counter(m["person_id"] for m in memories)
        named = len(cnt)
        print(f"{len(people)} 人，其中 {named} 人被点名过（{named*100.0/len(people):.2f}%），共 {len(memories)} 条记忆")
        for pid, n in cnt.most_common(5):
            who = next((p["called"] for p in people if p["id"] == pid), pid)
            print(f"  {who} · {n} 条")
        return 0

    if len(sys.argv) >= 2 and sys.argv[1] == "--list":
        print(f"{len(people)} 个人：")
        for p in people:
            n = sum(1 for m in memories if m["person_id"] == p["id"])
            print(f"  {p['id']}  {p['called']:<8} {regions.get(p['region_id'],'?'):<6} 记忆 {n} 条")
        return 0

    if len(sys.argv) < 2:
        print("用法: show.py <P0101> | --list")
        return 2

    pid = sys.argv[1]
    person = next((p for p in people if p["id"] == pid), None)
    if not person:
        print(f"✗ 没有这个人 {pid}")
        return 1

    mine = [m for m in memories if m["person_id"] == pid]
    print(f"【{person['called']}】{person.get('name') or '（正名待定）'} · {regions.get(person['region_id'],'?')}")
    if person.get("power"):
        print(f"  势力：{person['power']} · {person.get('org','')}（{person.get('alignment','-')}）")
    if person.get("host"):
        print(f"  族源：{person.get('species','-')} · 宿主：{person['host']} · 记忆跨度：{person.get('memory_span','-')}")
        print(f"  体征：{'、'.join(person.get('vital',[])) or '-'}　需求：{'、'.join(person.get('needs',[])) or '-'}")
    print(f"  他每天做：{person.get('role','')}")
    print(f"  未了的事：{person.get('unfinished','')}")
    print(f"  记忆 {len(mine)} 条：")
    if not mine:
        print("    （空的——这本身就是一件事）")
    for m in mine:
        line = f"    第 {m['day']} 天 · {KIND.get(m['kind'], m['kind'])} · {m['text']}"
        if m.get("unrecognized"):
            who = next((x["called"] for x in people if x["id"] == m["unrecognized"]), m["unrecognized"])
            line += f"  →  他认不出{who}了"
        print(line)
    lost = sum(1 for m in mine if m["kind"] == "lost")
    if lost:
        print(f"  丢失 {lost} 条。丢过的人，还是原来那个人吗？")
    return 0


if __name__ == "__main__":
    sys.exit(main())
