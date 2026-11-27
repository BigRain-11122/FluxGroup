#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""integrity_check.py - 全链路一致性自检：策略 / 通路 / 链条 / 规则是否成立。

CEO 2026-11-11：「测试主要目的要策略 通路 链条 规则等都是正常」。

不测"坏了会怎样"（那是 station_qa 的活），只测"现在这套东西是不是接得上"：

链条  产品→工序→任务类型→承接工位→硬件→产物契约→判据→席位，任一环断开就报
通路  模型端点阶梯、席位 cls 映射、跨机交接目标、命令面与自驱是否同源
策略  三桶是否互斥且覆盖全部工序、频率预算是否超载、每机是否有席位
规则  人判是否清零（权限件除外）、阈值是否单一来源、正典指针是否都在盘

用法：
  python3 Tools/fleet/integrity_check.py          # 全跑
  python3 Tools/fleet/integrity_check.py --group 链条
返回码：0 全通过 / 1 有断链或违规 / 3 台架自身错
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")

sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402

READY = ("ready", "ready_paused", "online", "network_ok_not_registered")
JUDGE_FILES = {"drama_rules": "Tools/fleet/drama_rules.py",
               "voice_gate": "Tools/fleet/voice_gate.py",
               "game_submit_pack": "Tools/fleet/game_submit_pack.py",
               "kf_hand_face": "Tools/fleet/drama_rules.py",
               "family_check": "Tools/family_compliance_check.py"}
CHECKS = []


def check(group, cid, name):
    def deco(fn):
        CHECKS.append((group, cid, name, fn))
        return fn
    return deco


def _j(name):
    try:
        with open(os.path.join(F, name), encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}


def ctx():
    return {"tax": _j("TAXONOMY-v1.json"), "prod": _j("PRODUCTS.json"),
            "st": _j("STATIONS.json"), "teams": _j("AGENT-TEAMS-v1.json"),
            "panels": _j("JUDGE-PANELS-v1.json"), "cap": _j("AGENT-CAPACITY-v1.json")}


# ------------------------------------------------------------------ 链条
@check("链条", "C1", "在产工序全部落到三桶之一（可自驱/待接命令/权限）")
def c1(c):
    tot = auto = pending = auth = noprod = parked = 0
    for p in c["prod"].get("products") or []:
        # 挂起产品不进分母：它们已经不派卡（station_drive 认 status），
        # 再算进"待接命令"只会让产能表虚高（2026-11-14）。
        if str(p.get("status") or "ACTIVE").upper() not in ("ACTIVE", "ASSET_ONLY"):
            parked += len(p.get("stages") or [])
            continue
        outs = p.get("outputs") or {}
        cmds = p.get("commands") or {}
        for s in p.get("stages") or []:
            tot += 1
            if s in (p.get("manual_stages") or []):
                auth += 1
            elif not outs.get(s):
                noprod += 1
            elif cmds.get(s):
                auto += 1
            else:
                pending += 1
    return (noprod == 0 and auto + pending + auth == tot,
            "共 %d：可自驱 %d / 待接命令 %d / 权限 %d / 无契约 %d｜挂起 %d 道（不计入）"
            % (tot, auto, pending, auth, noprod, parked))


@check("链条", "C2", "每道工序的 task_type 都在 TAXONOMY 里")
def c2(c):
    bad = []
    for p in c["prod"].get("products") or []:
        for s in p.get("stages") or []:
            tid = ((c["tax"].get("stage_map") or {}).get(p["id"]) or {}).get(s)
            if not tid or (tid not in {t["id"] for t in c["tax"].get("task_types") or []}):
                bad.append("%s/%s" % (p["id"], s))
    return (not bad, "断链 %d 道%s" % (len(bad), (": " + ", ".join(bad[:4])) if bad else ""))


@check("链条", "C3", "每个任务类型至少一个承接工位（权限件除外）")
def c3(c):
    smeta = {s["id"] for s in c["st"].get("stations") or []}
    bad = [t["id"] for t in c["tax"].get("task_types") or []
           if not (t.get("stations") or []) and not t.get("human")]
    ghost = [t["id"] for t in c["tax"].get("task_types") or []
             for s in (t.get("stations") or []) if s not in smeta]
    return (not bad and not ghost,
            "无承接 %d ｜ 承接方不存在 %d %s" % (len(bad), len(ghost), ghost[:3] or ""))


