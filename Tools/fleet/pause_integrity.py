#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pause_integrity.py - CEO 让路窗完整性检测（D-20261102-15）。

Why: 2026-11-02 09:00 pauseLite 记了 17 件任务停用，12:00 实读其中 3 件已复活并在跑
（IterationLoop 12:03 / LoopWatchdog 12:02 / bigmoney round 1236），复活源不可取证。
让路律是 CEO 最高机制，被绕过后没有任何机械面能报出来——所以立一个只看「应然 vs 实然」
的检测器，不追人：actor 取不到就写 UNVERIFIABLE，不编造。

判据（三段式，D-20261102-08）：
  flag 首 token   sidecar 内任务应然   实然 != 应然 即违规
  absent          —                    N/A（无让路窗，不适用）
  resumed         ENABLED              实然 DISABLED 记为 drift（由 D-16 面统一处理）
  paused/pausedLite  DISABLED          实然 ENABLED  记为 offender（本脚本只判这一面）

零 LLM / 零网络。--apply 仅按 sidecar 复位 Disabled，不做任何新增停用。
Usage: python Tools/fleet/pause_integrity.py [--apply]
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from lane_registry import query  # noqa: E402  同一取证链（schtasks /query /xml ONE 隐藏窗）

FLAG = os.path.join(ROOT, ".codely-cli", "machine-state.flag")
SIDECAR = os.path.join(ROOT, ".codely-cli", "machine-state.disabled.json")
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "pause-integrity.jsonl")
CREATE_NO_WINDOW = 0x08000000


def read_flag():
    if not os.path.exists(FLAG):
        return "absent", ""
    try:
        line = open(FLAG, encoding="utf-8").readline().strip()
    except OSError:
        return "absent", ""
    parts = line.split()
    return (parts[0] if parts else "absent"), line


def read_sidecar():
    """sidecar 实测是行式（每行一个任务名），也兼容 JSON 数组/对象——两种都读不出=空。"""
    try:
        raw = open(SIDECAR, encoding="utf-8").read()
    except OSError:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            data = data.get("tasks") or data.get("disabled") or []
        if isinstance(data, list):
            return [str(x) for x in data if str(x).strip()]
    except ValueError:
        pass
    return [ln.strip().strip('",') for ln in raw.splitlines() if ln.strip() and ln.strip() not in ("[", "]")]


def main() -> int:
    mode, raw = read_flag()
    expected = "DISABLED" if mode in ("paused", "pausedLite") else "ENABLED"
    sidecar = read_sidecar()
    live = {r["name"]: r["state"] for r in query()}
    if not live:
        print("[pause-integrity] EMPTY-SCOPE: schtasks 返回 0 行，不得据此称绿")
        return 3
    if mode in ("paused", "pausedLite") and not sidecar:
        print("[pause-integrity] SIDECAR-UNREADABLE: flag=%s 但 sidecar 0 件——让路窗应然面缺失，"
              "不得据此称绿" % mode)
        return 4

    offenders, missing = [], []
    for name in sidecar:
        st = live.get(name)
        if st is None:
            missing.append(name)
        elif mode in ("paused", "pausedLite") and st != "DISABLED":
            offenders.append(name)

    verdict = "NOT-APPLICABLE" if mode not in ("paused", "pausedLite") else (
        "VIOLATION" if offenders else "OK")
    rec = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "flag": mode,
        "flag_raw": raw,
        "expected_state": expected,
        "sidecar_count": len(sidecar),
        "live_scanned": len(live),
        "verdict": verdict,
        "offenders": offenders,
        "sidecar_missing_in_live": missing,
        "actor": "UNVERIFIABLE",
        "actor_note": "TaskScheduler Operational 无停用事件；目录未提权（CEO 物理件）——与 D-20261102-10 同族",
    }

    if "--apply" in sys.argv and offenders:
        for name in offenders:
            subprocess.run(["schtasks", "/change", "/tn", name, "/disable"],
                           capture_output=True, creationflags=CREATE_NO_WINDOW)
        after = {r["name"]: r["state"] for r in query()}
        rec["apply"] = {n: after.get(n, "MISSING") for n in offenders}
        rec["verdict_after_apply"] = "OK" if all(after.get(n) == "DISABLED" for n in offenders) else "STILL-VIOLATING"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print("[pause-integrity] flag=%s expected=%s sidecar=%d live_scanned=%d"
          % (mode, expected, len(sidecar), len(live)))
    print("[pause-integrity] VERDICT=%s offenders=%d %s"
          % (verdict, len(offenders), ",".join(offenders[:12]) or "-"))
    if missing:
        print("[pause-integrity] sidecar-not-in-live=%d %s" % (len(missing), ",".join(missing[:8])))
    print("[pause-integrity] actor=UNVERIFIABLE (Tasks 未提权 + 无停用事件)")
    return 0 if verdict in ("OK", "NOT-APPLICABLE") else 1


if __name__ == "__main__":
    sys.exit(main())