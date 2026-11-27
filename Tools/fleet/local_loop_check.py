#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_loop_check.py - 每台机的本地闭环体检（断网也要能出活）。

CEO 2026-11-11：「每个机器都要本地闭环，只有产出和统计、排单信息共享什么的上云。」

闭环五查（全部通过才算这台机能独立干活）：
  L1 本地推理   127.0.0.1 上的模型服务能答（断网也无所谓，它是本机）
  L2 分片可写   rt/<工位>/ 能写能删（否则干完记不下来）
  L3 队列可读   自己的 queue.jsonl 能读（坏行不算失败）
  L4 判据在盘   该机承接工序用到的判据脚本存在（否则自验是假的）
  L5 产物可落   out/<工位>/ 可写（产出没地方落 = 白干）

用法：
  python3 Tools/fleet/local_loop_check.py --station control
  python3 Tools/fleet/local_loop_check.py --station visual --no-net   # 只查文件面
  python3 Tools/fleet/local_loop_check.py --all
  python3 Tools/fleet/local_loop_check.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")

sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402
import local_model as lm  # noqa: E402

# judge 名 -> 判据脚本（缺了就等于没有自验能力）
JUDGE_FILES = {
    "drama_rules": "Tools/fleet/drama_rules.py",
    "voice_gate": "Tools/fleet/voice_gate.py",
    "family_check": "Tools/family_compliance_check.py",
    "game_submit_pack": "Tools/fleet/game_submit_pack.py",
    "kf_hand_face": "Tools/fleet/drama_rules.py",
}


def _load(name, root=None):
    base = os.path.join(root, "cph4", "fleet") if root else F
    with open(os.path.join(base, name), encoding="utf-8") as f:
        return json.load(f)


def _probe_model(url, timeout=1.5):
    try:
        with urllib.request.urlopen(url + "/api/tags", timeout=timeout) as r:
            data = json.loads(r.read() or b"{}")
        return [m.get("name") for m in (data.get("models") or []) if m.get("name")]
    except Exception:
        return []


