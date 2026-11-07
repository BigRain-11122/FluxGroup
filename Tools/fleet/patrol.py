#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patrol.py - 唯一的有序巡查：把七八个报告面合成一条按优先级排好的行动清单。

CEO 2026-11-07：「智能体巡查排序好，指挥好机队各个业务和自动化开展」。

问题：commander / CEO-NEXT / checkups / chief / supply_target / wait_map / next_actions
各自出报告，谁也不排谁——看起来很多信息，实际没有先后，派单全靠临时判断。
本工具做三件事：
  1. **采集**：从已有事实源读信号（PULSE blockers、线年龄、队列分布、车道、质量席、
     内存护栏、跨机收口状态）。不新造指标，只做归并。
  2. **排序**：五轮固定顺序（断链 → 供给 → 执行 → 质量 → 方向），轮内按
     阻塞他人 × 时间敏感 × 修复成本 打分；同分按年龄。排序规则写在 ROUNDS 里，
     让人能预期"先看什么"。
  3. **指挥**：--dispatch 时按排序落卡（调用既有铺卡器），不自己发明工作。

产出：cph4/fleet/PATROL.md（一屏，按顺序）+ state/patrol.json（机读）。
用法：
  python3 Tools/fleet/patrol.py                 # 只巡查
  python3 Tools/fleet/patrol.py --dispatch      # 巡查后按序补卡并派单
  python3 Tools/fleet/patrol.py --top 6         # 只看前 6 条
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
STALE_H = 72.0

