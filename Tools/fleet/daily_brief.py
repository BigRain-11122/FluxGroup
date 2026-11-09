#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_brief.py - 一屏日报：产出、阻塞、健康、决策，按 CEO 关心的顺序排。

为什么（2026-11-09）：「看不到产出」的另一半是没人把产出摆到一屏上。
本件不新造指标，只把已有事实合成一页：产出看板、巡视十席、队列/供给、韧性、待裁件。
用法：python3 Tools/fleet/daily_brief.py
产出：cph4/fleet/DAILY-BRIEF.md
"""
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
OUT = os.path.join(F, "DAILY-BRIEF.md")


def j(path, default=None):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def queue_stats():
    st = {}
    try:
        for line in open(os.path.join(F, "PRODUCTION-QUEUE.jsonl"), encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                st[d.get("state")] = st.get(d.get("state"), 0) + 1
    except OSError:
        pass
    return st


def ceo_queue():
    p = os.path.join(F, "CEO-QUEUE.md")
    try:
        t = open(p, encoding="utf-8").read()
    except OSError:
        return 0, []
    items = re.findall(r"^- \[([A-Z\-]+)\] (.+)$", t, re.M)
    return len(items), items


def main():
    subprocess.run([sys.executable, os.path.join(ROOT, "Tools", "fleet", "output_board.py")],
                   capture_output=True, timeout=120)
    ob = j(os.path.join(STATE, "output-board.json"))
    pat = j(os.path.join(STATE, "patrol-local.json"))
    sup = j(os.path.join(STATE, "supply-guard.json"))
    res = j(os.path.join(STATE, "resilience.json"))
    sync = j(os.path.join(STATE, "state-sync.json"))
    qs = queue_stats()
    n_ceo, ceo_items = ceo_queue()

    verdicts = [s.get("result", {}).get("verdict") for s in (pat.get("seats") or [])]
    reds = [s.get("domain") for s in (pat.get("seats") or [])
            if s.get("result", {}).get("verdict") == "RED"]
    counts = {v: verdicts.count(v) for v in ("GREEN", "YELLOW", "RED", "UNKNOWN")}

    sync_age = int(time.time() - float(sync.get("ok_ts") or 0)) if sync.get("ok_ts") else -1

    lines = ["# 一屏日报 %s" % time.strftime("%Y-%m-%d %H:%M"), ""]
    lines.append("## 1. 产出（盘上事实）")
    lines.append("")
    lines.append("- 产品件 **%s** · 内部件 %s · 交付物缺失 %s" %
                 (ob.get("product", "?"), ob.get("infra", "?"), ob.get("missing", "?")))
    lines.append("- 近 7 天产品文件：见 OUTPUT-BOARD.md「盘上成品」")
    lines.append("")
    lines.append("## 2. 巡视十席")
    lines.append("")
    lines.append("- G/Y/R = %d/%d/%d%s" % (counts["GREEN"], counts["YELLOW"], counts["RED"],
                                         (" · RED: " + ", ".join(reds)) if reds else ""))
    lines.append("")
    lines.append("## 3. 队列与供给")
    lines.append("")
    lines.append("- 卡：%s" % json.dumps(qs, ensure_ascii=False))
    lines.append("- 供给缺口：%s" % (sup.get("short_after") or "无"))
    lines.append("")
    lines.append("## 4. 健康")
    lines.append("")
    lines.append("- 韧性体检：%s（%d 项）" % (res.get("verdict", "?"), len(res.get("checks") or [])))
    lines.append("- 状态同步：%s" % ("从未成功" if sync_age < 0 else "%ds 前" % sync_age))
    lines.append("")
    lines.append("## 5. 等 CEO（%d 件）" % n_ceo)
    lines.append("")
    for st, txt in ceo_items[:5]:
        lines.append("- [%s] %s" % (st, txt[:80]))
    lines.append("")
    lines.append("## 6. 今日建议")
    lines.append("")
    if reds:
        lines.append("- 先看 RED 域：%s（巡视已写 NEED-JUDGMENT）" % ", ".join(reds))
    if ob.get("missing"):
        lines.append("- 有 %s 张 DONE 卡交付物不在盘上，建议改判 UNVERIFIED，别让它们冒充产出" % ob["missing"])
    if sup.get("short_after"):
        lines.append("- 供给缺口 %s：把 CEO 队列里「机队先做」的条目转成卡" % sup["short_after"])
    if not (reds or ob.get("missing") or sup.get("short_after")):
        lines.append("- 无阻塞级事项")

    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
