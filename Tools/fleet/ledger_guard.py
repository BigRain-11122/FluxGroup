#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger_guard.py — 台账只增不减的守门（发现被同步回滚）。

为什么需要（2026-11-22 实锚）：`cph4/fleet/social/practice-log.jsonl` 是**运行时只增台账**，
但它同时被 git 跟踪，机队每轮的 pulse 自动提交 / reset 会把它恢复成仓库里的旧版本——
我 14:03 真实发出的一条评论（rpid 324780193728）连同 lane/qualified/timing 四行，
在 14:08 被整段冲掉，文件末尾又回到 13:26。这不是"写失败"，是**历史被覆盖**：
配额、去重、可见率判据全部建立在它上面，丢行 = 判据悄悄变成假绿。

判据：每个台账记住见过的最大行数；下次若变小 → 红（rc=2）并打印差额与最后一行时间。
用法：
  python3 Tools/fleet/ledger_guard.py            # 检查（首次运行只记基线）
  python3 Tools/fleet/ledger_guard.py --update   # 确认无异常后刷新高水位
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
HWM = os.path.join(STATE, "LEDGER-HWM.json")
FILES = ["practice-log.jsonl", "USER-AGENT-LEDGER.jsonl", "comments-sent.jsonl"]


def _count(path):
    n = 0
    last = ""
    try:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                n += 1
                last = line.strip()[:120]
    except FileNotFoundError:
        return 0, ""
    return n, last


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="刷新高水位（确认无异常后）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(STATE, exist_ok=True)
    try:
        hwm = json.load(open(HWM, encoding="utf-8")) or {}
    except Exception:
        hwm = {}
    rows, bad = [], []
    for name in FILES:
        p = os.path.join(SOCIAL, name)
        n, last = _count(p)
        prev = int(hwm.get(name, 0) or 0)
        dropped = prev - n
        rows.append({"file": name, "lines": n, "hwm": prev, "dropped": max(0, dropped),
                     "last": last, "ok": dropped <= 0})
        if dropped > 0:
            bad.append("%s 少了 %d 行（%d→%d）" % (name, dropped, prev, n))
    if a.update or not hwm:
        for r in rows:
            hwm[r["file"]] = max(int(hwm.get(r["file"], 0) or 0), r["lines"])
        json.dump(hwm, open(HWM, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps({"checks": rows, "bad": bad}, ensure_ascii=False))
    else:
        for r in rows:
            print("%s %-24s %5d 行（高水位 %d）" % (
                "❗" if not r["ok"] else "✅", r["file"], r["lines"], r["hwm"]))
        if bad:
            print("❗ 台账被回滚：%s" % "；".join(bad))
            print("   正式处置：确认是谁做的 git 恢复（pulse 自动提交/机队 reset），"
                  "并把只增台账移出 git 跟踪；不要手工补行。")
    if bad:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
