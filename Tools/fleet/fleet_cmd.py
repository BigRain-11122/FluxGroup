#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_cmd.py - 主控命令面：随时对某台机、某张卡、某道工序下令。

CEO 2026-11-11：「主控要做到对每个机器和任务面了如指掌，随时可以给他们命令啊
修改啊什么的，但平常自动化靠机队自己。」

五个动词（默认 dry-run，加 --yes 才落盘）：
  card add|cancel|state   给某台机下单 / 撤卡 / 改状态
  station pause|resume    停/恢复一台机接活
  assign                  改某道工序由哪些工位承接
  proceed                 改派的优先级（写进卡）
  ledger                  看最近下过的命令

每条命令都写 command-ledger.jsonl（含人、原因、前后值），可追溯、可回滚。
落盘位置=分片/配置；机队按既有同步机制取，不需要主控去"推"。

用法：
  python3 Tools/fleet/fleet_cmd.py card add --station visual --product PROD-MV-SINGLE \\
      --stage mv-kf --task-type T-IMG-KF-FINAL --title "重跑 v716 第 12 镜" --why "首帧糊"
  python3 Tools/fleet/fleet_cmd.py station pause --station delivery --why "CEO 白天在用"
  python3 Tools/fleet/fleet_cmd.py assign --task-type T-ASM-SUB --stations visual,control
  python3 Tools/fleet/fleet_cmd.py ledger --tail 20
返回码：0 成功 / 1 参数或校验错 / 3 自检失败
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402

LEDGER = os.path.join("cph4", "fleet", "state", "command-ledger.jsonl")


def _path(name, root=None):
    return os.path.join(root or ROOT, "cph4", "fleet", name)


def _j(name, root=None):
    with open(_path(name, root), encoding="utf-8-sig") as f:
        return json.load(f)


def _w(name, obj, root=None):
    p = _path(name, root)
    tmp = p + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, p)


def log(cmd, row, root=None):
    p = os.path.join(root or ROOT, LEDGER)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    row = dict(row)
    row.update({"ts": datetime.now().isoformat(timespec="seconds"), "cmd": cmd})
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _card_id(station, product, stage):
    return "CMD-%s-%s-%s-%s" % (station, product, (stage or "").replace(" ", ""),
                                datetime.now().strftime("%Y%m%d%H%M"))


def card_add(a):
    tax = _j("TAXONOMY-v1.json", a.root)
    types = {t["id"]: t for t in tax["task_types"]}
    smap = (tax.get("stage_map") or {}).get(a.product) or {}
    tid = a.task_type or smap.get(a.stage)
    if not tid:
        return {"ok": False, "why": "没有 task_type：产品 %s 没有工序 %s 的映射" % (a.product, a.stage)}
    if tid not in types:
        return {"ok": False, "why": "task_type 不存在: %s" % tid}
    owners = types[tid].get("stations") or []
    if a.station not in owners:
        return {"ok": False, "why": "%s 不在承接方 %s 里（改派请用 assign）" % (a.station, owners or "无")}
    rows = ss.read_queue(a.station, a.root)
    if any(r.get("product_id") == a.product and r.get("stage") == a.stage
           and r.get("state") in ("OPEN", "RUNNING") for r in rows):
        return {"ok": False, "why": "同类卡已在飞，不重复下单（先去重）"}
    card = {"id": _card_id(a.station, a.product, a.stage), "title": a.title or "[cmd] %s·%s" % (a.product, a.stage),
            "product_id": a.product, "stage": a.stage, "task_type": tid,
            "station": a.station, "nodes": [a.station], "state": "OPEN", "owner": None,
            "created_by": "fleet_cmd", "created_at": datetime.now().isoformat(timespec="seconds"),
            "why": a.why or "", "prio": a.prio, "needs": "cpu",
            "deliverable": a.deliverable or "", "judge": types[tid].get("judge"),
            "accept": "判据见 task_type=%s" % tid}
    if a.cmd:
        card["cmd"] = a.cmd
    if not a.yes:
        return {"ok": True, "dry": True, "would_add": card}
    ss.upsert(a.station, card, a.root)
    log("card:add", {"station": a.station, "id": card["id"], "product": a.product,
                     "stage": a.stage, "task_type": tid, "why": a.why}, a.root)
    return {"ok": True, "added": card["id"]}


