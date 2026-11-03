#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_policy.py - 本地模型名字的唯一来源。

为什么（2026-11-03 实测）：同一个"现役模型"在 6 个工具里各写了一遍
（autowork/digest_agent/brain_service/local_ai_business/local_judge/fleet_lane），
策略文件改了也不会生效——这就是"判据两处定义=修一处等于没修"的同族病。
本模块只做一件事：谁要模型名，都从这里取；取不到就回退到写死值，绝不让工具起不来。

用法：
  from model_policy import resident, duty
  resident()            -> "qwen3.5:4b-mlx"
  duty("deep")          -> "qwen3.5:35b-a3b"
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
POLICY = os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json")

FALLBACK = {
    "resident": "qwen3:4b-instruct",
    "embedding": "qwen3-embedding:0.6b",
    "deep": "qwen3.5:35b-a3b",
}
_cache = {}


def _load():
    if "policy" in _cache:
        return _cache["policy"]
    try:
        with open(POLICY, encoding="utf-8") as f:
            _cache["policy"] = json.load(f)
    except Exception:
        _cache["policy"] = {}
    return _cache["policy"]


def duty(name, default=None):
    """按策略取某个职责的模型名；缺失则回退。"""
    d = (_load().get("duties") or {}).get(name) or {}
    return d.get("model") or default or FALLBACK.get(name)


def resident():
    return duty("resident") or FALLBACK["resident"]


def embedding():
    return duty("embedding") or FALLBACK["embedding"]


def duty_budget_gb(name):
    d = (_load().get("duties") or {}).get(name) or {}
    try:
        return float(d.get("budget_gb") or 0)
    except Exception:
        return 0.0


def thresholds():
    return _load().get("thresholds") or {}


def accept_upgrade():
    return _load().get("accept_upgrade") or {}