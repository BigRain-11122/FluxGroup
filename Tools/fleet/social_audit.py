#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_audit.py — 一次跑完"这条线在不在履职"，并落三份证据。

为什么要一个总入口（CEO 2026-11-21「智能体建立好，你好好规划，还有自动任务什么的」）：
三张表（量化账本 / 多样性 / 履职）如果各挂一个定时器，就是三个互相不知道的时钟；
合成一个按固定节拍跑，谁缺证据一次就能看见。它**只读和记账，不生产内容**，
所以可以高频跑、不占 GPU。

产出：
  cph4/fleet/social/METRICS.json      量化账本（训练轮次/增益/语料/动作）
  cph4/fleet/social/state/DIVERSITY.json 多样性体检
  cph4/fleet/social/state/AGENT-AUDIT.json 履职四态
  cph4/fleet/social/state/audit-tail.txt   一屏尾部（人读）

用法
  python3 Tools/fleet/social_audit.py
  python3 Tools/fleet/social_audit.py --quiet
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


def _run(args, timeout=600):
    try:
        p = subprocess.run([PY] + args, capture_output=True, text=True,
                           cwd=ROOT, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "超时 %ss" % timeout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    os.makedirs(STATE, exist_ok=True)
    out = []

    rc1, o1 = _run([os.path.join(HERE, "social_metrics.py"), "--save",
                    os.path.join(SOCIAL, "METRICS.json")])
    out.append("[账本] rc=%d %s" % (rc1, o1.strip().splitlines()[0] if o1.strip() else ""))

    rc2, o2 = _run([os.path.join(HERE, "diversity_audit.py"), "--json-out",
                    os.path.join(STATE, "DIVERSITY.json")])
    tail = [l for l in o2.strip().splitlines() if l.startswith(("✅", "❗"))]
    out.append("[多样性] rc=%d 达标 %d 条 / 不达标 %d 条"
               % (rc2, sum(1 for l in tail if l.startswith("✅")),
                  sum(1 for l in tail if l.startswith("❗"))))

    rc3, o3 = _run([os.path.join(HERE, "agent_audit.py"), "--json"])
    try:
        d3 = json.loads(o3[o3.find("{"):])
        s = d3.get("counts") or {}
        json.dump(d3, open(os.path.join(STATE, "AGENT-AUDIT.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        out.append("[履职] OK %d / STALE %d / MISSING %d / NO-EXECUTOR %d"
                   % (s.get("OK", 0), s.get("STALE", 0), s.get("MISSING", 0),
                      s.get("NO-EXECUTOR", 0)))
        gaps = [x for x in (d3.get("duties") or []) if x.get("state") != "OK"]
        for g in gaps:
            out.append("      未履职 %s %s：%s" % (g.get("id"), g.get("name"), g.get("why")))
    except Exception as e:
        out.append("[履职] 解析失败：%s" % str(e)[:60])

    body = time.strftime("%Y-%m-%dT%H:%M:%S") + "\n" + "\n".join(out) + "\n"
    with open(os.path.join(STATE, "audit-tail.txt"), "w", encoding="utf-8") as f:
        f.write(body)
    if not a.quiet:
        print(body.strip())
    return 0 if rc1 == 0 and rc3 == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
