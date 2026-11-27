#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prep_work.py - 等待期预排：机器在跑时，把下一批活准备好，不让主控空等。

为什么（CEO 2026-11-05「等待的同时可以继续推进后续工作而不是一直等着」）：
  实测过的烂形态：bm-c 跑一张 20 小时的卡，队列里只留 1 张待派；一旦这张结束，
  下一张才开始"想"要干什么——中间空档全靠运气。等待应该是**准备时间**，不是空闲。

它做三件不需要机器的事（纯主控侧）：
  P1 预排卡：每条 ACTIVE 线的"下一步"若还没有 OPEN/READY 卡，就预生成一张 READY（不进队列）。
  P2 预检输入：对每张待派卡的 requires/when_all 逐条查是否存在，标 precheck=PASS/MISSING。
  P3 预备清单：把"槽位一空就能立刻派"的卡列出来，并指出缺输入的（先修输入再派，不白跑）。

产出：state/prep-work.json + plans/PREP-<date>.md
用法：python3 Tools/fleet/prep_work.py [--json]
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "state", "prep-work.json")
MD = os.path.join(F, "plans", "PREP-%s.md" % time.strftime("%Y%m%d"))


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def rows(p):
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


def exists(rel):
    p = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
    return os.path.exists(p)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    cfg = jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}
    blocked = (cfg.get("capacity") or {}).get("blocked_active") or {}
    steps = (jload(os.path.join(F, "LINE-NEXT-STEPS.json"), {}) or {}).get("lines") or {}
    queue = rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
    backlog = rows(os.path.join(F, "PRODUCTION-BACKLOG.jsonl"))
    truth = {l.get("id"): l for l in ((jload(os.path.join(F, "state", "lines.json"), {}) or {})
                                      .get("lines") or [])}

    # 已在飞/待派的线
    busy_lines = {str(r.get("line")) for r in queue + backlog
                  if r.get("state") in ("OPEN", "READY", "RUNNING")}

    pre_staged, missing_inputs = [], []
    for line, spec in steps.items():
        st = truth.get(line) or {}
        if str(st.get("declared")) != "ACTIVE":
            continue
        if line in blocked:
            continue
        if line in busy_lines:
            continue
        # P1 预排：取该线声明里第一张卡，做成 READY 放进 backlog（不直接派）
        for c in (spec.get("cards") or []):
            cid = "%s-PREP-%s" % (c.get("key", "card").upper(), time.strftime("%Y%m%d"))
            if any(r.get("id") == cid for r in backlog):
                continue
            cmd = str(c.get("cmd") or "").replace("{date}", time.strftime("%Y%m%d"))
            dl = str(c.get("deliverable") or "").replace("{date}", time.strftime("%Y%m%d"))
            card = {"id": cid, "title": c.get("title"), "cmd": cmd, "cwd": "",
                    "needs": spec.get("needs") or "cpu", "minutes": 10,
                    "deliverable": dl, "accept": c.get("accept") or "",
                    "nodes": spec.get("nodes") or ["bm-a"], "prio": spec.get("prio") or "P2",
                    "line": line, "requires": c.get("requires") or [],
                    "state": "READY", "created_by": "prep_work",
                    "created_at": datetime.now().isoformat(timespec="seconds")}
            pre_staged.append(card)
            break

    # P2 预检：所有待派（OPEN/READY）卡的输入是否在盘
    for r in queue + backlog:
        if r.get("state") not in ("OPEN", "READY"):
            continue
        miss = []
        for rel in (r.get("requires") or []):
            if not exists(rel):
                miss.append(rel)
        for rel in (r.get("when_all") or []):
            if not exists(rel):
                miss.append(rel)
        if miss:
            missing_inputs.append({"id": r.get("id"), "nodes": r.get("nodes"),
                                   "missing": miss[:4]})

    if pre_staged:
        try:
            import fleet_lane as fl
            fl.merge_jsonl(os.path.join(F, "PRODUCTION-BACKLOG.jsonl"), pre_staged)
        except Exception as e:
            print("[prep] merge failed: %s" % str(e)[:80])

    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "pre_staged": [c["id"] for c in pre_staged],
           "missing_inputs": missing_inputs,
           "note": "预排卡是 READY（不进队列），槽位一空即可派；缺输入的卡先修输入，不白跑"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    lines = ["# 等待期预排 %s" % out["ts"], "",
             "## 已预排（槽位一空即可派）", ""]
    lines += ["- %s" % x for x in out["pre_staged"]] or ["- 无（各线都有在飞的活）"]
    lines += ["", "## 输入缺失（先修输入，避免白跑）", ""]
    for m in missing_inputs[:12]:
        lines.append("- %s（%s）：缺 %s" % (m["id"], ",".join(m["nodes"] or []),
                                            ", ".join(m["missing"])))
    if not missing_inputs:
        lines.append("- 无")
    os.makedirs(os.path.dirname(MD), exist_ok=True)
    with open(MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[prep] staged=%d missing-input=%d" % (len(pre_staged), len(missing_inputs)))
        for c in out["pre_staged"]:
            print("  + %s" % c)
        for m in missing_inputs[:5]:
            print("  ! %s 缺 %s" % (m["id"], ",".join(m["missing"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))