# 五轮固定顺序：轮次即优先级，不靠分数把它们混在一起
ROUNDS = [
    ("R1", "断链/停摆", "机器或通道断了，后面所有活都白派", 100),
    ("R2", "供给", "有机器空转但没有可跑的卡", 80),
    ("R3", "执行", "卡在飞但不动 / 失败无主 / 阻塞过期", 60),
    ("R4", "质量", "产物不合格或闸失效", 40),
    ("R5", "方向", "声明在跑但长时间没产物", 20),
]


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def jl(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


# ---------------------------------------------------------------- 采集
def collect():
    items = []

    # 线 → 席位责任人（来自 ri 注册表）；查不到就标"待指派"，不要一律堆给 bm-m
    _owners = {}
    try:
        _reg = jload(os.path.join(F, "ri", "registry.json"), {})
        for seat in (_reg.get("seats") or []):
            for ln in (seat.get("lines") or []):
                _owners[ln] = seat.get("id") or ""
    except Exception:
        pass

    def add(round_id, key, title, owner, action, evidence, age_h=0.0, blocks=1, cost=1):
        items.append({"round": round_id, "key": key, "title": title, "owner": owner,
                      "action": action, "evidence": evidence, "age_h": round(age_h, 1),
                      "blocks": blocks, "cost": cost})

    # R1 断链：脉自己的 blockers + 内存护栏
    pulse = jload(os.path.join(F, "dispatcher", "PULSE.json"), {})
    _merged = {"swap"}      # swap blocker 与内存护栏同源，下面统一报一条
    for b in (pulse.get("blockers") or []):
        if b.startswith("stage:") or b in _merged:
            continue          # 阶段红已由 closer/checkups 覆盖，避免重复
        add("R1", "pulse:%s" % b, "主控脉 blocker：%s" % b, "bm-m",
            "看 PULSE.json 该 blocker 的判据，修因不是压阈值",
            "cph4/fleet/dispatcher/PULSE.json", blocks=3, cost=2)

    mg = jload(os.path.join(STATE, "mem-guard.json"), {})
    if str(mg.get("verdict")) == "FAIL":
        add("R1", "mem:thrash", "内存护栏 FAIL：正在拿硬盘当内存", "bm-m",
            "按 MEM-GUARD.md 的建议卸档或降并发", "cph4/fleet/MEM-GUARD.md", blocks=3, cost=1)

    mp = jload(os.path.join(STATE, "model-plan.json"), {}) or {}
    if str(mp.get("verdict")) == "FAIL":
        add("R1", "model:plan", "模型排班 FAIL（档位/槽位/单源不一致）", "bm-m",
            "看 MODEL-PLAN.md，按矩阵修配置", "cph4/fleet/MODEL-PLAN.md", blocks=2, cost=1)

    # R1 跨机：仍未收口的节点
    for r in jl(os.path.join(F, "PRODUCTION-QUEUE.jsonl")):
        if str(r.get("id", "")).startswith("REMOTE-CLOSEOUT") and r.get("state") == "BLOCKED":
            add("R1", "xnode:%s" % r["id"], "跨机收口未完成：%s" % r["id"], r.get("owner") or "bm-m",
                "按卡上 note 里的一次性动作在那台机器执行", "cph4/fleet/PRODUCTION-QUEUE.jsonl",
                blocks=3, cost=2)

    # R2 供给：声明在跑但没卡的线
    lines = (jload(os.path.join(STATE, "lines.json"), {}) or {}).get("lines") or []
    opens = [r for r in jl(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
             if r.get("state") in ("OPEN", "RUNNING")]
    open_lines = set()
    for r in opens:
        for k in ("line", "needs", "nodes"):
            if isinstance(r.get(k), str):
                open_lines.add(r[k])
    for ln in lines:
        lid = ln.get("id") or ""
        age = float(ln.get("age_h") or 0)
        has_card = any(lid in json.dumps(r, ensure_ascii=False) for r in opens)
        if not has_card and age >= STALE_H:
            add("R2", "line:%s" % lid,
                "%s 已 %.0f 小时无产物且队列里没有它的卡" % (ln.get("name") or lid, age),
                _owners.get(lid) or "待指派", "给它铺一张真活卡（有输入、有交付路径、有判据）",
                "cph4/fleet/state/lines.json", age_h=age, blocks=2, cost=2)

    # R2 供给：槽位空
    lanes = {}
    for n in ("bm-a", "bm-b", "bm-c", "bm-m"):
        d = jload(os.path.join(F, "lanes", "%s.json" % n), {})
        if d:
            lanes[n] = len(d.get("jobs") or [])
    idle = [n for n, c in lanes.items() if c == 0]
    if idle and len(opens) < len(idle) + 2:
        add("R2", "slots", "%d 台机车道空（%s）而待派卡只有 %d 张"
            % (len(idle), ",".join(idle), len(opens)), "bm-m",
            "先补供给再谈调度：跑 supply_batch --apply + workgen",
            "cph4/fleet/lanes/", blocks=2, cost=1)

    # R3 执行：失败无主 / 阻塞过久
    for r in jl(os.path.join(F, "PRODUCTION-QUEUE.jsonl")):
        st = r.get("state")
        if st in ("FAILED", "BLOCKED") and not r.get("owner"):
            add("R3", "card:%s" % r.get("id"), "%s 无责任人（%s）" % (r.get("id"), st),
                "bm-m", "定责：改卡重派或落根因账", "cph4/fleet/PRODUCTION-QUEUE.jsonl",
                blocks=1, cost=1)

    # R4 质量
    qb = os.path.join(F, "QUALITY-BOARD.md")
    try:
        txt = open(qb, encoding="utf-8").read()
        if "闸失效" in txt:
            add("R4", "quality:fake", "质量席自证失败：有判据拦不住反例", "bm-m",
                "跑 quality_agents.py --selftest 并按输出修判据", "cph4/fleet/QUALITY-BOARD.md",
                blocks=2, cost=1)
        fails = [l for l in txt.splitlines() if l.startswith("|") and "FAIL" in l]
        if fails:
            add("R4", "quality:below", "%d 条线质量未达阈值" % len(fails), "bm-m",
                "逐条看 QUALITY-BOARD 的硬伤列，改产物不改阈值",
                "cph4/fleet/QUALITY-BOARD.md", blocks=1, cost=2)
    except FileNotFoundError:
        add("R4", "quality:none", "质量席没有一屏（未跑或没产物）", "bm-m",
            "跑 quality_agents.py --scan", "cph4/fleet/QUALITY-BOARD.md", blocks=1, cost=1)

    # R5 方向：声明 ACTIVE 但观测停摆（R2 已报过"没卡"的线不重复报，避免一件事两行）
    _r2_lines = {it["key"].split(":", 1)[1] for it in items
                 if it["round"] == "R2" and ":" in it["key"]}
    for ln in lines:
        if str(ln.get("id")) in _r2_lines:
            continue
        if str(ln.get("declared")) == "ACTIVE" and float(ln.get("age_h") or 0) >= STALE_H:
            add("R5", "dir:%s" % ln.get("id"),
                "%s 声明 ACTIVE 但已停 %.0f 小时" % (ln.get("name") or ln.get("id"),
                                                float(ln.get("age_h") or 0)),
                "bm-m", "要么给它真活，要么改声明为 PARKED（不许挂着 ACTIVE 骗人）",
                "cph4/fleet/state/lines.json", age_h=float(ln.get("age_h") or 0),
                blocks=0, cost=1)
    return items


# ---------------------------------------------------------------- 排序
def rank(items):
    w = {rid: w for rid, _n, _w, w in [(r[0], r[1], r[2], r[3]) for r in ROUNDS]}
    for it in items:
        base = w.get(it["round"], 10)
        # 阻塞他人 ×3、时间敏感（每 24h 加 1，封顶 5）、修复成本（越便宜越前）
        it["score"] = round(base + it["blocks"] * 3 + min(it["age_h"] / 24.0, 5.0)
                            - (it["cost"] - 1) * 2, 2)
    items.sort(key=lambda x: (-x["score"], x["round"], -x["age_h"]))
    for i, it in enumerate(items, 1):
        it["rank"] = i
    return items


# ---------------------------------------------------------------- 指挥
def dispatch(items, dry=False):
    """按排序补供给并把卡派进车道。只调用既有铺卡器，不发明工作。"""
    acts = []
    todo = [it for it in items if it["round"] == "R2"]
    if not todo:
        return acts
    for cmd in ([sys.executable, os.path.join(HERE, "supply_batch.py"), "--apply"],
                [sys.executable, os.path.join(HERE, "workgen.py"), "--root", ROOT],
                [sys.executable, os.path.join(HERE, "night_fill.py"), "--target", "6"]):
        if dry:
            acts.append("would run: %s" % " ".join(os.path.basename(c) for c in cmd[:2]))
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=420, cwd=ROOT)
            acts.append("%s -> rc=%d %s" % (os.path.basename(cmd[1]),
                                            r.returncode, (r.stdout or "").strip()[-120:]))
        except Exception as e:
            acts.append("%s -> E %s" % (os.path.basename(cmd[1]), str(e)[:80]))
    if not dry:
        try:
            r = subprocess.run([sys.executable, os.path.join(HERE, "master_agent.py"),
                                "--node", "bm-m", "--root", ROOT],
                               capture_output=True, text=True, timeout=420, cwd=ROOT)
            acts.append("master_agent -> rc=%d" % r.returncode)
        except Exception as e:
            acts.append("master_agent -> E %s" % str(e)[:60])
    return acts


# ---------------------------------------------------------------- 输出
def board(items, acts=None):
    L = ["# 巡查（有序）%s" % now(), "",
         "排序规则：**轮次决定先后**（断链 → 供给 → 执行 → 质量 → 方向），轮内按"
         "阻塞他人×3 + 停摆时长 + 修复成本。全部 %d 条。" % len(items), ""]
    for rid, name, why, _w in ROUNDS:
        grp = [it for it in items if it["round"] == rid]
        if not grp:
            continue
        L += ["## %s %s（%d 条）· %s" % (rid, name, len(grp), why), ""]
        for it in grp:
            L.append("%2d. **%s** → %s｜`%s`" % (it["rank"], it["title"], it["action"],
                                                it["owner"]))
        L.append("")
    tail = [it for it in items if it["round"] not in [r[0] for r in ROUNDS]]
    if tail:
        L += ["## 其他", ""] + ["%2d. %s" % (it["rank"], it["title"]) for it in tail] + [""]
    if acts:
        L += ["## 本轮指挥动作", ""] + ["- %s" % a for a in acts] + [""]
    L += ["---", "_巡查只做排序与定责；具体做法在各条目的 evidence 里，改判据请改对应正身件_"]
    p = os.path.join(F, "PATROL.md")
    open(p, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return p


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dispatch", action="store_true")
    ap.add_argument("--top", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    items = rank(collect())
    acts = dispatch(items, dry=not a.dispatch) if a.dispatch else []
    path = board(items, acts)

    if a.json:
        print(json.dumps({"ts": now(), "items": items, "acts": acts,
                          "board": path}, ensure_ascii=False, indent=1))
    show = items[:a.top] if a.top else items
    print("[patrol] %d 条 · 前 %d 条：" % (len(items), len(show)))
    for it in show:
        print("  %2d [%s] %-58s -> %s" % (it["rank"], it["round"], it["title"][:58], it["owner"]))
    for a2 in acts:
        print("  · %s" % a2)
    print("[patrol] board -> %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))