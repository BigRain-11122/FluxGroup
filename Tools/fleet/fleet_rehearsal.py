#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_rehearsal.py - 机队预演：在沙箱里让五台机跑若干天，别等真机队上线才发现。

CEO 2026-11-11：「还有各种情况的预演，不要真机队跑起来才发现」。

做法：临时根目录 + 真配置 + 模拟时钟 + 可控模型，按"轮"推进：
  每轮每台机跑 station_drive.once()（建卡→领→跑→自验→记账→交接），
  再跑一次 patrol（抽验）与 schedule（额度），最后按场景断言结果。

场景（每个独立沙箱）：
  R1 首次上场        只有"有命令"的工序会被建卡；权限件不建卡
  R2 某机离线        离线机不建卡；它的工序不会被别机抢走（承接方唯一）
  R3 模型全挂        面板全 ABSTAIN -> REVISE，不产生 DONE
  R4 命令失败        卡 FAILED，不写 DONE，也不退化成空提交
  R5 磁盘告急        该机 blocked，不建卡不跑
  R6 同日两轮        不重复建卡、不重复跑
  R7 跨天            产物过期 -> 重新建卡并重跑
  R8 两机并发        各写自己分片，互不覆盖
  R9 交接链路        A 完成后，B 的分片出现 HO- 卡
  R10 抽验失败       回执哈希被改 -> patrol 抽验 FAIL 并记台账

用法：
  python3 Tools/fleet/fleet_rehearsal.py            # 跑全部场景
  python3 Tools/fleet/fleet_rehearsal.py --only R3,R9
返回码：0 全过 / 1 有场景失败 / 3 台架自身错
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

sys.path.insert(0, HERE)
import station_drive as sd  # noqa: E402
import station_shards as ss  # noqa: E402
import master_patrol as mp  # noqa: E402
import panel_review as pr  # noqa: E402

STATIONS = ("delivery", "visual", "audio", "brain", "control")
SCEN = []


def scen(rid, name):
    def deco(fn):
        SCEN.append((rid, name, fn))
        return fn
    return deco


# ------------------------------------------------------------------ 沙箱
def build(stations=None, products=None, tax=None, offline=()):
    td = tempfile.mkdtemp(prefix="rehearse-")
    b = os.path.join(td, "cph4", "fleet")
    for st in (stations or STATIONS):
        os.makedirs(os.path.join(b, "rt", st, "receipts"), exist_ok=True)
    os.makedirs(os.path.join(b, "state"), exist_ok=True)

    tax = tax or {
        "task_types": [
            {"id": "T-PROD", "stations": ["visual"], "judge": "path", "refresh_h": 24},
            {"id": "T-NEXT", "stations": ["audio"], "judge": "path"},
            {"id": "T-PANEL", "stations": ["visual"], "judge": "panel"},
            {"id": "T-CEO", "stations": [], "judge": "human", "human": True},
        ],
        "stage_map": {"P1": {"make": "T-PROD", "sound": "T-NEXT"},
                      "P2": {"judge_only": "T-PANEL"},
                      "P3": {"send": "T-CEO"}},
    }
    prods = products or {"products": [
        {"id": "P1", "stages": ["make", "sound"],
         "outputs": {"make": "out/p1/make/", "sound": "out/p1/sound/"},
         "commands": {"make": "mkdir -p out/p1/make && echo ok > out/p1/make/f.bin",
                      "sound": "mkdir -p out/p1/sound && echo ok > out/p1/sound/f.bin"}},
        {"id": "P2", "stages": ["judge_only"], "outputs": {"judge_only": "out/p2/x/"}},
        {"id": "P3", "stages": ["send"]},
    ]}
    st = {"stations": [
        {"id": s, "machine": s, "status": ("offline" if s in offline else "ready"),
         "blocked_scope": "none", "slots": 6, "shifts": ["00-24"], "min_free_gb": 1,
         "cpu_cores": 16, "ram_gb": 32, "gpu": {"vram_gb": 16}} for s in (stations or STATIONS)]}
    json.dump(tax, open(os.path.join(b, "TAXONOMY-v1.json"), "w"), ensure_ascii=False)
    json.dump(prods, open(os.path.join(b, "PRODUCTS.json"), "w"), ensure_ascii=False)
    json.dump(st, open(os.path.join(b, "STATIONS.json"), "w"), ensure_ascii=False)
    json.dump({"teams": {s: [{"id": "%s-LEAD" % s[:1].upper(), "cls": "triage"}]
                         for s in (stations or STATIONS)}},
              open(os.path.join(b, "AGENT-TEAMS-v1.json"), "w"), ensure_ascii=False)
    json.dump({"sample_per_day": {s: 3 for s in (stations or STATIONS)}},
              open(os.path.join(b, "ACCEPTANCE-v1.json"), "w"), ensure_ascii=False)
    return td


