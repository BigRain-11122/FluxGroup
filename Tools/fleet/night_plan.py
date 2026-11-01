#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""night_plan.py - the master decides what each machine should do tonight, by itself.

Input (all on disk, no model, no guessing):
  cph4/fleet/lines/*.json      per-line spec: inputs / outputs / lanes / needs / cadence
  PRODUCTION-QUEUE.jsonl       what is already in flight (one in-flight card per line)
  dispatcher/MASTER-STATE.json which lanes are online

Output: cards appended to PRODUCTION-BACKLOG.jsonl with a real deliverable + acceptance,
         and a PLAN line in dispatcher/NIGHT-PLAN.md explaining the choice.

Rules (scientific, not optimistic):
  * never more than ONE in-flight card per line
  * only lines whose cadence deadline is missed get a card
  * a card is only created when it names a deliverable AND an acceptance check
  * machine chosen by declared lane + needs; if no lane is online, record WAITING (not idle)
"""
import json, os, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
LINES = os.path.join(F, "lines")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
B = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
OUT = os.path.join(F, "dispatcher", "NIGHT-PLAN.md")


def jl(p):
    out = []
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def newest(paths):
    import glob
    best = 0.0
    for pat in paths or []:
        for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
            if os.path.isfile(p):
                best = max(best, os.path.getmtime(p))
    return best


def main():
    online = set()
    try:
        ms = json.load(open(os.path.join(F, "dispatcher", "MASTER-STATE.json"), encoding="utf-8-sig"))
        online = {n for n, v in (ms.get("lanes") or {}).items() if v.get("online")}
    except Exception:
        pass
    queue = jl(Q)
    inflight = {}
    for r in queue:
        if r.get("state") in ("OPEN", "RUNNING"):
            inflight[r.get("line") or r.get("id")] = r.get("id")
    have = {r.get("id") for r in queue + jl(B)}
    now = datetime.now()
    made, waiting, lines = [], [], []

    for fn in sorted(os.listdir(LINES)) if os.path.isdir(LINES) else []:
        if not fn.endswith(".json"):
            continue
        spec = json.load(open(os.path.join(LINES, fn), encoding="utf-8"))
        lid = spec.get("id")
        if spec.get("status") == "PARKED":
            lines.append("- %s：CEO 已停产，不派" % lid)
            continue
        if lid in inflight:
            lines.append("- %s：在途 %s，不重复派" % (lid, inflight[lid]))
            continue
        age_h = (now.timestamp() - newest(spec.get("outputs"))) / 3600 if newest(spec.get("outputs")) else 999
        if age_h < float(spec.get("cadence_h") or 24):
            lines.append("- %s：%.1fh 前有产出，未到点" % (lid, age_h))
            continue
        # Declared lanes first; otherwise any online box. Five lines (bigcompute /
        # bigdomain / bighouse / biglife / ...) declare `lanes: []`, so the strict rule
        # made them WAITING for ever - a permanent idle that looked like "no owner".
        # The card these lines get is CPU-only evidence gathering, safe on any box.
        declared = spec.get("lanes") or []
        lane = next((n for n in declared if n in online), None)
        fallback = False
        if not lane and online:
            # Spread fallback work instead of stacking it on the alphabetically first box
            # (that was always bm-a = the CEO's workstation). The control plane bm-m is
            # only used when it is the single box online, per MASTER-NODE.json.
            pool_n = [n for n in sorted(online) if n != "bm-m"] or sorted(online)
            lane = pool_n[len(made) % len(pool_n)]
            fallback = True
        if not lane:
            waiting.append(lid)
            lines.append("- %s：全机队不在线，记 WAITING" % lid)
            continue
        day = now.strftime("%Y%m%d")
        cid = "R-PLAN-%s-%s" % (lid.upper().replace("-", "")[:12], day)
        if cid in have:
            lines.append("- %s：今日计划卡已在册" % lid)
            continue
        deliverable = (spec.get("outputs") or ["cph4/fleet/queue-receipts/"])[0].replace("*", "plan-%s.md" % lid)
        if deliverable.endswith("/"):
            deliverable += "plan-%s-%s.md" % (lid, day)
        card = {"id": cid, "title": "%s 线级体检与缺口清单" % (spec.get("name") or lid),
                "needs": "cpu", "nodes": [lane], "prio": "P3", "day_ok": True,
                "verify_on_node": True, "state": "READY",
                "cmd": "python Tools/fleet/line_triage.py --line %s" % lid,
                "cwd": "",
                "requires": ["Tools/fleet/line_triage.py"],
                "deliverable": "cph4/fleet/queue-receipts/triage-%s-%s.md" % (lid, day),
                "accept": "回执含每工段证据存在性/最新时间/缺什么",
                "line": lid, "created_by": "night_plan", "created_at": now.isoformat(timespec="seconds"),
                "why": ("线到期未产出；声明车道 %s 不在线，改派在线机 %s" % (",".join(declared) or "无", lane)
                        if fallback else "线到期未产出")}
        with open(B, "a", encoding="utf-8") as f:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
        made.append((lid, lane, card["id"]))

    body = ["# 夜间计划 %s" % now.strftime("%Y-%m-%d %H:%M"), "",
            "- 在线 %d 台：%s" % (len(online), ",".join(sorted(online)) or "无"),
            "- 新开卡 %d 张，等待承办机 %d 条线" % (len(made), len(waiting)), "", "## 决策"]
    body += ["- 派 %s → %s（%s）" % (l, m, c) for l, m, c in made] or ["- 本轮无线到期"]
    body += ["", "## 逐线状态"] + (lines or ["- 无"])
    open(OUT, "w", encoding="utf-8").write("\n".join(body) + "\n")
    print("[night_plan] cards=%d waiting=%d" % (len(made), len(waiting)))
    return 0


if __name__ == "__main__":
    sys.exit(main())