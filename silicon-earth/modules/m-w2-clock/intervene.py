# -*- coding: utf-8 -*-
"""
m-w2-clock · 介入（断电）v0.2

把「一个人被断电停机」写成世界事件，走同一把锁与同一个原子写。
v0.2 修：engine 改名后 write_time → write_atomic；锁改为返回 token，释放需比对。

运行：python intervene.py --person P0101
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from engine import (EVENTS, PEOPLE, TIME, acquire_lock, last_seq,  # noqa: E402
                    read_json, release_lock, write_atomic)


def main(person_id):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    people = read_json(PEOPLE)["people"]
    person = next((p for p in people if p["id"] == person_id), None)
    if person is None:
        print(f"✗ 没有这个人 {person_id}", file=sys.stderr)
        return 1

    mates = [m for m in people if m["region_id"] == person["region_id"] and m["id"] != person["id"]]
    if not mates:
        print(f"✗ {person_id} 所在区域没有别人，断电无人见证", file=sys.stderr)
        return 1
    witness = mates[0]

    me = acquire_lock()
    if not me:
        return 1
    try:
        t = read_json(TIME) if os.path.exists(TIME) else {"version": "1.1", "day": 0, "seq": 0}
        t["seq"] = max(int(t.get("seq", 0)), last_seq()) + 1
        day = max(1, int(t.get("day", 1)))

        event = {
            "id": "E%04d" % t["seq"],
            "day": day,
            "region_id": person["region_id"],
            "type": "blackout",
            "text": "{a} 被断电停机，{b} 是最后一个见他的人。".format(
                a=person["called"], b=witness["called"]),
            "actors": [person["id"], witness["id"]],
            "causes": [],
            "weights": {"positive": 0, "cost": 2},
        }
        with open(EVENTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        t["day"] = day
        write_atomic(TIME, t)
        print(f"✓ {event['id']} · 第 {day} 天 · {event['text']}")
        return 0
    finally:
        release_lock(me)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--person":
        sys.exit(main(sys.argv[2]))
    print("用法: python intervene.py --person P0101")
    sys.exit(2)
