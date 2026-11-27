# -*- coding: utf-8 -*-
"""
check_state · 派生内容校验 v2

v2 补群审指出的三个洞：
  1 只看 positivity/状态，不看 day → day 改成 999 也能过
  2 不检查区域完整性 → 删掉一个区域仍打印"一致"
  3 不检查事件计数 → events 字段改成 777 也能过

现在：day 必须等于 time.day；区域集合必须与 regions.json 完全一致；
每区 events 计数必须与事件流重算一致。

用法：python tools/check_state.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
TIME = os.path.join(ROOT, "modules", "m-w2-clock", "data", "time.json")
BASE = os.path.join(ROOT, "modules", "m-w3-settle", "data", "baseline.json")
STATE = os.path.join(ROOT, "modules", "m-w3-settle", "data", "state.json")
SCHEMA = os.path.join(ROOT, "CONTRACTS", "world.schema.json")


def load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def band_of(v, bands):
    for name, (lo, hi) in bands.items():
        if lo <= v <= hi:
            return name
    return None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    regions = load(REGIONS)["regions"]
    base = load(BASE, {"baseline": {}})["baseline"]
    bands = {k: v for k, v in load(SCHEMA)["state_bands"].items() if k != "note"}
    state = load(STATE)
    if not state:
        print("✗ 缺 state.json")
        return 1

    days = load(TIME, {"day": 0})["day"]
    pos = {r["id"]: int(base.get(r["id"], 50)) for r in regions}
    cnt = {r["id"]: 0 for r in regions}
    if os.path.exists(EVENTS):
        with open(EVENTS, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                rid = ev.get("region_id")
                if rid in pos:
                    cnt[rid] += 1
                    w = ev.get("weights", {})
                    pos[rid] += int(w.get("positive", 0)) - int(w.get("cost", 0))

    bad = []

    if state.get("day") != days:
        bad.append(f"day 盘上 {state.get('day')} / time {days}")

    got = [s.get("id") for s in state.get("regions", [])]
    want = [r["id"] for r in regions]
    if sorted(got) != sorted(want):
        bad.append(f"区域集合不符：盘上 {len(got)} 块，应 {len(want)} 块")

    for s in state.get("regions", []):
        rid = s.get("id")
        if rid not in pos:
            continue
        wp = max(0, min(100, pos[rid]))
        if s.get("positivity") != wp:
            bad.append(f"{rid} positivity 盘上 {s.get('positivity')} / 重算 {wp}")
            continue
        wb = band_of(wp, bands)
        if wb and s.get("state") != wb:
            bad.append(f"{rid} 状态 盘上 {s.get('state')} / 重算 {wb}")
        if s.get("events") != cnt[rid]:
            bad.append(f"{rid} 事件数 盘上 {s.get('events')} / 重算 {cnt[rid]}")

    if bad:
        print(f"✗ state.json 与重算不一致 {len(bad)} 处：")
        for x in bad[:10]:
            print("  - " + x)
        return 1
    print(f"✓ state.json 与重算一致（第 {days} 天 · {len(state.get('regions', []))} 块区域）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