@check("链条", "C4", "承接工位硬件满足任务类型资源下限")
def c4(c):
    smeta = {s["id"]: s for s in c["st"].get("stations") or []}
    bad = []
    for t in c["tax"].get("task_types") or []:
        need = t.get("res") or {}
        for sid in t.get("stations") or []:
            s = smeta.get(sid) or {}
            gpu = (s.get("gpu") or {})
            vram = gpu.get("usable_gb") or gpu.get("vram_gb") or 0
            if need.get("gpu_gb", 0) > vram or need.get("ram_gb", 0) > (s.get("ram_gb") or 0) \
                    or need.get("cores", 0) > (s.get("cpu_cores") or 0):
                bad.append("%s@%s" % (t["id"], sid))
    return (not bad, "硬件不够 %d 处%s" % (len(bad), (": " + ", ".join(bad[:4])) if bad else ""))


@check("链条", "C5", "判据都有可执行落点（脚本在盘 / 面板存在）")
def c5(c):
    panels = c["panels"].get("panels") or {}
    bad = []
    for t in c["tax"].get("task_types") or []:
        j = t.get("judge")
        if j in ("path", "hash", None):
            continue
        if j == "panel":
            if t["id"] not in panels:
                bad.append("%s(无面板)" % t["id"])
        elif j in JUDGE_FILES:
            if not os.path.exists(os.path.join(ROOT, JUDGE_FILES[j])):
                bad.append("%s(缺%s)" % (t["id"], JUDGE_FILES[j]))
        elif j not in ("manual", "human"):
            bad.append("%s(未知判据%s)" % (t["id"], j))
    return (not bad, "断判据 %d 处%s" % (len(bad), (": " + ", ".join(bad[:4])) if bad else ""))


@check("链条", "C6", "评审团没有幽灵席位，且至少一席来自承接工位")
def c6(c):
    teams = c["teams"].get("teams") or {}
    tax = {t["id"]: t for t in c["tax"].get("task_types") or []}
    home = {x["id"]: st for st, seats in teams.items() for x in seats}
    ghost, no_local = [], []
    for tid, pan in (c["panels"].get("panels") or {}).items():
        owners = set((tax.get(tid) or {}).get("stations") or [])
        seats = pan.get("seats") or []
        for seat in seats:
            if seat not in home:
                ghost.append("%s:%s" % (tid, seat))
        if owners and seats and not any(home.get(x) in owners for x in seats):
            no_local.append(tid)
    ok = not ghost and not no_local
    return (ok, "幽灵席位 %d ｜ 缺本方视角 %d %s" % (
        len(ghost), len(no_local), (no_local[:3] or "")))


# ------------------------------------------------------------------ 通路
@check("通路", "P1", "模型端点阶梯可解析，且本机在候选里")
def p1(c):
    import local_model as lm
    gs = lm.gateways()
    here = lm.local_station()
    return (bool(gs) and any("127.0.0.1" in g for g in gs),
            "阶梯=%s 本机=%s" % (gs, here))


@check("通路", "P2", "每个席位的 cls 都能映射到模型座位")
def p2(c):
    import local_model as lm
    duties = lm._duties() or {}
    bad = []
    for st, seats in (c["teams"].get("teams") or {}).items():
        for s in seats:
            seat = lm.seat_of(s.get("cls") or "triage")
            if seat not in duties:
                bad.append("%s/%s(cls=%s→%s)" % (st, s["id"], s.get("cls"), seat))
    return (not bad, "映射失败 %d 个%s" % (len(bad), (": " + ", ".join(bad[:3])) if bad else ""))


@check("通路", "P3", "交接目标必须是登记在册的工位")
def p3(c):
    smeta = {s["id"] for s in c["st"].get("stations") or []}
    ghost = sorted({s for t in c["tax"].get("task_types") or []
                    for s in (t.get("stations") or []) if s not in smeta})
    return (not ghost, "越界工位: %s" % (ghost or "无"))


@check("通路", "P4", "命令面与自驱读同一份分片（同源）")
def p4(c):
    import fleet_cmd  # noqa
    import station_drive as sd
    same = (fleet_cmd.ss.read_queue is ss.read_queue and sd.ss.read_queue is ss.read_queue)
    return (same, "三者都走 station_shards 的 read_queue")


