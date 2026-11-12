#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chain_cases.py - 全链路工况矩阵（分情况、多轮、含负控）。

Why（2026-11-12，CEO 追问"测了这么多轮怎么没发现问题"）：
根因不是测得不够多，是**测的形态不对**。原来的自检都在测"单次调用的返回值"，
而这一轮暴露的三类缺陷必须同时满足三个条件才会出现：
    多轮（每 5 分钟一轮） × 多分片（卡落在别的工位） × 新旧格式混存。
单轮单分片的用例永远照不到它们。所以这个文件专门测"连续跑会发生什么"，
并且每条关键断言都配一个负控——把闸拆掉必须变红，否则等于没有闸。

覆盖：
  A 供给去重   多轮 / 跨分片 / 老格式 / 产物签名未变 / BLOCKED 族 / 负控
  B 僵尸救援   心跳新鲜不动 / 心跳缺失才动 / 卡龄未超宽限不动 / 非主控不做
  C 抽验四态   已抽满 / 无回执 / 配置为 0 / 有候选却没抽到
  D 执行体     无心跳报红 / 心跳新鲜不报 / 轮次自增
  E 端到端     三轮只执行一次（不重复扣费）

用法：
    python3 Tools/fleet/chain_cases.py            # 跑全部工况
    python3 Tools/fleet/chain_cases.py -v         # 同时打印沙箱路径
