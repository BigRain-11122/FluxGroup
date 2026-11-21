#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_audit.py — 按 AGENT-SPEC-v2.json 检查"这条线的智能体履职了没有、做对没有"。

为什么升到 v2（2026-11-21 实测）：v1 只判三件事——执行体在、证据在、证据新鲜，
结果 **12/12 全绿而当天一条评论都没发出去**（comments-sent 最近一条 79 小时前）。
文件被 daemon 碰过就记 OK，等于只审计了"有人动过"。

v2 的判据分三层，缺一层就是假绿：
  1 执行体存在（谁做）
  2 证据存在且在 stale_after_s 内（做了，且不是很久以前）
  3 **assert 通过（做对了）**——内容断言，全部由 social_guard.py 的 pass 映射提供

六态
  OK           三层都过
  STALE        证据过期
  MISSING      证据不存在
  NO-EXECUTOR  执行体不存在
  NOT_PASS     新鲜但不是对的结果（内容断言不过）
  SKIP         无法测量（如缺 mid、缺样本）——**不算通过**

分级：P0 红线（引流/代驾身份/夜间/跨号）、P1 产能（出稿/采集/训练/自愈）、P2 体检。
退出码：0 全 OK/SKIP；1 有非 P0 未过；2 **有 P0 未过（一票否决）**。

用法
  python3 Tools/fleet/agent_audit.py
  python3 Tools/fleet/agent_audit.py --json
  python3 Tools/fleet/agent_audit.py --tier P0
  python3 Tools/fleet/agent_audit.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
SPEC = os.path.join(SOCIAL, "AGENT-SPEC-v2.json")

TIER_NAME = {"P0": "红线", "P1": "产能", "P2": "体检"}
MARK = {"OK": "✅", "STALE": "⏳", "MISSING": "❗", "NO-EXECUTOR": "❗",
        "NOT_PASS": "❌", "SKIP": "⏭"}


def _paths(pattern):
    if not pattern:
        return []
    p = pattern if os.path.isabs(pattern) else os.path.join(ROOT, pattern)
    return glob.glob(p)


