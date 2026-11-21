#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_audit.py — 按 AGENT-SPEC-v1.json 检查"这条线的智能体到底有没有在履职"。

判据三件，缺一样就算没履职（不认自述、不认"进程活着"）：
  1 executor 文件存在（谁执行）
  2 evidence 文件存在（产物落在盘上）
  3 evidence 的 mtime 在 stale_after_s 内（新鲜）

结果四态：OK / STALE（有产物但过期）/ MISSING（没产物）/ NO-EXECUTOR（执行体不存在）。
退出码：0 全 OK；1 有 STALE/MISSING（状态，不是故障）。

用法
  python3 Tools/fleet/agent_audit.py            # 一屏
  python3 Tools/fleet/agent_audit.py --json
  python3 Tools/fleet/agent_audit.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
SPEC = os.path.join(SOCIAL, "AGENT-SPEC-v1.json")


def _newest(pattern):
    hits = glob.glob(os.path.join(ROOT, pattern)) if not os.path.isabs(pattern) else glob.glob(pattern)
    if not hits:
        return None
    return max(hits, key=lambda p: os.path.getmtime(p))


def check(spec, now=None):
    now = now or time.time()
    rows = []
    for d in spec.get("duties") or []:
        ex = (d.get("exec") or "").split()[0]
        ex_path = os.path.join(ROOT, ex) if not os.path.isabs(ex) else ex
        ev = d.get("evidence") or ""
        ev_path = _newest(ev)
        rec = {"id": d.get("id"), "name": d.get("name"), "exec": ex,
               "evidence": ev, "cadence_h": round((d.get("cadence_s") or 0) / 3600, 1)}
        if not os.path.exists(ex_path):
            rec.update(state="NO-EXECUTOR", why="执行体不存在")
        elif not ev_path:
            rec.update(state="MISSING", why="证据文件不存在")
        else:
            age = now - os.path.getmtime(ev_path)
            limit = float(d.get("stale_after_s") or 86400)
            rec.update(age_h=round(age / 3600, 1), limit_h=round(limit / 3600, 1))
            if age > limit:
                rec.update(state="STALE", why="证据 %.1fh 前（上限 %.1fh）" % (age / 3600, limit / 3600))
            else:
                rec.update(state="OK", why="")
        rows.append(rec)
    return rows


def summarize(rows):
    from collections import Counter
    return dict(Counter(r["state"] for r in rows))


def self_test():
    """负控：证据缺失必须是 MISSING、执行体缺失必须是 NO-EXECUTOR、过期必须 STALE。"""
    import tempfile
    d = tempfile.mkdtemp()
    fresh = os.path.join(d, "fresh.json")
    open(fresh, "w").write("{}")
    old = os.path.join(d, "old.json")
    open(old, "w").write("{}")
    os.utime(old, (time.time() - 7200, time.time() - 7200))
    spec = {"duties": [
        {"id": "A", "exec": "Tools/fleet/agent_audit.py", "evidence": fresh, "stale_after_s": 3600},
        {"id": "B", "exec": "Tools/fleet/agent_audit.py", "evidence": old, "stale_after_s": 3600},
        {"id": "C", "exec": "Tools/fleet/agent_audit.py", "evidence": os.path.join(d, "nope.json"),
         "stale_after_s": 3600},
        {"id": "D", "exec": "Tools/fleet/nope.py", "evidence": fresh, "stale_after_s": 3600},
    ]}
    rows = {r["id"]: r["state"] for r in check(spec)}
    ok = (rows["A"] == "OK" and rows["B"] == "STALE"
          and rows["C"] == "MISSING" and rows["D"] == "NO-EXECUTOR")
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "states": rows}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    spec = json.load(open(SPEC, encoding="utf-8"))
    rows = check(spec)
    s = summarize(rows)
    if a.json:
        print(json.dumps({"version": spec.get("version"), "counts": s, "duties": rows},
                         ensure_ascii=False, indent=1))
    else:
        print("== 智能体履职（%s / %s）：OK %d / STALE %d / MISSING %d / NO-EXECUTOR %d =="
              % (spec.get("agent", {}).get("name"), spec.get("version"),
                 s.get("OK", 0), s.get("STALE", 0), s.get("MISSING", 0), s.get("NO-EXECUTOR", 0)))
        for r in rows:
            mark = {"OK": "✅", "STALE": "⏳", "MISSING": "❗", "NO-EXECUTOR": "❗"}[r["state"]]
            extra = ("%.1fh前" % r["age_h"]) if r.get("age_h") is not None else ""
            print("%s %-4s %-22s %-10s %s" % (mark, r["id"], r["name"][:22], extra, r["why"][:36]))
    bad = [r for r in rows if r["state"] in ("STALE", "MISSING", "NO-EXECUTOR")]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
