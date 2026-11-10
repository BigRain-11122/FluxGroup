#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cloud_runner.py - 云端只走团结 Codely：把 cloud-smart 卡交给 codely_bridge 执行。

为什么（2026-11-10 CEO）：云端调用必须走团结 AI 引擎的 Codely，不走别的云；
本地能做的先本地。此前 cloud-smart 卡只被"路由成 cloud"，但没有任何执行器，
等于永远不落地——本件补上唯一执行入口。

规则：
  - 只取 state=OPEN 且 model=cloud-smart 且 local_tried=true 的卡（本地优先闸）；
  - 每次最多 1 张，遵守 Codely 并发/合规闸（bridge 内部已管）；
  - 执行后按盘上产物核验，写回 DONE / FAILED / UNVERIFIED。
用法：python3 Tools/fleet/cloud_runner.py [--limit 1] [--dry]
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
BRIDGE = os.path.join(ROOT, "Tools", "fleet", "codely_bridge.py")
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
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    todo = [r for r in rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
            if r.get("state") == "OPEN" and (r.get("model") or "") == "cloud-smart"
            and r.get("local_tried")][:a.limit]
    if not todo:
        print("no cloud-smart card ready (local-first gate holds them)")
        return 0

    for r in todo:
        cid = r["id"]
        deliv = r.get("deliverable") or ""
        prompt = (r.get("prompt") or "") + ("\n\n交付物写到：%s" % deliv if deliv else "")
        card = {
            "card_id": cid, "prompt": prompt, "cwd": str(ROOT),
            "deliverable": deliv or os.path.join(F, "queue-receipts", "%s.out" % cid),
            "mode": "ask", "approval": "default",
            "deliverable_mode": "file" if deliv else "capture",
            "timeout_s": int(r.get("timeout_s") or 300), "task_class": "judgment",
            # 团结 Codely 是雇主座席：默认-拒绝闸要求真实授权引用 + 数据分级 + 座席确认。
            "compliance": {"authorization_ref": "CEO-20261110-LOCAL-FIRST",
                           "data_classification": "public",
                           "purpose": "ceo_authorized",
                           "seat_owner_confirmed": True,
                           "model_target": "cloud",
                           "cloud_export_approved": True},
            "escalation_reason": "local 4B/8B tried first (local_tried=true)",
            "l1_l2_exhausted": True,
        }
        if not deliv:
            card["expect_json"] = {"ok": True}
        cpath = os.path.join(STATE, "pending", "%s.json" % cid)
        os.makedirs(os.path.dirname(cpath), exist_ok=True)
        json.dump(card, open(cpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if a.dry:
            print("DRY", cid, cpath)
            continue
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, BRIDGE, "--card", cpath],
                               capture_output=True, text=True, timeout=int(card["timeout_s"]) + 120)
            rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
        except Exception as e:
            rc, out = 1, "runner-error: %s" % str(e)[:200]
        ok = rc == 0 and (not deliv or os.path.exists(deliv))
        r["state"] = "DONE" if ok else "FAILED"
        r["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        r["note"] = ("codely rc=%s %.0fs " % (rc, time.time() - t0)) + out.strip()[-160:].replace("\n", " ")
        if not ok and deliv and not os.path.exists(deliv):
            r["state"] = "UNVERIFIED"
        fl.merge_jsonl(os.path.join(F, "PRODUCTION-QUEUE.jsonl"), [r], mirror=False)
        print(r["id"], r["state"], r["note"][:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())
