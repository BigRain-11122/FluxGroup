#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evolve_audit.py — 反思 / 审查 / 迭代 / 创新 四件事必须有判据，不能只写在话里。

CEO 2026-11-21：「你的反思 审查 迭代 创新等属性都要在的，好好规划」。
此前的职责表只有"执行 + 度量"：出稿了没有、语料干不干净、训练有没有涨分。
但**错了之后有没有归因、改之前有没有对照、多久没往前走、有没有拿出新东西**——
这四件全都没人守，于是会出现：REJECT 只记一句分数、KEEP 连 why 都是 None、
阈值被悄悄放松、连续几天只重复干活、新能力上了却说不清有什么用。

五条判据（都能被"改坏"翻红）：
  EV01 反思覆盖  近 7 天每一轮都要有可判读的 why；失败轮必须在 LESSONS 里有归因条目
  EV02 变更审查  关键参数与 PARAMS-SNAPSHOT 的每一处差异，都必须有 CHANGE 条目（旧值/新值/为什么/证据）
  EV03 迭代节奏  近 7 天至少有 1 次实质前进（配方/数据/阈值/角度），否则判停滞
  EV04 创新落地  近 14 天至少 1 条创新条目，且必须带 measured（数字）与 verdict；无测量=没落地
  EV05 训练期换页 最近一轮训练的 swap 增量 ≤ 256MB（训练才是把 swap 顶起来的那一个）

三态：True/False/None（SKIP 不算通过）。
用法
  python3 Tools/fleet/evolve_audit.py                 # 体检
  python3 Tools/fleet/evolve_audit.py --snapshot      # 审查通过后把当前参数记为基线
  python3 Tools/fleet/evolve_audit.py --json / --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import sys
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(SOCIAL, "state")

TRAIN_LEDGER = os.path.join(SOCIAL, "train", "TRAIN-LOOP-LEDGER.jsonl")
LESSONS = os.path.join(SOCIAL, "LESSONS.jsonl")
CHANGES = os.path.join(SOCIAL, "CHANGE-LEDGER.jsonl")
INNOV = os.path.join(SOCIAL, "INNOVATION-LEDGER.jsonl")
SNAPSHOT = os.path.join(SOCIAL, "PARAMS-SNAPSHOT.json")
TRAIN_SWAP = os.path.join(STATE, "TRAIN-SWAP.jsonl")

FAIL_VERDICTS = ("REJECT", "TRAIN-FAIL", "BLOCKED", "NO-DATA")
SUBSTANTIVE_KINDS = ("recipe", "data", "threshold", "angle")
SWAP_BUDGET_MB = 256
# 反思判据生效时点：之前的行只报欠账、不判红（不伪造历史归因）
SINCE = "2026-11-21T23:40:00"


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
        pass
    return out


def _age_h(ts):
    try:
        return (datetime.now() - datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(
            tzinfo=None)).total_seconds() / 3600
    except Exception:
        return None


def _mk(cid, name, ok, detail, n=None):
    return {"id": cid, "name": name, "ok": ok, "detail": detail, "n": n}


def _import(name):
    sys.path.insert(0, HERE)
    try:
        return __import__(name)
    except Exception:
        return None


