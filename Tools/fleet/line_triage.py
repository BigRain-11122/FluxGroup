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
import re
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REG = os.path.join(ROOT, "cph4", "fleet", "LINE-REGISTRY.json")
OUT_DIR = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")


def resolve_evidence(e):
    """Resolve one registry evidence path ON THIS node.

    Registry paths are written with the author's box in mind, so `D:/FluxGroup/...` is
    literal where D: exists and `D:/FleetWorker/review` may belong to another node.
    os.path.join(ROOT, absolute) silently drops ROOT, which turned a path from another
    machine into a fake "this stage produced nothing" gap (bm-c 2026-10-31: mv-i2v read
    0/1 while 61 clips sat under K:/Fluxgroup/FluxGroup/media).

    mode: local (literal hit) | rebased (foreign path re-anchored onto our root)
          | offnode (foreign, exists nowhere here -> not our gap)
          | missing (repo-relative and absent -> a real local gap)
    """
    raw = str(e).replace("\\", "/")
    if os.path.exists(raw):
        return raw, "local"
    is_abs = bool(re.match(r"^[A-Za-z]:/", raw)) or raw.startswith("//")
    if is_abs:
        segs = [s for s in raw.split("/") if s]
        for i in range(1, len(segs)):
            cand = os.path.join(ROOT, *segs[i:])
            if os.path.exists(cand):
                return cand, "rebased"
        return None, "offnode"
    cand = os.path.join(ROOT, raw)
    if os.path.exists(cand):
        return cand, "local"
    return None, "missing"


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
    missing, offnode, newest_all = [], [], 0.0
    rows.append("## 工段与证据目录")
    for st in line.get("stages") or []:
        ev = st.get("evidence") or []
        found, files, newest = [], 0, 0.0
        for e in ev:
            p, mode = resolve_evidence(e)
            if mode == "offnode":
                offnode.append(e)
                continue
            if p:
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
                if mode == "rebased":
                    rows.append("  · %s 已从外机路径重定位到本机 %s" %
                                (e, os.path.relpath(p, ROOT)))
        newest_all = max(newest_all, newest)
        age = "%.1fh" % ((time.time() - newest) / 3600) if newest else "—"
        rows.append("- %-14s owner=%-8s lane=%-6s 证据 %d/%d 存在 · 文件 %d · 最新 %s"
                    % (st.get("id"), st.get("owner"), st.get("lane") or "-",
                       len(found), len(ev), files, age))
        if not found:
            # an evidence dir that only lives on another node is not this box's gap
            if all(resolve_evidence(e)[1] == "offnode" for e in ev):
                continue
            missing.append(st.get("id"))

    rows += ["", "## 判定"]
    if missing and len(missing) == len(line.get("stages") or []):
        rows.append("- 本机没有这条线的任何证据目录：这条线不归本机，请改派持有仓库的机器")
    elif newest_all:
        rows.append("- 最近产出 %.1fh 前（阈值 %sh）" % ((time.time() - newest_all) / 3600,
                                                    line.get("stale_after_h")))
    else:
        rows.append("- 证据目录存在但为空：工段已建未开工")
    if offnode:
        rows.append("- 另有 %d 个证据目录只在别的节点上（本机不据此判缺口）：%s"
                    % (len(offnode), "、".join(offnode)))

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