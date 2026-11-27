#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_audit.py — 一个时钟跑完"这条线履职了没有、做对没有"，并落全部证据。

为什么要有总入口（CEO 2026-11-21「智能体建立好，你好好规划，还有自动任务什么的」）：
三张表各挂一个定时器就是三个互相不知道的时钟；合成一个按固定节拍跑，谁缺证据一次就能看见。
它**只读和记账，不生产内容**，所以能高频跑、不占 GPU。

顺序是有讲究的（2026-11-21 教训：判据顺序会造假红）：
  1 守卫（social_guard）：先算领域判据 → GUARD-*.json（断言从哪来）
  2 闸回归（gate_regression --save）：正控/负控落盘 → GATE-RESULT.json
  3 账本 / 多样性 / 闸之前指标：METRICS / DIVERSITY（只读不产内容）
  4 审计器自检 → AUDIT-SELFTEST.json（自检不过，后面的绿都不算数）
  5 履职审计（agent_audit）：只读上面这些 pass 映射

产出
  cph4/fleet/social/state/GUARD-{CORPUS,TRAIN,ACCOUNTS,SENDS,SCHED}.json
  cph4/fleet/social/state/GATE-RESULT.json
  cph4/fleet/social/state/AUDIT-SELFTEST.json
  cph4/fleet/social/state/AGENT-AUDIT.json
  cph4/fleet/social/METRICS.json + state/DIVERSITY.json（由被调工具写）
  cph4/fleet/social/state/audit-tail.txt（人读一屏）

退出码：0 全绿；1 有非 P0 未过；2 P0 失守（停线）。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(SOCIAL, "state")
PY = sys.executable


def _run(args, timeout=900):
    try:
        p = subprocess.run([PY] + args, capture_output=True, text=True,
                           cwd=ROOT, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "超时 %ss" % timeout


def _first(text):
    text = (text or "").strip()
    return text.splitlines()[0] if text else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--skip-gpu", action="store_true",
                    help="跳过闸前指标（要跑模型，占 GPU）；只做守卫与审计")
    a = ap.parse_args()
    os.makedirs(STATE, exist_ok=True)
    out = []
    rc_all = 0

    # 0 内存探针：ME03 只认"真实生成时的增量"，所以每天至少跑一次 --gen 1；
    #   训练独占时不抢 GPU，只做静态采样（那时候换页由训练自己在账里说话）。
    last_gen_age = None
    try:
        with open(os.path.join(STATE, "MEM-PROBE.json"), encoding="utf-8") as f:
            lg = (json.load(f) or {}).get("last_gen") or {}
        ts = lg.get("ts")
        if ts:
            last_gen_age = (time.time() - time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))) / 3600
    except Exception:
        pass
    training = os.path.exists(os.path.join(ROOT, ".codely-cli", "state", "TRAIN-EXCLUSIVE"))
    if last_gen_age is None or last_gen_age > 24:
        args = [os.path.join(HERE, "mem_probe.py"), "--once"] + ([] if training else ["--gen", "1"])
        rc6, o6 = _run(args, timeout=240)
        out.append("[内存] rc=%d %s%s" % (rc6, _first(o6),
                                         "（训练独占，本轮只静态采样）" if training else ""))

    # 1 守卫（领域判据）
    rc0, o0 = _run([os.path.join(HERE, "social_guard.py"), "--all"])
    groups = {}
    for g in ("CORPUS", "TRAIN", "ACCOUNTS", "SENDS", "SCHED", "MEM", "EVOLVE"):
        d = None
        try:
            with open(os.path.join(STATE, "GUARD-%s.json" % g), encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            pass
        if d:
            groups[g] = d
    red = sum(1 for g in groups.values() for c in g["checks"] if c["ok"] is False)
    skip = sum(1 for g in groups.values() for c in g["checks"] if c["ok"] is None)
    out.append("[守卫] rc=%d %d 组：红 %d 项 / 跳过 %d 项" % (rc0, len(groups), red, skip))

    # 2 闸回归（落盘给 G01 断言）
    rc1, o1 = _run([os.path.join(HERE, "gate_regression.py"), "--save"])
    out.append("[闸回归] rc=%d %s" % (rc1, _first(o1)))

    # 3 账本 + 多样性（只读）
    rc2, o2 = _run([os.path.join(HERE, "social_metrics.py"), "--save",
                    os.path.join(SOCIAL, "METRICS.json")])
    out.append("[账本] rc=%d %s" % (rc2, _first(o2)))
    rc3, o3 = _run([os.path.join(HERE, "diversity_audit.py"), "--json-out",
                    os.path.join(STATE, "DIVERSITY.json")])
    tail = [l for l in o3.strip().splitlines() if l.startswith(("✅", "❗"))]
    out.append("[多样性] rc=%d 达标 %d / 不达标 %d" % (
        rc3, sum(1 for l in tail if l.startswith("✅")),
        sum(1 for l in tail if l.startswith("❗"))))

    # 4 审计器自检（负控）；不过就写 FAIL，S06 会红
    rc4, o4 = _run([os.path.join(HERE, "agent_audit.py"), "--self-test"])
    try:
        selftest = json.loads(o4[o4.find("{"):])
    except Exception:
        selftest = {"self_test": "FAIL", "raw": o4[:200]}
    selftest.update({"rc": rc4, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
    with open(os.path.join(STATE, "AUDIT-SELFTEST.json"), "w", encoding="utf-8") as f:
        json.dump(selftest, f, ensure_ascii=False, indent=1)
    out.append("[自检] %s" % selftest.get("self_test"))

    # 5 履职审计
    rc5, o5 = _run([os.path.join(HERE, "agent_audit.py"), "--json"])
    try:
        d5 = json.loads(o5[o5.find("{"):])
        with open(os.path.join(STATE, "AGENT-AUDIT.json"), "w", encoding="utf-8") as f:
            json.dump(d5, f, ensure_ascii=False, indent=1)
        tiers = d5.get("tiers") or {}
        for t in ("P0", "P1", "P2"):
            c = tiers.get(t) or {}
            bad = sum(v for k, v in c.items() if k not in ("OK", "SKIP"))
            out.append("[履职 %s] %d 项：未过 %d / 跳过 %d" % (
                t, sum(c.values()), bad, c.get("SKIP", 0)))
        for g in (d5.get("duties") or []):
            if g.get("state") not in ("OK", "SKIP"):
                out.append("       %s %s %s：%s" % (g.get("tier"), g.get("id"),
                                                   g.get("name"), g.get("why", "")[:80]))
        if d5.get("p0_bad"):
            out.append("!! P0 失守：%s" % ",".join(d5["p0_bad"]))
            rc_all = 2
        else:
            rc_all = 0 if rc5 == 0 else 1
    except Exception as e:
        out.append("[履职] 解析失败：%s" % str(e)[:80])
        rc_all = 1

    body = time.strftime("%Y-%m-%dT%H:%M:%S") + "\n" + "\n".join(out) + "\n"
    with open(os.path.join(STATE, "audit-tail.txt"), "w", encoding="utf-8") as f:
        f.write(body)
    if not a.quiet:
        print(body.strip())
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