返回码：0 全过 / 1 有用例失败
"""
from __future__ import annotations

import contextlib
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

import master_patrol as mp       # noqa: E402
import station_drive as sd       # noqa: E402
import station_shards as ss      # noqa: E402

OK = 0
FAILS = []


def chk(name, cond, detail=""):
    global OK
    if cond:
        OK += 1
        print("ok   %s" % name)
    else:
        FAILS.append("%s | %s" % (name, detail))
        print("FAIL %s | %s" % (name, detail))


@contextlib.contextmanager
def box(products=None, types=None, stations=None, accept=None, stage_map=None):
    """一个完整的 fleet 沙箱：五份分片 + 配置齐备，用完即删。"""
    td = tempfile.mkdtemp(prefix="chain-")
    b = os.path.join(td, "cph4", "fleet")
    for s in ss.STATIONS:
        os.makedirs(os.path.join(b, "rt", s, "receipts"), exist_ok=True)
    for d in ("state",):
        os.makedirs(os.path.join(b, d), exist_ok=True)
    os.makedirs(os.path.join(td, "out"), exist_ok=True)
    prod = {"products": products or [{
        "id": "PROD-P1", "stages": ["草稿"],
        "outputs": {"草稿": "out/p1.txt"},
        "commands": {"草稿": "echo hi > out/p1.txt"}}]}
    tax = {"task_types": types or [{"id": "T-C", "stations": ["control"],
                                    "refresh_h": 24, "judge": "path"}],
           "stage_map": stage_map or {"PROD-P1": {"草稿": "T-C"}}}
    json.dump(prod, open(os.path.join(b, "PRODUCTS.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(tax, open(os.path.join(b, "TAXONOMY-v1.json"), "w", encoding="utf-8"), ensure_ascii=False)
    sts = {"stations": [{"id": s, "status": (stations or {}).get(s, "ready"),
                         "charter": "x", "min_free_gb": 0} for s in ss.STATIONS]}
    json.dump(sts, open(os.path.join(b, "STATIONS.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(accept or {"sample_per_day": {"control": 3}},
              open(os.path.join(b, "ACCEPTANCE-v1.json"), "w", encoding="utf-8"))
    try:
        yield td
    finally:
        shutil.rmtree(td, ignore_errors=True)


def _cards(td, stage=("PROD-P1", "草稿")):
    return [c for c in ss.read_queue("control", td) if ss.stage_key(c) == stage]


def _running(td, station, cid, age_min, **extra):
    ts = (datetime.now() - timedelta(minutes=age_min)).isoformat(timespec="seconds")
    row = {"id": cid, "station": station, "state": "RUNNING", "owner": station,
           "claimed_at": ts, "created_at": ts, "needs": "cpu", "deliverable": "out/x.txt"}
    row.update(extra)
    ss.upsert(station, row, td)
    return row


def _receipt(td, station, cid, verdict="DONE"):
    """造一份合格回执 + 产物（sha 与产物一致）。"""
    out = os.path.join(td, "out", "p1.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("hi\n")
    rcpt = {"id": cid, "station": station, "verdict": verdict,
            "deliverable": "out/p1.txt", "sha256": mp._sha(out), "judge": "path",
            "ts": datetime.now().isoformat(timespec="seconds")}
    d = os.path.join(td, "cph4", "fleet", "rt", station, "receipts")
    os.makedirs(d, exist_ok=True)
    json.dump(rcpt, open(os.path.join(d, cid + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    return rcpt


# ---------------------------------------------------------------- A 供给去重
def case_supply():
    # A1 多轮：同一工序连续 6 轮，产物新鲜后不再建卡
    with box() as td:
        for _ in range(6):
            sd.once("control", td, run_limit=3)
        cs = _cards(td)
        chk("A1 连续 6 轮同工序只建 1 张卡", len(cs) == 1, [c["id"] for c in cs])
        chk("A1 该卡已 DONE", bool(cs) and cs[0].get("state") == "DONE", cs)

    # A1b 负控：卡在**别的分片**时，拆掉跨分片视图 -> 必须重建（证明闸真在起作用）
    with box() as td:
        _running(td, "visual", "V-RUN2", 1, product_id="PROD-P1", stage="草稿")
        orig = ss.inflight
        ss.inflight = lambda *a, **k: {}
        try:
            want, _ = sd.plan("control", td)
        finally:
            ss.inflight = orig
        chk("A1b 负控：拆掉 inflight -> 跨分片看不见，会重复建", want != [], want)

    # A2 同工序的卡落在别的分片（RUNNING）-> 本工位不建
    with box() as td:
        _running(td, "visual", "V-RUN", 1, product_id="PROD-P1", stage="草稿")
        want, _ = sd.plan("control", td)
        chk("A2 别的分片有在飞卡 -> 不重建", want == [], want)

    # A3 老格式卡（没有 product_id，只有标题）也要能挡住
    with box() as td:
        ss.upsert("visual", {"id": "V-OLD", "title": "[self-drive] PROD-P1 · 草稿",
                             "state": "RUNNING",
                             "claimed_at": datetime.now().isoformat(timespec="seconds")}, td)
        want, _ = sd.plan("control", td)
        chk("A3 老格式卡（只靠标题）也能挡住重建", want == [], want)

    # A4 上次 DONE 但产物内容没变（只有 mtime 被 touch）-> 报缺陷，不建卡
    with box() as td:
        p = os.path.join(td, "out", "p1.txt")
        open(p, "w", encoding="utf-8").write("hi\n")
        sig = sd._prodsig(p)
        ss.upsert("control", {"id": "C-DONE", "product_id": "PROD-P1", "stage": "草稿",
                              "state": "DONE", "deliverable": "out/p1.txt",
                              "product_sig": sig, "judge": "path",
                              "cmd": "echo hi > out/p1.txt",
                              "finished_at": datetime.now().isoformat(timespec="seconds")}, td)
        old = time.time() - 3 * 24 * 3600
        os.utime(p, (old, old))          # 过期，但内容一字节没变
        want, unknown = sd.plan("control", td)
        chk("A4 跑完产物没变 -> 不建卡且报 OUTPUT-NOT-REFRESHED",
            want == [] and any("OUTPUT-NOT-REFRESHED" in u["why"] for u in unknown),
            (want, [u["why"] for u in unknown]))

    # A5 产物有新内容且过期 -> 允许重建（负控：闸不能过严）
    with box() as td:
        p = os.path.join(td, "out", "p1.txt")
        open(p, "w", encoding="utf-8").write("hi\n")
        sig = sd._prodsig(p)
        ss.upsert("control", {"id": "C-DONE2", "product_id": "PROD-P1", "stage": "草稿",
                              "state": "DONE", "deliverable": "out/p1.txt",
                              "product_sig": sig, "judge": "path",
                              "cmd": "echo hi > out/p1.txt",
                              "finished_at": datetime.now().isoformat(timespec="seconds")}, td)
        open(p, "a", encoding="utf-8").write("new line\n")
        old = time.time() - 3 * 24 * 3600
        os.utime(p, (old, old))
        want, _ = sd.plan("control", td)
        chk("A5 产物有新内容且过期 -> 允许重建", [w["stage"] for w in want] == ["草稿"], want)

    # A6 BLOCKED 属于在飞，不许每轮刷卡
    with box() as td:
        ss.upsert("control", {"id": "C-BLK", "product_id": "PROD-P1", "stage": "草稿",
                              "state": "BLOCKED", "deliverable": "out/p1.txt"}, td)
        want, _ = sd.plan("control", td)
        chk("A6 BLOCKED 在飞 -> 不重建", want == [], want)


# ---------------------------------------------------------------- B 僵尸救援
def case_rescue():
    # B1 负控：心跳新鲜 -> 一张都不许动
    with box() as td:
        _running(td, "visual", "V-LIVE", 600)
        ss.heartbeat_write("visual", td)
        got, note = sd.rescue_stale("control", td)
        chk("B1 负控：心跳新鲜 -> 不救援", got == [] and "不动" in note, (got, note))

    # B2 心跳缺失 -> 主控代回收（带留痕）
    with box() as td:
        _running(td, "visual", "V-DEAD", 600)
        got, note = sd.rescue_stale("control", td)
        rows = {c["id"]: c for c in ss.read_queue("visual", td)}
        chk("B2 心跳缺失 -> 回收为 OPEN 且带 rescue_by",
            len(got) == 1 and rows["V-DEAD"]["state"] == "OPEN"
            and rows["V-DEAD"].get("rescue_by") == "control",
            (got, rows.get("V-DEAD")))

    # B3 心跳超时但卡龄未超宽限 -> 不救（防误杀刚接手的机器）
    with box() as td:
        _running(td, "visual", "V-YOUNG", 10)
        hb = ss.heartbeat_write("visual", td)
        hb["ts"] = (datetime.now() - timedelta(minutes=60)).isoformat(timespec="seconds")
        json.dump(hb, open(ss.heartbeat_path("visual", td), "w", encoding="utf-8"))
        got, _ = sd.rescue_stale("control", td)
        chk("B3 卡龄未超宽限 -> 不救", got == [], got)

    # B4 非主控不许跨机救援（多机互救会互相踩）
    with box() as td:
        _running(td, "visual", "V-X", 600)
        got, note = sd.rescue_stale("visual", td)
        chk("B4 非主控调用 -> 一律不做", got == [] and "只有主控" in note, (got, note))

    # B5 没有 RUNNING 卡时不产生任何动作（不刷噪声）
    with box() as td:
        got, note = sd.rescue_stale("control", td)
        chk("B5 无 RUNNING 卡 -> 空动作", got == [] and note == "", (got, note))


# ---------------------------------------------------------------- C 抽验四态
def case_acceptance():
    # C1 当天全抽完 -> 不该报红（这是本轮实测的假红）
    with box() as td:
        for i in range(3):
            _receipt(td, "control", "R%d" % i)
        led = os.path.join(td, "cph4", "fleet", "state", "acceptance-ledger.jsonl")
        with open(led, "w", encoding="utf-8") as f:
            for i in range(3):
                f.write(json.dumps({"station": "control", "id": "R%d" % i}) + "\n")
        res, fails = mp.sample(td)
        meta = getattr(mp.sample, "last_meta", {})
        chk("C1 今日已抽满 -> 不报 NO-SAMPLE",
            res == [] and mp.no_sample_issue(meta) is None, (res, meta))

    # C2 没有任何合格回执 -> 不报红（链路还没产出，不等于闸坏了）
    with box() as td:
        res, _ = mp.sample(td)
        meta = getattr(mp.sample, "last_meta", {})
        chk("C2 没有合格回执 -> 不报 NO-SAMPLE", res == [] and mp.no_sample_issue(meta) is None, meta)

    # C3 抽验比例为 0 -> 必须报（配置问题）
    with box(accept={"sample_per_day": {"control": 0}}) as td:
        _receipt(td, "control", "R-Z")
        mp.sample(td)
        meta = getattr(mp.sample, "last_meta", {})
        chk("C3 配置比例为 0 -> 必须报红", mp.no_sample_issue(meta) is not None, meta)

    # C4 有未抽的候选却一份没抽到 -> 必须报（真 bug）
    with box() as td:
        _receipt(td, "control", "R-NEW")
        mp.sample(td, limit_override=0)
        meta = getattr(mp.sample, "last_meta", {})
        iss = mp.no_sample_issue(meta)
        chk("C4 有候选却没抽到 -> 必须报红", iss is not None and "逻辑有问题" in iss["why"], iss)

    # C5 正常抽验：产物在盘 + 哈希一致 -> PASS
    with box() as td:
        _receipt(td, "control", "R-OK")
        res, fails = mp.sample(td)
        chk("C5 正常抽验 -> PASS 且失败 0",
            len(res) == 1 and res[0]["pass"] and fails == 0, (res, fails))


# ---------------------------------------------------------------- D 执行体
def case_executor():
    with box(stations={"control": "ready"}) as td:
        snap = {"machines": [{"station": "control", "status": "ready"}]}
        iss = mp._executor_issues(snap, td)
        chk("D1 本机 ready 但无心跳 -> 报 STATION-NO-EXECUTOR",
            len(iss) == 1 and iss[0]["kind"] == "STATION-NO-EXECUTOR", iss)

        ss.heartbeat_write("control", td)
        iss2 = mp._executor_issues(snap, td)
        chk("D2 心跳新鲜 -> 不报", iss2 == [], iss2)

        hb1 = ss.heartbeat_write("control", td)
        hb2 = ss.heartbeat_write("control", td)
        chk("D3 心跳轮次自增且带 pid",
            hb2["round"] == hb1["round"] + 1 and hb2["pid"] == os.getpid(), (hb1, hb2))

    with box(stations={"audio": "offline"}) as td:
        snap = {"machines": [{"station": "audio", "status": "offline"}]}
        chk("D4 离线工位不要求心跳（不制造噪声）", mp._executor_issues(snap, td) == [])

    # D5 远端心跳要随分片同步才可见：看不到不等于没注册，一律判死就是假红
    with box(stations={"delivery": "network_ok_not_registered"}) as td:
        snap = {"machines": [{"station": "delivery", "status": "network_ok_not_registered"}]}
        chk("D5 负控：远端无心跳 -> 不判死（避免假红）", mp._executor_issues(snap, td, me="control") == [])

        hb = ss.heartbeat_write("delivery", td)
        hb["ts"] = (datetime.now() - timedelta(minutes=90)).isoformat(timespec="seconds")
        json.dump(hb, open(ss.heartbeat_path("delivery", td), "w", encoding="utf-8"))
        iss = mp._executor_issues(snap, td, me="control")
        chk("D6 远端心跳存在但已停 90 分钟 -> 必须报",
            len(iss) == 1 and "心跳已停" in iss[0]["why"], iss)


# ---------------------------------------------------------------- E 端到端
def case_e2e():
    with box() as td:
        for _ in range(3):
            sd.once("control", td, run_limit=3)
        rc = os.listdir(os.path.join(td, "cph4", "fleet", "rt", "control", "receipts"))
        chk("E1 三轮只执行一次（回执 1 份）", len(rc) == 1, rc)

        rep = sd.once("control", td, run_limit=3)
        chk("E2 第四轮无活可干且不报错", rep.get("ran") == [] and not rep.get("blocked"), rep)

        hb = ss.heartbeat_read("control", td)
        chk("E3 每轮都写心跳（执行体可被判活）", hb and hb.get("round", 0) >= 4, hb)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    print("== 全链路工况矩阵 ==")
    case_supply()
    case_rescue()
    case_acceptance()
    case_executor()
    case_e2e()
    total = OK + len(FAILS)
    print("\n[chain_cases] %d/%d" % (OK, total))
    if FAILS:
        print("失败项：")
        for f in FAILS:
            print("  - " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
