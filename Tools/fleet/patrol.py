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

产出：cph4/fleet/PATROL.md（一屏，按顺序）+ cph4/fleet/state/patrol.json（机读）。
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
# 巡检时因 declared != ACTIVE 被跳过的线（PARKED/DORMANT）：报给机读件，但不进行动清单
PARKED_SKIPPED = []

# 五轮固定顺序：轮次即优先级，不靠分数把它们混在一起
ROUNDS = [
    ("R1", "断链/停摆", "机器或通道断了，后面所有活都白派", 100),
    ("R2", "供给", "有机器空转但没有可跑的卡", 80),
    ("R3", "执行", "卡在飞但不动 / 失败无主 / 阻塞过期", 60),
    ("R4", "质量", "产物不合格或闸失效", 40),
    ("R5", "方向", "声明在跑但长时间没产物", 20),
]


def is_selfreport(card):
    """交付物落在 state/ 或回执目录的卡是体检/自述，不是产物：它不会让线前进。"""
    d = str(card.get("deliverable") or "")
    if "/state/" in d or "queue-receipts/" in d:
        return True
    return d.endswith(".json") and any(k in d for k in ("state", "receipt", "audit"))


def remote_repos():
    """子仓清单：quant/bigmoney、gaming/FluxVerse、compute/BigCompute、domain/BigDomain
    这些是别的机器上的**独立仓库**（见 Tools/fleet-nodes.json），本机当然没有。
    对它们判"目录不存在"= 把远端产物当本地缺失，是假红。"""
    out = {}
    try:
        cfg = jload(os.path.join(ROOT, "Tools", "fleet-nodes.json"), {}) or {}
        for n in (cfg.get("nodes") or []):
            for r in (n.get("repos") or []):
                r = str(r).strip("./")
                if r and r != ".":
                    out.setdefault(r, set()).add(n.get("id"))
    except Exception:
        pass
    return out


