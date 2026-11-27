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
import re
import sys
import time
from datetime import datetime

FLOOR = 3
STALL_HOURS = 3
MAX_CARDS_PER_RUN = 8
ONLINE_MIN = 30  # lane ts fresher than this counts as an online box


def _autonomy_cfg():
    try:
        with open(os.path.join(ROOT if "ROOT" in globals() else
                               os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                               "cph4", "fleet", "AUTONOMY-CONFIG.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_CFG = _autonomy_cfg()
FLOOR = int((_CFG.get("supply") or {}).get("floor_cards_per_node") or FLOOR)
MAX_ATTEMPTS = int((_CFG.get("failures") or {}).get("max_attempts") or 3)


def blocked_stems(rows):
    """同一任务（去掉日期后缀）失败到上限 = 停线，不许第四天换个日期号再派。

    2026-11-05 实测：asset-lib-voice-corpus 11-03/11-04/11-05 连续三天对四台机重派、
    全 FAILED、error_class 为空。重派不是解决，必须先有根因。
    """
    import collections
    import re
    fails = collections.Counter()
    for r in rows or []:
        rid = str(r.get("id") or "")
        hard = str(r.get("state") or "") == "FAILED"
        many = int(r.get("retries") or 0) >= MAX_ATTEMPTS
        if hard or many:
            fails[re.sub(r"-20\d{6}(T\d{6})?$", "", rid)] += 1
    return {k for k, v in fails.items() if v >= MAX_ATTEMPTS}

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


def merge_rows(p, rows):
    """队列/积压只有一个写入口（2026-11-02）：交给 fleet_lane 的加锁合并。

    以前这里是"读全表→改→整表 os.replace"，与另外五个脚本同轮互踩，谁后写谁赢，
    另一方的行直接消失。现在只提交本工具碰过的行，按 id 合并回磁盘现状。
    """
    import fleet_lane as _fl
    return _fl.merge_jsonl(p, rows)


def read_json(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def lane_fresh(root, node):
    """机器在线与否。

    2026-11-05：原判据只看 cph4/fleet/lanes/<node>.json 的 mtime。机器一进长任务就不再
    写这个文件（实测 bm-a 42 分钟、bm-m 34 分钟），于是被当成离线跳过——而它正是空槽最多
    的那台（31 个）。心跳新鲜（MASTER-STATE.hb_age_s）同样证明在线，取两者之一即可。
    """
    p = os.path.join(root, "cph4", "fleet", "lanes", "%s.json" % node)
    if os.path.exists(p):
        if (time.time() - os.path.getmtime(p)) / 60.0 <= ONLINE_MIN:
            return True
    try:
        ms = json.load(open(os.path.join(root, "cph4", "fleet", "dispatcher",
                                         "MASTER-STATE.json"), encoding="utf-8-sig"))
        lane = (ms.get("lanes") or {}).get(node) or {}
        hb = lane.get("hb_age_s")
        if lane.get("online") and hb is not None and float(hb) <= ONLINE_MIN * 60:
            return True
    except Exception:
        pass
    return False


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
    r3_rows = []
    for r in queue:
        if r.get("state") == "FAILED" and not r.get("cmd"):
            r["state"] = "CANCELLED"
            r["finished_at"] = stamp
            r["result"] = {"rc": None, "seconds": 0, "deliverable_exists": False,
                           "note": "workgen R3: FAILED row with no cmd is an authored stub, not a runnable job"}
            changed += 1
            r3_rows.append(r)
            report.append("- R3 cancelled stub `%s`" % r.get("id"))
    # 单写入口（2026-11-02）：只合并自己改过的行，不再整表覆盖（整表写会抹掉别人同轮写入）。
    if r3_rows and not a.dry:
        merge_rows(queue_p, r3_rows)

    # R1 inventory per online node
    nodes = [f[:-5] for f in os.listdir(os.path.join(root, "cph4", "fleet", "lanes")) if f.endswith(".json")]

    # R0 LEGACY-ROOT HEAL: cards that point at a machine's old tree can never pass the
    # lane-side input check, so they sit READY forever while the box idles. Rewrite the
    # legacy prefix to the canonical one and let the owning lane re-check locally
    # (verify_on_node), instead of promoting cards whose inputs cannot exist.
    healed = 0
    healed_rows = []
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
            healed_rows.append(r)
    if healed_rows and not a.dry:
        merge_rows(backlog_p, healed_rows)
    if healed:
        report.append("- R0 healed %d card(s) off a legacy root path" % healed)

    # R7 DEAD-READY: 积压里 READY、但队列里同名卡早已了结（DONE/CANCELLED/ARCHIVED）的行。
    # 2026-11-02 实测 11 张这种尸体：night_fill 用"id 在队列出现过"就排除，于是既不给活
    # 也不报缺口，队列永远 0 张、机器空转。这里按事实归档，让"有供给"不再说谎。
    qstate = {}
    for r in queue:
        qstate[r.get("id")] = r.get("state")
    dead = []
    for r in backlog:
        if r.get("state") != "READY":
            continue
        st = qstate.get(r.get("id"))
        if st in ("DONE", "CANCELLED", "ARCHIVED", "SUPERSEDED"):
            r["state"] = "ARCHIVED"
            r["archived_at"] = stamp
            r["archived_by"] = "workgen R7: queue twin already %s" % st
            dead.append(r)
    if dead:
        report.append("- R7 archived %d dead READY row(s) whose queue twin is finished" % len(dead))
        if not a.dry:
            merge_rows(backlog_p, dead)

    # 已存在卡的状态表（2026-11-05 十轮演练实证）：补料器原只查"开放态"是否重复，
    # 于是把已经 DONE/FAILED/ARCHIVED 的卡重新声明成 READY——每轮制造 12 处双账本冲突，
    # 还可能导致做完的活被重派。任何已存在的 id 都不许再造。
    existing_states = {}
    for _r in queue + backlog:
        if _r.get("id"):
            existing_states[str(_r["id"])] = str(_r.get("state") or "")
    budget = MAX_CARDS_PER_RUN
    triaged_lines = set()   # one triage card per line per run, whichever box holds it

    def runnable(r):
        """A card is real inventory only if it can still become work.

        2026-11-01: pending cards whose deliverable already exists were counted as held
        work, so every box reported "inventory ok" while nothing was running - the queue
        was full of corpses and the machines idled. Count only what can still execute.
        """
        if r.get("state") not in ("OPEN", "READY", "RUNNING"):
            return False
        out = r.get("deliverable")
        if out:
            p = out if os.path.isabs(out) else os.path.join(root, out)
            if os.path.exists(p):
                return False
        return True

    for node in sorted(nodes):
        if not lane_fresh(root, node):
            continue
        held = [i for i in open_ids()
                if any(str(r.get("id")) == i and node in (r.get("nodes") or [])
                       for r in backlog + queue
                       if r.get("state") == "RUNNING" or runnable(r))]
        # 产能配额（CEO 2026-11-05「自动化和业务齐头并进」）：机制卡（fleet-ops 等）
        # 每机最多 infra_max_cards_per_node 张。实测曾出现 12 张在飞里 8 张是机制活，
        # 业务线反而没卡——机制把产能吃光了。
        _cap = (_CFG.get("capacity") or {})
        _infra_lines = set(_cap.get("infra_lines") or ["fleet-ops"])
        _infra_cap = int(_cap.get("infra_max_cards_per_node") or 2)
        _held_infra = [i for i in held
                       if any(str(r.get("id")) == i and (r.get("line") or "") in _infra_lines
                              for r in backlog + queue)]
        infra_full = len(_held_infra) >= _infra_cap

        def infra_ok(card):
            return (str(card.get("line") or "") not in _infra_lines) or (not infra_full)

        if len(held) >= FLOOR:
            report.append("- %s inventory ok (%d open)" % (node, len(held)))
            continue
        need = FLOOR - len(held)
        # 1) work-bank pending
        # Both banks are real supply: GPU work and CPU work. CEO 2026-11-01: CPU must not idle
        # either - finance backtests and the voice bank are CPU lines that were sitting empty.
        for bank_name in ("%s-gpu-bank.json" % node, "%s-cpu-bank.json" % node):
            bank = read_json(os.path.join(root, "cph4", "fleet", "work-bank", bank_name), {}) or {}
            for j in (bank.get("jobs") or []):
                if need <= 0 or budget <= 0:
                    break
                if j.get("status") != "pending" or not j.get("cmd") or str(j.get("id")) in open_ids():
                    continue
                if not (j.get("deliverable") or j.get("accept")):
                    report.append("- %s skip `%s`: bank job has no deliverable/accept" % (node, j.get("id")))
                    continue
                # An artifact already on disk means the job is done, not pending. Without
                # this the bank re-declared the same backtest every cycle (无效产出).
                dpath = j.get("deliverable") or ""
                if dpath:
                    dp = dpath if os.path.isabs(dpath) else os.path.join(root, dpath)
                    if os.path.exists(dp):
                        report.append("- %s skip `%s`: deliverable already on disk" % (node, j.get("id")))
                        continue
                cmd = j["cmd"] if isinstance(j["cmd"], str) else " ".join(str(x) for x in j["cmd"])
                card = {"id": j["id"], "title": (j.get("title") or j["id"])[:90], "cmd": cmd,
                        "cwd": "", "requires": j.get("requires") or [],
                        "deliverable": j.get("deliverable") or "",
                        "accept": j.get("accept") or "",
                        "needs": str(j.get("needs") or "cpu"), "nodes": [node], "prio": j.get("prio") or "P2",
                        # Bank jobs are heavy unless they say otherwise: bm-a is the CEO's
                        # workstation, so CPU work must not ignore its 09-19 quiet window.
                        "day_ok": bool(j.get("day_ok")), "heavy": False,
                        "why": "workgen R1: work-bank pending promoted so the box is not idle",
                        "created_by": "workgen", "created_at": stamp, "state": "READY",
                        # The control plane never holds the production trees (quant repo,
                        # media masters): without this the master's own existence check
                        # blocks the card forever and the CPU stays idle.
                        "verify_on_node": True}
                added.append(card); budget -= 1; need -= 1
        # 2) node task table
        for (cid, title, cmd, needs, prio, reqs, why) in NODE_TASKS.get(node, []):
            if need <= 0 or budget <= 0:
                break
            # 2026-11-02：id 必须带日期。原来用固定 id，队列里同名卡一旦 DONE/CANCELLED，
            # 这里补出来的 READY 行会被 R7 判成"尸体"归档——补料→归档的死循环，
            # 队列永远 0 张、机器空转（实测 19:2x 全队无活可派）。日期化后每天是一张新卡。
            _base = cid
            cid = "%s-%s" % (_base, now.strftime("%Y%m%d"))
            if cid in open_ids() or recent_receipt(root, _base):
                continue
            if not all(os.path.exists(os.path.join(root, r)) for r in reqs):
                report.append("- %s skip `%s`: input missing" % (node, cid))
                continue
            # A card with no deliverable AND no acceptance is rejected by backlog_fill as
            # SPEC-REQUIRED (2026-11-01: both director-packet cards went INVALID here and
            # never ran). Mechanically well-known tools get their real output path.
            deliverable = ""
            if "review_packet.py" in cmd:
                m = re.search(r"--line\s+(\S+)", cmd)
                if m:
                    deliverable = ("cph4/fleet/queue-receipts/review-packet-%s-%s.md"
                                   % (m.group(1), now.strftime("%Y%m%d")))
            added.append({"id": cid, "title": title, "cmd": cmd,
                          "cwd": "", "requires": reqs, "deliverable": deliverable,
                          "accept": "卷内四件齐全（成片/闸结论/证据/签字位）且 mtime 为当日",
                          "needs": needs, "nodes": [node], "prio": prio, "day_ok": True,
                          "heavy": False, "why": why, "created_by": "workgen",
                          "created_at": stamp, "state": "READY"})
            budget -= 1; need -= 1
        # 3) R5 generic evidence pass: still short with nothing authored. A read-only
        # line_triage card is safe on any box and always produces a real file, so "no
        # safe declaration" stops meaning "stand idle" (CEO 2026-11-01: 门槛太多导致闲置).
        if need > 0:
            try:
                reg = read_json(os.path.join(root, "cph4", "fleet", "LINE-REGISTRY.json"), {}) or {}
                day = now.strftime("%Y%m%d")
                for ln in (reg.get("lines") or []):
                    if need <= 0 or budget <= 0:
                        break
                    lid = ln.get("id")
                    if not lid or str(ln.get("status") or "").upper() == "PARKED":
                        continue
                    if lid in triaged_lines:
                        continue
                    tok = "R-TRIAGE-%s-" % lid.upper().replace("-", "")
                    # One evidence pass per line+day, fleet-wide: line_triage writes a
                    # single path per line, so a second box would overwrite the first
                    # box's receipt and both would look "done" (2026-11-01).
                    if any(str(r.get("id") or "").startswith(tok) and r.get("state") in ("OPEN", "READY", "RUNNING")
                           for r in backlog + queue):
                        continue
                    # node belongs in the id: the same line triaged on two boxes is two
                    # different evidence sets, and a shared id made the second card dead.
                    cid = "R-TRIAGE-%s-%s-%s" % (lid.upper().replace("-", ""),
                                                  node.upper().replace("-", ""), day)
                    # line_triage writes ONE path per line+day (no node component), so a
                    # second box on the same line would produce the identical file. Skip
                    # when that evidence already exists instead of declaring busywork.
                    if os.path.exists(os.path.join(root, "cph4", "fleet", "queue-receipts",
                                                   "triage-%s-%s-%s.md" % (lid, node, day))):
                        continue
                    if cid in open_ids() or recent_receipt(root, cid):
                        continue
                    added.append({
                        "id": cid, "title": "%s 线证据扫描（%s 本机可判面）" % (ln.get("name") or lid, node),
                        "cmd": ("python Tools/fleet/line_triage.py --line %s --node %s "
                                "--out cph4/fleet/queue-receipts/triage-%s-%s-%s.md"
                                % (lid, node, lid, node, day)),
                        "cwd": "",
                        "requires": ["Tools/fleet/line_triage.py"],
                        "deliverable": "cph4/fleet/queue-receipts/triage-%s-%s-%s.md"
                                       % (lid, node, day),
                        "accept": "回执含每工段证据存在性/最新时间/缺什么",
                        "needs": "cpu", "nodes": [node], "prio": "P3", "day_ok": True,
                        "heavy": False,
                        "why": "workgen R5: 本机缺活且无既有宣告，派只读证据扫描（产出可核验，非空转）",
                        "created_by": "workgen", "created_at": stamp, "state": "READY"})
                    budget -= 1; need -= 1
                    triaged_lines.add(lid)
            except Exception as e:
                report.append("- R5 skipped: %s" % str(e)[:100])
        if need > 0:
            report.append("- %s STILL SHORT %d card(s): no safe declaration available" % (node, need))

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
                      "cwd": "",
                      "requires": ["Tools/fleet/review_packet.py"], "deliverable": "",
                      "needs": "cpu", "nodes": ["bm-a"], "prio": "P1", "day_ok": True,
                      "heavy": False,
                      "why": "R4 line-unblock: MV stalls at the director seat with no packet to read; build the packet first (older than 24h or absent)",
                      "created_by": "workgen", "created_at": stamp, "state": "READY"})
        budget -= 1
        report.append("- R4 declared MV-DIRECTOR-PACKET -> bm-a (no fresh review packet)")

    # R8 MODEL-RADAR: every online box, once a day, searches upstream for newer local models,
    # benchmarks them against its own baseline, and swaps only when the two-path rule passes
    # (CEO 2026-11-03: 闲时搜最新、适配、测不过不换). Idle gating lives in the tool itself
    # (--idle-only), so a box that is producing simply returns a SKIPPED-IDLE receipt.
    if os.path.exists(os.path.join(root, "Tools", "fleet", "model_radar.py")):
        day = now.strftime("%Y%m%d")
        for node in sorted(nodes):
            if not lane_fresh(root, node):
                continue
            cid = "R-MODEL-RADAR-%s-%s" % (node.upper().replace("-", ""), day)
            deliverable = "cph4/fleet/queue-receipts/model-radar-%s-%s.json" % (node, day)
            if cid in open_ids():
                continue
            if os.path.exists(os.path.join(root, deliverable)):
                continue
            added.append({
                "id": cid,
                "title": "本地模型日报：扫上游新档+实测+按两条判据决定是否换档（%s）" % node,
                "cmd": "python Tools/fleet/model_radar.py run --node %s --idle-only --apply" % node,
                "cwd": "",
                "requires": ["Tools/fleet/model_radar.py", "cph4/fleet/LOCAL-MODEL-POLICY.json"],
                "deliverable": deliverable,
                "accept": "回执 verdict=OK（或 SKIPPED-IDLE 且写明原因）；换档必须带 applied.from/to 与 rollback",
                "needs": "cpu", "nodes": [node], "prio": "P3",
                "day_ok": not ("bm-a" == node),   # 公司生产力机白天让路，夜间跑
                "heavy": False,
                "why": "R8 fleet model radar: 每台在线机每天一次，闲时搜新模型；测不过不换",
                "created_by": "workgen", "created_at": stamp, "state": "READY",
                "verify_on_node": True})
            report.append("- R8 declared model radar -> %s" % node)

    # R6 CLOSE-PRODUCED: a READY card whose deliverable is already on disk is not work.
    # 2026-11-01: 22 such rows sat READY and every box read them as inventory, so the
    # fleet reported "inventory ok" while nothing ran. Closing on a file that exists is a
    # fact, not a claim: the evidence is the path itself.
    closed = 0
    closed_rows = []
    for r in backlog:
        if r.get("state") != "READY":
            continue
        d = r.get("deliverable")
        if not d:
            continue
        p = d if os.path.isabs(d) else os.path.join(root, d)
        if os.path.exists(p):
            r["state"] = "DONE"
            r["closed_at"] = stamp
            r["closed_by"] = "workgen R6: deliverable already on disk"
            closed += 1
            closed_rows.append(r)
    if closed:
        report.append("- R6 closed %d READY card(s) whose deliverable already exists" % closed)
        if not a.dry:
            merge_rows(backlog_p, closed_rows)

    # Persist AFTER every rule has had its say. 2026-11-01: the R4 unblock card used to be
    # appended after this write, so it was reported as declared and never reached the
    # backlog - a silent no-op that left the director seat idle.
    if added and not a.dry:
        # 停线判据：同一任务已失败到上限就不再新造卡（换日期号也不行）。
        _blocked = blocked_stems(list(queue) + list(backlog))
        _keep = []
        for c in added:
            _old = existing_states.get(str(c.get("id")))
            if _old:
                report.append("- SKIP `%s`: id 已存在（state=%s），不许重声明" % (c.get("id"), _old))
                continue
            _stem = re.sub(r"-20\d{6}(T\d{6})?$", "", str(c.get("id") or ""))
            if _stem in _blocked:
                report.append("- BLOCKED `%s`: 同一任务已失败 %d 次，先落根因再派" % (c.get("id"), MAX_ATTEMPTS))
                continue
            _keep.append(c)
        added = _keep
        # 只合并新卡；别人的行原样留在盘上（旧写法先整表重写再 append，既丢更新又可能写重）。
        if added:
            merge_rows(backlog_p, added)

    # Declaring is not enough: backlog rows only become queue jobs when the box-side
    # promotion pass runs. Do that here (after the persist) so a declared card cannot
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