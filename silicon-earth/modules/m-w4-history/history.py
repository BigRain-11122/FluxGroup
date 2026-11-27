# -*- coding: utf-8 -*-
"""m-w4-history · 纪年（v0.1）

把事件流切成「纪元」：用大事给年代划界，再给每段起一个能查出来的名字。

口径（写死，改口径＝改契约，须走总控）：
  * 大事 = 事件类型 blackout（断电）或 breach（失守）
  * 边界 = 大事发生的那一天；第 1 段从第 1 天开始
  * 纪元名 = 「<段号>·<该段事件最多的区域名>的<触发词>」
      - 首段触发词 = 开城
      - blackout 后 = 断电后
      - breach 后 = 失守后
  * 一段内没有任何事件时，仍成立（空段不合法：边界同日合并）

输出：modules/m-w4-history/data/history.json
运行：python modules/m-w4-history/history.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
TIME = os.path.join(ROOT, "modules", "m-w2-clock", "data", "time.json")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")
OUT = os.path.join(DATA, "history.json")

MARK_TYPES = {"blackout": "断电后", "breach": "失守后"}


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


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    day = read_json(TIME, {"day": 0}).get("day", 0)
    names = {r["id"]: r["name"] for r in read_json(REGIONS, {"regions": []}).get("regions", [])}

    events = []
    bad = 0
    if os.path.exists(EVENTS):
        with open(EVENTS, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    bad += 1

    # 边界日 → 触发词（同一天多条大事取第一条，不重复开纪）
    marks = {}
    for e in events:
        t = e.get("type")
        if t in MARK_TYPES:
            d = int(e.get("day") or 0)
            if d > 0 and d not in marks:
                marks[d] = (MARK_TYPES[t], e.get("id"))

    starts = [1] + sorted(d for d in marks if d > 1)
    eras = []
    for i, s in enumerate(starts, 1):
        nxt = starts[i] if i < len(starts) else None
        e_day = (nxt - 1) if nxt else day
        seg = [e for e in events if s <= int(e.get("day") or 0) <= e_day]
        per_region = {}
        for e in seg:
            rid = e.get("region_id")
            per_region[rid] = per_region.get(rid, 0) + 1
        if per_region:
            dom = sorted(per_region.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        else:
            dom = None
        trigger = marks[s][0] if s in marks else "开城"
        rname = names.get(dom, "无人区")
        eras.append({
            "index": i,
            "from_day": s,
            "to_day": e_day,
            "name": f"{i}·{rname}的{trigger}",
            "trigger": trigger,
            "trigger_event": marks[s][1] if s in marks else None,
            "events": len(seg),
            "dominant_region": dom,
            "regions_hit": len(per_region),
        })

    out = {
        "version": "1.0",
        "day": day,
        "rule": "大事(blackout/breach)开新纪；纪元名=段号·该段事件最多的区域·触发词",
        "summary": {"eras": len(eras), "events": len(events),
                    "marks": len(marks), "bad_lines": bad},
        "eras": eras,
    }
    write_atomic(OUT, out)

    print(f"第 {day} 天 · 纪年：{len(eras)} 纪 · {len(events)} 条事件 · {len(marks)} 个大事")
    for e in eras[:5]:
        print(f"  {e['from_day']:>3}-{e['to_day']:<3} {e['name']}（{e['events']} 事）")
    if len(eras) > 5:
        print(f"  … 末纪 {eras[-1]['from_day']}-{eras[-1]['to_day']} {eras[-1]['name']}")


if __name__ == "__main__":
    sys.exit(main() or 0)
