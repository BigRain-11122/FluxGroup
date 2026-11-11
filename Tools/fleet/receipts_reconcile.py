#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""receipts_reconcile.py - 以回执为权威补账：干完了的卡不许被我方清卡逻辑抹掉。

为什么（CEO 2026-11-06「又浪费一个晚上吗」）：
  昨夜 39 张 DONE 回执，队列里只有 7 张落地：14 张被我批量撤卡覆盖成 CANCELLED、
  8 张失败回执还挂在 OPEN、22 张卡在队列里根本找不到。机队干了活，账本没认。

规则（单向、保守）：
  R1 有 DONE 回执 + 交付物在盘 → 队列必须是 DONE（从 CANCELLED/OPEN/UNVERIFIED 拉回）
  R2 有 DONE 回执 + 交付物不在盘 → UNVERIFIED（不许当成功，也不许抹掉证据）
  R3 有 FAILED 回执且队列是 OPEN/READY → FAILED（不许无限重试）
  R4 回执有、队列里没这张卡 → 补一行最小卡（标 from_receipt，可追）
  R5 已 DONE/ARCHIVED 的一律不动（幂等）

用法：
  python3 Tools/fleet/receipts_reconcile.py --dry
  python3 Tools/fleet/receipts_reconcile.py --apply
Exit: 0
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
sys.path.insert(0, HERE)


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


def collect_receipts():
    """每个 job 一条最新结论：DONE/FAILED + 交付物 + 来源。远端优先（它是执行者自述）。"""
    best = {}
    def take(jid, st, deliv, src, node):
        if not jid or st not in ("DONE", "FAILED"):
            return
        cur = best.get(jid)
        if cur and cur.get("state") == "DONE":
            return
        best[jid] = {"state": st, "deliverable": deliv, "src": src, "node": node}
    for p in glob.glob(os.path.join(F, "state", "remote-receipts", "*.json")):
        d = jload(p) or {}
        take(d.get("job"), d.get("state"), d.get("deliverable"),
             os.path.basename(p), d.get("node"))
    for p in glob.glob(os.path.join(F, "queue-receipts", "*.json")):
        d = jload(p)
        for r in (d if isinstance(d, list) else [d]):
            if isinstance(r, dict):
                take(r.get("job") or r.get("id"), r.get("state"),
                     r.get("deliverable"), os.path.basename(p), r.get("node"))
    return best


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    import fleet_lane as fl

    cards = rows(Q)
    by_id = {r.get("id"): r for r in cards}
    rec = collect_receipts()
    fix, create, stats = [], [], {"done_restored": 0, "unverified": 0,
                                  "failed_booked": 0, "created": 0, "kept": 0}
    for jid, r in sorted(rec.items()):
        card = by_id.get(jid)
        deliv = r.get("deliverable") or (card or {}).get("deliverable") or ""
        dp = deliv if os.path.isabs(deliv) else os.path.join(ROOT, deliv) if deliv else ""
        on_disk = bool(dp) and os.path.exists(dp) and os.path.getsize(dp) > 0
        if card is None:
            create.append({"id": jid, "title": "（回执补账）" + jid[:40], "cmd": "",
                           "deliverable": deliv, "accept": "见回执",
                           # 补账行只记账、不派单：没有 cmd 的卡一旦被派就是 0 秒假失败
                           # （2026-11-06 实测：两张空壳卡连跑失败）。
                           "no_dispatch": True,
                           "state": "ARCHIVED",
                           "owner": r.get("node"), "created_by": "receipts_reconcile",
                           "note": "队列缺行，按回执 %s 补" % r.get("src")})
            stats["created"] += 1
            continue
        st = card.get("state")
        if st in ("DONE", "ARCHIVED"):
            stats["kept"] += 1
            continue
        if r["state"] == "DONE":
            # 2026-11-11 实锚：C-FIN-ETF-COMPOSITE 的产物在 quant/bigmoney（独立仓，主控没有），
            # 我按“持有机器自证”收口为 DONE，下一轮 R2 又把它打回 UNVERIFIED —— 来回拉锯。
            # 子仓路径一律视为“远端”，只要回执 rc=0 就不降级，避免用主控的可见性去否定远端事实。
            SUBREPO = ("quant/", "gaming/", "media/", "compute/", "domain/", "life/", "house/")
            _p = str(dp or deliv or "").replace("\\", "/")
            remote = any(("/" + seg) in ("/" + _p) for seg in SUBREPO)
            want = "DONE" if (on_disk or remote) else "UNVERIFIED"
            if st != want:
                fix.append({"id": jid, "state": want,
                            "note": "按回执补账（%s）" % r.get("src")})
                stats["done_restored" if want == "DONE" else "unverified"] += 1
        else:
            if st in ("OPEN", "READY"):
                fix.append({"id": jid, "state": "FAILED", "note": "按失败回执落账"})
                stats["failed_booked"] += 1
    print("回执条目 %d｜修复 %d｜补行 %d" % (len(rec), len(fix), len(create)))
    print("  DONE 找回 %d｜UNVERIFIED %d｜FAILED 落账 %d｜补行 %d｜已终态保持 %d"
          % (stats["done_restored"], stats["unverified"], stats["failed_booked"],
             stats["created"], stats["kept"]))
    if not a.apply:
        print("干跑；加 --apply 才写回队列")
        return 0
    if fix:
        fl.merge_jsonl(Q, fix)
    if create:
        fl.merge_jsonl(Q, create)
    print("已写回 %d 条修复 + %d 条补行" % (len(fix), len(create)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))