# ------------------------------------------------------------ 现行参数（live）
def live_params():
    """把"会被悄悄改掉、改了就影响判据"的参数收集成一张扁平表。"""
    p = {}
    pl = os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.ollamamodel.plist")
    try:
        d = plistlib.load(open(pl, "rb"))
        env = d.get("EnvironmentVariables") or {}
        p["ollama.MAX_LOADED_MODELS"] = env.get("OLLAMA_MAX_LOADED_MODELS")
        p["ollama.KEEP_ALIVE"] = env.get("OLLAMA_KEEP_ALIVE")
    except Exception:
        p["ollama.MAX_LOADED_MODELS"] = None
        p["ollama.KEEP_ALIVE"] = None
    tb = _import("train_build")
    p["train.RECIPE"] = getattr(tb, "RECIPE", None) if tb else None
    da = _import("diversity_audit")
    p["diversity.SHAPE_MAX"] = getattr(da, "SHAPE_MAX", None) if da else None
    p["diversity.SHORT_MIN"] = getattr(da, "SHORT_MIN", None) if da else None
    gr = _import("gate_regression")
    p["gate.POS_MIN_PASS"] = getattr(gr, "POS_MIN_PASS", None) if gr else None
    mp = _import("mem_probe")
    p["mem.RESIDENT_BUDGET_GB"] = getattr(mp, "RESIDENT_BUDGET_GB", None) if mp else None
    p["mem.MAX_RESIDENT_MODELS"] = getattr(mp, "MAX_RESIDENT_MODELS", None) if mp else None
    try:
        tk = os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.practicetick.plist")
        p["sched.practicetick_s"] = plistlib.load(open(tk, "rb")).get("StartInterval")
    except Exception:
        p["sched.practicetick_s"] = None
    return {k: v for k, v in p.items() if v is not None}


# ------------------------------------------------------------ EV01 反思
def check_reflection(now_h=24 * 7):
    allrows = [r for r in _rows(TRAIN_LEDGER) if (_age_h(r.get("ts")) or 1e9) <= now_h]
    rows = [r for r in allrows if str(r.get("ts") or "") >= SINCE]
    debt = len(allrows) - len(rows)
    if not rows:
        return _mk("EV01", "反思覆盖（每轮有归因）", None,
                   "%dh 内没有训练轮次（判据自 %s 起）" % (now_h, SINCE[:16]))
    blind, fails, lessons = [], [], _rows(LESSONS)
    keys = set()
    for l in lessons:
        for k in ("run", "seg", "key"):
            if l.get(k):
                keys.add(str(l[k]))
    for r in rows:
        why = str(r.get("why") or "").strip()
        verdict = r.get("verdict")
        # 让路不是失败（2026-11-21 反思：music_seeker/peer_pro 两条 BLOCKED 的 why 是
        # 「GPU 让路：selfgen 占用」，把它算成失败会让"失败率"和"反思覆盖"同时失真）
        routed = verdict == "BLOCKED" and ("让路" in why or "占用" in why)
        if verdict in FAIL_VERDICTS and not routed:
            fails.append(r)
        if (not why) or why in ("None", "nan", "-"):
            blind.append("%s %s(why 空)" % (r.get("ts"), r.get("seg")))
        elif verdict == "KEEP" and not any(ch.isdigit() for ch in why):
            blind.append("%s %s(KEEP 无数字)" % (r.get("ts"), r.get("seg")))
    uncovered = [r for r in fails
                 if not ({str(r.get("run") or ""), str(r.get("seg") or "")} & keys)]
    ok = (not blind) and (not uncovered)
    detail = "判据起 %s：%d 轮，无可判读 why %d 条%s；真失败 %d 轮（让路不计），未归因 %d 轮；历史欠账 %d 条（不判红）" % (
        SINCE[:16], len(rows), len(blind), ("（" + "；".join(blind[:3]) + "）") if blind else "",
        len(fails), len(uncovered), debt)
    if uncovered:
        detail += "：" + ",".join(str(r.get("seg")) for r in uncovered[:4])
    return _mk("EV01", "反思覆盖（每轮有归因）", ok, detail, len(rows))


# ------------------------------------------------------------ EV02 变更审查
def check_change_review():
    live = live_params()
    try:
        snap = json.load(open(SNAPSHOT, encoding="utf-8"))
    except Exception:
        return _mk("EV02", "变更审查（参数留痕）", None,
                   "没有基线 PARAMS-SNAPSHOT.json，先跑 --snapshot 并逐条补 CHANGE")
    base = snap.get("params") or {}
    diffs = []
    for k, v in live.items():
        if k in base and str(base[k]) != str(v):
            diffs.append((k, base[k], v))
        elif k not in base:
            diffs.append((k, None, v))
    ledger = _rows(CHANGES)
    covered = set()
    for c in ledger:
        if c.get("param"):
            covered.add(str(c["param"]))
    un = [d for d in diffs if d[0] not in covered]
    ok = not un
    detail = "参数 %d 项，与基线差 %d 处%s" % (
        len(live), len(diffs),
        ("；未审查：" + "，".join("%s %s→%s" % d for d in un[:4])) if un else
        ("（均有 CHANGE 条目）" if diffs else "（无差异）"))
    return _mk("EV02", "变更审查（参数留痕）", ok, detail, len(diffs))


