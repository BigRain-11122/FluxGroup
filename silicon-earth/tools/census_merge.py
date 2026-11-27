# -*- coding: utf-8 -*-
"""
census_merge · 从分区文件合并出 people.json（生成物，不进 git）

新克隆或分区更新后都跑它。运行：python tools/census_merge.py
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "modules", "m-p1-census", "data")
PEOPLE = os.path.join(DATA, "people.json")
PARTS = os.path.join(DATA, "regions")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.isdir(PARTS):
        print("✗ 没有分区目录（先跑 split_census.py）")
        return 1
    rows = []
    for name in sorted(os.listdir(PARTS)):
        if not name.endswith(".json"):
            continue
        rows += json.load(io.open(os.path.join(PARTS, name), encoding="utf-8"))["people"]
    rows.sort(key=lambda p: int(p["id"][1:]))
    json.dump({"version": "3.1", "people": rows},
              io.open(PEOPLE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✓ 合并 {len(rows)} 人 → people.json（生成物）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
