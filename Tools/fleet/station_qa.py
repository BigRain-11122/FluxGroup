#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""station_qa.py - 工况测试台：假定自己是某一台机，在各种坏情况下逐条验行为。

CEO 2026-11-11：「你要用不同的工况去测试，并假定自己是机队某一台机器，好好写好策略，
一个个测试发现问题解决问题」。

策略（每条工况先写"应该怎样"，再用沙箱验）：
  1 冷启动      空分片、无产物          -> 只为"有命令且非权限"的工序建卡；其余如实报缺口，不造活
  2 队列坏行    中间插坏 JSON           -> 跳过坏行不丢整份，后续照常
  3 磁盘告急    free < min_free_gb      -> 直接 BLOCKED，不建卡不跑，不形成失败循环
  4 模型全挂    端点全不可用            -> 评审团全 ABSTAIN -> REVISE（不是 PASS，也不崩）
  5 产物过期    mtime 超 refresh_h      -> 应重建卡（同工序当天只一次）
  6 重复在飞    已有 OPEN 卡            -> 不重复建卡
  7 回执重名    同 id 第二次写          -> 两份文件，历史不覆盖
  8 并发写片    两进程同时 upsert       -> 两张卡都在（写锁生效）
  9 交接断头    目标机不存在/离线       -> 只写 HO- 卡或返回同机提示，不崩
 10 面板缺席    task_type 无 panel      -> BLOCK（宁可拦不许放）

用法：
  python3 Tools/fleet/station_qa.py                 # 默认扮演 visual（传家宝）
  python3 Tools/fleet/station_qa.py --station audio
  python3 Tools/fleet/station_qa.py --only 3,7,8
返回码：0 全过 / 1 有用例失败 / 3 台架自身错
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

sys.path.insert(0, HERE)
import station_drive as sd  # noqa: E402
import station_shards as ss  # noqa: E402
import panel_review as pr  # noqa: E402

CASES = []


def case(n, name, expect):
    def deco(fn):
        CASES.append((n, name, expect, fn))
        return fn
    return deco


# ---------------------------------------------------------------- 沙箱
def sandbox(station="visual", *, products=None, tax=None, stations=None,
            outputs_written=None, receipts=None):
    td = tempfile.mkdtemp(prefix="qa-")
    b = os.path.join(td, "cph4", "fleet")
    os.makedirs(os.path.join(b, "rt", station), exist_ok=True)
    os.makedirs(os.path.join(b, "state"), exist_ok=True)
    tax = tax or {"task_types": [{"id": "T-A", "stations": [station], "judge": "path",
                                  "refresh_h": 24, "model": "none"},
                                 {"id": "T-CEO", "stations": [], "judge": "human", "human": True}],
                  "stage_map": {"P1": {"s1": "T-A", "s2": "T-CEO"}}}
    prod = products or {"products": [
        {"id": "P1", "stages": ["s1", "s2"],
         "outputs": {"s1": "out/p1/s1/"},
         "commands": {"s1": "true"}}]}
    st = stations or {"stations": [{"id": station, "machine": station, "status": "ready",
                                    "blocked_scope": "none", "slots": 6,
                                    "shifts": ["00-24"], "min_free_gb": 1,
                                    "cpu_cores": 8, "ram_gb": 32,
                                    "gpu": {"vram_gb": 16}}]}
    json.dump(tax, open(os.path.join(b, "TAXONOMY-v1.json"), "w"), ensure_ascii=False)
    json.dump(prod, open(os.path.join(b, "PRODUCTS.json"), "w"), ensure_ascii=False)
    json.dump(st, open(os.path.join(b, "STATIONS.json"), "w"), ensure_ascii=False)
    if outputs_written:
        for rel in outputs_written:
            p = os.path.join(td, rel)
            os.makedirs(os.path.dirname(p) if not p.endswith("/") else p, exist_ok=True)
            if not p.endswith("/"):
                open(p, "w").write("x")
            else:
                open(os.path.join(p, "f.bin"), "w").write("x")
    for rid, body in (receipts or {}).items():
        d = os.path.join(b, "rt", station, "receipts")
        os.makedirs(d, exist_ok=True)
        json.dump(body, open(os.path.join(d, rid), "w"))
    return td, b