def card_cancel(a):
    rows = ss.read_queue(a.station, a.root)
    hit = [r for r in rows if r.get("id") == a.id]
    if not hit:
        return {"ok": False, "why": "卡不存在: %s" % a.id}
    before = hit[0].get("state")
    if before in ("DONE", "CANCELLED"):
        return {"ok": False, "why": "卡已终结（%s），不重复撤" % before}
    if not a.why:
        return {"ok": False, "why": "撤卡必须写原因（不许无原因作废）"}
    if not a.yes:
        return {"ok": True, "dry": True, "would_cancel": a.id, "from": before}
    row = dict(hit[0])
    row.update({"state": "CANCELLED", "cancel_reason": a.why,
                "finished_at": datetime.now().isoformat(timespec="seconds")})
    ss.upsert(a.station, row, a.root)
    log("card:cancel", {"station": a.station, "id": a.id, "from": before, "why": a.why}, a.root)
    return {"ok": True, "cancelled": a.id, "from": before}


def card_state(a):
    rows = ss.read_queue(a.station, a.root)
    hit = [r for r in rows if r.get("id") == a.id]
    if not hit:
        return {"ok": False, "why": "卡不存在: %s" % a.id}
    if a.state not in ("OPEN", "RUNNING", "BLOCKED", "FAILED", "PENDING_HUMAN", "SHELVED"):
        return {"ok": False, "why": "不接受的状态: %s" % a.state}
    if not a.yes:
        return {"ok": True, "dry": True, "would_set": a.state, "current": hit[0].get("state")}
    row = dict(hit[0])
    row.update({"state": a.state, "note": (a.why or "")[:200]})
    ss.upsert(a.station, row, a.root)
    log("card:state", {"station": a.station, "id": a.id, "state": a.state, "why": a.why}, a.root)
    return {"ok": True, "id": a.id, "state": a.state}


def station_set(a):
    d = _j("STATIONS.json", a.root)
    tgt = [s for s in d["stations"] if s["id"] == a.station]
    if not tgt:
        return {"ok": False, "why": "工位不存在: %s" % a.station}
    s = tgt[0]
    before = s.get("status")
    new = "paused_by_ceo" if a.action == "pause" else "ready_paused"
    if not a.why:
        return {"ok": False, "why": "停/恢复必须写原因"}
    if not a.yes:
        return {"ok": True, "dry": True, "would_set": new, "current": before}
    s["status"] = new
    s["status_note"] = "%s（%s）" % (a.why, datetime.now().strftime("%Y-%m-%d %H:%M"))
    _w("STATIONS.json", d, a.root)
    log("station:" + a.action, {"station": a.station, "from": before, "to": new,
                                "why": a.why}, a.root)
    return {"ok": True, "station": a.station, "from": before, "to": new}


def assign(a):
    d = _j("TAXONOMY-v1.json", a.root)
    tgt = [t for t in d["task_types"] if t["id"] == a.task_type]
    if not tgt:
        return {"ok": False, "why": "任务类型不存在: %s" % a.task_type}
    want = [x.strip() for x in (a.stations or "").split(",") if x.strip()]
    bad = [x for x in want if x not in ss.STATIONS]
    if bad:
        return {"ok": False, "why": "未知工位: %s" % bad}
    t = tgt[0]
    before = list(t.get("stations") or [])
    if not a.yes:
        return {"ok": True, "dry": True, "task_type": a.task_type,
                "from": before, "to": want}
    t["stations"] = want
    _w("TAXONOMY-v1.json", d, a.root)
    log("assign", {"task_type": a.task_type, "from": before, "to": want,
                   "why": getattr(a, "why", "")}, a.root)
    return {"ok": True, "task_type": a.task_type, "from": before, "to": want}


def ledger_show(a):
    p = os.path.join(a.root or ROOT, LEDGER)
    if not os.path.exists(p):
        print("（还没有命令记录）")
        return 0
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()][-a.tail:]
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    return 0


