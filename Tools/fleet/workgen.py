#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""workgen.py - the missing "declare work" seat, made deterministic.

Root problem it fixes: the master never invents work ("every card must be declared
by a producing seat"), so an online box with an empty backlog simply idles forever.
Nothing in the fleet turned real disk state into declarations. This does, with
rules rather than opinions:

  R1 INVENTORY  every online node keeps >= FLOOR open cards; shortage is filled from
                that node's work-bank, then from the node's mechanical task table.
  R2 STALLED    a bank job claimed for > STALL_HOURS is reported (never silently
                closed - closing needs evidence).
  R3 STUBS      queue rows FAILED with no cmd are cancelled with a written reason.
  R4 UNBLOCK    a STALLED/BLOCKED business line whose next step is a mechanical tool
                gets one card on the seat that owns it (director read packet etc.).

Cards are appended to cph4/fleet/PRODUCTION-BACKLOG.jsonl (the master's source), so
the normal pulse promotes them into lanes/<node>.json. No LLM, no network, idempotent.

Usage:
  python Tools/fleet/workgen.py --root K:\\Fluxgroup\\FluxGroup [--dry]
"""
import argparse
import glob
import json
import os
import sys
import time
from datetime import datetime

FLOOR = 2
STALL_HOURS = 3
MAX_CARDS_PER_RUN = 4
ONLINE_MIN = 30  # lane ts fresher than this counts as an online box

# A machine that migrated its tree leaves cards pointing at a dead prefix. Left alone
# they look like declared work but can never pass the lane-side input check.
LEGACY_ROOTS = {
    "C:\\Users\\sjs20\\Desktop\\FluxGroup": "C:\\Fluxgroup\\FluxGroup",
    "C:/Users/sjs20/Desktop/FluxGroup": "C:/Fluxgroup/FluxGroup",
}

# Mechanical steps that are safe to declare without a human: (id, title, cmd, needs, prio, requires, why)
NODE_TASKS = {
    "bm-c": [
        ("KN-FILM-GATE-LATEST",
         "KN PACK-A 最新复核版跑全片闸（重复帧/亮度/时长三查）",
         "python cph4/fleet/mv-album-001-jay/kn_film_gate.py --film media/mv-album-001-jay/assembly-packA/KN-PACKA-CONFORM-v1-c2171.mp4 --tag gate-rerun",
         "cpu", "P2",
         ["cph4/fleet/mv-album-001-jay/kn_film_gate.py",
          "media/mv-album-001-jay/assembly-packA/KN-PACKA-CONFORM-v1-c2171.mp4"],
         "闸不重跑就没有签字依据；KN21 换 take 后必须重出 PASS/REDO 结论"),
        ("LINE-TRIAGE-MV",
         "MV 线证据陈旧扫描（line_triage·本机可判面）",
         "python Tools/fleet/line_triage.py --line bigstream-mv",
         "cpu", "P3",
         ["Tools/fleet/line_triage.py"],
         "把『这条线多久没产出』从印象变成证据，顺带抓 offnode 假缺口"),
    ],
    "bm-a": [
        ("MV-DIRECTOR-PACKET",
         "导演席拉片包：KN 复核卷一页卷（成片+闸+证据+签字位）",
         "python Tools/fleet/review_packet.py --line kn --root .",
         "cpu", "P1",
         ["Tools/fleet/review_packet.py"],
         "MV 线卡在导演席没有成卷可读；先出卷再签字，消掉『找不到东西看』这类空转"),
        ("MV-NEWPROC-PACKET",
         "导演席新流程卷：四曲立意/分镜/合规矩阵一页卷",
         "python Tools/fleet/review_packet.py --line mv --root .",
         "cpu", "P2",
         ["Tools/fleet/review_packet.py"],
         "四曲新流程件散在十几个文件里，导演要一次读完才能给 verdict"),
    ],
}


def read_jsonl(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def write_jsonl(p, rows):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, p)


def read_json(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def lane_fresh(root, node):
    p = os.path.join(root, "cph4", "fleet", "lanes", "%s.json" % node)
    if not os.path.exists(p):
        return False
    return (time.time() - os.path.getmtime(p)) / 3600.0 * 60 <= ONLINE_MIN


def recent_receipt(root, card_id):
    pat = os.path.join(root, "cph4", "fleet", "queue-receipts", "*%s*" % card_id)
    hits = [p for p in glob.glob(pat) if time.time() - os.path.getmtime(p) < 24 * 3600]
    return bool(hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--node", default="", help="also promote READY cards into the queue for this box")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    now = datetime.now()
    stamp = now.isoformat(timespec="seconds")

    backlog_p = os.path.join(root, "cph4", "fleet", "PRODUCTION-BACKLOG.jsonl")
    queue_p = os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    backlog = read_jsonl(backlog_p)
    queue = read_jsonl(queue_p)
    report = []
    added = []

    def open_ids():
        s = set()
        for r in backlog:
            if r.get("state") in ("OPEN", "READY", "RUNNING"):
                s.add(str(r.get("id")))
        for r in queue:
            if r.get("state") in ("OPEN", "RUNNING"):
                s.add(str(r.get("id")))
        return s

    # R3 stubs
    changed = 0
    for r in queue:
        if r.get("state") == "FAILED" and not r.get("cmd"):
            r["state"] = "CANCELLED"
            r["finished_at"] = stamp
            r["result"] = {"rc": None, "seconds": 0, "deliverable_exists": False,
                           "note": "workgen R3: FAILED row with no cmd is an authored stub, not a runnable job"}
            changed += 1
            report.append("- R3 cancelled stub `%s`" % r.get("id"))
    if changed and not a.dry:
        write_jsonl(queue_p, queue)

    # R1 inventory per online node
    nodes = [f[:-5] for f in os.listdir(os.path.join(root, "cph4", "fleet", "lanes")) if f.endswith(".json")]

    # R0 LEGACY-ROOT HEAL: cards that point at a machine's old tree can never pass the
    # lane-side input check, so they sit READY forever while the box idles. Rewrite the
    # legacy prefix to the canonical one and let the owning lane re-check locally
    # (verify_on_node), instead of promoting cards whose inputs cannot exist.
    healed = 0
    for r in backlog:
        if r.get("state") != "READY":
            continue
        changed_r = False
        for legacy, canon in LEGACY_ROOTS.items():
            for key in ("cmd", "deliverable"):
                v = r.get(key)
                if isinstance(v, str) and legacy in v:
                    r[key] = v.replace(legacy, canon)
                    changed_r = True
            reqs = r.get("requires") or []
            new = [p.replace(legacy, canon) if isinstance(p, str) else p for p in reqs]
            if new != reqs:
                r["requires"] = new
                changed_r = True
        if changed_r:
            r["verify_on_node"] = True
            r["healed_at"] = stamp
            r["healed_note"] = "legacy root rewritten to the canonical tree; lane re-checks on the owning box"
            healed += 1
    if healed and not a.dry:
        write_jsonl(backlog_p, backlog)
    if healed:
        report.append("- R0 healed %d card(s) off a legacy root path" % healed)
    budget = MAX_CARDS_PER_RUN
    for node in sorted(nodes):
        if not lane_fresh(root, node):
            continue
        held = [i for i in open_ids()
                if any(str(r.get("id")) == i and node in (r.get("nodes") or [])
                       for r in backlog + queue)]
        if len(held) >= FLOOR:
            report.append("- %s inventory ok (%d open)" % (node, len(held)))
            continue
        need = FLOOR - len(held)
        # 1) work-bank pending
        bank = read_json(os.path.join(root, "cph4", "fleet", "work-bank", "%s-gpu-bank.json" % node), {}) or {}
        for j in (bank.get("jobs") or []):
            if need <= 0 or budget <= 0:
                break
            if j.get("status") != "pending" or not j.get("cmd") or str(j.get("id")) in open_ids():
                continue
            cmd = j["cmd"] if isinstance(j["cmd"], str) else " ".join(str(x) for x in j["cmd"])
            card = {"id": j["id"], "title": (j.get("title") or j["id"])[:90], "cmd": cmd,
                    "cwd": root.replace("\\", "/"), "requires": [], "deliverable": "",
                    "needs": str(j.get("needs") or "cpu"), "nodes": [node], "prio": "P2",
                    "day_ok": True, "heavy": False,
                    "why": "workgen R1: work-bank pending promoted so the box is not idle",
                    "created_by": "workgen", "created_at": stamp, "state": "READY"}
            added.append(card); budget -= 1; need -= 1
        # 2) node task table
        for (cid, title, cmd, needs, prio, reqs, why) in NODE_TASKS.get(node, []):
            if need <= 0 or budget <= 0:
                break
            if cid in open_ids() or recent_receipt(root, cid):
                continue
            if not all(os.path.exists(os.path.join(root, r)) for r in reqs):
                report.append("- %s skip `%s`: input missing" % (node, cid))
                continue
            added.append({"id": cid, "title": title, "cmd": cmd,
                          "cwd": root.replace("\\", "/"), "requires": reqs, "deliverable": "",
                          "needs": needs, "nodes": [node], "prio": prio, "day_ok": True,
                          "heavy": False, "why": why, "created_by": "workgen",
                          "created_at": stamp, "state": "READY"})
            budget -= 1; need -= 1
        if need > 0:
            report.append("- %s STILL SHORT %d card(s): no safe declaration available" % (node, need))

    if added and not a.dry:
        with open(backlog_p, "a", encoding="utf-8", newline="") as f:
            for c in added:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Declaring is not enough: backlog rows only become queue jobs when the box-side
    # promotion pass runs. Do that here for the local node so a declared card cannot
    # sit READY forever while the machine idles.
    promoted = 0
    if a.node and not a.dry:
        try:
            sys.path.insert(0, os.path.join(root, "Tools"))
            import importlib
            fl = importlib.import_module("backlog_fill")
            before = len(read_jsonl(queue_p))
            fl.fill(root, node=a.node)
            promoted = len(read_jsonl(queue_p)) - before
            report.append("- queue promotion on %s: +%d job(s)" % (a.node, promoted))
        except Exception as e:
            report.append("- queue promotion FAILED: %s" % str(e)[:120])

    # R4 LINE-UNBLOCK: the director seat stalls because nothing hands it a packet. If the
    # newest review packet is older than a day, declare the builder card even when that
    # box already looks "inventoried" - stale cards are not the same as work.
    packets = glob.glob(os.path.join(root, "cph4", "fleet", "queue-receipts", "review-packet-kn-*.md"))
    fresh_packet = any(time.time() - os.path.getmtime(p) < 24 * 3600 for p in packets)
    if (not fresh_packet and budget > 0 and not a.dry
            and "MV-DIRECTOR-PACKET" not in open_ids()
            and not recent_receipt(root, "MV-DIRECTOR-PACKET")
            and os.path.exists(os.path.join(root, "Tools", "fleet", "review_packet.py"))):
        added.append({"id": "MV-DIRECTOR-PACKET",
                      "title": "导演席拉片包：KN 复核卷一页卷（成片+闸+证据+签字位）",
                      "cmd": "python Tools/fleet/review_packet.py --line kn --root .",
                      "cwd": root.replace("\\", "/"),
                      "requires": ["Tools/fleet/review_packet.py"], "deliverable": "",
                      "needs": "cpu", "nodes": ["bm-a"], "prio": "P1", "day_ok": True,
                      "heavy": False,
                      "why": "R4 line-unblock: MV stalls at the director seat with no packet to read; build the packet first (older than 24h or absent)",
                      "created_by": "workgen", "created_at": stamp, "state": "READY"})
        budget -= 1
        report.append("- R4 declared MV-DIRECTOR-PACKET -> bm-a (no fresh review packet)")

    # R2 stalled claims (report only)
    for node in sorted(nodes):
        bank = read_json(os.path.join(root, "cph4", "fleet", "work-bank", "%s-gpu-bank.json" % node), {}) or {}
        for j in (bank.get("jobs") or []):
            if j.get("status") != "claimed":
                continue
            ct = j.get("claimed_ts") or ""
            try:
                age_h = (now - datetime.fromisoformat(ct)).total_seconds() / 3600.0
            except Exception:
                continue
            if age_h > STALL_HOURS:
                report.append("- R2 %s `%s` claimed %.1fh ago with no close (needs evidence before closing)"
                              % (node, j.get("id"), age_h))

    out_dir = os.path.join(root, "cph4", "fleet", "plans")
    os.makedirs(out_dir, exist_ok=True)
    body = ["# workgen report %s" % stamp,
            "",
            "- added cards: %d%s" % (len(added), " (dry)" if a.dry else ""),
            ""]
    for c in added:
        body.append("- + `%s` -> %s (%s, %s)" % (c["id"], c["nodes"][0], c["needs"], c["prio"]))
    body += [""] + report
    open(os.path.join(out_dir, "workgen-report.md"), "w", encoding="utf-8", newline="").write("\n".join(body) + "\n")

    print("WORKGEN added=%d%s" % (len(added), " DRY" if a.dry else ""))
    for c in added:
        print("  + %s -> %s" % (c["id"], c["nodes"][0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())