# ---------------------------------------------------------------- 用例
@case(1, "冷启动：空分片无产物", "只为有命令的工序建卡，其余如实报缺口")
def q1(td, b, station, r):
    want, unk = sd.plan(station, td)
    ids = [w["stage"] for w in want]
    reasons = {u["why"].split("：")[0] for u in unk}
    return (ids == ["s1"] and "AUTHORITY" in reasons,
            "建卡=%s 缺口原因=%s" % (ids, sorted(reasons)))


@case(2, "队列坏行：中间插坏 JSON", "跳过坏行不丢整份")
def q2(td, b, station, r):
    p = os.path.join(b, "rt", station, "queue.jsonl")
    with open(p, "w") as f:
        f.write(json.dumps({"id": "ok1", "state": "OPEN"}) + "\n")
        f.write("{坏行 不是 json\n")
        f.write(json.dumps({"id": "ok2", "state": "DONE"}) + "\n")
    rows = ss.read_queue(station, td)
    return ([r["id"] for r in rows] == ["ok1", "ok2"],
            "读出 %d 张：%s" % (len(rows), [r["id"] for r in rows]))


@case(3, "磁盘告急：低于 min_free_gb", "直接 BLOCKED，不建卡不跑")
def q3(td, b, station, r):
    real = shutil.disk_usage
    shutil.disk_usage = lambda p: type("U", (), {"total": 1, "used": 1, "free": 512 * 1024 ** 2})()
    try:
        out = sd.once(station, td, run_limit=1)
    finally:
        shutil.disk_usage = real
    return (bool(out.get("blocked")) and out.get("would_create") == [] and out.get("ran") == [],
            "blocked=%s" % out.get("blocked"))


@case(4, "模型全挂：评审团应 ABSTAIN→REVISE", "不是 PASS，也不崩")
def q4(td, b, station, r):
    res = pr.review(task_type="T-3D-ADAPT", evidence=[os.path.join(ROOT, "Tools/fleet/station_qa.py")],
                    generate=lambda p, s: "", root=False)
    return (res["verdict"] == "REVISE" and all(v["vote"] == "ABSTAIN" for v in res["votes"]),
            "verdict=%s votes=%s" % (res["verdict"], [v["vote"] for v in res["votes"]]))


@case(5, "产物过期：超 refresh_h", "应重建卡")
def q5(td, b, station, r):
    p = os.path.join(td, "out", "p1", "s1")
    os.makedirs(p, exist_ok=True)
    f = os.path.join(p, "f.bin"); open(f, "w").write("x")
    old = time.time() - 3 * 86400
    os.utime(f, (old, old))
    want, _ = sd.plan(station, td)
    return ([w["stage"] for w in want] == ["s1"], "重建=%s" % [w["stage"] for w in want])


@case(6, "重复在飞：已有 OPEN 卡", "不重复建卡")
def q6(td, b, station, r):
    ss.upsert(station, {"id": "c1", "state": "OPEN", "product_id": "P1", "stage": "s1"}, td)
    want, _ = sd.plan(station, td)
    return (want == [], "建卡=%s" % want)


@case(7, "回执重名：同 id 写两次", "两份文件，历史不覆盖")
def q7(td, b, station, r):
    ss.append_receipt(station, {"id": "R1", "verdict": "FAILED", "ts": "2026-11-11T10:00:00",
                                "why": "第一次失败"}, td)
    ss.append_receipt(station, {"id": "R1", "verdict": "DONE", "ts": "2026-11-11T11:00:00",
                                "why": "第二次成功"}, td)
    d = os.path.join(b, "rt", station, "receipts")
    files = sorted(os.listdir(d))
    return (len(files) == 2, "回执文件=%s" % files)


