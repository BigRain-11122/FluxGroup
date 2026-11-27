#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seat_dispatch.py — 把 39 席的排班真正跑起来（桥接 schedule 与 team）。

为什么需要它（2026-11-11 实测缺口）：
  `agent_schedule.py --tick` 只做「到点判定 + 额度记账」，它**不调用席位**；
  `agent_team.py --run` 才是执行器。两者之间从来没有桥——于是设定齐全、
  两套自检全绿（12/12、9/9），但线上一个席位都没跑过，界面上看是「没人干活」。

设计纪律（与 AGENT-TEAMS 的 _contract 一致）：
  1. 只喂可复算的事实：时间/工位/队列计数/磁盘余量。不喂猜测、不喂旧结论。
  2. 判据不过就照实记 ok=false，不重试凑分、不改写 agent_team 的 degraded 结论。
  3. 每条结果落 cph4/fleet/agent-runs/<date>.jsonl，供复盘与额度核对。

用法：
  python3 Tools/fleet/seat_dispatch.py              # 五个工位各 tick 一次并跑到点席位
  python3 Tools/fleet/seat_dispatch.py --station control --max-runs 2
  python3 Tools/fleet/seat_dispatch.py --dry-run    # 只看谁到点，不调模型
"""
import argparse
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import agent_schedule as sched          # noqa: E402
import agent_team as team               # noqa: E402
import station_shards as ss             # noqa: E402

QUEUE = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
RUNS_DIR = os.path.join(ROOT, "cph4", "fleet", "agent-runs")


def _queue_counts():
    """队列状态计数。读不到就返回空字典——不猜数字。"""
    c = {}
    try:
        with open(QUEUE, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    st = str((json.loads(line) or {}).get("state") or "?")
                except Exception:
                    continue
                c[st] = c.get(st, 0) + 1
    except OSError:
        return {}
    return c


def facts(station, seat_id):
    """席位输入：只要可复算的事实。"""
    try:
        du = shutil.disk_usage(ROOT)
        disk_gb = round(du.free / 1e9, 1)
    except OSError:
        disk_gb = None
    return {
        "now": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "station": station,
        "seat": seat_id,
        "queue_states": _queue_counts(),
        "disk_free_gb": disk_gb,
        "scope_note": "facts are a local snapshot; anything not listed here is unknown",
    }


def record(rows):
    os.makedirs(RUNS_DIR, exist_ok=True)
    path = os.path.join(RUNS_DIR, time.strftime("%Y%m%d") + ".jsonl")
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default=None)
    ap.add_argument("--max-runs", type=int, default=2, help="每个工位本轮最多跑几席")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    cap = sched._j(sched._p("AGENT-CAPACITY-v1.json", None), {}) or {}
    st = sched._state(None)
    stations = [a.station] if a.station else list(ss.STATIONS)

    rows, planned = [], []
    for station in stations:
        try:
            out = sched.tick(station, cap, st, max_runs=a.max_runs)
        except Exception as e:
            rows.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "station": station,
                         "seat": None, "ok": False, "why": "tick 失败: %s" % str(e)[:120],
                         "degraded": True})
            continue
        due = [c.get("seat") for c in (out.get("ran") or []) if c.get("seat")]
        planned.append({"station": station, "due": due,
                        "skipped": len(out.get("skipped") or [])})
        if a.dry_run:
            continue
        for seat_id in due:
            t0 = time.time()
            try:
                r = team.run_seat(station, seat_id, json.dumps(facts(station, seat_id),
                                                              ensure_ascii=False))
            except Exception as e:
                r = {"ok": False, "why": "执行异常: %s" % str(e)[:120], "degraded": True}
            r = dict(r or {})
            r.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
            r["station_out"] = station
            r["elapsed_stdout_s"] = round(time.time() - t0, 1)
            rows.append(r)

    if a.dry_run:
        # 干跑绝不能落状态：tick() 会写"已跑"标记，提前保存会把到点席位白白吃掉。
        print(json.dumps({"dry_run": True, "plan": planned}, ensure_ascii=False, indent=1))
        return 0

    sched._save_state(st, None)

    path = record(rows) if rows else None
    ok = sum(1 for r in rows if r.get("ok"))
    deg = sum(1 for r in rows if r.get("degraded"))
    print(json.dumps({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "ran": len(rows), "ok": ok, "failed": len(rows) - ok, "degraded": deg,
        "ledger": os.path.relpath(path, ROOT) if path else None,
        "by_station": planned,
    }, ensure_ascii=False, indent=1))
    return 0 if len(rows) == ok else 1


if __name__ == "__main__":
    sys.exit(main())
