#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_schedule.py - 智能体频率与额度裁决（高频但不过载）。

CEO 2026-11-11：「智能体你好好规划，我要高频率且科学，但要在主控和算力大脑的
能力范围内，不要过载。」

三件事：
  --plan    算出每个席位"多久跑一次、一天几次、吃多少 token"，并对主控/算力大脑做额度核算
  --tick    到点的席位才跑：事件型席位先比输入指纹，指纹没变直接跳过（高频不靠死盯时间）
  --check   超预算返回非零，接进主控脉当闸

零成本优先：est_tokens=0 的席位（记账）不调模型，只跑脚本，可以高频。
用法：
  python3 Tools/fleet/agent_schedule.py --plan
  python3 Tools/fleet/agent_schedule.py --tick --station visual --max-runs 3
  python3 Tools/fleet/agent_schedule.py --check
  python3 Tools/fleet/agent_schedule.py --self-test
返回码：0 正常 / 1 有超预算 / 3 自检失败
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402

STATE_REL = os.path.join("cph4", "fleet", "state", "agent-schedule.json")


def _p(name, root=None):
    return os.path.join(root or ROOT, "cph4", "fleet", name)


def _j(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _state(root=None):
    return _j(os.path.join(root or ROOT, STATE_REL), {}) or {}


def _save_state(st, root=None):
    p = os.path.join(root or ROOT, STATE_REL)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def policy(seat_id, cap):
    """席位按 id 精确匹配，其次按后缀通配（*-INSPECT），最后默认。"""
    seats = cap.get("seat_policy") or cap.get("seats") or {}
    if seat_id in seats:
        return seats[seat_id]
    for k, v in seats.items():
        if k.startswith("*") and seat_id.endswith(k[1:]):
            return v
    return seats.get("_default") or {}


def plan(root=None):
    """核算：每席"实际预期用量"（不是上限）× 单价 token → 按机器分账，看谁超。"""
    cap = _j(_p("AGENT-CAPACITY-v1.json", root), {}) or {}
    teams = (_j(_p("AGENT-TEAMS-v1.json", root), {}) or {}).get("teams") or {}
    machines = cap.get("machines") or {}
    rows, totals = [], {}
    for station, seats in teams.items():
        ev = int((machines.get(station) or {}).get("events_per_day") or 24)
        for s in seats:
            pol = policy(s["id"], cap)
            freq = max(60, int(pol.get("freq_s") or 1800))
            ceiling = min(int(pol.get("max_per_day") or 16), 86400 // freq)
            gate = pol.get("gate") or "event"
            # 事件型：一天真正触发的次数≈事件数（受硬上限约束）；定时型：按周期
            expected = ceiling if gate == "time" else min(ceiling, ev)
            tok = int(pol.get("est_tokens") or 0)
            where = pol.get("endpoint") or "local"
            acct = station if where == "local" else "brain"
            tok_day = tok * expected
            spec = machines.get(acct) or {}
            mins = round(tok_day / max(1, int(spec.get("tok_s") or 40)) / 60, 1)
            t = totals.setdefault(acct, {"calls": 0, "tokens": 0, "minutes": 0.0})
            if tok:                      # 零模型席位（记账）不占模型额度
                t["calls"] += expected
            t["tokens"] += tok_day; t["minutes"] = round(t["minutes"] + mins, 1)
            rows.append({"station": station, "seat": s["id"], "gate": gate, "freq_s": freq,
                         "ceiling": ceiling, "expected": expected, "tokens": tok,
                         "acct": acct, "tok_day": tok_day, "minutes_day": mins})
    verdict = []
    for acct, t in totals.items():
        b = (machines.get(acct) or {}).get("budget") or {}
        over = []
        if t["calls"] > (b.get("calls_per_day") or 10 ** 9):
            over.append("调用 %d>%s" % (t["calls"], b.get("calls_per_day")))
        if t["minutes"] > (b.get("model_minutes_per_day") or 10 ** 9):
            over.append("模型时间 %s>%s 分钟" % (t["minutes"], b.get("model_minutes_per_day")))
        verdict.append({"acct": acct, "machine": (machines.get(acct) or {}).get("name"),
                        "calls_day": t["calls"], "minutes_day": round(t["minutes"], 1),
                        "budget_calls": b.get("calls_per_day"),
                        "budget_minutes": b.get("model_minutes_per_day"),
                        "over": over})
    return {"rows": rows, "verdict": verdict, "over": [v for v in verdict if v["over"]]}


def _fingerprint(station, root=None):
    """输入指纹：队列状态 + 承接工序的产物 mtime + 回执数。变了才叫事件。"""
    h = hashlib.sha256()
    for r in sorted(ss.read_queue(station, root), key=lambda x: str(x.get("id"))):
        h.update(("%s:%s|" % (r.get("id"), r.get("state"))).encode())
    tax = _j(_p("TAXONOMY-v1.json", root), {}) or {}
    prods = (_j(_p("PRODUCTS.json", root), {}) or {}).get("products") or []
    types = {t["id"]: t for t in tax.get("task_types") or []}
    smap = tax.get("stage_map") or {}
    for p in prods:
        outs = p.get("outputs") or {}
        for stg in (p.get("stages") or []):
            tid = (smap.get(p["id"]) or {}).get(stg)
            if station not in ((types.get(tid) or {}).get("stations") or []):
                continue
            rel = outs.get(stg)
            if not rel:
                continue
            fp = os.path.join(root or ROOT, rel)
            h.update(("%s:%s|" % (rel, os.path.getmtime(fp) if os.path.exists(fp) else 0)).encode())
    rd = os.path.join(root or ROOT, "cph4", "fleet", "rt", station, "receipts")
    h.update(str(len(os.listdir(rd)) if os.path.isdir(rd) else 0).encode())
    return h.hexdigest()[:16]


def due(station, seats, cap, st, now=None, root=None):
    """返回本轮该跑的席位（含跳过原因）。"""
    now = now or time.time()
    runs = st.get("runs") or {}
    fps = st.get("fingerprints") or {}
    today = date.today().isoformat()
    used = (st.get("day") or {}).get(today) or {}
    out = []
    fp_now = None
    for s in seats:
        pol = policy(s["id"], cap)
        freq = max(60, int(pol.get("freq_s") or 1800))
        last = runs.get(s["id"])
        if last is not None and (now - float(last)) < freq:   # 从未跑过=立刻该跑
            continue
        gate = pol.get("gate") or "event"
        if gate == "event":
            if fp_now is None:
                fp_now = _fingerprint(station, root)
            prev = fps.get(station)
            if prev and prev == fp_now:
                out.append({"seat": s["id"], "skip": "输入未变（事件门）"})
                continue
        where = pol.get("endpoint") or "local"
        ep = station if where == "local" else "brain"
        cap_calls = (((cap.get("machines") or {}).get(ep) or {}).get("budget") or {}).get("calls_per_day") or 10 ** 9
        if used.get(ep, 0) >= cap_calls:
            out.append({"seat": s["id"], "skip": "当日额度用尽(%s)" % ep})
            continue
        per_day = int(pol.get("max_per_day") or 16)
        ran_today = ((st.get("day_seats") or {}).get(today) or {}).get(s["id"], 0)
        if ran_today >= per_day:
            out.append({"seat": s["id"], "skip": "单席日上限(%d)" % per_day})
            continue
        out.append({"seat": s["id"], "run": True, "endpoint": ep,
                    "tokens": int(pol.get("est_tokens") or 0)})
    return out, fp_now


def tick(station, cap, st, now=None, max_runs=3, root=None):
    seats = ((_j(_p("AGENT-TEAMS-v1.json", root), {}) or {}).get("teams") or {}).get(station) or []
    cands, fp_now = due(station, seats, cap, st, now, root)
    to_run = [c for c in cands if c.get("run")][:max_runs]
    for c in to_run:
        st.setdefault("runs", {})[c["seat"]] = now or time.time()
        today = date.today().isoformat()
        if c["tokens"]:
            d = st.setdefault("day", {}).setdefault(today, {})
            d[c["endpoint"]] = d.get(c["endpoint"], 0) + 1
        ds = st.setdefault("day_seats", {}).setdefault(today, {})
        ds[c["seat"]] = ds.get(c["seat"], 0) + 1
    if fp_now:
        st.setdefault("fingerprints", {})[station] = fp_now
    return {"station": station, "ran": to_run,
            "skipped": [c for c in cands if c.get("skip")]}


def self_test():
    import tempfile
    ok = total = 0

    def chk(n, c):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s" % ("ok  " if c else "FAIL", n))

    cap = {"machines": {"control": {"tok_s": 40, "events_per_day": 40,
                                    "budget": {"calls_per_day": 10, "model_minutes_per_day": 60}},
                        "visual": {"tok_s": 24, "events_per_day": 40,
                                   "budget": {"calls_per_day": 50, "model_minutes_per_day": 60}},
                        "brain": {"tok_s": 18, "events_per_day": 20,
                                  "budget": {"calls_per_day": 100, "model_minutes_per_day": 600}}},
           "seat_policy": {"*-INSPECT": {"gate": "event", "freq_s": 300, "est_tokens": 700,
                                   "max_per_day": 96, "endpoint": "control"},
                     "X-LEAD": {"gate": "time", "freq_s": 3600, "est_tokens": 900,
                                "max_per_day": 12, "endpoint": "local"},
                     "_default": {"gate": "time", "freq_s": 1800, "est_tokens": 100,
                                  "max_per_day": 4, "endpoint": "local"}}}
    chk("通配匹配 *-INSPECT", policy("V-INSPECT", cap)["freq_s"] == 300)
    chk("精确匹配优先", policy("X-LEAD", cap)["gate"] == "time")
    chk("未知席位走默认", policy("Z-UNKNOWN", cap)["freq_s"] == 1800)

    with tempfile.TemporaryDirectory() as td:
        b = os.path.join(td, "cph4", "fleet")
        os.makedirs(os.path.join(b, "rt", "visual"), exist_ok=True)
        json.dump({"teams": {"visual": [{"id": "V-INSPECT", "cls": "triage"},
                                        {"id": "X-LEAD", "cls": "triage"}]}},
                  open(os.path.join(b, "AGENT-TEAMS-v1.json"), "w"))
        json.dump({"task_types": [], "stage_map": {}}, open(os.path.join(b, "TAXONOMY-v1.json"), "w"))
        json.dump({"products": []}, open(os.path.join(b, "PRODUCTS.json"), "w"))

        st = {}
        r1 = tick("visual", cap, st, now=1000.0, root=td)
        chk("首轮事件门放行两个", len(r1["ran"]) == 2)
        r2 = tick("visual", cap, st, now=1010.0, root=td)
        chk("间隔未到不重复跑", r2["ran"] == [])
        r3 = tick("visual", cap, st, now=1000.0 + 400, root=td)
        chk("到点后事件未变 -> INSPECT 被跳过",
            [x["seat"] for x in r3["skipped"]] == ["V-INSPECT"])
        # 改变输入 -> 指纹变化
        with open(os.path.join(b, "rt", "visual", "queue.jsonl"), "w") as f:
            f.write(json.dumps({"id": "a", "state": "OPEN"}) + "\n")
        r4 = tick("visual", cap, st, now=1000.0 + 800, root=td)
        chk("输入变化 -> INSPECT 重新放行",
            any(x["seat"] == "V-INSPECT" for x in r4["ran"]))

        # 超预算判定
        json.dump({"teams": {"visual": [{"id": "X-LEAD"}] * 20}},
                  open(os.path.join(b, "AGENT-TEAMS-v1.json"), "w"))
        json.dump({"machines": cap["machines"], "seat_policy": {"X-LEAD": {
            "gate": "time", "freq_s": 60, "est_tokens": 100000, "max_per_day": 1440,
            "endpoint": "local"}}}, open(os.path.join(b, "AGENT-CAPACITY-v1.json"), "w"))
        pl = plan(td)
        chk("超预算被报出", bool(pl["over"]))
        chk("额度占比数字可读", all(v["budget_calls"] for v in pl["verdict"]))

    print("[agent_schedule] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tick", action="store_true")
    ap.add_argument("--station")
    ap.add_argument("--max-runs", type=int, default=3)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    pl = plan(a.root)
    if a.plan or a.check:
        print("%-9s %-11s %-6s %6s %6s %6s %7s %-8s %8s" % (
            "工位", "席位", "门", "间隔s", "上限", "预期", "token", "记账", "日token"))
        for r in pl["rows"]:
            print("%-9s %-11s %-6s %6d %6d %6d %7d %-8s %8d" % (
                r["station"], r["seat"], r["gate"], r["freq_s"], r["ceiling"],
                r["expected"], r["tokens"], r["acct"], r["tok_day"]))
        print("\n== 额度核算 ==")
        for v in pl["verdict"]:
            print("  %-8s 调用 %4d/%s 次 ｜ 模型时间 %6.1f/%s 分钟 %s" % (
                v["acct"], v["calls_day"], v["budget_calls"],
                v["minutes_day"], v["budget_minutes"],
                "超限" if v["over"] else "OK"))
        if a.check:
            return 1 if pl["over"] else 0
        return 0

    if a.tick:
        cap = _j(_p("AGENT-CAPACITY-v1.json", a.root), {}) or {}
        st = _state(a.root)
        stations = [a.station] if a.station else list(ss.STATIONS)
        out = [tick(s, cap, st, max_runs=a.max_runs, root=a.root) for s in stations]
        _save_state(st, a.root)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    ap.error("需要 --plan / --check / --tick")


if __name__ == "__main__":
    sys.exit(main())