def self_test():
    import tempfile
    ok = total = 0

    def chk(n, c):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s" % ("ok  " if c else "FAIL", n))

    with tempfile.TemporaryDirectory() as td:
        b = os.path.join(td, "cph4", "fleet")
        os.makedirs(os.path.join(b, "rt", "visual"))
        os.makedirs(os.path.join(b, "state"))
        json.dump({"stations": [{"id": "visual", "machine": "传家宝", "status": "ready"},
                                {"id": "control", "machine": "MacBook", "status": "ready"}]},
                  open(os.path.join(b, "STATIONS.json"), "w"))
        json.dump({"task_types": [{"id": "T-A", "stations": ["visual"], "judge": "path"},
                                  {"id": "T-B", "stations": ["visual"]}],
                   "stage_map": {"P": {"s1": "T-A", "s2": "T-B"}}},
                  open(os.path.join(b, "TAXONOMY-v1.json"), "w"))

        class A:
            pass

        a = A(); a.root = td; a.station = "visual"; a.product = "P"; a.stage = "s1"
        a.task_type = ""; a.title = "t"; a.why = "w"; a.prio = "P2"; a.deliverable = "out/x"
        a.cmd = "true"; a.yes = False
        r = card_add(a)
        chk("dry-run 不落盘", r.get("dry") is True and ss.read_queue("visual", td) == [])
        a.yes = True
        r = card_add(a)
        chk("落盘后队列有卡且带 task_type",
            r.get("ok") and ss.read_queue("visual", td)[0]["task_type"] == "T-A")
        r2 = card_add(a)
        chk("同类卡在飞时拒绝重复下单", r2.get("ok") is False)

        a.station = "control"
        chk("非承接工位不许硬塞", card_add(a).get("ok") is False)
        a.station = "visual"

        a.id = ss.read_queue("visual", td)[0]["id"]; a.why = ""
        chk("撤卡必须写原因", card_cancel(a).get("ok") is False)
        a.why = "改派"; a.yes = False
        chk("撤卡 dry-run", card_cancel(a).get("dry") is True)
        a.yes = True
        chk("撤卡落盘为 CANCELLED", card_cancel(a).get("ok") and
            ss.read_queue("visual", td)[0]["state"] == "CANCELLED")

        a.id = ss.read_queue("visual", td)[0]["id"]; a.state = "OPEN"; a.why = "复用"
        chk("改状态生效", card_state(a).get("ok") and
            ss.read_queue("visual", td)[0]["state"] == "OPEN")

        a.action = "pause"; a.why = "CEO 在用"; a.yes = False
        chk("停机 dry-run", station_set(a).get("dry") is True)
        a.yes = True
        station_set(a)
        chk("停机写入 paused_by_ceo",
            [s for s in _j("STATIONS.json", td)["stations"] if s["id"] == "visual"][0]["status"]
            == "paused_by_ceo")
        a.action = "resume"; a.why = "恢复"
        station_set(a)
        chk("恢复写入 ready_paused",
            [s for s in _j("STATIONS.json", td)["stations"] if s["id"] == "visual"][0]["status"]
            == "ready_paused")

        a.task_type = "T-B"; a.stations = "visual,control"; a.yes = True
        assign(a)
        chk("改承接方生效",
            [t for t in _j("TAXONOMY-v1.json", td)["task_types"] if t["id"] == "T-B"][0]["stations"]
            == ["visual", "control"])
        a.stations = "nope"
        chk("未知工位被拒", assign(a).get("ok") is False)

        p = os.path.join(td, LEDGER)
        chk("命令台账有记录", os.path.exists(p) and len(open(p).readlines()) >= 3)

    print("[fleet_cmd] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--yes", action="store_true")
    sub = ap.add_subparsers(dest="verb")

    c = sub.add_parser("card").add_subparsers(dest="op", required=True)
    ca = c.add_parser("add"); ca.add_argument("--station", required=True)
    ca.add_argument("--product", required=True); ca.add_argument("--stage", required=True)
    ca.add_argument("--task-type", default=""); ca.add_argument("--title", default="")
    ca.add_argument("--why", default=""); ca.add_argument("--prio", default="P2")
    ca.add_argument("--cmd", default=""); ca.add_argument("--deliverable", default="")
    cc = c.add_parser("cancel"); cc.add_argument("--station", required=True)
    cc.add_argument("--id", required=True); cc.add_argument("--why", default="")
    cs = c.add_parser("state"); cs.add_argument("--station", required=True)
    cs.add_argument("--id", required=True); cs.add_argument("--state", required=True)
    cs.add_argument("--why", default="")

    st = sub.add_parser("station"); st.add_argument("action", choices=["pause", "resume"])
    st.add_argument("--station", required=True); st.add_argument("--why", default="")

    ag = sub.add_parser("assign"); ag.add_argument("--task-type", required=True)
    ag.add_argument("--stations", default="")

    lg = sub.add_parser("ledger"); lg.add_argument("--tail", type=int, default=20)

    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.verb:
        ap.error("需要一个动词：card / station / assign / ledger")

    if a.verb == "ledger":
        return ledger_show(a)
    if a.verb == "card":
        fn = {"add": card_add, "cancel": card_cancel, "state": card_state}[a.op]
    elif a.verb == "station":
        fn = station_set
    else:
        fn = assign
    r = fn(a)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
