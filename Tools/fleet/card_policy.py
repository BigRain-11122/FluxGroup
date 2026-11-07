#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""card_policy.py - 卡片生命周期策略的唯一读取入口。

Why (2026-11-07 审计)：同一套"卡握太久要不要收回、重试几次"的判据曾分散在四个
脚本里各写一份（closer 心跳 600s / chief 写死 1h / master_agent 重试 3 / master_solver
重试 2 / 租约两处重复）。四个写者用四套阈值改同一张卡，正是卡状态抖动和跨机抢卡的
根。现在只有 cph4/fleet/CARD-POLICY-v1.json 一个定义源，这里只负责读与给默认值。

用法：
    import card_policy as cp
    cp.lease_minutes("cpu")      # 45
    cp.heartbeat_timeout_s()     # 600
    cp.stall_after_s()           # 1800
    cp.stuck_requeue_s()         # 3600
    cp.max_attempts()            # 3
    cp.retry_error_classes()     # ("E-PATH","E-UNKNOWN","E-TIMEOUT")
    cp.load()                    # 整份 dict（含 notes，便于自检打印）

纪律：文件缺失或损坏一律用内置默认值并打印一次告警，绝不让判据失效变成"永不收回"。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PATH = os.path.join(ROOT, "cph4", "fleet", "CARD-POLICY-v1.json")

DEFAULTS = {
    "lease_minutes": {"cpu": 45, "gpu": 180, "cloud": 60, "default": 45},
    "heartbeat_timeout_s": 600,
    "stall_after_s": 1800,
    "stuck_requeue_s": 3600,
    "max_attempts": 3,
    "retry_error_classes": ["E-PATH", "E-UNKNOWN", "E-TIMEOUT"],
}

_CACHE = {}
_WARNED = [False]


def load(force=False):
    if _CACHE and not force:
        return _CACHE
    pol = dict(DEFAULTS)
    try:
        with open(PATH, encoding="utf-8") as f:
            doc = json.load(f)
        for k in DEFAULTS:
            if k in doc and doc[k] not in (None, "", [], {}):
                pol[k] = doc[k]
    except Exception as e:
        if not _WARNED[0]:
            print("[card-policy] WARN using defaults: %s" % str(e)[:100])
            _WARNED[0] = True
    _CACHE.clear()
    _CACHE.update(pol)
    return _CACHE


def lease_minutes(need="cpu"):
    d = load().get("lease_minutes") or {}
    try:
        return int(d.get(need) or d.get("default") or 45)
    except Exception:
        return 45


def heartbeat_timeout_s():
    return int(load().get("heartbeat_timeout_s") or 600)


def stall_after_s():
    return int(load().get("stall_after_s") or 1800)


def stuck_requeue_s():
    return int(load().get("stuck_requeue_s") or 3600)


def max_attempts():
    return int(load().get("max_attempts") or 3)


def retry_error_classes():
    return tuple(load().get("retry_error_classes") or ())


if __name__ == "__main__":
    p = load()
    print(json.dumps(p, ensure_ascii=False, indent=1))