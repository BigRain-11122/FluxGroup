# -*- coding: utf-8 -*-
"""cadence.py - 节奏表的校验器与排期器（不执行任务，避免与主控脉双调度）。

三个问题它必须能回答：
  1. 这张表本身科不科学：周期/相位/依赖/撞车/预算/环。
  2. 表与执行体是否一致：表里的 stage 在 master_pulse.STAGES 存在吗？脉在跑的阶段
     有没有漏登记？（两处各写一套是所有漂移的源头）
  3. 这一秒该跑谁：算出每个任务的下次触发时刻与被推迟的原因。

Exit: 0 全绿；2 有 ERROR（表不可用）；1 只有 WARN。
"""
import argparse
import ast
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
TABLE = os.path.join(FLEET, "COMMAND-CADENCE-v2.json")
PULSE = os.path.join(ROOT, "Tools", "fleet", "master_pulse.py")
OUT = os.path.join(FLEET, "state", "cadence-plan.json")
BASE_TICK = 45
KNOWN_ACTORS = {"rule", "model", "embed"}


def pulse_stages():
    """Read STAGES from master_pulse without importing it (import has side effects)."""
    names = []
    try:
        with open(PULSE, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "STAGES":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, (ast.Tuple, ast.List)) and elt.elts:
                                first = elt.elts[0]
                                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                                    names.append(first.value)
    return names


def load_table():
    with open(TABLE, encoding="utf-8") as f:
        return json.load(f)


def validate(tbl, stages):
    errs, warns, notes = [], [], []
    tasks = tbl.get("tasks") or []
    if not tasks:
        errs.append("E-EMPTY: 表里没有任务")
        return errs, warns, notes, {}

    ids, by_id = [], {}
    for t in tasks:
        i = t.get("id")
        if not i:
            errs.append("E-NOID: 有任务缺 id")
            continue
        if i in by_id:
            errs.append("E-DUP-ID: %s 重复" % i)
        ids.append(i)
        by_id[i] = t

    per_period = {}
    for i, t in by_id.items():
        p = t.get("period_s")
        ph = t.get("phase_s", 0)
        actor = t.get("actor")
        if not isinstance(p, int) or p <= 0:
            errs.append("E-PERIOD: %s period_s 非法(%r)" % (i, p))
            continue
        if p < BASE_TICK:
            warns.append("W-PERIOD: %s period_s=%d < 基础节拍 %d，将取整" % (i, p, BASE_TICK))
        if not isinstance(ph, int) or ph < 0 or ph >= p:
            errs.append("E-PHASE: %s phase_s=%r 必须落在 [0,%d)" % (i, ph, p))
        if actor not in KNOWN_ACTORS:
            errs.append("E-ACTOR: %s actor=%r 不在 %s" % (i, actor, sorted(KNOWN_ACTORS)))
        # 撞车：同周期同相位
        key = (p, ph)
        per_period.setdefault(key, []).append(i)
        # 与执行体一致性
        st = t.get("stage")
        if st and stages and st not in stages:
            warns.append("W-STAGE: %s 的 stage=%s 不在 master_pulse.STAGES（未接线）" % (i, st))
        # 必填
        for req in ("domain", "action", "output", "accept", "on_fail"):
            if not str(t.get(req) or "").strip():
                errs.append("E-REQ: %s 缺字段 %s" % (i, req))

    for key, lst in per_period.items():
        if len(lst) > 1 and not any(by_id[x].get("depends_on") for x in lst):
            errs.append("E-COLLIDE: 周期%d 相位%d 有 %d 个任务且无依赖串行: %s"
                        % (key[0], key[1], len(lst), ",".join(lst)))

    # 依赖存在性与成环
    for i, t in by_id.items():
        for d in (t.get("depends_on") or []):
            if d not in by_id:
                errs.append("E-DEP-MISSING: %s 依赖不存在的 %s" % (i, d))

    color = {}

    def visit(n, stack):
        if color.get(n) == 1:
            errs.append("E-CYCLE: 依赖成环 %s" % "->".join(stack + [n]))
            return
        if color.get(n) == 2:
            return
        color[n] = 1
        for d in (by_id.get(n) or {}).get("depends_on") or []:
            visit(d, stack + [n])
        color[n] = 2

    for i in by_id:
        visit(i, [])

    # 反向一致性：脉在跑的阶段没登记。表声明了 excludes 时这是"范围外"而非缺陷——
    # 但未登记数量突然暴涨仍然值得看一眼，所以记 note 不记 WARN。
    registered = {t.get("stage") for t in by_id.values() if t.get("stage")}
    unregistered = [s for s in stages if s not in registered]
    scoped_out = bool((tbl.get("scope") or {}).get("excludes"))
    if unregistered:
        msg = "脉在跑但表里没登记的阶段 %d 个: %s" % (len(unregistered),
                                                 ",".join(unregistered[:12]))
        if scoped_out:
            notes.append("I-OUT-OF-SCOPE: " + msg)
        else:
            warns.append("W-UNREG: " + msg)

    # 模型预算
    model_tasks = [t for t in by_id.values() if t.get("actor") in ("model", "embed")]
    for t in model_tasks:
        b = t.get("budget") or {}
        if int(b.get("tokens") or 0) > 400:
            warns.append("W-BUDGET: %s tokens=%s > 400（4B 长输出易跑偏）" % (t["id"], b.get("tokens")))
    return errs, warns, notes, by_id


def plan(tbl, by_id, now=None):
    now = now if now is not None else time.time()
    rows = []
    for t in by_id.values():
        p = int(t.get("period_s") or BASE_TICK)
        ph = int(t.get("phase_s") or 0)
        elapsed = (now - ph) % p
        nxt = now + (p - elapsed if elapsed else 0)
        rows.append({"id": t["id"], "stage": t.get("stage"), "domain": t.get("domain"),
                     "actor": t.get("actor"), "period_s": p, "phase_s": ph,
                     "due_in_s": int(round(nxt - now)), "depends_on": t.get("depends_on") or []})
    rows.sort(key=lambda r: r["due_in_s"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--table", default=TABLE)
    a = ap.parse_args()

    try:
        tbl = load_table()
    except Exception as e:
        print(json.dumps({"verdict": "E-TABLE", "detail": str(e)[:200]}, ensure_ascii=False))
        return 2
    stages = pulse_stages()
    errs, warns, notes, by_id = validate(tbl, stages)
    rows = plan(tbl, by_id) if by_id else []
    verdict = "FAIL" if errs else ("WARN" if warns else "PASS")

    state = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "verdict": verdict,
             "tasks": len(by_id), "pulse_stages": len(stages),
             "errors": errs, "warnings": warns, "notes": notes,
             "next": rows[:6],
             "model_tasks": sum(1 for t in by_id.values() if t.get("actor") in ("model", "embed"))}
    try:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
    except Exception:
        pass

    if a.plan:
        for r in rows[:20]:
            print("%4ds  %-8s %-22s %s" % (r["due_in_s"], r["id"], r["stage"], r["domain"]))
    print(json.dumps({"verdict": verdict, "tasks": len(by_id), "errors": len(errs),
                      "warnings": len(warns), "notes": len(notes), "state": os.path.relpath(OUT, ROOT)},
                     ensure_ascii=False))
    for e in errs[:10]:
        print("  ERROR", e)
    for w in warns[:10]:
        print("  WARN ", w)
    return 2 if errs else (1 if warns else 0)


if __name__ == "__main__":
    sys.exit(main())