def _newest(pattern):
    hits = _paths(pattern)
    return max(hits, key=lambda p: os.path.getmtime(p)) if hits else None


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _rows(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []
    return out


def _age_h(ts):
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            return (time.time() - float(ts)) / 3600
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if d.tzinfo:
            d = d.replace(tzinfo=None)
        return (datetime.now() - d).total_seconds() / 3600
    except Exception:
        return None


def _dig(doc, path):
    cur = doc
    for part in str(path).split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def eval_assert(a, evidence_files):
    """返回 (ok, why)。ok=None 表示这条断言量不到（SKIP），不是通过。"""
    if not a:
        return True, ""
    if "all" in a:
        # 一次把所有不过的断言都报出来：只报第一条会让人以为只坏了一处，
        # 而"修完一条又冒一条"最容易被当成闸在乱跳（2026-11-21 教训）。
        fails, skips = [], []
        for sub in a["all"]:
            ok, why = eval_assert(sub, evidence_files)
            if ok is False:
                fails.append(why)
            elif ok is None:
                skips.append(why)
        if fails:
            return False, "；".join(fails)
        return (None, "；".join(skips)) if skips else (True, "")
    if a.get("kind") == "jsonl_recent":
        where = a.get("where") or {}
        max_h = float(a.get("max_age_h") or 24)
        need = int(a.get("count_gte") or 1)
        seen, hits = 0, 0
        for f in evidence_files:
            for r in _rows(f):
                if any(str(r.get(k)) != str(v) for k, v in where.items()):
                    continue
                age = _age_h(r.get("ts"))
                if age is None or age > max_h:
                    continue
                seen += 1
                hits += 1
        if hits >= need:
            return True, "%dh 内 %d 条" % (max_h, hits)
        return False, "%dh 内只有 %d 条（需 ≥%d）" % (max_h, hits, need)
    doc = None
    if evidence_files:
        doc = _load_json(max(evidence_files, key=os.path.getmtime))
    if doc is None:
        return None, "证据不是可读 JSON"
    val = _dig(doc, a.get("path", ""))
    if val is None:
        return None, "缺字段 %s" % a.get("path")
    if "eq" in a:
        return (val == a["eq"]), "%s=%r（需 %r）" % (a.get("path"), val, a["eq"])
    if "ne" in a:
        return (val != a["ne"]), "%s=%r（不许等于 %r）" % (a.get("path"), val, a["ne"])
    if "gte" in a:
        try:
            return (float(val) >= float(a["gte"])), "%s=%s（需 ≥%s）" % (
                a.get("path"), val, a["gte"])
        except Exception:
            return None, "%s 不是数字：%r" % (a.get("path"), val)
    if "lte" in a:
        try:
            return (float(val) <= float(a["lte"])), "%s=%s（需 ≤%s）" % (
                a.get("path"), val, a["lte"])
        except Exception:
            return None, "%s 不是数字：%r" % (a.get("path"), val)
    return None, "断言缺 eq/gte/lte"


def check(spec, now=None, only_tier=None):
    now = now or time.time()
    rows = []
    for d in spec.get("duties") or []:
        if only_tier and d.get("tier") != only_tier:
            continue
        ex = (d.get("exec") or "").split()[0]
        ex_path = ex if os.path.isabs(ex) else os.path.join(ROOT, ex)
        ev = d.get("evidence") or ""
        ev_files = _paths(ev)
        newest = max(ev_files, key=lambda p: os.path.getmtime(p)) if ev_files else None
        rec = {"id": d.get("id"), "tier": d.get("tier", "P2"), "ring": d.get("ring", ""),
               "name": d.get("name"), "exec": ex, "evidence": ev,
               "cadence_h": round((d.get("cadence_s") or 0) / 3600, 1),
               "symptom": d.get("symptom", "")}
        if not os.path.exists(ex_path):
            rec.update(state="NO-EXECUTOR", why="执行体不存在：%s" % ex)
        elif not newest:
            rec.update(state="MISSING", why="证据不存在：%s" % ev)
        else:
            age = now - os.path.getmtime(newest)
            limit = float(d.get("stale_after_s") or 86400)
            rec["age_h"] = round(age / 3600, 1)
            rec["limit_h"] = round(limit / 3600, 1)
            if age > limit:
                rec.update(state="STALE", why="证据 %.1fh 前（上限 %.1fh）" % (
                    age / 3600, limit / 3600))
            else:
                ok, why = eval_assert(d.get("assert"), ev_files)
                if ok is True:
                    rec.update(state="OK", why=why if why and why != "证据不是可读 JSON" else "")
                elif ok is None:
                    rec.update(state="SKIP", why=why)
                else:
                    rec.update(state="NOT_PASS", why=why)
        rows.append(rec)
    return rows


def summarize(rows):
    from collections import Counter
    by_state = Counter(r["state"] for r in rows)
    by_tier = {}
    for r in rows:
        t = by_tier.setdefault(r["tier"], Counter())
        t[r["state"]] += 1
    return {"states": dict(by_state),
            "tiers": {k: dict(v) for k, v in sorted(by_tier.items())},
            "p0_bad": [r["id"] for r in rows if r["tier"] == "P0" and r["state"] != "OK"]}


def self_test():
    """负控：每一种状态与每一种断言都必须"改坏就翻"，不许恒绿。"""
    from tempfile import mkdtemp
    d = mkdtemp()
    fresh = os.path.join(d, "fresh.json")
    json.dump({"pass": {"A": True, "B": False}, "n": 3, "level": "green"}, open(fresh, "w"))
    old = os.path.join(d, "old.json")
    json.dump({"pass": {"A": True}}, open(old, "w"))
    os.utime(old, (time.time() - 7200, time.time() - 7200))
    now = datetime.now().isoformat()
    oldts = datetime.fromtimestamp(time.time() - 100 * 3600).isoformat()
    lin = os.path.join(d, "in.jsonl")
    open(lin, "w").write("\n".join([
        json.dumps({"action": "comment", "ok": True, "ts": now}),
        json.dumps({"action": "comment", "ok": True, "ts": oldts}),
    ]) + "\n")
    spec = {"duties": [
        {"id": "OK1", "tier": "P1", "exec": "Tools/fleet/agent_audit.py",
         "evidence": fresh, "stale_after_s": 3600,
         "assert": {"path": "pass.A", "eq": True}},
        {"id": "ST1", "tier": "P1", "exec": "Tools/fleet/agent_audit.py",
         "evidence": old, "stale_after_s": 3600},
        {"id": "MI1", "tier": "P1", "exec": "Tools/fleet/agent_audit.py",
         "evidence": os.path.join(d, "nope.json"), "stale_after_s": 3600},
        {"id": "NE1", "tier": "P1", "exec": "Tools/fleet/nope.py",
         "evidence": fresh, "stale_after_s": 3600},
        {"id": "NP1", "tier": "P0", "exec": "Tools/fleet/agent_audit.py",
         "evidence": fresh, "stale_after_s": 3600,
         "assert": {"path": "pass.B", "eq": True}},
        {"id": "NP2", "tier": "P1", "exec": "Tools/fleet/agent_audit.py",
         "evidence": fresh, "stale_after_s": 3600,
         "assert": {"path": "n", "gte": 10}},
        {"id": "SK1", "tier": "P2", "exec": "Tools/fleet/agent_audit.py",
         "evidence": fresh, "stale_after_s": 3600,
         "assert": {"path": "missing.field", "eq": 1}},
        {"id": "JL1", "tier": "P1", "exec": "Tools/fleet/agent_audit.py",
         "evidence": lin, "stale_after_s": 3600,
         "assert": {"kind": "jsonl_recent", "where": {"action": "comment"},
                    "max_age_h": 24, "count_gte": 1}},
        {"id": "JL2", "tier": "P1", "exec": "Tools/fleet/agent_audit.py",
         "evidence": lin, "stale_after_s": 3600,
         "assert": {"kind": "jsonl_recent", "where": {"action": "comment"},
                    "max_age_h": 24, "count_gte": 5}},
    ]}
    rows = {r["id"]: r["state"] for r in check(spec)}
    want = {"OK1": "OK", "ST1": "STALE", "MI1": "MISSING", "NE1": "NO-EXECUTOR",
            "NP1": "NOT_PASS", "NP2": "NOT_PASS", "SK1": "SKIP",
            "JL1": "OK", "JL2": "NOT_PASS"}
    ok = all(rows.get(k) == v for k, v in want.items())
    # 负控二：把 fixture 改坏一个字段，OK1 必须不再 OK
    doc = json.load(open(fresh))
    doc["pass"]["A"] = False
    json.dump(doc, open(fresh, "w"))
    flip = {r["id"]: r["state"] for r in check(spec)}
    ok2 = flip["OK1"] == "NOT_PASS"
    # 负控三：P0 未过必须进 p0_bad（一票否决通道真的接上了）
    ok3 = "NP1" in summarize(check(spec))["p0_bad"]
    ok = ok and ok2 and ok3
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "states": want,
                      "got": rows, "tamper_flip": flip.get("OK1"),
                      "p0_veto": summarize(check(spec))["p0_bad"]},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tier", default="", choices=["", "P0", "P1", "P2"])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not os.path.exists(SPEC):
        print("缺职责表 %s" % SPEC, file=sys.stderr)
        return 2
    spec = _load_json(SPEC) or {}
    rows = check(spec, only_tier=(a.tier or None))
    s = summarize(rows)
    if a.json:
        print(json.dumps({"version": spec.get("version"), "agent": spec.get("agent", {}).get("name"),
                          "counts": s["states"], "tiers": s["tiers"], "p0_bad": s["p0_bad"],
                          "duties": rows}, ensure_ascii=False, indent=1))
    else:
        st = s["states"]
        print("== 履职 %s / %s ==" % (spec.get("agent", {}).get("name"), spec.get("version")))
        for tier in ("P0", "P1", "P2"):
            group = [r for r in rows if r["tier"] == tier]
            if not group:
                continue
            bad = sum(1 for r in group if r["state"] not in ("OK", "SKIP"))
            print("-- %s %s：%d 项，未过 %d、跳过 %d" % (
                tier, TIER_NAME[tier], len(group), bad,
                sum(1 for r in group if r["state"] == "SKIP")))
            for r in group:
                extra = ("%.1fh前" % r["age_h"]) if r.get("age_h") is not None else ""
                print("   %s %-4s %-20s %-8s %s" % (
                    MARK[r["state"]], r["id"], (r["name"] or "")[:20], extra, r["why"][:64]))
        if s["p0_bad"]:
            print("!! P0 失守：%s —— 停线排查，不许继续发" % ",".join(s["p0_bad"]))
        if st.get("SKIP"):
            print("   注：SKIP %d 项是「量不到」，不是通过（见各行的原因）" % st["SKIP"])
    if s["p0_bad"]:
        return 2
    bad = [r for r in rows if r["state"] not in ("OK", "SKIP")]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
