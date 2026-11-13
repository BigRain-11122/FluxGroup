#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""duties_audit.py - 主控职责履行审计（把"职责表"变成"可核验的账"）。

Why（2026-11-13 CEO「把你自己职责颗粒度做细做全」）：
职责写进文档等于没写——过去 60 项职责表躺了两个月，没人能回答"哪几项今天真做了"。
判据只能是三件事，缺一项就算未履行：
    1) 有执行体：executor 指向的工具文件真的存在（不是纸面职责）
    2) 有证据：evidence 指向的产物真的存在（不是"我记得跑过"）
    3) 在周期内：证据龄期不超过该职责周期的 3 倍（事件触发型 T1 只查前两项）

用法：
    python3 Tools/fleet/duties_audit.py
    python3 Tools/fleet/duties_audit.py --json
    python3 Tools/fleet/duties_audit.py --self-test
返回码：0 全部 OK / 1 有 STALE 或 NO-EVIDENCE / 2 有 NO-EXECUTOR（纸面职责）
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import tempfile
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "MASTER-DUTIES-v3.json")

MINUTES = {"T1": None, "T5": 5, "T15": 15, "T30": 30,
           "T360": 360, "T1440": 1440, "T10080": 10080}


def _newest(paths):
    """给定若干路径（可含通配），返回最新 mtime；无命中返回 None。"""
    best = None
    for p in paths:
        for f in glob.glob(p):
            try:
                m = os.path.getmtime(f)
            except OSError:
                continue
            if best is None or m > best:
                best = m
    return best


def audit(spec, root=None, now=None):
    root = root or ROOT
    now = now or time.time()
    rows = []
    for d in spec.get("duties") or []:
        exe = os.path.join(root, d.get("executor") or "")
        ev = os.path.join(root, d.get("evidence") or "")
        item = {"id": d.get("id"), "name": d.get("name"), "domain": d.get("domain"),
                "cad": d.get("cad")}
        if not d.get("executor") or not os.path.exists(exe):
            item.update({"state": "NO-EXECUTOR",
                         "why": "执行体不存在：%s" % (d.get("executor") or "(未写)")})
            rows.append(item)
            continue
        mt = _newest([ev]) if d.get("evidence") else None
        if mt is None:
            # 事件触发型（on_demand）没有固定周期，没触发时为空转，不算未履行。
            # 但只有显式声明 on_demand 的才算——否则"什么都没做"会被当成空转洗白。
            if d.get("on_demand") and str(d.get("cad")) == "T1":
                item.update({"state": "IDLE", "why": "事件触发型，当前无触发条件"})
            else:
                item.update({"state": "NO-EVIDENCE",
                             "why": "证据不存在：%s" % (d.get("evidence") or "(未写)")})
            rows.append(item)
            continue
        cad = MINUTES.get(str(d.get("cad")))
        if cad is None:                      # T1 事件触发：只要求有证据
            item.update({"state": "OK", "age_min": round((now - mt) / 60, 1)})
        else:
            age = (now - mt) / 60
            if age > cad * 3:
                item.update({"state": "STALE", "age_min": round(age, 1),
                             "why": "证据 %.0f 分钟前，超过周期 %d 分钟的 3 倍" % (age, cad)})
            else:
                item.update({"state": "OK", "age_min": round(age, 1)})
        rows.append(item)
    return rows


def summarize(rows):
    out = {}
    for r in rows:
        out[r["state"]] = out.get(r["state"], 0) + 1
    return out


