#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""line_agents.py - the operational half of the multi-agent master.

Two jobs, both grounded in what exists on disk:

1. Recurring work (`cph4/fleet/RECURRING-WORK.jsonl`): rows with `every_h`. A row is due
   again `every_h` hours after its last receipt, so the queue cannot stay dry just because
   a one-shot rule was consumed once. No model, no invention - every row names a command
   that exists in this repo and a deliverable path it must produce.

2. Line verdicts: for every line/stage in LINE-REGISTRY that is STALLED/BLOCKED, write the
   *missing input* and the *owner* into NEED-SUPPLY. It deliberately does NOT invent
   engineering steps: when a line is stuck on a human decision or a machine we cannot
   reach, saying so is the correct output.

Usage:
  python3 Tools/fleet/line_agents.py            # re-arm recurring work + verdicts
  python3 Tools/fleet/line_agents.py --dry
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
RECUR = os.path.join(FLEET, "RECURRING-WORK.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
NEED = os.path.join(FLEET, "dispatcher", "NEED-SUPPLY.md")
REGISTRY = os.path.join(FLEET, "LINE-REGISTRY.json")


def rows(path):
    out = []
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def append(path, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def arm_recurring(dry=False):
    """A recurring row is due when its deliverable is missing or older than every_h."""
    armed, backlog, queue = [], rows(BACKLOG), rows(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    active = {r.get("id") for r in backlog + queue
              if r.get("state") in ("OPEN", "RUNNING", "PROMOTED")}
    now = time.time()
    for r in rows(RECUR):
        rid = r.get("id")
        if not rid or rid in active:
            continue
        every = float(r.get("every_h") or 24) * 3600
        dl = r.get("deliverable") or ""
        # deliverable may be a directory or a dated file; use mtime when it exists
        hit = None
        if dl and os.path.exists(dl):
            hit = os.path.getmtime(dl)
        if hit is not None and now - hit < every:
            continue
        if dry:
            armed.append(rid)
            continue
        row = dict(r, state="READY", created_at=datetime.now(timezone.utc)
                   .astimezone().isoformat(timespec="seconds"),
                   created_by="line_agents:recurring")
        append(BACKLOG, row)
        armed.append(rid)
    return armed


def arm_triage(dry=False, limit=3):
    """Turn "this line is silent" into one executable card on the machine that owns it.

    The Mac cannot read six of the sub-repos (0 files), so it can never diagnose them itself.
    A triage card asks the owning lane for facts from its own disk: what exists, what is
    newest, what is missing. Only ACTIVE lines whose lane is online get one, at most `limit`
    per run, so a quiet fleet cannot be flooded with paperwork.
    """
    reg = json.load(open(REGISTRY, encoding="utf-8")) if os.path.exists(REGISTRY) else {}
    try:
        ms = json.load(open(os.path.join(FLEET, "dispatcher", "MASTER-STATE.json"),
                            encoding="utf-8-sig"))
    except Exception:
        ms = {}
    online = {n for n, v in (ms.get("lanes") or {}).items() if v.get("online")}
    have = {r.get("id") for r in rows(BACKLOG) + rows(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))}
    day = datetime.now().strftime("%Y%m%d")
    armed = []
    for ln in reg.get("lines") or []:
        if len(armed) >= limit:
            break
        if (ln.get("status") or "") != "ACTIVE":
            continue
        want = [st.get("lane") for st in (ln.get("stages") or []) if st.get("lane")]
        target = next((w for w in want if w in online), None)
        if not target:
            continue
        lid = ln.get("id")
        deliverable = "cph4/fleet/queue-receipts/triage-%s-%s.md" % (lid, day)
        jid = "Q-TRIAGE-%s-%s" % (lid.upper().replace("-", ""), day)
        if jid in have or os.path.exists(os.path.join(ROOT, deliverable)):
            continue
        row = {"id": jid, "title": "%s 线级体检（本机证据目录实况）" % lid, "needs": "cpu",
               "nodes": [target], "prio": "P3", "day_ok": True, "heavy": False,
               "cmd": "python Tools/fleet/line_triage.py --line %s" % lid, "cwd": "",
               "requires": ["Tools/fleet/line_triage.py"],
               "deliverable": deliverable,
               "why": "该线 24h 无落库产出，主控看不到其仓库（本机 0 文件），只能由承办机自证缺口",
               "created_at": datetime.now().isoformat(timespec="seconds"),
               "created_by": "line_agents:triage"}
        if not dry:
            append(BACKLOG, row)
        armed.append(jid)
    return armed


def line_verdicts(dry=False):
    try:
        reg = json.load(open(REGISTRY, encoding="utf-8"))
    except Exception:
        return []
    out = []
    for ln in reg.get("lines") or []:
        for st in ln.get("stages") or []:
            ev = st.get("evidence") or []
            # On the control plane most business evidence lives on another machine; that is
            # NO-DATA, not a stall - do not accuse a line of being idle just because we
            # cannot see its disk.
            seen = any(os.path.exists(os.path.join(ROOT, e)) for e in ev) if ev else False
            if not seen:
                out.append((ln.get("id"), st.get("id"), "NO-DATA",
                            st.get("owner") or ln.get("owner") or "?",
                            "证据目录不在本机（在 %s），需该机上报" % (st.get("lane") or "生产机")))
    return out


def main():
    dry = "--dry" in sys.argv
    armed = arm_recurring(dry) + arm_triage(dry)
    verdicts = line_verdicts(dry)
    if not dry and armed:
        lines = ["", "## 条线 Agent 续卡 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "", "- 本轮续卡 %d：%s" % (len(armed), ", ".join(armed)),
                 "- NO-DATA（证据不在主控盘上，需生产机上报）%d 段" % len(verdicts)]
        with open(NEED, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print("[line_agents] armed=%d no_data=%d%s"
          % (len(armed), len(verdicts), " (dry)" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())