# ------------------------------------------------------------ EV03 迭代节奏
def check_iteration(days=7):
    rows = [c for c in _rows(CHANGES)
            if (_age_h(c.get("ts")) or 1e9) <= days * 24]
    subst = [c for c in rows if str(c.get("kind")) in SUBSTANTIVE_KINDS]
    ok = len(subst) >= 1
    detail = "近 %d 天变更 %d 条，其中实质前进（配方/数据/阈值/角度）%d 条%s" % (
        days, len(rows), len(subst),
        "" if ok else "；只调参不动结构＝原地踏步")
    return _mk("EV03", "迭代节奏（%d 天有前进）" % days, ok, detail, len(subst))


# ------------------------------------------------------------ EV04 创新落地
def check_innovation(days=14):
    rows = [c for c in _rows(INNOV)
            if (_age_h(c.get("ts")) or 1e9) <= days * 24]
    if not rows:
        return _mk("EV04", "创新落地（带测量）", False, "近 %d 天没有创新条目" % days, 0)
    bad = [c for c in rows if c.get("measured") in (None, "") or
           str(c.get("verdict") or "") not in ("kept", "rolled_back")]
    ok = (not bad) and any(str(c.get("verdict")) == "kept" for c in rows)
    detail = "近 %d 天 %d 条：%s" % (
        days, len(rows),
        "全部带 measured 与 verdict" if not bad
        else "缺测量/缺结论：" + ",".join(str(c.get("what"))[:14] for c in bad[:3]))
    return _mk("EV04", "创新落地（带测量）", ok, detail, len(rows))


# ------------------------------------------------------------ EV05 训练期换页
def check_train_swap(days=7):
    rows = [r for r in _rows(TRAIN_SWAP) if (_age_h(r.get("ts")) or 1e9) <= days * 24]
    if not rows:
        return _mk("EV05", "训练期换页（≤%dMB）" % SWAP_BUDGET_MB, None,
                   "近 %d 天没有 TRAIN-SWAP 记录（训练侧未落盘）" % days)
    r = rows[-1]
    try:
        delta = round(float(r.get("sw1")) - float(r.get("sw0")), 1)
    except Exception:
        return _mk("EV05", "训练期换页（≤%dMB）" % SWAP_BUDGET_MB, None, "记录缺 sw0/sw1")
    ok = delta <= SWAP_BUDGET_MB
    return _mk("EV05", "训练期换页（≤%dMB）" % SWAP_BUDGET_MB, ok,
               "最近一轮 %s：swap %.0f→%.0fMB（%+.0fMB）" % (
                   str(r.get("ts"))[:19], float(r.get("sw0")), float(r.get("sw1")), delta))


CHECKS = [check_reflection, check_change_review, check_iteration, check_innovation,
          check_train_swap]