def production(root=None, now=None, hours=24):
    """产出面：近 N 小时全机队有多少张卡真跑完、几台机在执行。

    Why（2026-11-14 实锚）：36 项职责全 OK、执行体都在、证据都新鲜，可全机队近 24h
    只跑完 3 张卡——职责判据只问"我在不在做动作"，不问"动作有没有变成产物"。
    主控的第一考核面是产物，所以把产出单列一条：有机器在执行却零产出，必须红。
    """
    root = root or ROOT
    now = now or time.time()
    done = 0
    per = {}
    for st in ("control", "delivery", "visual", "audio", "brain"):
        rd = os.path.join(root, "cph4", "fleet", "rt", st, "receipts")
        n = 0
        for f in glob.glob(os.path.join(rd, "*.json")):
            try:
                d = json.load(open(f, encoding="utf-8"))
            except Exception:
                continue
            if str(d.get("verdict", "")).upper() not in ("DONE", "PASS"):
                continue
            try:
                ts = time.mktime(time.strptime(str(d.get("ts"))[:19], "%Y-%m-%dT%H:%M:%S"))
            except Exception:
                continue
            if now - ts <= hours * 3600:
                n += 1
        done += n
        per[st] = n
    alive = 0
    for st in ("control", "delivery", "visual", "audio", "brain"):
        hb = os.path.join(root, "cph4", "fleet", "rt", st, "heartbeat.json")
        if not os.path.exists(hb):
            continue
        age = (now - os.path.getmtime(hb)) / 60
        if age <= 30:
            alive += 1
    return {"hours": hours, "done": done, "per_station": per, "alive": alive}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    try:
        spec = json.load(open(SPEC, encoding="utf-8"))
    except Exception as e:
        print("职责表读不到：%s" % e)
        return 2
    rows = audit(spec)
    s = summarize(rows)
    prod = production()
    if a.json:
        print(json.dumps({"summary": s, "rows": rows, "production": prod},
                         ensure_ascii=False, indent=1))
    else:
        print("== 主控职责履行（%d 项 / %s）==" % (len(rows), spec.get("version")))
        print("OK %d｜IDLE(按需未触发) %d｜STALE %d｜NO-EVIDENCE %d｜NO-EXECUTOR %d"
              % (s.get("OK", 0), s.get("IDLE", 0), s.get("STALE", 0),
                 s.get("NO-EVIDENCE", 0), s.get("NO-EXECUTOR", 0)))
        print("产出面：近 %d 小时 DONE %d 张（%s）｜近 30 分钟有心跳的机器 %d 台"
              % (prod["hours"], prod["done"],
                 "、".join("%s %d" % (k, v) for k, v in prod["per_station"].items()), prod["alive"]))
        bad = [r for r in rows if r["state"] not in ("OK", "IDLE")]
        if bad:
            print("\n未履行/待补：")
            for r in sorted(bad, key=lambda x: (x["state"] != "NO-EXECUTOR", x["id"])):
                print("  [%s] %s %s（%s）：%s" % (r["state"], r["id"], r["name"],
                                                r["domain"], r.get("why", "")))
        else:
            print("\n全部职责都有执行体、有证据、在周期内。")
        if prod["alive"] >= 1 and prod["done"] == 0:
            print("产出断言：有 %d 台机器在执行，但近 %d 小时零 DONE——职责满分不等于有产出"
                  % (prod["alive"], prod["hours"]))
    if prod["alive"] >= 1 and prod["done"] == 0:
        return 1
    if any(r["state"] == "NO-EXECUTOR" for r in rows):
        return 2
    if any(r["state"] in ("STALE", "NO-EVIDENCE") for r in rows):
        return 1
    return 0


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "Tools"), exist_ok=True)
        tool = os.path.join(td, "Tools", "demo.py")
        open(tool, "w").write("# demo")
        ev = os.path.join(td, "state", "ev.json")
        os.makedirs(os.path.dirname(ev), exist_ok=True)
        open(ev, "w").write("{}")

        spec = {"duties": [
            {"id": "X1", "domain": "测", "name": "正常项", "cad": "T5",
             "executor": "Tools/demo.py", "evidence": "state/ev.json"},
            {"id": "X2", "domain": "测", "name": "缺执行体", "cad": "T5",
             "executor": "Tools/nope.py", "evidence": "state/ev.json"},
            {"id": "X3", "domain": "测", "name": "缺证据", "cad": "T5",
             "executor": "Tools/demo.py", "evidence": "state/nope.json"},
            {"id": "X4", "domain": "测", "name": "事件触发", "cad": "T1",
             "executor": "Tools/demo.py", "evidence": "state/ev.json"},
        ]}
        rows = {r["id"]: r for r in audit(spec, root=td)}
        chk("正常项 OK", rows["X1"]["state"] == "OK", rows["X1"])
        chk("执行体缺失 -> NO-EXECUTOR", rows["X2"]["state"] == "NO-EXECUTOR", rows["X2"])
        chk("证据缺失 -> NO-EVIDENCE", rows["X3"]["state"] == "NO-EVIDENCE", rows["X3"])
        chk("事件触发型只查存在性（不判龄期）", rows["X4"]["state"] == "OK", rows["X4"])

        # 负控：把证据改旧 -> 必须 STALE（不做这道检查，职责表就永远是绿的）
        old = time.time() - 60 * 60 * 24
        os.utime(ev, (old, old))
        rows2 = {r["id"]: r for r in audit(spec, root=td)}
        chk("负控：证据超期 -> STALE", rows2["X1"]["state"] == "STALE", rows2["X1"])

        # 事件触发型未触发 -> IDLE（不算红），但没声明 on_demand 的仍要报
        spec2 = {"duties": [
            {"id": "Y1", "domain": "测", "name": "按需未触发", "cad": "T1",
             "executor": "Tools/demo.py", "evidence": "state/none.json", "on_demand": True},
            {"id": "Y2", "domain": "测", "name": "T1 但未声明按需", "cad": "T1",
             "executor": "Tools/demo.py", "evidence": "state/none.json"},
        ]}
        r2 = {r["id"]: r for r in audit(spec2, root=td)}
        chk("按需型未触发 -> IDLE", r2["Y1"]["state"] == "IDLE", r2["Y1"])
        chk("负控：T1 未声明按需 -> 仍报 NO-EVIDENCE", r2["Y2"]["state"] == "NO-EVIDENCE", r2["Y2"])

        # 汇总与返回码优先级：NO-EXECUTOR 最严重
        s = summarize(list(rows2.values()))
        chk("汇总包含四态", set(s).issubset({"OK", "STALE", "NO-EVIDENCE", "NO-EXECUTOR"}), s)

        # 真表体检：必须 36 项且每项都写了 executor/evidence
        real = json.load(open(SPEC, encoding="utf-8"))
        ds = real.get("duties") or []
        chk("真表 36 项", len(ds) == 36, len(ds))
        chk("每项都有 executor", all(d.get("executor") for d in ds))
        chk("每项都有 evidence", all(d.get("evidence") for d in ds))
        chk("六个域各 6 项",
            len({d["domain"] for d in ds}) == 6 and
            all(sum(1 for x in ds if x["domain"] == dom) == 6
                for dom in {d["domain"] for d in ds}))
        chk("明确写了主控不做什么", len(real.get("not_master") or []) >= 3)

    print("\n[duties_audit] %d/%d" % (ok, total))
    return 0 if ok == total else 3


if __name__ == "__main__":
    sys.exit(main())
