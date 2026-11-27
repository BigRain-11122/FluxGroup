#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""promote_ready.py - 把备队列里 READY 的卡自动提成队列 OPEN。

为什么（2026-11-09 实测）：重派的卡停在 READY，派单只认 OPEN，于是永远不动——
闭环从"派单"这一步就断了，靠人手动 promote 不是自动化。

规则：
  - 只提有 cmd 或 prompt 的卡（空壳不进队列）；
  - 队列里已有同 id 且状态不是 CANCELLED 的，跳过；
  - 队列里是 CANCELLED/ARCHIVED 的，必须 backlog 带 requeued_by 才复活（终态闸纪律）；
  - 每轮最多 20 张，避免一次灌爆。
用法：python3 Tools/fleet/promote_ready.py [--limit 20]
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
import fleet_lane as fl


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
    except OSError:
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()
    q = {r.get("id"): r for r in rows(QUEUE) if r.get("id")}
    made = []
    for r in rows(BACKLOG):
        if len(made) >= a.limit:
            break
        if r.get("state") != "READY" or not r.get("id"):
            continue
        if not (str(r.get("cmd") or "").strip() or str(r.get("prompt") or "").strip()):
            continue
        cur = q.get(r["id"])
        if cur:
            st = cur.get("state")
            if st in ("OPEN", "RUNNING", "DONE", "UNVERIFIED", "BLOCKED"):
                continue
            if st in ("CANCELLED", "ARCHIVED") and not r.get("requeued_by"):
                continue
        row = dict(r)
        row["state"] = "OPEN"
        row.setdefault("created_by", r.get("created_by") or "promote_ready")
        made.append(row)
    if made:
        fl.merge_jsonl(QUEUE, made, mirror=False)
    print("promoted %d -> OPEN" % len(made))
    return 0


if __name__ == "__main__":
    sys.exit(main())
