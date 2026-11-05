#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seat_runner.py - 一机多席：把主控拆成 7 个专责智能体，串行轮转执行。

为什么要分席（CEO 2026-11-05「我需要多个智能体分工协作，尤其这台机器专门做这些」）：
  一个 60 项的智能体做不到"专责"——它每轮都在切上下文，谁也不知道哪件事被漏了。
  但**不能起 7 个并发进程**：今天一天就撞车 4 次，同一工作树多个写者会把提交、
  配置、阶段接线全部冲掉。

  所以采用「一机多席 + 串行轮转」：
    * 一个进程（本脚本）按顺序扮演 7 个席位，每席只做自己域内的事；
    * 每席有独立目录 state/agents/<seat>/（日志、心跳、产出），互不覆盖；
    * 共享账本（QUEUE/CONFIG/orders）只有席位 S4 账房 与 S2 调度 写，其余只发提案；
    * 任意时刻只有一个席位在动 → 不存在并发写。

席位（对应 MASTER-AGENT-DUTIES-v1.json 的域）：
    S1 值班 值守+监督   S2 调度 派单        S3 验收 验收
    S4 账房 账本+成本    S5 资产 资产+备份   S6 汇报 汇报
    S7 自愈 自愈+演进

用法：
    python3 Tools/fleet/seat_runner.py --seat S1        # 跑一次某一席
    python3 Tools/fleet/seat_runner.py --rotate         # 串行跑完全部席位（供 launchd 定时）
    python3 Tools/fleet/seat_runner.py --status         # 各席最近一次心跳
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
AG = os.path.join(F, "state", "agents")

# 席位 → (中文名, 负责域, 要跑的命令序列, 写权说明)
SEATS = {
    "S1": ("值班", ["值守", "监督"], [
        ["Tools/fleet/fleet_hb.py"],
        ["Tools/fleet/master_loop.py"],
    ], "只读+写自己的日志"),
    "S2": ("调度", ["派单"], [
        ["Tools/fleet/workgen.py", "--root", ROOT],
        ["Tools/fleet/master_agent.py", "--node", "bm-m", "--root", ROOT],
    ], "写 QUEUE/BACKLOG/lanes（唯一派单写者）"),
    "S3": ("验收", ["验收"], [
        ["Tools/fleet/verify_done.py"],
        ["Tools/fleet/closer.py"],
    ], "写 QUEUE 状态（收口）"),
    "S4": ("账房", ["账本", "成本"], [
        ["Tools/fleet/queue_integrity.py", "--purge-meta", "--reconcile"],
        ["Tools/fleet/order_watch.py"],
        ["Tools/fleet/cloud_budget.py", "check"],
        ["Tools/fleet/decision_router.py"],
    ], "写 QUEUE/BACKLOG/DECISIONS/orders（账本唯一写者）"),
    "S5": ("资产", ["资产"], [
        ["Tools/fleet/asset_reach.py"],
        ["Tools/fleet/done_audit.py", "--apply"],
    ], "只读台账+写审计结果"),
    "S6": ("汇报", ["汇报"], [
        ["Tools/fleet/day_plan.py"],
        ["Tools/fleet/ops_metrics.py"],
    ], "只写自己的报表"),
    "S7": ("自愈", ["自愈", "演进"], [
        ["Tools/fleet/fleet_health.py"],
        ["Tools/fleet/fleet_contingency.py"],
    ], "自愈动作+写自己的日志"),
}


def seat_dir(seat):
    d = os.path.join(AG, seat)
    os.makedirs(d, exist_ok=True)
    return d


def lock_path(seat):
    return os.path.join(AG, "%s.lock" % seat)


def run_seat(seat, timeout=300):
    name, domains, cmds, write_scope = SEATS[seat]
    d = seat_dir(seat)
    lp = lock_path(seat)
    if os.path.exists(lp):
        try:
            age = time.time() - os.path.getmtime(lp)
        except OSError:
            age = 0
        if age > 600:          # 陈旧锁自动失效
            os.remove(lp)
        else:
            print("[%s] busy (lock %.0fs), skip" % (seat, age))
            return {"seat": seat, "skipped": "locked"}
    open(lp, "w").write(str(os.getpid()))
    results = []
    try:
        for c in cmds:
            if not os.path.exists(os.path.join(ROOT, c[0])):
                results.append({"cmd": c[0], "rc": -2, "tail": "missing tool"})
                continue
            try:
                p = subprocess.run([sys.executable] + c, cwd=ROOT, capture_output=True,
                                   text=True, timeout=timeout)
                tail = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()
                results.append({"cmd": os.path.basename(c[0]), "rc": p.returncode,
                                "tail": tail[-1][:160] if tail else ""})
            except subprocess.TimeoutExpired:
                results.append({"cmd": os.path.basename(c[0]), "rc": 124, "tail": "timeout"})
            except Exception as e:
                results.append({"cmd": os.path.basename(c[0]), "rc": -1, "tail": str(e)[:120]})
    finally:
        try:
            os.remove(lp)
        except OSError:
            pass

    beat = {"seat": seat, "name": name, "domains": domains, "write_scope": write_scope,
            "ts": datetime.now().isoformat(timespec="seconds"),
            "results": results,
            "failed": [r["cmd"] for r in results if r["rc"] not in (0, 1, 2, 3)]}
    with open(os.path.join(d, "beat.json"), "w", encoding="utf-8") as f:
        json.dump(beat, f, ensure_ascii=False, indent=1)
    with open(os.path.join(d, "log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(beat, ensure_ascii=False) + "\n")
    print("[%s %s] %s" % (seat, name, " ".join("%s=%s" % (r["cmd"], r["rc"]) for r in results)))
    return beat


def rotate():
    out = []
    for seat in SEATS:
        out.append(run_seat(seat))
    return out


def status():
    rows = []
    for seat, (name, domains, cmds, scope) in SEATS.items():
        p = os.path.join(AG, seat, "beat.json")
        try:
            with open(p, encoding="utf-8") as f:
                b = json.load(f)
            rows.append({"seat": seat, "name": name, "ts": b.get("ts"),
                         "failed": b.get("failed") or []})
        except Exception:
            rows.append({"seat": seat, "name": name, "ts": None, "failed": []})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seat", choices=list(SEATS), default="")
    ap.add_argument("--rotate", action="store_true")
    ap.add_argument("--auto", action="store_true",
                    help="跑最久没跑的那个席位（供 launchd 定时轮转，一次只跑一席）")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.status:
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return 0
    if a.seat:
        run_seat(a.seat)
        return 0
    if a.auto:
        rows = status()
        rows.sort(key=lambda r: (r.get("ts") or ""))
        run_seat(rows[0]["seat"])
        return 0
    if a.rotate:
        rotate()
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())