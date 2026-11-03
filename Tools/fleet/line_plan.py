#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""line_plan.py - 把"工序表"变成真生产卡（供给层缺的那一环）。

为什么（2026-11-03 实测）：机队整夜在跑，49 张卡里 33 张是自检、15 张是体检，
零成片零可玩——因为派单侧手里只有"扫这条线缺什么"这类只读活，没有工序。
工序表声明在 cph4/fleet/ri/<group>/lines/<line>.json：每段有 cmd / deliverable /
accept / 依赖 / 机器偏好。本工具按盘上事实推进：上一段的产物没出就不派下一段，
同一段当天只派一次。

它只写 BACKLOG（READY），由 night_fill / master_agent 照常提成 OPEN；
不直接写队列（守 I7 单写入口）。

用法：
  python3 line_plan.py [--dry] [--line bigstream-mv] [--json]
Exit: 0 正常（0 张也算正常，会说明原因），1 工序表读不了。
"""
import argparse
import glob
import json
import os
import sys
import time
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
TABLES = os.path.join(FLEET, "ri", "*", "lines", "*.json")

sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402
import market_brief as MB  # noqa: E402

ACTIVE = ("OPEN", "RUNNING", "READY", "DONE", "UNVERIFIED")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def rows(path):
    out = []
    try:
        for line in open(path, encoding="utf-8-sig"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    except FileNotFoundError:
        pass
    return out


def render(tpl, table, stage, day):
    root_tools = "Tools"
    return (str(tpl).replace("{root_tools}", root_tools)
            .replace("{master}", str(table.get("master") or ""))
            .replace("{date}", day)
            .replace("{stage}", str(stage.get("id"))))


def plan_table(table, day, existing, dry):
    line = table.get("line")
    stages = table.get("stages") or []
    made, skipped = [], []
    done_today = set()
    for st in stages:
        sid = "%s-%s-%s" % (line, st.get("id"), day)
        dl = render(st.get("deliverable") or "", table, st, day)
        dl_abs = dl if os.path.isabs(dl) else os.path.join(ROOT, dl)
        if st["id"] in done_today or (dl and os.path.exists(dl_abs)):
            done_today.add(st["id"])
        deps = st.get("depends_on") or []
        if deps and not all(d in done_today for d in deps):
            skipped.append((sid, "等上一段 " + ",".join(deps)))
            continue
        if sid in existing:
            skipped.append((sid, "已在队列(%s)" % existing[sid]))
            continue
        card = {
            "id": sid,
            "title": "[%s] %s" % (table.get("name") or line, st.get("name") or st["id"]),
            "cmd": render(st.get("cmd") or "", table, st, day),
            "cwd": "",
            "requires": [render(r, table, st, day) for r in (st.get("requires") or [])],
            "deliverable": dl,
            "accept": st.get("accept") or "",
            "needs": st.get("needs") or "cpu",
            "nodes": st.get("nodes") or [],
            "prio": table.get("priority") or "P1",
            "line": line,
            "day_ok": bool(st.get("day_ok", True)),
            "heavy": bool(st.get("heavy")),
            "verify_on_node": True,
            "ok_rc": st.get("ok_rc") or [0, 3],
            "minutes": st.get("minutes"),
            "why": "line_plan: 工序表 %s 段 %s（上一段产物已出）" % (line, st["id"]),
            "created_by": "line_plan",
            "created_at": fl.now_iso(),
            "state": "READY",
        }
        made.append(card)
        done_today.add(st["id"])
        break          # 一条线一次只推进一步，避免同线堆卡
    return made, skipped


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--line", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    day = date.today().isoformat()
    have = {}
    for r in rows(QUEUE) + rows(BACKLOG):
        if r.get("id"):
            have[r["id"]] = r.get("state")
    made, report = [], []
    files = sorted(glob.glob(TABLES))
    if not files:
        print("没有工序表：%s" % TABLES)
        return 1
    for p in files:
        t = jload(p)
        if not t:
            print("工序表读不了：%s" % p)
            return 1
        if a.line and t.get("line") != a.line:
            continue
        # 市场门（2026-11-03 CEO「务必有市场调研，不要产出垃圾」）：
        # 没有合格市场简报就不派生产卡——先调研再开工，不让机器拿体检充数。
        mk = MB.check(t.get("line"))
        if mk.get("verdict") != "PASS":
            report.append({"line": t.get("line"), "table": os.path.relpath(p, ROOT), "cards": [],
                           "skipped": [("MARKET-GATE", "; ".join(mk.get("gaps") or []))]})
            continue
        cards, skipped = plan_table(t, day, have, a.dry)
        made.extend(cards)
        report.append({"line": t.get("line"), "table": os.path.relpath(p, ROOT),
                       "cards": [c["id"] for c in cards],
                       "skipped": skipped[:6]})
    if made and not a.dry:
        fl.merge_jsonl(BACKLOG, made)
    if a.json:
        print(json.dumps({"ts": fl.now_iso(), "dry": a.dry, "made": made, "report": report},
                         ensure_ascii=False, indent=1))
        return 0
    print("工序推进 %s%s" % (day, "（dry）" if a.dry else ""))
    for r in report:
        print("  %-18s 新卡 %s" % (r["line"], ", ".join(r["cards"]) or "0"))
        for sid, why in r["skipped"]:
            print("      - 跳过 %s：%s" % (sid, why))
    print("合计 %d 张%s" % (len(made), "（已写 BACKLOG READY）" if made and not a.dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))