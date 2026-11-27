#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""practice_due.py — 出稿到期判断：训练开训前问一句"是不是该让给出稿"。

为什么（2026-11-21 CEO「把本地算力利用到位」）：训练一轮 40–50 分钟连续占 GPU，
而养号出稿每 30 分钟只要 60 秒。谁先谁后不能靠"谁先起"——训练每 5 分钟 tick 一次，
它一起来就把出稿挤掉 50 分钟。判据：距上一次成功发帖超过 (间隔 - 3 分钟) 就算到期。

用法：python3 Tools/fleet/practice_due.py [--within 180]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOG = os.path.join(ROOT, "cph4", "fleet", "social", "practice-log.jsonl")
# 2026-11-21 实锚：养号动作有两条落账路径——practice_tick 写 practice-log，
# 常驻 agent 写 USER-AGENT-LEDGER。只看前者会得出"今天 0 出稿"的错结论，
# 于是训练永远不让路，把养号活活饿死一整天。
AGENT_LOG = os.path.join(ROOT, "cph4", "fleet", "social", "USER-AGENT-LEDGER.jsonl")
INTERVAL_S = int(os.environ.get("FLUX_PUBLISH_INTERVAL_S") or 1800)          # 与 com.fluxgroup.practicetick 的 StartInterval 一致


def last_post_ts():
    ts = None
    try:
        for line in open(LOG, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("action") == "post" and r.get("ok") in (True, "True", "true"):
                ts = r.get("ts") or ts
    except Exception:
        return None
    if not ts:
        return None
    try:
        return time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return None


YIELD_STATE = os.path.join(ROOT, "cph4", "fleet", "state", "publish-yield.json")
YIELD_COOLDOWN_S = 1500    # 出稿一轮 30 分钟，让过一次后 25 分钟内不再让（保证每个出稿窗口都有机会）


def _last_yield():
    try:
        return float(json.load(open(YIELD_STATE, encoding="utf-8")).get("ts") or 0)
    except Exception:
        return 0.0


def last_activity_ts():
    """两条台账里最新的动作时间（任意动作都算"机器在动"）。"""
    best = None
    for path in (LOG, AGENT_LOG):
        try:
            for line in open(path, encoding="utf-8"):
                if not line.strip():
                    continue
                ts = str(json.loads(line).get("ts") or "")[:19]
                if len(ts) < 19:
                    continue
                try:
                    t = time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))
                except Exception:
                    continue
                best = t if best is None else max(best, t)
        except Exception:
            continue
    return best


def due(within_s=180, interval_s=INTERVAL_S, mark=False):
    """到期判断。mark=True 时记一次"已让路"，用于冷却，防止训练被永久饿死。

    2026-11-21 实锚：出稿如果因为没登录/账号被限流长期发不出去，而训练每 tick 都
    让路，"该让"就变成"永远不让训练"。所以让路本身要有冷却。
    """
    if time.time() - _last_yield() < YIELD_COOLDOWN_S:
        return False, "刚让过一次（%d 秒内不再让）" % YIELD_COOLDOWN_S
    ts = last_activity_ts()
    if ts is None:
        ok, why = True, "没有任何养号动作记录"
    else:
        age = time.time() - ts
        ok = age >= interval_s - within_s
        why = ("距上帖 %.0f 分钟（间隔 %d 分钟）" % (age / 60, interval_s // 60)
               if ok else "距上帖 %.0f 分钟，未到期" % (age / 60))
    if ok and mark:
        try:
            os.makedirs(os.path.dirname(YIELD_STATE), exist_ok=True)
            json.dump({"ts": time.time(), "why": why},
                      open(YIELD_STATE, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception:
            pass
    return ok, why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--within", type=int, default=180)
    a = ap.parse_args()
    d, why = due(a.within)
    print(json.dumps({"due": d, "why": why}, ensure_ascii=False))
    return 0 if d else 1


if __name__ == "__main__":
    sys.exit(main())
