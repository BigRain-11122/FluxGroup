#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""契约校验器：宪法 + 类别 + 项目三层，确定性判定，零 LLM。

用法:
    python Tools/agents/contract_lint.py            # 校验 contracts/*.yaml
    python Tools/agents/contract_lint.py --self-test # 负控自检
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "cph4" / "fleet" / "game-v2"
CONST = BASE / "constitution.yaml"
CLASSES = BASE / "classes.yaml"
CONTRACTS = BASE / "contracts"
REPORT = CONTRACTS / "_lint-report.json"

REQUIRED = [
    "schema", "version", "project_id", "name", "class",
    "constitution_version", "class_version",
    "phase", "experiment_id",
    "player", "scene", "core_verb",
    "session_seconds", "session_minutes",
    "strongest_second_what", "strongest_second_at",
    "primary_platforms", "shells", "price_usd",
    "content_hours", "wishlist_target", "refund_max", "tax_rate_assumed", "net_target_cny",
    "ads", "server", "reskin_only", "multi_touch_required",
    "reuse_ratio", "cycle_weeks",
    "done_gates", "done_addenda", "not_doing", "kill", "status",
]

VERB_SEPS = ["、", ",", "，", "/", "／", "和", "与", "+"]


def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def as_list(v):
    return v if isinstance(v, list) else []


def check_articles(p, const):
    fails = []
    for art in const.get("articles", []):
        chk = art.get("check") or {}
        kind = chk.get("kind")

        if kind == "enum":
            f = chk["field"]
            if f in p and p[f] not in chk["values"]:
                fails.append(f"{art['id']} enum: {f}={p[f]} 不在 {chk['values']}")

        elif kind == "range_map":
            for f, (lo, hi) in (chk.get("fields") or {}).items():
                if f not in p:
                    continue
                try:
                    v = float(p[f])
                except (TypeError, ValueError):
                    fails.append(f"{art['id']} range: {f} 非数字")
                    continue
                if not (lo <= v <= hi):
                    fails.append(f"{art['id']} range: {f}={v} 超出 [{lo},{hi}]")

        elif kind == "bool":
            scope = chk.get("scope")
            if scope and p.get("class") not in scope:
                continue
            for f, expected in (chk.get("fields") or {}).items():
                if f not in p:
                    continue
                if bool(p[f]) is not bool(expected):
                    fails.append(f"{art['id']} bool: {f}={p[f]} 应为 {expected}")

        elif kind == "receipt":
            gates = set(as_list(p.get("done_gates")))
            missing = [g for g in chk.get("gates", []) if g not in gates]
            if missing:
                fails.append(f"{art['id']} receipt: 缺闸 {missing}")

        # manual 闸由人判，不在本脚本判定
    return fails


def check_class(p, classes):
    fails = []
    cls_name = p.get("class")
    cls = (classes.get("classes") or {}).get(cls_name)
    if not cls:
        return [f"class 未定义: {cls_name}"]

    allowed = set(as_list(cls.get("primary_platforms")))
    if not set(as_list(p.get("primary_platforms"))) <= allowed:
        fails.append(f"主平台 {p.get('primary_platforms')} 超出类别允许 {sorted(allowed)}")

    allowed_shells = set(as_list(cls.get("allowed_shells")))
    if not set(as_list(p.get("shells"))) <= allowed_shells:
        fails.append(f"壳 {p.get('shells')} 超出类别允许 {sorted(allowed_shells)}")

    lo, hi = (cls.get("price_usd") or [0, 0])
    try:
        price = float(p.get("price_usd"))
        if not (lo <= price <= hi):
            fails.append(f"价格 {price} 超出类别区间 [{lo},{hi}]")
    except (TypeError, ValueError):
        fails.append("price_usd 非数字")

    for f in ("ads", "server"):
        if f in cls and bool(p.get(f)) is not bool(cls[f]):
            fails.append(f"{f}={p.get(f)} 与类别要求 {cls[f]} 不符")

    if "cycle_weeks" in cls:
        lo, hi = cls["cycle_weeks"]
        try:
            cw = float(p.get("cycle_weeks"))
            if not (lo <= cw <= hi):
                fails.append(f"周期 {cw} 周超出类别区间 [{lo},{hi}]")
        except (TypeError, ValueError):
            fails.append("cycle_weeks 非数字")

    if "content_levels" in cls and p.get("content_levels") != cls["content_levels"]:
        fails.append(f"content_levels 应为 {cls['content_levels']}，实际 {p.get('content_levels')}")

    if cls_name == "A":
        try:
            ch = float(p.get("content_hours"))
            lo, hi = cls.get("content_hours", [0, 99])
            if not (lo <= ch <= hi):
                fails.append(f"content_hours {ch} 超出类别区间 [{lo},{hi}]")
        except (TypeError, ValueError):
            fails.append("content_hours 非数字")
        try:
            wt = float(p.get("wishlist_target", 0))
            if wt < 5000:
                fails.append(f"A 类 wishlist_target 不得低于 5000，实际 {wt}")
        except (TypeError, ValueError):
            fails.append("wishlist_target 非数字")

    if cls.get("monetization") == "iaa":
        pol = p.get("ad_policy") or {}
        req = cls.get("ad_policy") or {}
        if not pol:
            fails.append("B 类必须写 ad_policy")
        else:
            if pol.get("first_levels_no_ads", 0) < req.get("first_levels_no_ads", 0):
                fails.append("ad_policy: 前 N 关无广告不足")
            if pol.get("interstitial_cooldown_s", 0) < req.get("interstitial_cooldown_s", 0):
                fails.append("ad_policy: 插屏冷却过短")
            if pol.get("daily_cap", 999) > req.get("daily_cap", 0):
                fails.append("ad_policy: 每日广告上限过高")
            if bool(pol.get("during_play", True)):
                fails.append("ad_policy: 核心玩法中不得插广告")

    need = set(as_list(cls.get("gates_add")))
    got = set(as_list(p.get("done_addenda")))
    missing = sorted(need - got)
    if missing:
        fails.append(f"类别附加验收缺失: {missing}")
    return fails