# ------------------------------------------------------------------ 策略
@check("通路", "P5", "分片写路径不依赖 git（推送失败也不丢卡）")
def p5(c):
    src = open(os.path.join(ROOT, "Tools", "fleet", "station_shards.py"), encoding="utf-8").read()
    write_part = src[src.find("def write_queue"):src.find("def read_remote_queue")]
    bad = [k for k in ("subprocess", "git ") if k in write_part]
    return (not bad, "写队列段出现 %s" % (bad or "无外部依赖"))


@check("策略", "S1", "三桶互斥：同一工序不会既待接命令又权限")
def s1(c):
    bad = []
    for p in c["prod"].get("products") or []:
        man = set(p.get("manual_stages") or [])
        cmds = set((p.get("commands") or {}).keys())
        if man & cmds:
            bad.append("%s:%s" % (p["id"], ",".join(sorted(man & cmds))))
    return (not bad, "重叠 %d 处%s" % (len(bad), (": " + ", ".join(bad)) if bad else ""))


@check("策略", "S2", "频率预算不超载")
def s2(c):
    import agent_schedule as asch
    pl = asch.plan()
    return (not pl["over"], "；".join("%s %d/%s 次 %.0f/%s 分" % (
        v["acct"], v["calls_day"], v["budget_calls"], v["minutes_day"], v["budget_minutes"])
        for v in pl["verdict"]))


@check("策略", "S3", "每台机至少一个席位（不许有没脑子的机器）")
def s3(c):
    teams = c["teams"].get("teams") or {}
    bad = [s["id"] for s in c["st"].get("stations") or [] if not (teams.get(s["id"]) or [])]
    return (not bad, "无席位机器: %s（共 %d 席）" % (bad or "无", sum(len(v) for v in teams.values())))


# ------------------------------------------------------------------ 规则
@check("规则", "R1", "人判桶已清零（只允许权限件）")
def r1(c):
    bad = []
    for p in c["prod"].get("products") or []:
        for s in p.get("manual_stages") or []:
            if s != "人工发送":
                bad.append("%s/%s" % (p["id"], s))
    manual_types = [t["id"] for t in c["tax"].get("task_types") or []
                    if t.get("judge") in ("manual", "human") and not t.get("human")]
    return (not bad and not manual_types,
            "残留人判工序 %d ｜ 人判任务类型 %s" % (len(bad), manual_types or "无"))


@check("规则", "R2", "阈值单一来源：refresh_h 只在 TAXONOMY，min_free_gb 只在 STATIONS")
def r2(c):
    bad = []
    for t in c["tax"].get("task_types") or []:
        if "min_free_gb" in t:
            bad.append("TAXONOMY 混入 min_free_gb")
    for s in c["st"].get("stations") or []:
        if "refresh_h" in s:
            bad.append("STATIONS 混入 refresh_h")
    return (not bad, "串源 %d 处%s" % (len(bad), (": " + ", ".join(bad)) if bad else ""))


@check("规则", "R3", "正典索引指向的文件都在盘")
def r3(c):
    p = os.path.join(ROOT, "cph4", "registry", "CANON-V2-20261111.md")
    txt = open(p, encoding="utf-8").read()
    refs = set(re.findall(r"`(cph4/[^`]+?|Tools/[^`]+?|docs/[^`]+?)`", txt))
    missing = sorted(r for r in refs if not os.path.exists(os.path.join(ROOT, r)))
    return (not missing, "引用 %d 个，缺 %d %s" % (len(refs), len(missing), missing[:3] or ""))


def run(group=None):
    c = ctx()
    bad = 0
    groups = ["链条", "通路", "策略", "规则"]
    for g in groups:
        if group and g != group:
            continue
        print("== %s ==" % g)
        for cg, cid, name, fn in CHECKS:
            if cg != g:
                continue
            try:
                ok, detail = fn(c)
            except Exception as e:
                ok, detail = False, "台架异常: %r" % e
            bad += 0 if ok else 1
            print("  %s %-3s %-40s %s" % ("ok  " if ok else "FAIL", cid, name, detail))
    total = len([x for x in CHECKS if not group or x[0] == group])
    print("[integrity] %d/%d" % (total - bad, total))
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", choices=["链条", "通路", "策略", "规则"])
    a = ap.parse_args()
    return run(a.group)


if __name__ == "__main__":
    sys.exit(main())
