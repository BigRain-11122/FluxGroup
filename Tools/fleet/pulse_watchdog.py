#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pulse_watchdog.py - 主控自己崩溃时，由这条独立进程把它拉起来。

Why (2026-11-02): 一夜之间主控哑了 8 小时，今早我自己的改动又让循环崩了 2.5 小时
（`cold` 未定义）。launchd 的 KeepAlive 只在**进程退出**时重拉，而崩溃的循环是
"进程活着、什么都不做"——这种形态 KeepAlive 永远看不见。

判据只用一个事实：PULSE.json 的 mtime。超过 STALE_S 没更新，就 kickstart 脉搏。
本脚本自己由 launchd 每 2 分钟起一次，跑完即退，不常驻、不占资源。

用法: python3 Tools/fleet/pulse_watchdog.py [--stale-s 420] [--apply]
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PULSE = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "PULSE.json")
LOG = "/tmp/fluxgroup-watchdog.log"
LABEL = "com.fluxgroup.pulse"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg))


SYNC = os.path.join(ROOT, "cph4", "fleet", "state", "state-sync.json")
SYNC_LABEL = "com.fluxgroup.statesync"


def sync_check(apply, stale_s=900):
    """状态同步面也要有人看：它静默死掉时，跨机可见性会慢慢变旧而没人报警。"""
    try:
        d = json.load(open(SYNC, encoding="utf-8"))
        ok = float(d.get("ok_ts") or 0)
        until = float(d.get("until") or 0)
    except Exception:
        ok, until = 0.0, 0.0
    if until and time.time() < until:
        return 0
    age = (time.time() - ok) if ok else 1e9
    if age <= stale_s:
        return 0
    if not apply:
        print("SYNC-STALE %.0fs - would kickstart %s" % (age, SYNC_LABEL))
        return 0
    log("watchdog: statesync stale %.0fs -> kickstart" % age)
    subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/%s" % (os.getuid(), SYNC_LABEL)],
                   capture_output=True)
    print("RESTARTED %s (stale %.0fs)" % (SYNC_LABEL, age))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-s", type=int, default=420)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    try:
        age = time.time() - os.path.getmtime(PULSE)
    except Exception:
        age = 1e9
    alive = subprocess.run(["pgrep", "-f", "master_pulse.py --loop"],
                           capture_output=True, text=True).stdout.strip()
    sync_check(a.apply)
    if age <= a.stale_s:
        return 0
    # A stale heartbeat with a live process is the dangerous case: the loop is wedged.
    kind = "WEDGED(alive-pid)" if alive else "DEAD(no-pid)"
    if not a.apply:
        print("STALE %.0fs %s - would kickstart %s" % (age, kind, LABEL))
        return 0
    log("watchdog: pulse %s stale %.0fs -> kickstart" % (kind, age))
    if alive:
        # kill the wedged loop first, otherwise kickstart is a no-op (job is "running")
        subprocess.run(["pkill", "-f", "master_pulse.py --loop"], capture_output=True)
        time.sleep(2)
    subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/%s" % (os.getuid(), LABEL)],
                   capture_output=True)
    print("RESTARTED %s (was %s, stale %.0fs)" % (LABEL, kind, age))
    return 0


if __name__ == "__main__":
    sys.exit(main())