#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comms_check.py - one screen that answers "is the fleet actually talking?"

Why: the loop has four signals that were repeatedly confused (2026-11-02 review):
  hb        machine alive?          (MASTER-STATE.lanes[n].hb_age_s)
  report    executor reporting?     (lanes/<node>.json mtime)
  claim     card taken?             (queue state=RUNNING + owner)
  receipt   product landed?         (queue-receipts/<id>-<node>.json mtime)

A machine can be alive, busy, and still produce nothing. This script separates the four
and prints one line per node plus the queue side, so a silent leg is named instead of
being averaged into "healthy".

Read-only. Writes cph4/fleet/state/comms.json.
Usage: python3 comms_check.py [--json]
Exit: 0 = every online node is coherent, 2 = at least one incoherent leg.
"""
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
MASTER = os.path.join(FLEET, "dispatcher", "MASTER-STATE.json")
PULSE = os.path.join(FLEET, "dispatcher", "PULSE.json")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
LANES = os.path.join(FLEET, "lanes")
RECEIPTS = os.path.join(FLEET, "queue-receipts")

import card_policy as _cp   # 阈值唯一源：cph4/fleet/CARD-POLICY-v1.json
HB_SILENT_S = 300        # machine heartbeat older than this = silent
REPORT_SILENT_S = 900    # executor report older than this while it has a job = suspicious

NAME = {"bm-a": "公司生产力", "bm-b": "小钢炮", "bm-c": "传家宝",
        "bm-d": "算力大脑", "bm-m": "MacBook Pro"}


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def age(path):
    try:
        return round(time.time() - os.path.getmtime(path), 1)
    except OSError:
        return None


def newest_receipt(node):
    best = None
    try:
        for n in os.listdir(RECEIPTS):
            if n.endswith("-%s.json" % node):
                a = age(os.path.join(RECEIPTS, n))
                if a is not None and (best is None or a < best):
                    best = a
    except OSError:
        pass
    return best


def main(argv):
    os.makedirs(STATE, exist_ok=True)
    ms = jload(MASTER, {}) or {}
    pulse = jload(PULSE, {}) or {}
    nodes = ms.get("lanes") or {}
    queue = []
    try:
        for l in open(QUEUE, encoding="utf-8"):
            l = l.strip()
            if l:
                queue.append(json.loads(l))
    except FileNotFoundError:
        pass
    running = {r.get("owner"): r for r in queue if r.get("state") == "RUNNING" and r.get("owner")}
    openings = [r for r in queue if r.get("state") == "OPEN"]

    rows = []
    bad = 0
    for n, v in sorted(nodes.items()):
        hb = v.get("hb_age_s")
        hb = round(hb, 1) if isinstance(hb, (int, float)) else None
        lane_f = os.path.join(LANES, "%s.json" % n)
        rep = age(lane_f)
        rc = newest_receipt(n)
        job = v.get("job") or (running.get(n) or {}).get("id")
        online = bool(v.get("online"))
        flags = []
        if not online:
            flags.append("OFFLINE")
        if hb is not None and hb > HB_SILENT_S:
            flags.append("HB-SILENT")
        if job and rep is not None and rep > REPORT_SILENT_S:
            flags.append("BUSY-NO-REPORT")
        if not job and openings:
            flags.append("IDLE-WITH-QUEUE")
        # 2026-11-07 修：原判据写成 `rc > 3600`——rc 是返回码（0/1/2），永远不可能
        # 大于 3600，于是这条"握着卡却一小时没回执"的旗标从未真正亮过，chief 的重排
        # 规则也就从未生效。改为按回执龄（rep 秒）比策略阈值，阈值只在 CARD-POLICY 里写。
        if job and rep is not None and rep > _cp.stuck_requeue_s():
            flags.append("NO-RECEIPT-STUCK")
        if job and rc is None:
            flags.append("NEVER-RECEIPTED")
        if flags:
            bad += 1
        rows.append({"node": n, "name": NAME.get(n, n), "online": online,
                     "hb_s": hb, "report_s": rep, "last_receipt_s": rc,
                     "job": job, "flags": flags})

    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "pulse": {"ts": pulse.get("ts"), "ok": pulse.get("ok"),
                     "git": pulse.get("git"), "push": pulse.get("push")},
           "queue": {"open": len(openings), "running": len(running),
                     "cards_done": sum(1 for r in queue if r.get("state") == "DONE")},
           "nodes": rows, "incoherent": bad}
    with open(os.path.join(STATE, "comms.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if bad == 0 else 2

    p = out["pulse"]
    print("中枢脉冲 %s ok=%s git=%s push=%s" % (p["ts"], p["ok"], p["git"], p["push"]))
    print("队列：在飞 %d ｜ 待领 %d ｜ 已完成 %d" %
          (out["queue"]["running"], out["queue"]["open"], out["queue"]["cards_done"]))
    print("%-10s %-8s %-9s %-11s %-13s %-28s %s" %
          ("节点", "机器活", "机在干活", "上报年龄", "最近回执", "当前卡", "信号"))
    for r in rows:
        print("%-10s %-8s %-9s %-11s %-13s %-28s %s" % (
            r["name"], "在线" if r["online"] else "离线",
            "是" if r["job"] else "空",
            "%ss" % r["hb_s"] if r["hb_s"] is not None else "-",
            "%ss" % r["last_receipt_s"] if r["last_receipt_s"] is not None else "无",
            (r["job"] or "-")[:28],
            "、".join(r["flags"]) or "正常"))
    print("不一致节点 %d（0=全通）  -> cph4/fleet/state/comms.json" % bad)
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))