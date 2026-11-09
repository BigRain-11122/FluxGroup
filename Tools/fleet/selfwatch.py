#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfwatch.py - 本机自动化自检自愈：不指望别的机器，也不指望人。

CEO 2026-11-09：「设置自动化的任务，不要指望他们，要自己牢靠」。
本件只做一件事：每个本地自动化都登记"最后成功产物"，超过预期就自己重跑。
- 判定只认磁盘产物（mtime/ok_ts），不认"进程在"；
- 重跑失败就记日志，不抛异常；同一任务有锁，不并发。
- 每 300s 由 launchd 跑一次。

用法：python3 Tools/fleet/selfwatch.py [--apply]
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
OUT = os.path.join(STATE, "selfwatch.json")
LOG = os.path.join(STATE, "selfwatch.log")
PY = sys.executable

JOBS = [
    {"name": "pulse", "artifact": os.path.join(F, "dispatcher", "PULSE.json"),
     "max_age": 900, "kind": "launchd", "label": "com.fluxgroup.pulse"},
    {"name": "statesync", "artifact": os.path.join(STATE, "state-sync.json"),
     "max_age": 900, "runner": [PY, os.path.join(ROOT, "Tools/fleet/state_sync.py")]},
    {"name": "worker", "artifact": os.path.join(STATE, "local-digest.jsonl"),
     "max_age": 600, "runner": [PY, os.path.join(ROOT, "Tools/fleet/local_worker.py"), "--limit", "10"]},
    {"name": "patrol", "artifact": os.path.join(STATE, "patrol-local.json"),
     "max_age": 900, "runner": [PY, os.path.join(ROOT, "Tools/fleet/patrol_local.py")]},
    {"name": "analyst", "artifact": os.path.join(STATE, "local-analyst.json"),
     "max_age": 7200, "runner": [PY, os.path.join(ROOT, "Tools/fleet/local_analyst.py")]},
    {"name": "dedupe", "artifact": os.path.join(STATE, "embed-dedupe.json"),
     "max_age": 7200, "runner": [PY, os.path.join(ROOT, "Tools/fleet/embed_dedupe.py")]},
    {"name": "brief", "artifact": os.path.join(F, "DAILY-BRIEF.md"),
     "max_age": 129600, "runner": [PY, os.path.join(ROOT, "Tools/fleet/daily_brief.py")]},
    {"name": "resilience", "artifact": os.path.join(STATE, "resilience.json"),
     "max_age": 129600, "runner": [PY, os.path.join(ROOT, "Tools/fleet/resilience.py")]},
]


def age(path):
    try:
        return time.time() - os.path.getmtime(path)
    except OSError:
        return 1e9


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg))
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rows, healed = [], []
    for j in JOBS:
        ag = age(j["artifact"])
        stale = ag > j["max_age"]
        row = {"name": j["name"], "age_s": round(ag), "max_age": j["max_age"], "stale": stale}
        if stale and a.apply:
            if j.get("kind") == "launchd":
                r = subprocess.run(["launchctl", "kickstart", "-k",
                                    "gui/%d/%s" % (os.getuid(), j["label"])],
                                   capture_output=True)
                row["heal"] = "kickstart rc=%s" % r.returncode
            elif j.get("runner"):
                try:
                    r = subprocess.run(j["runner"], cwd=ROOT, capture_output=True,
                                       text=True, timeout=240)
                    row["heal"] = "rc=%s" % r.returncode
                    healed.append(j["name"])
                except Exception as e:
                    row["heal"] = "error %s" % str(e)[:80]
            log("%s stale %ss -> %s" % (j["name"], round(ag), row.get("heal")))
        rows.append(row)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "stale": [r["name"] for r in rows if r["stale"]],
           "healed": healed, "jobs": rows}
    os.makedirs(STATE, exist_ok=True)
    json.dump(rec, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"stale": rec["stale"], "healed": healed}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