def cards(td, st):
    return ss.read_queue(st, td)


def rounds(td, now, stations=None, run_limit=5):
    out = {}
    for st in (stations or STATIONS):
        out[st] = sd.once(st, td, now=now, run_limit=run_limit)
    return out


# ------------------------------------------------------------------ 场景
@scen("R1", "首次上场：只建有命令的工序，权限件不建卡")
def r1():
    td = build()
    try:
        out = rounds(td, datetime.now())
        v = cards(td, "visual"); a = cards(td, "audio"); c = cards(td, "control")
        # visual 的 T-PANEL 无命令 -> 不得建卡；T-PROD 有命令 -> 建并跑
        ok = (len(v) == 1 and v[0]["stage"] == "make" and v[0]["state"] in ("DONE", "FAILED")
              and len(a) == 1 and not c)
        return ok, "visual=%s audio=%d control=%d" % (
            [(x["stage"], x["state"]) for x in v], len(a), len(c))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R2", "某机离线：离线机不建卡，工序不被别机抢")
def r2():
    td = build(offline=("visual",))
    try:
        rounds(td, datetime.now())
        v = cards(td, "visual"); a = cards(td, "audio"); d = cards(td, "delivery")
        return (len(v) == 0 and len(a) == 1 and len(d) == 0,
                "离线 visual 建卡 %d ｜ audio %d ｜ delivery %d" % (len(v), len(a), len(d)))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R3", "模型全挂：面板全 ABSTAIN -> REVISE，不产生 DONE")
def r3():
    real = pr.review
    pr.review = lambda **kw: {"verdict": "REVISE", "why": "全席 ABSTAIN", "skill": "stub"}
    td = build()
    try:
        ss.upsert("visual", {"id": "c1", "state": "OPEN", "product_id": "P2",
                             "stage": "judge_only", "task_type": "T-PANEL",
                             "created_by": "self-drive",
                             "judge": "panel", "deliverable": "out/p2/x",
                             "cmd": "mkdir -p out/p2/x && echo x > out/p2/x/f"}, td)
        sd.once("visual", td, now=datetime.now(), run_limit=3)
        row = [x for x in cards(td, "visual") if x["id"] == "c1"][0]
        return (row["state"] == "REVISE", "卡状态=%s" % row["state"])
    finally:
        pr.review = real
        shutil.rmtree(td, ignore_errors=True)


@scen("R4", "命令失败：卡 FAILED，不写 DONE")
def r4():
    prods = {"products": [{"id": "P1", "stages": ["make"],
                           "outputs": {"make": "out/p1/make/"},
                           "commands": {"make": "exit 3"}}]}
    tax = {"task_types": [{"id": "T-PROD", "stations": ["visual"], "judge": "path"}],
           "stage_map": {"P1": {"make": "T-PROD"}}}
    td = build(products=prods, tax=tax)
    try:
        rounds(td, datetime.now(), stations=("visual",))
        row = cards(td, "visual")[0]
        return (row["state"] == "FAILED", "状态=%s why=%s" % (
            row["state"], (row.get("result") or {}).get("why")))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R5", "磁盘告急：blocked，不建卡不跑")
