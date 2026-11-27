# -*- coding: utf-8 -*-
"""
import_census · 把 BigLife 的全体居民接进这个世界

设计：**创始 27 人保留原 id**（他们的事件与记忆还活着），
      census 10114 人接在后面，id 从 P10001 起，互不冲突。

运行：python tools/import_census.py [--apply]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.environ.get("SILICON_CENSUS") or r"D:\FluxGroup\life\BigLife\census\export\citizens-light.jsonl"
DATA = os.path.join(ROOT, "modules", "m-p1-census", "data")
PEOPLE = os.path.join(DATA, "people.json")
BACKUP = os.path.join(DATA, "people.seed27.json")
ORIGIN = os.path.join(DATA, "origin-map.json")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")

DISTRICT = {"NS": "R01", "GM": "R02", "OR": "R03", "RV": "R04", "MD": "R05", "QT": "R06", "": "R01"}
START = 10001


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.exists(SRC):
        print(f"✗ 找不到户籍源：{SRC}")
        return 1
    apply = "--apply" in sys.argv

    rows = []
    with io.open(SRC, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue

    founders = []
    if os.path.exists(BACKUP):
        founders = json.load(io.open(BACKUP, encoding="utf-8")).get("people", [])
    print(f"户籍 {len(rows)} 人 · 创始 {len(founders)} 人")

    people = list(founders)
    origin = {}
    counts = {}
    for p in founders:
        counts[p["region_id"]] = counts.get(p["region_id"], 0) + 1

    for i, r in enumerate(rows):
        pid = "P%05d" % (START + i)
        rid = DISTRICT.get(r.get("district", ""), "R01")
        counts[rid] = counts.get(rid, 0) + 1
        role = (r.get("profession") or "居民").strip() or "居民"
        unc = (r.get("hook") or r.get("creed") or "").strip() or "还有一件事没做完。"
        people.append({"id": pid, "called": role, "name": r.get("name") or None,
                       "region_id": rid, "role": role, "unfinished": unc[:80],
                       "species": r.get("species") or "silicon",
                       "faction": r.get("faction") or "newcomer",
                       "gender": r.get("gender") or "无定",
                       "age": r.get("age") if isinstance(r.get("age"), int) else None,
                       "block": r.get("block") or ""})
        origin[pid] = {"census_id": r.get("id"), "name": r.get("name"),
                       "species": r.get("species"), "faction": r.get("faction"),
                       "gender": r.get("gender"), "age": r.get("age"),
                       "district": r.get("district"), "block": r.get("block")}

    print("区域分布：", counts)
    if not apply:
        print("（试跑，未写盘。加 --apply 落盘）")
        return 0

    json.dump({"version": "2.0", "people": people},
              io.open(PEOPLE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"note": "P id → 原户籍记录（字段不丢）", "map": origin},
              io.open(ORIGIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    regs = json.load(io.open(REGIONS, encoding="utf-8"))
    for r in regs["regions"]:
        r["population"] = counts.get(r["id"], 0)
    json.dump(regs, io.open(REGIONS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    size = os.path.getsize(PEOPLE) / 1048576.0
    print(f"✓ 共 {len(people)} 人（创始 {len(founders)} + 户籍 {len(rows)}）· {size:.1f}MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
