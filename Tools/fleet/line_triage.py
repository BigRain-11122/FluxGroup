#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""line_triage.py - the first executable step for a silent line, run ON the owning machine.

Chain this closes (2026-10-31): the control plane could only *see* that a line had no output,
because the repo lives on a machine it cannot read (six sub-repos are 0 files on bm-m). So the
recommendation ("this line is silent, find out why") is turned into a card that the owning
lane executes against its own disk. Output is a receipt with facts, not prose: what exists,
what is newest, what is missing, and the three next actions with an owner.

Deterministic: no model, no invention, so two runs on the same tree give the same answer.

Usage (on the lane): python Tools/fleet/line_triage.py --line biggame
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REG = os.path.join(ROOT, "cph4", "fleet", "LINE-REGISTRY.json")
OUT_DIR = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")


def main() -> int:
    args = sys.argv[1:]
    line_id = args[args.index("--line") + 1] if "--line" in args else ""
    if not line_id:
        print("usage: line_triage.py --line <line-id>")
        return 2
    try:
        reg = json.load(open(REG, encoding="utf-8"))
    except Exception:
        print("no LINE-REGISTRY")
        return 2
    line = next((l for l in reg.get("lines") or [] if l.get("id") == line_id), None)
    if not line:
        print("unknown line %s" % line_id)
        return 2

    rows = ["# 线级体检 %s · %s" % (line_id, datetime.now().strftime("%Y-%m-%d %H:%M")), ""]
    missing, newest_all = [], 0.0
    rows.append("## 工段与证据目录")
    for st in line.get("stages") or []:
        ev = st.get("evidence") or []
        found, files, newest = [], 0, 0.0
        for e in ev:
            p = os.path.join(ROOT, e)
            if os.path.exists(p):
                found.append(e)
                if os.path.isdir(p):
                    for dirpath, _dirs, fn in os.walk(p):
                        for f in fn:
                            files += 1
                            try:
                                newest = max(newest, os.path.getmtime(os.path.join(dirpath, f)))
                            except OSError:
                                pass
                else:
                    files += 1
                    try:
                        newest = max(newest, os.path.getmtime(p))
                    except OSError:
                        pass
        newest_all = max(newest_all, newest)
        age = "%.1fh" % ((time.time() - newest) / 3600) if newest else "—"
        rows.append("- %-14s owner=%-8s lane=%-6s 证据 %d/%d 存在 · 文件 %d · 最新 %s"
                    % (st.get("id"), st.get("owner"), st.get("lane") or "-",
                       len(found), len(ev), files, age))
        if not found:
            missing.append(st.get("id"))

    rows += ["", "## 判定"]
    if missing and len(missing) == len(line.get("stages") or []):
        rows.append("- 本机没有这条线的任何证据目录：这条线不归本机，请改派持有仓库的机器")
    elif newest_all:
        rows.append("- 最近产出 %.1fh 前（阈值 %sh）" % ((time.time() - newest_all) / 3600,
                                                    line.get("stale_after_h")))
    else:
        rows.append("- 证据目录存在但为空：工段已建未开工")

    rows += ["", "## 下一步（按缺口）"]
    acts = []
    for sid in missing:
        acts.append("- %s：建目录/补输入后再谈产出（责任人=%s）" % (sid, line.get("owner")))
    if not acts:
        acts.append("- 产出正常：按工段顺序继续，主控不再介入")
    rows += acts[:3]

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "triage-%s-%s.md" % (line_id, datetime.now().strftime("%Y%m%d")))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print("[triage] %s -> %s" % (line_id, os.path.relpath(path, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())