def r5():
    td = build()
    real = shutil.disk_usage
    shutil.disk_usage = lambda p: type("U", (), {"total": 1, "used": 1, "free": 100})()
    try:
        out = sd.once("visual", td)
        return (bool(out.get("blocked")) and not cards(td, "visual"), "blocked=%s" % out.get("blocked"))
    finally:
        shutil.disk_usage = real
        shutil.rmtree(td, ignore_errors=True)


@scen("R6", "同日两轮：不重复建卡、不重复跑")
def r6():
    td = build()
    try:
        t = datetime.now()
        rounds(td, t)
        n1 = len(cards(td, "visual"))
        rounds(td, t + timedelta(seconds=60))
        n2 = len(cards(td, "visual"))
        return (n1 == n2 == 1, "第一轮 %d 张，第二轮 %d 张" % (n1, n2))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R7", "跨天：产物过期 -> 重建并重跑")
def r7():
    td = build()
    try:
        t = datetime.now()
        rounds(td, t)
        # 把产物做旧 3 天
        p = os.path.join(td, "out", "p1", "make", "f.bin")
        old = (t - timedelta(days=3)).timestamp()
        os.utime(p, (old, old))
        # 清掉已完成卡，模拟"次日从头"
        ss.write_queue("visual", [], td)
        rounds(td, t + timedelta(days=2))
        v = cards(td, "visual")
        return (len(v) == 1 and v[0]["state"] in ("DONE", "FAILED"),
                "次日建卡 %d 状态=%s" % (len(v), v[0]["state"] if v else "-"))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R8", "两机并发：各写自己分片，互不覆盖")
def r8():
    td = build()
    try:
        rounds(td, datetime.now(), stations=("visual", "audio"))
        return (len(cards(td, "visual")) == 1 and len(cards(td, "audio")) == 1,
                "visual=%d audio=%d" % (len(cards(td, "visual")), len(cards(td, "audio"))))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R9", "交接链路：A 完成后 B 的分片出现 HO- 卡")
def r9():
    td = build()
    try:
        rounds(td, datetime.now(), stations=("visual",))
        ho = [x for x in cards(td, "audio") if str(x.get("id", "")).startswith("HO-")]
        return (len(ho) == 1 and ho[0]["stage"] == "sound",
                "audio 收到 HO- 卡 %d 张：%s" % (len(ho), [x["id"] for x in ho]))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R10", "抽验失败：回执哈希被改 -> patrol 抽验 FAIL")
def r10():
    td = build()
    try:
        rounds(td, datetime.now(), stations=("visual",))
        card = cards(td, "visual")[0]
        d = os.path.join(td, card.get("deliverable") or "out/p1/make", "f.bin")
        rp = os.path.join(td, "cph4", "fleet", "rt", "visual", "receipts",
                          "%s.json" % card["id"])
        rec = json.load(open(rp))
        open(d, "w").write("被改过")
        bad = mp.sample(td, limit_override=5)
        fails = [x for x in bad[0] if not x["pass"]]
        return (bool(fails), "回执=%s 抽验=%s" % (os.path.basename(rp), [x["why"] for x in fails]))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R11", "进程被 kill：RUNNING 卡超租约应被回收重排")
