# -*- coding: utf-8 -*-
"""
m-w3-settle · 状态结算 v0.2

v0.2 按运维席意见修：①原子写（tmp+fsync+replace），不再直接截断重写；
②逐行容错，遇到坏行只计数不整跑崩；③记录 day，便于 validate 判断新鲜度。

运行：python settle.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
TIME = os.path.join(ROOT, "modules", "m-w2-clock", "data", "time.json")
SCHEMA = os.path.join(ROOT, "CONTRACTS", "world.schema.json")
BASE = os.path.join(DATA, "baseline.json")
STATE = os.path.join(DATA, "state.json")


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


def band_of(positivity, bands):
    for name, (lo, hi) in bands.items():
        if lo <= positivity <= hi:
            return name
    return "waiting"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    regions = read_json(REGIONS)["regions"]
    base = read_json(BASE, {"baseline": {}})["baseline"]
    bands = {k: v for k, v in read_json(SCHEMA)["state_bands"].items() if k != "note"}
    day = read_json(TIME, {"day": 0})["day"]

    pos = {r["id"]: int(base.get(r["id"], 50)) for r in regions}
    counts = {r["id"]: 0 for r in regions}
    bad = 0

    if os.path.exists(EVENTS):
        with open(EVENTS, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    bad += 1
                    continue
                if not isinstance(ev, dict) or "region_id" not in ev:
                    bad += 1
                    continue
                rid = ev.get("region_id")
                if rid not in pos:
                    continue
                counts[rid] += 1
                w = ev.get("weights", {})
                pos[rid] += int(w.get("positive", 0)) - int(w.get("cost", 0))

    out = []
    for r in regions:
        p = max(0, min(100, pos[r["id"]]))
        out.append({"id": r["id"], "name": r["name"], "positivity": p,
                    "state": band_of(p, bands), "events": counts[r["id"]]})

    write_atomic(STATE, {"version": "1.1", "day": day, "regions": out})
    print(f"第 {day} 天 · 结算 {len(out)} 块区域" + (f" · 跳过坏行 {bad}" if bad else ""))
    for x in out:
        print(f"  {x['name']:<6} positivity={x['positivity']:>3} · {x['state']:<10} · 事件 {x['events']}")


if __name__ == "__main__":
    sys.exit(main() or 0)