def run_all():
    out = [f() for f in CHECKS]
    doc = {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "pass": {c["id"]: c["ok"] for c in out}, "checks": out}
    os.makedirs(STATE, exist_ok=True)
    p = os.path.join(STATE, "EVOLVE.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    return doc


def write_snapshot():
    doc = {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "_why": "参数基线：任何与它的差异都必须有 CHANGE-LEDGER 条目，否则判未审查",
           "params": live_params()}
    tmp = SNAPSHOT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    os.replace(tmp, SNAPSHOT)
    return doc


def self_test():
    """负控：why 空必须红、参数漂移无台账必须红、无前进必须红、无测量必须红。"""
    from tempfile import mkdtemp
    d = mkdtemp()
    res = {}
    globals_backup = {k: globals()[k] for k in
                      ("TRAIN_LEDGER", "LESSONS", "CHANGES", "INNOV", "SNAPSHOT", "TRAIN_SWAP")}

    def put(name, rows):
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return p

    now = datetime.now().isoformat()

    def scenario(name, train, lessons, changes, innov, snapshot, expect):
        globals()["TRAIN_LEDGER"] = put("t_%s.jsonl" % name, train)
        globals()["LESSONS"] = put("l_%s.jsonl" % name, lessons)
        globals()["CHANGES"] = put("c_%s.jsonl" % name, changes)
        globals()["INNOV"] = put("i_%s.jsonl" % name, innov)
        globals()["SNAPSHOT"] = os.path.join(d, "s_%s.json" % name)
        with open(globals()["SNAPSHOT"], "w", encoding="utf-8") as f:
            json.dump({"params": snapshot}, f)

        def fake_live():
            return snapshot
        old = globals()["live_params"]
        globals()["live_params"] = fake_live
        try:
            got = {c["id"]: c["ok"] for c in run_all()["checks"]}
        finally:
            globals()["live_params"] = old
        res[name] = "PASS" if got.get(expect[0]) is expect[1] else "FAIL:%s" % got.get(expect[0])

    globals()["SINCE"] = "2000-01-01T00:00:00"
    good_train = [{"ts": now, "seg": "a", "verdict": "KEEP", "why": "均分 +12.0"}]
    good_les = [{"ts": now, "seg": "b", "why": "缺料"}]
    good_ch = [{"ts": now, "kind": "threshold", "param": "train.RECIPE", "old": "v4", "new": "v5"}]
    good_in = [{"ts": now, "what": "形状配额", "measured": "短评 15%→29%", "verdict": "kept"}]
    snap = {"train.RECIPE": "v5"}

    scenario("all_good", good_train, good_les, good_ch, good_in, snap, ("EV01", True))
    scenario("why_blank", [{"ts": now, "seg": "a", "verdict": "KEEP", "why": None}],
             good_les, good_ch, good_in, snap, ("EV01", False))
    scenario("fail_uncovered", good_train + [{"ts": now, "seg": "z", "verdict": "REJECT", "why": "均分 -3"}],
             good_les, good_ch, good_in, snap, ("EV01", False))
    scenario("param_drift", good_train, good_les, [],
             good_in, {"train.RECIPE": "v5"}, ("EV02", True))
    globals()["TRAIN_LEDGER"] = put("t_drift.jsonl", good_train)
    globals()["LESSONS"] = put("l_drift.jsonl", good_les)
    globals()["CHANGES"] = put("c_drift.jsonl", [])
    globals()["SNAPSHOT"] = os.path.join(d, "s_drift.json")
    json.dump({"params": {"train.RECIPE": "v4"}}, open(globals()["SNAPSHOT"], "w"))
    old = globals()["live_params"]
    globals()["live_params"] = lambda: {"train.RECIPE": "v5"}
    try:
        got = {c["id"]: c["ok"] for c in run_all()["checks"]}
    finally:
        globals()["live_params"] = old
    res["param_drift_unreviewed"] = "PASS" if got.get("EV02") is False else "FAIL"
    scenario("stagnant", good_train, good_les, [], good_in, snap, ("EV03", False))
    scenario("no_measure", good_train, good_les, good_ch,
             [{"ts": now, "what": "新角度池", "verdict": "kept"}], snap, ("EV04", False))
    for k, v in globals_backup.items():
        globals()[k] = v
    ok = all(v == "PASS" for v in res.values())
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "cases": res},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.snapshot:
        print(json.dumps(write_snapshot(), ensure_ascii=False, indent=1))
        return 0
    doc = run_all()
    if a.json:
        print(json.dumps(doc, ensure_ascii=False, indent=1))
    else:
        print("== 反思/审查/迭代/创新 %s ==" % doc["ts"])
        for c in doc["checks"]:
            mark = {True: "✅", False: "❗", None: "⏭"}[c["ok"]]
            print("%s %-4s %-22s %s" % (mark, c["id"], c["name"], c["detail"]))
    return 0 if all(c["ok"] is not False for c in doc["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