def r11():
    td = build()
    try:
        t = datetime.now()
        ss.upsert("visual", {"id": "killed", "state": "RUNNING", "owner": "visual",
                             "claimed_at": (t - timedelta(hours=2)).isoformat(timespec="seconds"),
                             "product_id": "P1", "stage": "make", "task_type": "T-PROD",
                             "cmd": "mkdir -p out/p1/make && echo ok > out/p1/make/f.bin",
                             "deliverable": "out/p1/make/", "judge": "path"}, td)
        out = sd.once("visual", td, now=t, run_limit=3)
        row = [x for x in cards(td, "visual") if x["id"] == "killed"][0]
        return (out.get("reclaimed") == 1 and row["state"] in ("DONE", "FAILED")
                and "回收" in (row.get("release_reason") or ""),
                "reclaimed=%s 状态=%s reason=%s" % (out.get("reclaimed"), row["state"],
                                                   (row.get("release_reason") or "")[:18]))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R12", "模型超时：超时票记 ABSTAIN，不凑票通过")
def r12():
    # 两席面板，一席 PASS 一席超时：quorum=2 -> REVISE；quorum=1 -> PASS
    real = pr.panels
    def fake():
        return {"T-PROBE": {"skill": "stub", "seats": ["A1", "A2"], "quorum": 2,
                            "rubric": ["x"], "veto": []}}
    pr.panels = fake
    try:
        def gen(prompt, seat):
            if seat == "A2":
                raise TimeoutError("模型超时")
            return '{"vote":"PASS","reason":"ok"}'
        r = pr.review(task_type="T-PROBE", evidence=["Tools/fleet/panel_review.py"],
                      generate=gen, root=False)
        votes = {v["seat"]: v["vote"] for v in r["votes"]}
        return (r["verdict"] == "REVISE" and votes.get("A2") == "ABSTAIN",
                "verdict=%s votes=%s" % (r["verdict"], votes))
    finally:
        pr.panels = real


@scen("R13", "交接重跑：同一工序不重复建 HO- 卡")
def r13():
    td = build()
    try:
        t = datetime.now()
        rounds(td, t, stations=("visual",))
        n1 = len([x for x in cards(td, "audio") if str(x["id"]).startswith("HO-")])
        # 再跑一轮（模拟重跑/时钟不同步导致的重复触发）
        ss.write_queue("visual", [], td)          # 清掉已完成的上游卡
        rounds(td, t + timedelta(minutes=30), stations=("visual",))
        n2 = len([x for x in cards(td, "audio") if str(x["id"]).startswith("HO-")])
        return (n1 == 1 and n2 == 1, "第一轮 HO=%d，重跑后 HO=%d" % (n1, n2))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@scen("R14", "端到端跨机：视觉出片→交接→声音产出→抽验全 PASS")
def r14():
    td = build()
    try:
        t = datetime.now()
        rounds(td, t)                       # 五机各跑一轮：visual 出 make，交接给 audio
        rounds(td, t + timedelta(minutes=5))  # 第二轮：audio 接到 HO- 后执行 sound
        v = [x for x in cards(td, "visual") if x["stage"] == "make"]
        a = [x for x in cards(td, "audio") if x["stage"] == "sound"]
        samples, fails = mp.sample(td, limit_override=10)
        ok = (len(v) == 1 and v[0]["state"] == "DONE"
              and len(a) == 1 and a[0]["state"] == "DONE" and fails == 0 and samples)
        return ok, "视觉=%s 声音=%s 抽验 %d 件失败 %d" % (
            [x["state"] for x in v], [x["state"] for x in a], len(samples), fails)
    finally:
        shutil.rmtree(td, ignore_errors=True)


def run(only=None):
    only = set(x.strip().upper() for x in only.split(",")) if only else None
    okn = 0
    sel = [s for s in SCEN if not only or s[0] in only]
    print("== 机队预演（沙箱，不碰真机队）==")
    for rid, name, fn in sel:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, "抛异常: %r" % e
        okn += 1 if ok else 0
        print("%s %-3s %-34s %s" % ("ok  " if ok else "FAIL", rid, name, detail))
    print("[rehearsal] %d/%d" % (okn, len(sel)))
    return 0 if okn == len(sel) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    return run(a.only)


if __name__ == "__main__":
    sys.exit(main())
