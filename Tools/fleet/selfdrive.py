#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfdrive.py - 机队自驱：不需要人点名，自己从"盘上的缺口"长出活来。

2026-11-10 CEO：不希望闲置算力，满负荷生产需要的东西。
原则：只从**真实缺口**造卡，不编活：
  A. FAILED / UNVERIFIED 的卡 -> 修复分析卡（本地模型出根因+下一步）
  B. BLOCKED 的卡 -> 解锁分析卡（原因摘要 + 可执行动作）
  C. 队列供给低于水位 -> 把 A/B 未覆盖的缺口补成"巡检/核对"卡
每轮最多 4 张，按 id 去重；只写备份队列，派单仍由 master_agent 单写手负责。

用法：python3 Tools/fleet/selfdrive.py [--limit 4] [--dry]
"""
import argparse
import json
import os
import sys
import time
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
import fleet_lane as fl


def rows(name):
    out = []
    try:
        for line in open(os.path.join(F, name), encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=4)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    q = {r.get("id"): r for r in rows("PRODUCTION-QUEUE.jsonl") if r.get("id")}
    b = {r.get("id"): r for r in rows("PRODUCTION-BACKLOG.jsonl") if r.get("id")}
    now = datetime.datetime.now().isoformat(timespec="seconds")

    def exists(cid):
        return cid in q or cid in b

    made = []
    # A. 失败/未核验 -> 修复分析
    for r in q.values():
        if len(made) >= a.limit:
            break
        if r.get("state") not in ("FAILED", "UNVERIFIED"):
            continue
        cid = "REPAIR-%s" % r["id"]
        if exists(cid):
            continue
        made.append({
            "id": cid, "title": "[repair] %s 的根因与下一步" % r["id"], "state": "READY",
            "cmd": "", "prompt": ("这张卡失败了。请只依据给出的证据，写一页诊断："
                                  "①最可能的根因 ②下一步具体动作（谁、做什么、怎么验证）。"
                                  "不要编造文件或命令。"),
            "when_all": [], "deliverable": "cph4/fleet/repairs/%s.md" % r["id"],
            "prompt_extra": "状态=%s；备注=%s；交付物=%s；重试=%s" % (
                r.get("state"), (r.get("note") or "")[:200], r.get("deliverable") or "-", r.get("retries")),
            "needs": "cpu", "nodes": ["bm-m"], "hard_nodes": ["bm-m"], "model": "local-small",
            "prio": "P1", "line": r.get("line") or "fleet-ops", "day_ok": True, "heavy": False,
            "verify_on_node": True, "ok_rc": [0, 3], "minutes": 10,
            "why": "自驱修复：%s" % (r.get("note") or "")[:120],
            "created_by": "selfdrive", "created_at": now,
        })
    # B. BLOCKED -> 解锁分析
    for r in q.values():
        if len(made) >= a.limit:
            break
        if r.get("state") != "BLOCKED":
            continue
        cid = "UNBLOCK-%s" % r["id"]
        if exists(cid):
            continue
        made.append({
            "id": cid, "title": "[unblock] %s 的解锁动作" % r["id"], "state": "READY",
            "cmd": "", "prompt": ("这张卡被标记 BLOCKED。只依据证据，给出：①阻塞类型（缺人/缺料/缺权限/环境）"
                                  "②最小解锁动作 ③解锁后应由哪台机执行。40 字以内一条，不要客套。"),
            "when_all": [], "deliverable": "cph4/fleet/repairs/%s-unblock.md" % r["id"],
            "prompt_extra": "状态=%s；备注=%s；owner=%s" % (
                r.get("state"), (r.get("note") or "")[:200], r.get("owner") or "-"),
            "needs": "cpu", "nodes": ["bm-m"], "hard_nodes": ["bm-m"], "model": "local-small",
            "prio": "P2", "line": r.get("line") or "fleet-ops", "day_ok": True, "heavy": False,
            "verify_on_node": True, "ok_rc": [0, 3], "minutes": 10,
            "why": "自驱解锁：%s" % (r.get("note") or "")[:120],
            "created_by": "selfdrive", "created_at": now,
        })

    for m in made:
        if m.get("prompt_extra"):
            m["prompt"] = m["prompt"] + "\n\n证据：" + m.pop("prompt_extra")
    if made and not a.dry:
        fl.merge_jsonl(os.path.join(F, "PRODUCTION-BACKLOG.jsonl"), made, mirror=False)
    print("selfdrive: made %d (%s)" % (len(made), [m["id"] for m in made]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
