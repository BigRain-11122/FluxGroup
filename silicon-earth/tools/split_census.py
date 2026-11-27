# -*- coding: utf-8 -*-
"""
split_census · 把 12,361 人的大文件按区拆开

问题：people.json 已 7.4MB，每次改动都是数兆 diff。
做法：
  data/regions/Rxx.json   每个区一份（进 git，diff 只落在被改的区）
  data/people.json        由分区合并生成（不进 git）
幂等：随时可重跑。

运行：python tools/split_census.py
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
    if not os.path.exists(PEOPLE):
        print("✗ 没有 people.json（先跑 census_merge.py）")
        return 1

    people = json.load(io.open(PEOPLE, encoding="utf-8"))["people"]
    groups = {}
    for p in people:
        groups.setdefault(p["region_id"], []).append(p)

    os.makedirs(PARTS, exist_ok=True)
    for rid, rows in sorted(groups.items()):
        json.dump({"region": rid, "count": len(rows), "people": rows},
                  io.open(os.path.join(PARTS, rid + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(f"✓ 拆成 {len(groups)} 个分区文件：" +
          "、".join(f"{k}={len(v)}" for k, v in sorted(groups.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