def check_project(p, const, classes):
    fails = []
    if not isinstance(p, dict):
        return ["文件不是映射"]

    if p.get("schema") != "fluxgame/project":
        fails.append(f"schema 应为 fluxgame/project，实际 {p.get('schema')}")

    for k in REQUIRED:
        if k not in p:
            fails.append(f"缺字段: {k}")

    if p.get("constitution_version") != const.get("version"):
        fails.append("constitution_version 与当前宪法不一致")
    if p.get("class_version") != classes.get("version"):
        fails.append("class_version 与当前类别不一致")

    phase = p.get("phase")
    if phase not in ("experiment", "mass"):
        fails.append(f"phase 必须为 experiment/mass，实际 {phase}")
    if phase == "experiment" and not p.get("experiment_id"):
        fails.append("experiment 阶段必须写 experiment_id")

    try:
        refund = float(p.get("refund_max"))
        if not (0 <= refund <= 0.15):
            fails.append(f"refund_max 必须在 0–0.15，实际 {refund}")
    except (TypeError, ValueError):
        fails.append("refund_max 非数字")

    try:
        tax = float(p.get("tax_rate_assumed"))
        if tax < 0.20:
            fails.append(f"tax_rate_assumed 不得低于 0.20，实际 {tax}")
    except (TypeError, ValueError):
        fails.append("tax_rate_assumed 非数字")

    try:
        nt = float(p.get("net_target_cny"))
        if p.get("class") == "A" and nt < 30000:
            fails.append(f"A 类 net_target_cny 不得低于 30000，实际 {nt}")
        if p.get("class") in ("B", "C") and nt != 0:
            fails.append(f"{p.get('class')} 类 net_target_cny 应为 0，实际 {nt}")
    except (TypeError, ValueError):
        fails.append("net_target_cny 非数字")

    verb = str(p.get("core_verb") or "")
    if not verb or any(s in verb for s in VERB_SEPS):
        fails.append(f"core_verb 必须是单一动词，实际: {verb!r}")

    for f, minimum in (("not_doing", 3), ("kill", 3)):
        if len(as_list(p.get(f))) < minimum:
            fails.append(f"{f} 至少 {minimum} 条")

    gates = as_list(p.get("done_gates"))
    if len(gates) != 8:
        fails.append(f"done_gates 必须 8 个，实际 {len(gates)}")

    try:
        r = float(p.get("reuse_ratio"))
        if not (0 <= r <= 1):
            fails.append("reuse_ratio 必须在 0–1")
    except (TypeError, ValueError):
        fails.append("reuse_ratio 非数字")

    fails.extend(check_articles(p, const))
    fails.extend(check_class(p, classes))
    return fails


def contract_hash(p) -> str:
    raw = json.dumps(p, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def self_test(const, classes):
    bad = {
        "schema": "fluxgame/project", "version": "1.0.0",
        "project_id": "BAD", "name": "bad", "class": "A",
        "constitution_version": "1.0.0", "class_version": "1.0.0",
        "player": "x", "scene": "x", "core_verb": "吸/清",
        "session_seconds": 180, "session_minutes": 45,
        "strongest_second_what": "x", "strongest_second_at": 60,
        "primary_platforms": ["steam"], "shells": ["wechat_slice"],
        "price_usd": 4.99,
        "ads": True, "server": True, "reskin_only": True, "multi_touch_required": True,
        "reuse_ratio": 1.5, "cycle_weeks": 20,
        "done_gates": ["G1"], "done_addenda": [],
        "not_doing": ["x"], "kill": ["x"], "status": "candidate",
    }
    fails = check_project(bad, const, classes)
    expect = [
        "session_seconds", "session_minutes", "strongest_second_at",
        "core_verb", "not_doing", "kill", "done_gates",
        "reuse_ratio", "价格", "ads", "server",
    ]
    hit = sum(1 for e in expect if any(e in f for f in fails))
    ok = hit >= 8
    print(json.dumps({"self_test": "PASS" if ok else "FAIL",
                      "hit": hit, "expected": len(expect), "failures": len(fails)},
                     ensure_ascii=False))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    const = load_yaml(CONST)
    classes = load_yaml(CLASSES)

    if args.self_test:
        return 0 if self_test(const, classes) else 1

    rows = []
    ok_all = True
    for f in sorted(CONTRACTS.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        try:
            p = load_yaml(f)
        except Exception as exc:  # noqa: BLE001
            rows.append({"file": f.name, "pass": False, "failures": [f"YAML 解析失败: {exc}"]})
            ok_all = False
            continue
        fails = check_project(p, const, classes)
        rows.append({
            "file": f.name,
            "project_id": p.get("project_id") if isinstance(p, dict) else None,
            "hash": contract_hash(p) if isinstance(p, dict) else None,
            "pass": not fails,
            "failures": fails,
        })
        ok_all = ok_all and not fails

    report = {
        "schema": "fluxgame/lint/1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "constitution_version": const.get("version"),
        "classes_version": classes.get("version"),
        "contracts": rows,
        "all_pass": ok_all,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    for r in rows:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{status}] {r['file']} ({r.get('project_id')}) hash={r.get('hash')}")
        for x in r.get("failures", []):
            print(f"    - {x}")
    print(json.dumps({"report": str(REPORT), "all_pass": ok_all, "n": len(rows)}, ensure_ascii=False))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