def check(station, root=None, net=True, url="http://127.0.0.1:11434"):
    """返回 [(项, 通过?, 说明)]。"""
    rroot = root or ROOT
    out = []
    tax = _load("TAXONOMY-v1.json", root)
    types = {t["id"]: t for t in tax["task_types"]}
    smap = tax.get("stage_map") or {}
    products = _load("PRODUCTS.json", root)["products"]

    # 本机承接哪些判据
    judges, stages = set(), 0
    for p in products:
        for st in (p.get("stages") or []):
            tid = (smap.get(p["id"]) or {}).get(st)
            if not tid or tid not in types:
                continue
            t = types[tid]
            if station not in (t.get("stations") or []):
                continue
            stages += 1
            j = t.get("judge")
            if j and j not in ("manual", "human", "path", "hash"):
                judges.add(j)

    # L1 本地推理：只有本机才能验 127.0.0.1——异地机器必须在那台机上跑，不许替它签字
    here = lm.local_station()
    if station != here:
        out.append(("L1 本地推理", None, "需在 %s 本机执行（当前主机=%s）" % (station, here)))
    elif not net:
        out.append(("L1 本地推理", None, "未检查（--no-net）"))
    else:
        models = _probe_model(url)
        if models:
            out.append(("L1 本地推理", True, "本机模型服务可用（%d 个模型）" % len(models)))
        else:
            out.append(("L1 本地推理", False, "127.0.0.1 上没有模型服务：断网即停工"))

    # L2 分片可写
    try:
        d = ss.rt_dir(station, root)
        os.makedirs(d, exist_ok=True)
        probe = os.path.join(d, ".write-probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        out.append(("L2 分片可写", True, d))
    except Exception as e:
        out.append(("L2 分片可写", False, str(e)[:80]))

    # L3 队列可读
    try:
        rows = ss.read_queue(station, root)
        out.append(("L3 队列可读", True, "%d 张卡" % len(rows)))
    except Exception as e:
        out.append(("L3 队列可读", False, str(e)[:80]))

    # L4 判据在盘
    missing = [j for j in judges if not os.path.exists(os.path.join(rroot, JUDGE_FILES.get(j, "")))]
    if missing:
        out.append(("L4 判据在盘", False, "缺判据脚本: " + ",".join(sorted(missing))))
    else:
        out.append(("L4 判据在盘", True, "承接 %d 道工序，判据齐（%s）" % (
            stages, ",".join(sorted(judges)) or "无需脚本判据")))

    # L5 产物可落
    try:
        d = os.path.join(rroot, "cph4", "fleet", "out", station)
        os.makedirs(d, exist_ok=True)
        probe = os.path.join(d, ".write-probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        out.append(("L5 产物可落", True, os.path.join("cph4", "fleet", "out", station)))
    except Exception as e:
        out.append(("L5 产物可落", False, str(e)[:80]))
    return out


def report(station, rows):
    bad = [r for r in rows if r[1] is False]
    skip = [r for r in rows if r[1] is None]
    print("== %s 本地闭环 ==" % station)
    for name, ok, why in rows:
        tag = "PASS" if ok is True else ("SKIP" if ok is None else "FAIL")
        print("  %s %-12s %s" % (tag, name, why))
    if bad:
        print("  结论：不能闭环（%d 项不过）" % len(bad))
    elif skip:
        print("  结论：文件面通过；%d 项需在该机自测（不能替它签字）" % len(skip))
    else:
        print("  结论：可独立闭环")
    return 1 if bad else 0


def self_test():
    import tempfile
    ok = 0
    total = 0

    def chk(name, cond):
        nonlocal ok, total
        total += 1
        ok += 1 if cond else 0
        print("%s %s" % ("ok  " if cond else "FAIL", name))

    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, "cph4", "fleet")
        os.makedirs(os.path.join(base, "rt", "control"))
        json.dump({"task_types": [
            {"id": "T-A", "stations": ["control"], "judge": "drama_rules"},
            {"id": "T-B", "stations": ["control"], "judge": "manual"}],
            "stage_map": {"P": {"x": "T-A", "y": "T-B"}}},
            open(os.path.join(base, "TAXONOMY-v1.json"), "w"))
        json.dump({"products": [{"id": "P", "stages": ["x", "y"]}]},
                  open(os.path.join(base, "PRODUCTS.json"), "w"))

        rows = check("control", td, net=False)
        d = {n: (o, w) for n, o, w in rows}
        chk("文件面五项齐全", set(d) == {"L1 本地推理", "L2 分片可写", "L3 队列可读",
                                       "L4 判据在盘", "L5 产物可落"})
        chk("异地/未查的 L1 记 SKIP 而非 PASS", d["L1 本地推理"][0] is None)
        chk("缺判据脚本必须 FAIL",
            d["L4 判据在盘"][0] is False and "drama_rules" in d["L4 判据在盘"][1])
        chk("分片可写 PASS", d["L2 分片可写"][0] is True)
        chk("人判型不要求脚本", "manual" not in d["L4 判据在盘"][1])

        # 放一个同名判据脚本后应变 PASS
        os.makedirs(os.path.join(td, "Tools", "fleet"), exist_ok=True)
        open(os.path.join(td, "Tools", "fleet", "drama_rules.py"), "w").write("# stub\n")
        rows2 = check("control", td, net=False)
        chk("判据补齐后 PASS",
            [o for n, o, _ in rows2 if n == "L4 判据在盘"][0] is True)

    print("[local_loop_check] %d/%d" % (ok, total))
    return 0 if ok == total else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", choices=list(ss.STATIONS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--root", default=None)
    ap.add_argument("--no-net", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    targets = list(ss.STATIONS) if a.all else ([a.station] if a.station else ["control"])
    rc = 0
    for st in targets:
        rc = max(rc, report(st, check(st, a.root, net=not a.no_net)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
