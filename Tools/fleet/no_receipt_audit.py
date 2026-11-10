#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""no_receipt_audit.py - 给「跑完没回执」的卡补一条诊断回执，让这类失败可被看见。

为什么（2026-11-10 实锚）：bm-a/bm-b 上有卡被领走后既无产物也无回执，主控只能看到
state=FAILED + error_class 空，root-cause 无从判起；同样的形态一晚上出现 6 次，
每次都靠人回忆「那台机当时是不是卡住了」。回执是唯一能把「谁、哪台、多久、为什么」
固定下来的东西——没有回执的失败等于没发生，只会被下一轮重派掩盖。

本工具只做一件事：对 FAILED/UNVERIFIED 且 24h 内没有回执的卡，写一条
`<id>-<node>-noreceipt.json`，error_class=E-NO-RECEIPT，并列出分布（按节点/按 cmd 首词），
让人第一眼看到「不是卡写错，是那台机没交付」。

用法：python3 Tools/fleet/no_receipt_audit.py [--apply] [--json]
Exit: 0 无缺口 / 2 有缺口（--apply 时已补诊断回执）
"""
import argparse
import glob
import json
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
R = os.path.join(F, "queue-receipts")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ignore-write-suspect", action="store_true",
                    help="跳过写链路已可疑的节点（由 L4/node_write_health 判定），避免同一根因报两遍")
    a = ap.parse_args(argv)
    rows = []
    for ln in open(Q, encoding="utf-8"):
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass
    now = time.time()
    holes = []
    for r in rows:
        if str(r.get("state")).upper() not in ("FAILED", "UNVERIFIED"):
            continue
        jid = r.get("id")
        if not jid:
            continue
        # 自己写的占位回执不算"有回执"，否则补完一次就永远绿了（假绿）
        real = [x for x in glob.glob(os.path.join(R, "%s-*.json" % jid))
                if not x.endswith("-noreceipt.json")]
        if real:
            continue
        fin = r.get("finished_at") or ""
        try:
            from datetime import datetime
            age = now - datetime.fromisoformat(fin.replace("Z", "")).timestamp()
        except Exception:
            age = 0
        if age and age > 86400:
            continue
        holes.append({"id": jid, "owner": r.get("owner"), "state": r.get("state"),
                      "cmd": (r.get("cmd") or "")[:60], "age_h": round((age or 0) / 3600, 1)})
    if a.ignore_write_suspect:
        try:
            wh = json.load(open(os.path.join(F, "state", "write-health.json"), encoding="utf-8"))
            sus = set(wh.get("suspect") or [])
        except Exception:
            sus = set()
        if sus:
            before = len(holes)
            holes = [h for h in holes if (h.get("owner") or "") not in sus]
            if before != len(holes) and not a.json:
                print("[no-receipt] 跳过写链路可疑节点 %s 的 %d 张（L4 已单独报）"
                      % (sorted(sus), before - len(holes)))
    by_node = Counter(h["owner"] or "?" for h in holes)
    by_verb = Counter((h["cmd"].split() or ["?"])[0] for h in holes)
    if a.apply:
        for h in holes:
            p = os.path.join(R, "%s-%s-noreceipt.json" % (h["id"], h["owner"] or "unknown"))
            json.dump({"id": h["id"], "node": h["owner"], "rc": None, "seconds": None,
                       "outcome": "NO-RECEIPT", "error_class": "E-NO-RECEIPT",
                       "note": ("该卡被领取后既无产物也无回执；按节点集中出现=那台机的 lane 交付链路坏了"
                                "（不是卡写错）。处置：重启该机 HQ-ProductionClaim 后再派。"),
                       "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
                      open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps({"holes": len(holes), "by_node": by_node, "by_verb": by_verb,
                          "items": holes}, ensure_ascii=False))
    else:
        print("[no-receipt] 无回执的失败卡 %d 张 · 按节点 %s · 按命令 %s"
              % (len(holes), dict(by_node), dict(by_verb)))
        for h in holes[:8]:
            print("  %-36s %-6s %s" % (h["id"], h["owner"], h["cmd"]))
    return 0 if not holes else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