def outputs_missing(lid):
    """线的"产物面"目录是否真的没有。返回 (missing, remote_nodes)：
    remote_nodes 非空表示产物面在别的机器的子仓里——本机不可判，不算缺失。"""
    spec = jload(os.path.join(F, "lines", "%s.json" % lid), {}) or {}
    outs = spec.get("outputs") or []
    if not outs:
        return False, set()
    rr = remote_repos()
    remote = set()
    for o in outs:
        base = str(o).split("**")[0].rstrip("/*")
        if base and os.path.exists(os.path.join(ROOT, base)):
            return False, set()
        for repo, nodes in rr.items():
            if base == repo or base.startswith(repo + "/"):
                remote |= nodes
    return (not remote), remote


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
    # 只看 declared=ACTIVE 的线：PARKED/DORMANT 是「声明停下」，给它铺卡等于违背声明
    # （实测假红：bigstream-shortvideo 129h、car-gaming 122h 都被报成供给失败）。
    next_steps = (jload(os.path.join(F, "LINE-NEXT-STEPS.json"), {}) or {}).get("lines") or {}
    parked_skipped = PARKED_SKIPPED
    del parked_skipped[:]
    for ln in lines:
        lid = ln.get("id") or ""
        age = float(ln.get("age_h") or 0)
        declared = str(ln.get("declared") or "").upper()
        if declared and declared != "ACTIVE":
            parked_skipped.append({"id": lid, "declared": declared, "age_h": age})
            continue
        has_card = any(lid in json.dumps(r, ensure_ascii=False) for r in opens)
        if has_card:
            continue
        decl = next_steps.get(lid) or {}
        decl_cards = decl.get("cards") or []
        # 「体检卡」不算真活：交付物落在 state/ 或 queue-receipts/ 的，是自述与核查，
        # 产物面不会前进（实锚：fluxverse 唯一的下一步是 city_state.py 写一份自述 JSON，
        # 派完 DONE 了，线的产物 glob 一动不动 → 年龄永远停在 103h）。
        def _is_selfreport(c):
            return is_selfreport(c)
        real = [c for c in decl_cards if not _is_selfreport(c)]
        # 声明卡今天已经跑完、产物在盘 → 不是堵点，别再报（否则同一条线每天挂一遍）
        _done_today = any(
            str(r.get("id", "")).startswith("R-NEXT-%s" % lid.upper().replace("-", "")[:10])
            and str(r.get("state") or "").upper() == "DONE"
            and os.path.exists(os.path.join(ROOT, str(r.get("deliverable") or "")))
            for r in jl(os.path.join(F, "PRODUCTION-QUEUE.jsonl")))
        if _done_today:
            continue
        if decl_cards and not real and age >= STALE_H:
            add("R2", "decl:%s" % lid,
                "%s 的下一步声明只有体检/自述卡（%s），没有产物卡" % (
                    ln.get("name") or lid,
                    ",".join(c.get("key", "") for c in decl_cards)),
                _owners.get(lid) or (decl.get("nodes") or ["待指派"])[0],
                "换一张真产物卡：交付物必须是该线的产品文件，不是 state/ 或回执",
                "cph4/fleet/LINE-NEXT-STEPS.json", age_h=age, blocks=2, cost=2)
        elif decl_cards and age >= STALE_H:
            add("R2", "decl:%s" % lid,
                "%s 已声明下一步（%s）但队列里没有它的卡" % (
                    ln.get("name") or lid,
                    ",".join(c.get("key", "") for c in decl_cards)),
                _owners.get(lid) or (decl.get("nodes") or ["待指派"])[0],
                "把 LINE-NEXT-STEPS 的声明转成卡（night_plan/backlog_fill），不要再手写一张",
                "cph4/fleet/LINE-NEXT-STEPS.json", age_h=age, blocks=2, cost=1)
        elif age >= STALE_H:
            _miss, _remote = outputs_missing(lid)
            if _remote:
                # 产物面在别的机器的子仓里：本机不可判，判"不存在"是假红。
                # 该做的是把真产物卡派到持有子仓的机器，而不是在本机悬着一条红。
                add("R2", "remote:%s" % lid,
                    "%s 的产物面在子仓（%s），本机不可判；最后一次可得证据已停 %.0f 小时" % (
                        ln.get("name") or lid, "、".join(sorted(_remote)), age),
                    _owners.get(lid) or sorted(_remote)[0],
                    "派一张真产物卡到持有子仓的机器（%s）；本机只做监督不做生产"
                    % "、".join(sorted(_remote)),
                    "Tools/fleet-nodes.json", age_h=age, blocks=2, cost=3)
                continue
            if _miss:
                add("R2", "line:%s" % lid,
                    "%s 声明 ACTIVE 但产物目录根本不存在（%s），也没有生产工具" % (
                        ln.get("name") or lid,
                        ",".join((jload(os.path.join(F, "lines", "%s.json" % lid), {})
                                  or {}).get("outputs") or [])[:60]),
                    _owners.get(lid) or "待指派",
                    "二选一：定第一件真产物并给它一个工具，或把声明改成 PARKED；"
                    "不许铺体检卡充数",
                    "cph4/fleet/lines/%s.json" % lid, age_h=age, blocks=2, cost=3)
                continue
            add("R2", "line:%s" % lid,
                "%s 已 %.0f 小时无产物、队列里没有它的卡、也没有下一步声明" % (
                    ln.get("name") or lid, age),
                _owners.get(lid) or "待指派",
                "先定这一条线唯一的下一个可交付产物，写进 LINE-NEXT-STEPS 再铺卡",
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
            _miss, _remote = outputs_missing(str(ln.get("id")))
            if _remote:
                # 产物面在子仓：本机判"停摆"等于拿看不见的东西定罪。R2 已按
                # "派到持有子仓的机器"报过，这里不再重复一条方向红。
                continue
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

    # 机读件（此前只写在文档里、代码从未生成，下游只能靠剥 Markdown 拿顺序）
    os.makedirs(STATE, exist_ok=True)
    jp = os.path.join(STATE, "patrol.json")
    try:
        with open(jp, "w", encoding="utf-8") as f:
            json.dump({"ts": now(), "items": items, "acts": acts,
                       "parked_skipped": PARKED_SKIPPED, "board": path},
                      f, ensure_ascii=False, indent=1)
    except Exception as e:
        print("[patrol] W-PATROL-JSON %s" % str(e)[:80])

    if a.json:
        print(json.dumps({"ts": now(), "items": items, "acts": acts,
                          "parked_skipped": PARKED_SKIPPED, "board": path,
                          "json": jp}, ensure_ascii=False, indent=1))
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