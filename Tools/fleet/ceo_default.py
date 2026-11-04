#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ceo_default.py - 待裁件默认推进：不许因为等 CEO 停工。

为什么（2026-11-04 主控职责面 mc-ceo 实测）：
  BUSINESS-MAP 里 4 条 STALLED 线全是 CEO / EXTERNAL 卡点，而 next_actions 只写
  「CEO: —」就结束——等于把整条线挂起等一个人。CEO 最高规则是反过来的：
  默认自动放行、事后复核，只有「不可逆 / 对外发布 / 花钱」三类才真的留给人。

它给每件待裁件三样东西：
  1) 一句话问句（要 CEO 决定的到底是什么）；
  2) 机队现在就能做的准备件（不对外、不花钱，立刻算"已推进"）；
  3) 到期时间：方向类到 48h 未裁即按默认继续；对外类永不自动执行，但草稿照做。

判据可核验：每件都有 due_at、gate、prep（准备件）三条字段；到期未裁的会进
「已按默认继续」区，而不是继续躺在「等」里。

用法：
  python3 Tools/fleet/ceo_default.py            # 一屏 + state/ceo-queue.json
  python3 Tools/fleet/ceo_default.py --json
Exit: 0 无需 CEO；2 仍有到期未裁且属对外/不可逆门的项（可见欠账）
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

FLEET = os.path.join(ROOT, "cph4", "fleet")
BM = os.path.join(FLEET, "BUSINESS-MAP-v1.json")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
OUT = os.path.join(FLEET, "state", "ceo-queue.json")
MD = os.path.join(FLEET, "CEO-QUEUE.md")

DUE_H = 48
# 三类硬门：永不自动执行，签名权在 CEO（其余类别到期按默认继续）
HARD_GATES = ("对外", "花钱", "不可逆")
MONEY_WORDS = ("采购", "报价", "预算", "费用", "成本", "下单", "付款", "充值")
LIVE = ("RUNNING", "CLAIMED", "OPEN", "READY")


def classify(biz):
    bt = (biz.get("blocker_type") or "").upper()
    text = "%s %s" % (biz.get("blocker") or "", biz.get("next_product") or "")
    if bt == "EXTERNAL":
        return "对外"
    if any(w in text for w in MONEY_WORDS):
        return "花钱"
    return "方向"


def live(line_id):
    for p in (QUEUE, BACKLOG):
        if not os.path.exists(p):
            continue
        for r in fl.read_jsonl(p):
            if r.get("line") == line_id and str(r.get("state")).upper() in LIVE:
                return r
    return None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    bm = json.load(open(BM, encoding="utf-8")).get("businesses") or []
    old = {}
    if os.path.exists(OUT):
        try:
            for it in json.load(open(OUT, encoding="utf-8")).get("items", []):
                old[it.get("line")] = it
        except Exception:
            old = {}

    now = datetime.now()
    items, need_ceo = [], 0
    for b in bm:
        bt = (b.get("blocker_type") or "").upper()
        if bt not in ("CEO", "EXTERNAL"):
            continue
        lid = b.get("id")
        c = live(lid)
        prev = old.get(lid) or {}
        first = prev.get("first_seen") or now.isoformat(timespec="seconds")
        due = datetime.fromisoformat(first) + timedelta(hours=DUE_H)
        gate = classify(b)
        overdue = now > due
        # 准备件必须真的"机队能自己干"：硬门（对外/花钱/不可逆）下不能把 CEO 的动作
        # 抄成准备件（实测首版把「OEM 材料送出（需 CEO 渠道）」写成了机队先做，自相矛盾）。
        if gate == "对外":
            prep = "把对外件做成待签草稿（一页摘要+附件清单），不发送、不代署名"
        elif gate == "花钱":
            prep = "只做报价/成本测算材料，不下单、不付款、不对外承诺价格"
        elif gate == "不可逆":
            prep = "只做影响面与回滚方案，不执行任何不可逆动作"
        else:
            prep = "机队先做不依赖该决定的部分：%s（不对外、不花钱）" % (
                b.get("next_product") or "备料与预研")
        item = {
            "line": lid, "name": b.get("name"), "prio": b.get("prio"),
            "gate": gate, "blocker_type": bt,
            "ask": "「%s」下一步=%s；卡在：%s —— 是否放行？"
                   % (b.get("name"), b.get("next_product"), (b.get("blocker") or "")[:80]),
            "prep": prep,
            "accept": b.get("accept"),
            "owner": b.get("owner"),
            "first_seen": first,
            "due_at": due.isoformat(timespec="seconds"),
            "overdue": overdue,
            "live_card": (c or {}).get("id"),
            "mode": ("DEFAULT-ACTIVATED" if (overdue and gate not in HARD_GATES)
                     else ("CEO-ONLY" if gate in HARD_GATES else "WAIT-DUE")),
        }
        if c:
            item["mode"] = "RUNNING"
            item["prep"] = "已有卡 %s(%s) 在跑，不需要另起" % (c.get("id"), c.get("state"))
        if item["mode"] == "CEO-ONLY" and overdue:
            need_ceo += 1
        items.append(item)

    items.sort(key=lambda x: (0 if x["mode"] in ("CEO-ONLY", "DEFAULT-ACTIVATED") else 1,
                              x["due_at"]))
    state = {"ts": now.isoformat(timespec="seconds"), "due_h": DUE_H,
             "count": len(items), "need_ceo": need_ceo,
             "default_activated": len([i for i in items if i["mode"] == "DEFAULT-ACTIVATED"]),
             "items": items}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)

    lines = ["# 待 CEO 裁决件（ceo-queue）%s" % now.strftime("%Y-%m-%d %H:%M"), "",
             "共 %d 件：按默认继续 %d · 仅 CEO %d · 到期时限 %dh" %
             (len(items), state["default_activated"], need_ceo, DUE_H), ""]
    for it in items:
        lines.append("- [%s] %s（%s·%s）到期 %s" %
                     (it["mode"], it["name"], it["prio"], it["gate"], it["due_at"][:16]))
        lines.append("    问：%s" % it["ask"])
        lines.append("    机队先做：%s" % it["prep"])
        if it["live_card"]:
            lines.append("    在跑卡：%s" % it["live_card"])
    with open(MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(state, ensure_ascii=False))
    else:
        print("[ceo-queue] items=%d default-activated=%d ceo-only=%d"
              % (len(items), state["default_activated"], need_ceo))
        for it in items:
            print("  [%-16s] %-22s %-4s %s" % (it["mode"], it["name"][:20], it["gate"],
                                               it["due_at"][:16]))
    return 2 if need_ceo else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))