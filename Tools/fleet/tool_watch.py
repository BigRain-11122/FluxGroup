#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tool_watch.py - 常驻工具完整性哨兵：脚本没了必须当场报警，不能静默。

为什么（2026-11-05 真事故）：
  load_watch.py 被合并/rebase 删掉，launchd 仍在每 60s 调它，报错没人看；
  主控脉残留进程还把未提交的新工具一起删了（asset_pull / asset_gap_audit）。
  没有这一层，"能不能持续供给"根本无从保证。

判据：
  1) ~/Library/LaunchAgents/com.fluxgroup.*.plist 里 ProgramArguments 的脚本路径必须存在；
  2) 关键工具清单必须存在（缺一个就红）。

用法：python3 Tools/fleet/tool_watch.py [--json out.json]
Exit: 0 全在；1 有缺失（红）
"""
import argparse
import glob
import json
import os
import plistlib
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "Tools", "fleet")
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "tool-watch.json")

CRITICAL = [
    "master_pulse.py", "lane_agent.py", "closer.py", "master_agent.py",
    "workgen.py", "supply_guard.py", "demand_gen.py", "asset_pull.py",
    "asset_gap_audit.py", "soak_watch.py", "fleet_lane.py", "console_server.py",
]


def check_launchd():
    rows = []
    for p in sorted(glob.glob(os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.*.plist"))):
        job = os.path.basename(p).replace(".plist", "")
        try:
            d = plistlib.load(open(p, "rb"))
        except Exception as e:
            rows.append({"job": job, "ok": False, "why": "plist 解析失败 %s" % str(e)[:60]})
            continue
        args = d.get("ProgramArguments") or []
        scripts = [a for a in args[1:] if isinstance(a, str) and a.endswith((".py", ".sh"))]
        missing = [s for s in scripts if not os.path.exists(s)]
        rows.append({"job": job, "scripts": scripts, "missing": missing, "ok": not missing})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=OUT)
    a = ap.parse_args(argv)
    launchd = check_launchd()
    missing_tools = [t for t in CRITICAL if not os.path.isfile(os.path.join(HERE, t))]
    bad_jobs = [r["job"] for r in launchd if not r["ok"]]
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "launchd": launchd, "bad_jobs": bad_jobs,
           "missing_tools": missing_tools,
           "verdict": "PASS" if not bad_jobs and not missing_tools else "RED"}
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("[toolwatch] launchd 作业 %d，坏 %d；关键工具缺 %d"
          % (len(launchd), len(bad_jobs), len(missing_tools)))
    for r in launchd:
        if not r["ok"]:
            print("  ! %s 缺 %s" % (r["job"], ", ".join(r.get("missing") or [r.get("why", "")])))
    for t in missing_tools:
        print("  ! 缺工具 %s" % t)
    return 0 if rec["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())