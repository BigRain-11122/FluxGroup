# -*- coding: utf-8 -*-
"""m-r2-translate · 翻译表自检：条数、字段、事件类型枚举。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RULES = os.path.join(HERE, "data", "rules.json")
SCHEMA = os.path.join(ROOT, "CONTRACTS", "world.schema.json")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.exists(RULES):
        print("✗ 缺 rules.json")
        return 1
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f).get("rules", [])
    with open(SCHEMA, encoding="utf-8") as f:
        types = set(json.load(f)["definitions"]["event"]["properties"]["type"]["enum"])

    bad = []
    for i, r in enumerate(rules, 1):
        for k in ("real", "translate", "event_type", "region_hint"):
            if not r.get(k):
                bad.append(f"第 {i} 条缺 {k}")
        if r.get("event_type") not in types:
            bad.append(f"第 {i} 条 event_type 非法：{r.get('event_type')}")

    if len(rules) != 20:
        bad.append(f"条数 {len(rules)}，应为 20")
    if bad:
        print(f"✗ {len(bad)} 处问题")
        for x in bad[:10]:
            print("  - " + x)
        return 1
    print(f"✓ 翻译表 20/20 条，类型全部合法")
    return 0


if __name__ == "__main__":
    sys.exit(main())
