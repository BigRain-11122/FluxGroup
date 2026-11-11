#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vault.py - 素材库根目录的唯一解析口。

规矩（CEO 2026-11-11：移动硬盘退出长期存储）：
  环境变量 FLUX_VAULT > cph4/fleet/ASSET-VAULT.json 的 vault.path > 空（或按需报错）
两处都没有时**绝不**回落到某个写死的 /Volumes 路径——旧盘已清空，指过去只会静默失败。

用法：
    from vault import root, require
    base = root()                 # "" 表示未配置
    base = require("素材库")       # 未配置直接 SystemExit 并说清怎么配
"""
import json
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = os.path.join(ROOT_DIR, "cph4", "fleet", "ASSET-VAULT.json")


def root(cfg_path=None):
    v = os.environ.get("FLUX_VAULT")
    if v:
        return v.rstrip("/")
    try:
        with open(cfg_path or CFG, encoding="utf-8-sig") as f:
            p = ((json.load(f) or {}).get("vault") or {}).get("path")
        return (p or "").rstrip("/")
    except Exception:
        return ""


def require(what="素材库", cfg_path=None):
    p = root(cfg_path)
    if p:
        return p
    raise SystemExit(
        "未配置%s：设环境变量 FLUX_VAULT，或在 cph4/fleet/ASSET-VAULT.json 写 vault.path。"
        "移动盘已于 2026-11-11 清空退出，不再回落到 /Volumes。" % what)


def sub(*parts, cfg_path=None):
    p = root(cfg_path)
    return os.path.join(p, *parts) if p else ""
