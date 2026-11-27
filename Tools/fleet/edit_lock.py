#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""edit_lock.py - 人工手术期间的编辑锁：让主控脉只做心跳，不动任何文件。

为什么（2026-11-05 一天 4 次事故）：主控脉与人工会话共用同一工作树。脉每轮会写
state/、队列、dispatcher/，还会（关闭前）跑 git。人工在改代码时，两边的写会互相
覆盖：我的 6 个提交被 rebase 摘掉、order_watch.py 消失、--purge-meta 被回退、
配置四段被冲成旧版——每次都要人重新发现并重建。

用法（人工手术前）：
    python3 Tools/fleet/edit_lock.py on  --why "改 X"
    ... 干活 ...
    python3 Tools/fleet/edit_lock.py off
    python3 Tools/fleet/edit_lock.py status

脉的行为：锁在位且未过期（默认 30 分钟）→ 只跑 hb/console 这类只读或自写心跳阶段，
其余全部 SKIP-BY-LOCK，并在 PULSE.json 里写明。过期锁自动失效，不会把机器锁死。
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOCK = os.path.join(ROOT, ".codely-cli", "tmp", "EDITING.lock")
TTL_S = 1800


def read_lock():
    try:
        with open(LOCK, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None
    try:
        age = time.time() - float(d.get("ts_epoch") or 0)
    except Exception:
        age = 1e9
    d["age_s"] = int(age)
    d["active"] = age < TTL_S
    return d


def is_locked():
    d = read_lock()
    return bool(d and d.get("active"))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["on", "off", "status"])
    ap.add_argument("--why", default="")
    a = ap.parse_args(argv)
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)

    if a.action == "on":
        with open(LOCK, "w", encoding="utf-8") as f:
            json.dump({"ts_epoch": time.time(),
                       "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       "why": a.why or "manual surgery",
                       "pid": os.getpid()}, f, ensure_ascii=False, indent=1)
        print("[edit-lock] ON (%ds TTL): %s" % (TTL_S, a.why or "-"))
        return 0
    if a.action == "off":
        try:
            os.remove(LOCK)
            print("[edit-lock] OFF")
        except FileNotFoundError:
            print("[edit-lock] already off")
        return 0
    d = read_lock()
    print(json.dumps(d or {"active": False}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))