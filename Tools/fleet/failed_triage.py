#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""failed_triage.py - 失败卡定性：按回执 rc 归类，缺输入的销卡，别让它们每轮重排。

为什么（2026-11-04 实测）：队列里有 21 张 FAILED 卡，error_class 全空——于是
master_solver 只能"再试一次"，必然再失败；其中一批是空投料（rc=3 E-BLOCKED-INPUT），
正确处置是 CANCELLED 并写原因，等投料后再由工序表重出卡。

规则（只认回执事实，不猜）：
  rc=3 / E-BLOCKED-INPUT / E-INPUT   → CANCELLED（等投料，写 cancel_reason）
  rc=127 / 9009 / E-PATH             → 保留 FAILED 并标 E-ENV（环境/解释器问题，改机不重试）
  rc=2 / E-CONTRACT                  → 保留 FAILED 并标 E-CONTRACT（要改卡）
  其它                                → 标 E-UNKNOWN 并保留（交人判）
Exit: 0 全部已定性；2 仍有无法定性的卡
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

FLEET = os.path.join(ROOT, "cph4", "fleet")
QC = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
QB = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
RCPT = os.path.join(FLEET, "queue-receipts")
OUT = os.path.join(FLEET, "state", "failed-triage.json")


def receipts():
    idx = {}
    if not os.path.isdir(RCPT):
        return idx
    for f in os.listdir(RCPT):
        if not f.endswith(".json"):
            continue
        try:
            j = json.load(open(os.path.join(RCPT, f), encoding="utf-8-sig"))
        except Exception:
            continue
        if not isinstance(j, dict):
            continue
        k = j.get("id")
        if k:
            idx.setdefault(k, []).append(j)
    return idx


def classify(card, rcpt):
    rc = rcpt.get("rc")
    ec = str(rcpt.get("error_class") or "")
    if rc == 3 or "E-BLOCKED-INPUT" in ec or "E-INPUT" in ec:
        return "CANCEL-NO-INPUT", ("rc=3 缺输入（%s）" % (rcpt.get("stdout_tail") or "")[:80])
    if rc in (127, 9009) or "E-PATH" in ec:
        return "KEEP-ENV", "rc=%s 执行环境缺解释器/路径" % rc
    if rc == 2 or "E-CONTRACT" in ec:
        return "KEEP-CONTRACT", "rc=2 契约不符，要改卡"
    return "KEEP-UNKNOWN", "rc=%s 未归类" % rc


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    idx = receipts()
    now = datetime.now().isoformat(timespec="seconds")
    stats, patch_q, patch_b, unknown = {}, [], [], []
    for path, patch in ((QC, patch_q), (QB, patch_b)):
        rows = fl.read_jsonl(path) if os.path.exists(path) else []
        for r in rows:
            if str(r.get("state")).upper() != "FAILED":
                continue
            rs = sorted(idx.get(r.get("id")) or [],
                        key=lambda x: str(x.get("ts") or ""), reverse=True)
            if not rs:
                unknown.append({"id": r.get("id"), "why": "没有回执，无法定性"})
                stats["NO-RECEIPT"] = stats.get("NO-RECEIPT", 0) + 1
                continue
            verdict, why = classify(r, rs[0])
            stats[verdict] = stats.get(verdict, 0) + 1
            nr = dict(r)
            nr["triage"] = verdict
            nr["triage_why"] = why
            nr["triage_at"] = now
            if verdict == "CANCEL-NO-INPUT":
                nr["state"] = "CANCELLED"
                nr["cancel_reason"] = "空投料销卡：" + why
            else:
                nr["error_class"] = {"KEEP-ENV": "E-PATH", "KEEP-CONTRACT": "E-CONTRACT",
                                     "KEEP-UNKNOWN": "E-UNKNOWN"}[verdict]
            patch.append(nr)
    if a.apply and patch_q:
        fl.merge_jsonl(QC, patch_q)
    if a.apply and patch_b:
        fl.merge_jsonl(QB, patch_b)
    state = {"ts": now, "stats": stats, "undecidable": unknown,
             "applied": bool(a.apply)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(state, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[failed-triage] %s%s" % (json.dumps(stats, ensure_ascii=False),
                                    "" if a.apply else " (dry)"))
    for u in unknown[:6]:
        print("  ? %s: %s" % (u["id"], u["why"]))
    return 2 if unknown else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))