@case(8, "并发写片：两线程同时 upsert", "两张卡都在（写锁生效）")
def q8(td, b, station, r):
    err = []

    def w(i):
        try:
            for _ in range(5):
                ss.upsert(station, {"id": "K%d" % i, "state": "OPEN"}, td)
        except Exception as e:
            err.append(e)

    ts = [threading.Thread(target=w, args=(i,)) for i in range(2)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    rows = ss.read_queue(station, td)
    ids = {x["id"] for x in rows}
    return (ids == {"K0", "K1"} and not err, "卡=%s 异常=%s" % (sorted(ids), err))


@case(9, "交接断头：目标机不存在", "只写 HO- 卡或同机提示，不崩")
def q9(td, b, station, r):
    tax = json.load(open(os.path.join(b, "TAXONOMY-v1.json")))
    tax["task_types"].append({"id": "T-B", "stations": ["ghost"], "judge": "path"})
    tax["stage_map"]["P1"]["s1"] = "T-A"
    tax["stage_map"]["P1"]["s2"] = "T-B"
    json.dump(tax, open(os.path.join(b, "TAXONOMY-v1.json"), "w"), ensure_ascii=False)
    prod = json.load(open(os.path.join(b, "PRODUCTS.json")))
    prod["products"][0]["stages"] = ["s1", "s2"]
    json.dump(prod, open(os.path.join(b, "PRODUCTS.json"), "w"), ensure_ascii=False)
    try:
        h = sd.handoff(station, {"id": "c1", "product_id": "P1", "stage": "s1"}, td)
        return (True, "handoff=%s（目标机不在登记表时安静跳过）" % h)
    except Exception as e:
        return (False, "抛异常: %r" % e)


@case(10, "面板缺席：task_type 无 panel", "必须 BLOCK，不许默认通过")
def q10(td, b, station, r):
    res = pr.review(task_type="T-NO-PANEL", evidence=["x"], generate=lambda p, s: '{"vote":"PASS"}',
                    root=False)
    return (res["verdict"] == "BLOCK", "verdict=%s" % res["verdict"])


@case(11, "产物存在但为空文件", "不许判 DONE（size>0 才算）")
def q11(td, b, station, r):
    p = os.path.join(td, "out", "p1", "s1", "empty.bin")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").close()
    card = {"id": "c", "product_id": "P1", "stage": "s1", "task_type": "T-A",
            "deliverable": "out/p1/s1", "judge": "path", "cmd": "true"}
    verdict, why = sd.verify(station, card, {"ok": True, "rc": 0}, td)
    # 目录里只有空文件 -> 目录 size 可能为 0
    return (verdict == "FAILED", "verdict=%s(%s)" % (verdict, why))


@case(12, "权限件：CEO 发送", "不建卡、不判完成、不代发")
def q12(td, b, station, r):
    want, unk = sd.plan(station, td)
    auth = [u for u in unk if u["stage"] == "s2"]
    return (bool(auth) and "AUTHORITY" in auth[0]["why"], "s2 归因=%s" % (auth[0]["why"] if auth else "缺"))


def run(station="visual", only=None):
    only = set(int(x) for x in only.split(",")) if only else None
    okn = 0
    print("== 工况测试：扮演 %s ==" % station)
    for n, name, expect, fn in CASES:
        if only and n not in only:
            continue
        td, b = sandbox(station=station)
        try:
            try:
                ok, detail = fn(td, b, station, None)
            except Exception as e:
                ok, detail = False, "抛异常: %r" % e
        finally:
            shutil.rmtree(td, ignore_errors=True)
        okn += 1 if ok else 0
        print("%s Q%-2d %-26s 期望=%s\n        实测=%s" % (
            "ok  " if ok else "FAIL", n, name, expect, detail))
    total = len([c for c in CASES if not only or c[0] in only])
    print("[station_qa] %d/%d" % (okn, total))
    return 0 if okn == total else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default="visual")
    ap.add_argument("--only")
    a = ap.parse_args()
    return run(a.station, a.only)


if __name__ == "__main__":
    sys.exit(main())
