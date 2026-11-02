#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""night_fill.py - 睡前灌卡：让机器在没人管的时候也有活干。

为什么（2026-11-02）：主控是笔记本，合盖就停；但机器上的执行器会自取 OPEN 卡。
所以"夜里能不能干活"只取决于一件事——队列里有没有留着的 OPEN 卡。
本工具在夜间窗口前，按配额把候选卡提成 OPEN，并打上夜间标记（不许对外发布、不许花钱）。

规则：
  1. 只提 backlog 里 READY 且命令/交付物齐全的卡；
  2. 每组按配额（QUOTA.json）封顶，先给 P0；
  3. 夜间卡一律加 night:true，执行器遇到"发布/报价/删"类动作要拒；
  4. 队列里 OPEN 已够（默认 3 张）就不加，避免堆卡。

用法：python3 night_fill.py [--target 3] [--dry]
"""
import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")

sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=3)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)

    reg = jload(os.path.join(FLEET, "LINE-REGISTRY.json"), {}) or {}
    org_of = {l.get("id"): (l.get("org") or "platform") for l in (reg.get("lines") or [])}
    prio_of = {l.get("id"): str(l.get("priority") or "P2") for l in (reg.get("lines") or [])}
    quota = jload(os.path.join(FLEET, "QUOTA.json"), {}) or {}
    caps = quota.get("caps") or {}

    q = fl.read_jsonl(QUEUE)
    open_cards = [r for r in q if r.get("state") == "OPEN"]
    if len(open_cards) >= a.target:
        print("队列已有 %d 张待领，够用，不灌" % len(open_cards))
        return 0

    have_ids = {r.get("id") for r in q}
    used = Counter(org_of.get(r.get("line") or "", "platform")
                   for r in q if r.get("state") in ("OPEN", "RUNNING"))
    nights = [r for r in q if r.get("night")]
    if nights:
        print("夜间包已在（%d 张），不重复灌" % len(nights))
        return 0

    cands = []
    for r in fl.read_jsonl(BACKLOG):
        if r.get("state") != "READY" or not r.get("cmd"):
            continue
        if r.get("id") in have_ids:
            continue
        if not (r.get("line") or r.get("nodes")):
            continue
        cands.append(r)
    # 先 P0，再按创建时间
    cands.sort(key=lambda r: (prio_of.get(r.get("line"), "P2"), str(r.get("created_at") or "")))

    picked = []
    for r in cands:
        if len(open_cards) + len(picked) >= a.target:
            break
        org = org_of.get(r.get("line"), "platform")
        if caps and used[org] >= int(caps.get(org, 999)):
            continue
        c = dict(r)
        c.update({"state": "OPEN", "night": True, "created_by": "night_fill",
                  "ok_rc": c.get("ok_rc") or [0],
                  "night_rules": ["no-cloud", "no-publish", "no-spend", "no-delete"]})
        picked.append(c)
        used[org] += 1

    if not picked:
        print("候选卡为 0（README 里没活可补）——这属于供给缺口，不是调度故障")
        return 0
    if a.dry:
        print("将灌入 %d 张：%s" % (len(picked), ", ".join(p["id"] for p in picked)))
        return 0
    fl.merge_jsonl(QUEUE, picked)
    print("夜间灌入 %d 张：%s" % (len(picked), ", ".join(p["id"] for p in picked)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))