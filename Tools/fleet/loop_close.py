#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""loop_close.py - 把"断点"接上：假绿清理、CEO 决策转卡、巡视 RED 转卡。

三件闭环（2026-11-09 CEO「按你的方案去闭环，自己推进」）：
  1 假绿：DONE 但本地交付物不在盘上 → 改判 UNVERIFIED；远端路径（D:\\ / UNC）只打标，
         不越权判死（应由 verify_on_node 在目标机核）。
  2 决策→派单：CEO-QUEUE 里「机队先做：」的条目 → READY 卡（去重、限 5 张/轮）。
  3 巡视→派单：patrol-local.json 的 RED 域（且无在办卡）→ 一张处置卡。

用法：
  python3 Tools/fleet/loop_close.py [--all] [--dry]
退出：0 正常。
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
CEOQ = os.path.join(F, "CEO-QUEUE.md")
PATROL = os.path.join(F, "state", "patrol-local.json")
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
import fleet_lane as fl


def rows(path):
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        pass
    return out


def is_remote(p):
    return bool(re.match(r"^[A-Za-z]:[\\/]", p) or p.startswith("\\\\"))


def hygiene(dry=False):
    q = rows(QUEUE)
    upd, remote = [], 0
    for r in q:
        if r.get("state") != "DONE":
            continue
        d = (r.get("deliverable") or "").strip()
        if not d:
            continue
        if is_remote(d):
            r["remote_unverified"] = True
            remote += 1
            upd.append(r)
        elif not os.path.exists(d if os.path.isabs(d) else os.path.join(ROOT, d)):
            r["state"] = "UNVERIFIED"
            r["note"] = "deliverable-not-on-disk(local)"
            upd.append(r)
    if upd and not dry:
        fl.merge_jsonl(QUEUE, upd, mirror=False)
    print("hygiene: local->UNVERIFIED %d, remote tagged %d" %
          (len([u for u in upd if u.get("state") == "UNVERIFIED"]), remote))
    return 0


def _exists_any(ids):
    have = {r.get("id") for r in rows(QUEUE) + rows(BACKLOG)}
    return [i for i in ids if i in have]


def ceo_demand(dry=False, cap=5):
    try:
        t = open(CEOQ, encoding="utf-8").read()
    except OSError:
        return 0
    made = []
    for block in re.split(r"\n- \[", t)[1:]:
        lines = block.splitlines()
        head = lines[0]
        m = None
        for l in lines:
            m = re.search(r"机队先做[^：]*：(.*)", l)
            if m:
                break
        if not m:
            continue
        ask = m.group(1).strip().split("（不对外")[0].strip()
        if not ask or ask.startswith("—"):
            continue
        _topic = ("隐私政策", "配音", "隐私")
        _have = " ".join((r.get("title") or "") + " " + (r.get("prompt") or "")
                         for r in rows(QUEUE) + rows(BACKLOG))
        if ask in _have:
            continue
        if any(x in ask and x in _have for x in _topic):
            continue
        title = "[ceo-queue] " + ask[:60]
        cid = "CEOQ-" + hashlib.sha1(ask.encode()).hexdigest()[:10]
        if _exists_any([cid]):
            continue
        made.append({
            "id": cid, "title": title, "cmd": "", "cwd": "", "requires": [],
            "deliverable": "cph4/fleet/queue-receipts/%s.md" % cid,
            "accept": "回执含执行说明、产物路径、未对外/未花钱声明；引用卡 id。",
            "needs": "cpu", "nodes": [], "hard_nodes": [], "prio": "P2", "line": "group",
            "day_ok": True, "heavy": False, "verify_on_node": True, "ok_rc": [0, 3],
            "minutes": 60, "why": "CEO-QUEUE：机队先做的那一半，不依赖 CEO 物理件",
            "prompt": ask, "created_by": "loop_close", "state": "READY",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })
        if len(made) >= cap:
            break
    if made and not dry:
        fl.merge_jsonl(BACKLOG, made, mirror=False)
    print("ceo_demand: +%d cards %s" % (len(made), [c["id"] for c in made]))
    return 0


def patrol_cards(dry=False, cap=3):
    try:
        d = json.load(open(PATROL, encoding="utf-8"))
    except Exception:
        return 0
    open_ids = {r.get("id") for r in rows(QUEUE) if r.get("state") in ("OPEN", "RUNNING", "READY")}
    made = []
    for seat in d.get("seats") or []:
        res = seat.get("result") or {}
        if res.get("verdict") != "RED":
            continue
        dom = seat["domain"]
        cid = "PATROL-%s-%s" % (dom, time.strftime("%Y%m%d"))
        if cid in open_ids:
            continue
        made.append({
            "id": cid, "title": "[patrol] %s RED 处置" % dom, "cmd": "", "cwd": "", "requires": [],
            "deliverable": "cph4/fleet/queue-receipts/%s.md" % cid,
            "accept": "回执说明：核实了哪条发现、证据路径、处置动作；未核实则写未核实原因。",
            "needs": "cpu", "nodes": [], "hard_nodes": [], "prio": "P1", "line": dom,
            "day_ok": True, "heavy": False, "verify_on_node": True, "ok_rc": [0, 3],
            "minutes": 60, "why": "十域巡视 RED：%s" % "；".join((res.get("findings") or [])[:2])[:120],
            "prompt": "核实并处置 %s 域巡视 RED：%s。动作建议：%s" %
                      (dom, "；".join((res.get("findings") or [])[:2]), res.get("action") or ""),
            "created_by": "loop_close", "state": "READY",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })
        if len(made) >= cap:
            break
    if made and not dry:
        fl.merge_jsonl(BACKLOG, made, mirror=False)
    print("patrol_cards: +%d %s" % (len(made), [c["id"] for c in made]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    hygiene(a.dry)
    ceo_demand(a.dry)
    patrol_cards(a.dry)
    return 0


if __name__ == "__main__":
    sys.exit(main())
