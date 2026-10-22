# -*- coding: utf-8 -*-
"""director.py —— 导演介入权（SOP §十二）

四权：
  hold     叫停任意工单（任何状态 → HOLD）
  release  解除叫停（HOLD → READY）
  art      艺术判定（S/A/B/C + 理由）；C 档可直接否决技术 PASS
  note     纯记录（不改变状态）

边界（不可越过）：
  - 不能改硬指标（响度/时长/孤岛/非计划硬跳）
  - 不能自己签复核席（双签仍需 S/C/E/G/T 对应席位）
  - 每次介入必须给理由，写进 DIRECTOR-LOG.jsonl
"""
import argparse, json, os, sys, datetime

WO = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\WORK-ORDERS.jsonl"
DL = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\DIRECTOR-LOG.jsonl"


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def save(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def addlog(kind, tid, payload):
    rows = load(DL)
    rows.append({"ts": now(), "kind": kind, "id": tid, **payload})
    save(DL, rows)


def find(rows, tid):
    for r in rows:
        if r["id"] == tid:
            return r
    return None


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("hold"); p.add_argument("--id", required=True); p.add_argument("--reason", required=True)
    p = sub.add_parser("release"); p.add_argument("--id", required=True); p.add_argument("--reason", required=True)
    p = sub.add_parser("art"); p.add_argument("--id", required=True); p.add_argument("--tier", required=True,
                                                                                    choices=["S", "A", "B", "C"])
    p.add_argument("--reason", required=True); p.add_argument("--veto", action="store_true",
                                                              help="C 档否决技术 PASS，打回 READY")
    p = sub.add_parser("note"); p.add_argument("--id", required=True); p.add_argument("--text", required=True)
    a = ap.parse_args()

    rows = load(WO)
    r = find(rows, a.id) or sys.exit("工单不存在: %s" % a.id)

    if a.cmd == "hold":
        r["prev"] = r["state"]
        r["state"] = "HOLD"
        r["history"].append({"ts": now(), "to": "HOLD", "reason": a.reason, "by": "D"})
        save(WO, rows)
        addlog("hold", a.id, {"reason": a.reason, "from": r["prev"]})
        print("HOLD", a.id, "(was", r["prev"], ")")

    elif a.cmd == "release":
        if r["state"] != "HOLD":
            sys.exit("只有 HOLD 可解除（当前 %s）" % r["state"])
        r["state"] = "READY"
        r["history"].append({"ts": now(), "to": "READY", "reason": a.reason, "by": "D"})
        save(WO, rows)
        addlog("release", a.id, {"reason": a.reason})
        print("RELEASED", a.id, "-> READY")

    elif a.cmd == "art":
        addlog("art", a.id, {"tier": a.tier, "reason": a.reason, "veto": bool(a.veto)})
        print("ART", a.id, a.tier, "veto" if a.veto else "")
        if a.tier == "C" and a.veto:
            if r["state"] == "PASS":
                r["state"] = "READY"
                r["history"].append({"ts": now(), "to": "READY", "reason": "导演艺术否决: " + a.reason, "by": "D"})
                save(WO, rows)
                print("VETOED", a.id, "PASS -> READY")
            else:
                print("注意：当前状态 %s，未执行否决（只适用于 PASS）" % r["state"])

    elif a.cmd == "note":
        addlog("note", a.id, {"text": a.text})
        print("NOTE", a.id)


if __name__ == "__main__":
    main()