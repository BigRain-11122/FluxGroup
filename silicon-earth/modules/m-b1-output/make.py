# -*- coding: utf-8 -*-
"""m-b1-output · 每日日报（一句话，≤100 字）"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")

ACTION = {"build": "动工", "help": "搭了把手", "teach": "教了人",
          "repair": "把旧线接上", "weather": "照旧过日子",
          "slip": "出了点错", "breach": "有件事没做到", "blackout": "断了电"}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.exists(EVENTS):
        print("✗ 没有事件流")
        return 1
    events = []
    with open(EVENTS, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    if not events:
        print("✗ 事件流是空的")
        return 1

    day = max(e["day"] for e in events)
    if len(sys.argv) >= 3 and sys.argv[1] == "--day":
        day = int(sys.argv[2])
    today = [e for e in events if e["day"] == day]
    names = {r["id"]: r["name"] for r in
             json.load(open(REGIONS, encoding="utf-8"))["regions"]}

    if not today:
        print(f"第{day}天：这一天什么都没发生。")
        return 0

    good = [e for e in today if not e["weights"]["cost"]]
    bad = [e for e in today if e["weights"]["cost"]]
    parts = []
    for e in (good[:2] or today[:2]):
        parts.append(f"{names.get(e['region_id'], '某处')}有人在{ACTION.get(e['type'], '做事')}")
    if bad:
        parts.append(f"{names.get(bad[0]['region_id'], '某处')}那边{ACTION.get(bad[0]['type'], '出了状况')}")
    line = f"第{day}天：" + "；".join(parts) + "。"
    print(line[:100])
    return 0


if __name__ == "__main__":
    sys.exit(main())
