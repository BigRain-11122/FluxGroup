# -*- coding: utf-8 -*-
"""woticket.py —— 工单状态机（SOP §三）

状态: NEW → READY → IN_PROGRESS → QA → PASS → BURNED
                        ↘ FAIL → READY
任意 → BLOCKED

用法:
  python woticket.py new     --id R6_water_reflection --kind shot --title "水面无脸倒影" --station S3
  python woticket.py move    --id R6_water_reflection --to READY
  python woticket.py move    --id R6_water_reflection --to IN_PROGRESS --owner A
  python woticket.py fail    --id R6_water_reflection --reason "倒影出现人脸" --station S2
  python woticket.py list    [--state READY]
"""
import argparse, json, os, sys, datetime

LEDGER = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\WORK-ORDERS.jsonl"
LEGAL = {
    "NEW": {"READY", "BLOCKED"},
    "READY": {"IN_PROGRESS", "BLOCKED"},
    "IN_PROGRESS": {"QA", "FAIL", "BLOCKED"},
    "QA": {"PASS", "FAIL"},
    "FAIL": {"READY", "BLOCKED"},
    "PASS": {"BURNED"},
    "BURNED": set(),
    "BLOCKED": {"READY"},
}
WIP = {"IN_PROGRESS": 2, "QA": 6}


def load():
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def save_all(rows):
    with open(LEDGER, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def find(rows, tid):
    for r in rows:
        if r["id"] == tid:
            return r
    return None


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def cmd_new(a, rows):
    if find(rows, a.id):
        sys.exit("工单已存在: %s" % a.id)
    rows.append({"id": a.id, "kind": a.kind, "title": a.title, "station": a.station,
                 "state": "NEW", "owner": "", "history": [{"ts": now(), "to": "NEW"}]})
    save_all(rows)
    print("CREATED", a.id)


def cmd_move(a, rows):
    r = find(rows, a.id) or sys.exit("工单不存在: %s" % a.id)
    to = a.to.upper()
    if to not in LEGAL[r["state"]]:
        sys.exit("非法迁移: %s → %s（允许: %s）" % (r["state"], to, sorted(LEGAL[r["state"]])))
    cnt = sum(1 for x in rows if x["state"] == to)
    if to in WIP and cnt >= WIP[to]:
        sys.exit("WIP 超限: %s 已有 %d 张（上限 %d）" % (to, cnt, WIP[to]))
    r["state"] = to
    if a.owner:
        r["owner"] = a.owner
    r["history"].append({"ts": now(), "to": to, **({"owner": a.owner} if a.owner else {})})
    save_all(rows)
    print("MOVED", a.id, "->", to)


def cmd_fail(a, rows):
    r = find(rows, a.id) or sys.exit("工单不存在: %s" % a.id)
    if r["state"] not in ("IN_PROGRESS", "QA"):
        sys.exit("只有 IN_PROGRESS/QA 可判 FAIL（当前 %s）" % r["state"])
    if not a.reason or not a.station:
        sys.exit("FAIL 必须给 --reason 与 --station")
    r["state"] = "FAIL"
    r["history"].append({"ts": now(), "to": "FAIL", "reason": a.reason, "station": a.station})
    save_all(rows)
    print("FAILED", a.id, "-> 打回", a.station)


def cmd_list(a, rows):
    for r in rows:
        if a.state and r["state"] != a.state.upper():
            continue
        print("%-28s %-10s %-4s %s" % (r["id"], r["state"], r["station"], r["title"]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new"); p.add_argument("--id", required=True); p.add_argument("--kind", default="shot")
    p.add_argument("--title", required=True); p.add_argument("--station", required=True)
    p = sub.add_parser("move"); p.add_argument("--id", required=True); p.add_argument("--to", required=True)
    p.add_argument("--owner", default="")
    p = sub.add_parser("fail"); p.add_argument("--id", required=True); p.add_argument("--reason", required=True)
    p.add_argument("--station", required=True)
    p = sub.add_parser("list"); p.add_argument("--state", default="")
    a = ap.parse_args()
    rows = load()
    {"new": cmd_new, "move": cmd_move, "fail": cmd_fail, "list": cmd_list}[a.cmd](a, rows)


if __name__ == "__main__":
    main()