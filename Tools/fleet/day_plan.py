#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""day_plan.py - 把主控智能体的职责表排成一天的时间轴，串行执行。

为什么（CEO 2026-11-05「不是并行，是一天安排起来」）：
  之前所有阶段挤在一轮脉冲里并发跑（71 个阶段，444 秒），谁也不知道"这个时刻该做什么"，
  长活和快活抢同一块资源，撞车三次。改成：一天分 7 个窗口，每个窗口有明确的可干清单，
  一个时刻只干一件事，按节拍（3/15/60 分钟）轮转。

产出：
  state/day-plan.json   今天的时间表（机读）
  DAY-PLAN.md           人读一页（你现在该干什么、下一班干什么）

用法：python3 Tools/fleet/day_plan.py [--json] [--at HH:MM]
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
DUTIES = os.path.join(F, "MASTER-AGENT-DUTIES-v1.json")
OUT_JSON = os.path.join(F, "state", "day-plan.json")
OUT_MD = os.path.join(F, "DAY-PLAN.md")


def load():
    with open(DUTIES, encoding="utf-8") as f:
        return json.load(f)


def hhmm(t):
    return t.strftime("%H:%M")


def window_of(now, windows):
    cur = hhmm(now)
    for w in windows:
        a, b = w["from"], w["to"]
        if a <= b:
            if a <= cur < b:
                return w
        else:  # 跨零点
            if cur >= a or cur < b:
                return w
    return windows[0]


def due(d, w, minute_now):
    """这一班该不该干这项。窗口必须匹配；节拍按分钟取模。"""
    if w["id"] not in (d.get("windows") or [w["id"]]):
        return False
    cad = d.get("cad") or "T15"
    if cad == "D1":
        return minute_now < 180        # 日班：每小时头 3 小时窗内做一次
    every = {"T3": 3, "T15": 15, "T60": 60}.get(cad, 15)
    return minute_now % every < 3


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--at", default="")
    a = ap.parse_args(argv)

    spec = load()
    now = datetime.now()
    if a.at:
        h, m = a.at.split(":")
        now = now.replace(hour=int(h), minute=int(m))
    w = window_of(now, spec["windows"])
    minutes = now.hour * 60 + now.minute
    duties = spec["duties"]

    todo = [d for d in duties if due(d, w, minutes)]
    todo.sort(key=lambda d: {"T3": 0, "T15": 1, "T60": 2, "D1": 3}.get(d.get("cad"), 9))

    # 下一个窗口
    ids = [x["id"] for x in spec["windows"]]
    nxt = spec["windows"][(ids.index(w["id"]) + 1) % len(spec["windows"])]

    out = {
        "ts": now.isoformat(timespec="seconds"),
        "window": {"id": w["id"], "name": w["name"], "mode": w["mode"], "why": w["why"],
                   "from": w["from"], "to": w["to"]},
        "serial": True,
        "now_duties": [{"id": d["id"], "name": d["name"], "domain": d["domain"],
                        "cad": d["cad"], "action": d["action"], "out": d["out"],
                        "verify": d["verify"], "fallback": d["fallback"]} for d in todo],
        "next_window": {"id": nxt["id"], "name": nxt["name"], "from": nxt["from"],
                        "duties": len([d for d in duties if nxt["id"] in (d.get("windows") or [])])},
        "counts": {"total": len(duties),
                   "by_domain": {dom: len([d for d in duties if d["domain"] == dom])
                                 for dom in sorted({d["domain"] for d in duties})}},
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    lines = ["# 主控智能体·今日时间轴 %s" % now.strftime("%Y-%m-%d %H:%M"), "",
             "**当前班次**：%s（%s–%s，%s）— %s" % (w["name"], w["from"], w["to"],
                                                w["mode"], w["why"]), "",
             "**串行执行**：同一时刻只做一项，按下面顺序一件一件来。", "",
             "| # | 域 | 事项 | 节拍 | 动作 | 判据 | 兜底 |", "|---|---|---|---|---|---|---|"]
    for i, d in enumerate(todo, 1):
        lines.append("| %d | %s | %s | %s | %s | %s | %s |" % (
            i, d["domain"], d["name"], d["cad"], d["action"], d["verify"], d["fallback"]))
    lines += ["", "**下一班**：%s（%s 起，%d 项职责）" % (nxt["name"], nxt["from"],
                                                  out["next_window"]["duties"]), "",
              "**职责全表**：%d 项，分布 %s" % (
                  out["counts"]["total"],
                  "，".join("%s %d" % (k, v) for k, v in out["counts"]["by_domain"].items()))]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))