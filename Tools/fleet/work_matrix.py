#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""work_matrix.py - 工序×能力×机器 的一致性校验与一屏矩阵。

背景（2026-11-11 复盘）：2250 张在册卡里 task_type 0 个、stage 6 个（0.3%），
派单词表只有 needs=cpu/gpu 两档，机器能力是 28 个模糊词条。也就是说
"哪台机做哪个产品的哪道工序"从来没有被机器表达过，只存在于人的脑子里。

本工具把这一层补上并守住它：
  TAXONOMY-v1.json  任务类型（工具/资源/承接工位/模型档/判据）+ 工序映射
  PRODUCTS.json     产品与工序清单（正身，不改）
  STATIONS.json     机器硬件与状态（正身，不改）

五类缺陷（每种都能指出具体是哪个产品哪道工序）：
  UNMAPPED       产品有工序，但没写任务类型 -> 派单无从判能力
  UNKNOWN_TYPE   映射到的任务类型不存在
  UNSERVICEABLE  任务类型没有任何工位承接（且不是 CEO 物理件）
  HARDWARE       承接工位硬件达不到任务类型的资源下限
  BOTTLENECK     能做的工位全部不在线/未就绪（有活没人干）

用法：
  python3 Tools/fleet/work_matrix.py                 # 校验 + 一屏（rc: 0 干净 / 1 有告警 / 2 有错误）
  python3 Tools/fleet/work_matrix.py --json          # 机读
  python3 Tools/fleet/work_matrix.py --selftest      # 1 正例 + N 反例
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")

# 工位状态里哪些算"现在能接活"
READY = ("ready", "ready_paused", "online", "network_ok_not_registered")


def _load(name):
    with open(os.path.join(F, name), encoding="utf-8") as f:
        return json.load(f)


def evaluate(tax, products, stations):
    """纯函数，便于自检注入假数据。返回 (errors, warnings, matrix)。"""
    errors, warnings = [], []
    types = {t["id"]: t for t in tax["task_types"]}
    smap = tax.get("stage_map") or {}
    smeta = {s["id"]: s for s in stations}

    # 能力反查：任务类型 -> 工位
    demand = {tid: [] for tid in types}
    matrix = {}

    for p in products:
        pid = p["id"]
        m = smap.get(pid) or {}
        matrix[pid] = []
        for stage in (p.get("stages") or []):
            tid = m.get(stage)
            if not tid:
                errors.append(("UNMAPPED", pid, stage, "工序没有任务类型"))
                continue
            if tid not in types:
                errors.append(("UNKNOWN_TYPE", pid, stage, "任务类型不存在: %s" % tid))
                continue
            t = types[tid]
            matrix[pid].append((stage, tid, t.get("stations") or []))
            demand[tid].append((pid, stage))

    # 承接与硬件
    for tid, t in types.items():
        sts = t.get("stations") or []
        if not sts:
            if not t.get("human"):
                errors.append(("UNSERVICEABLE", tid, "-", "没有任何工位承接"))
            continue
        ok_any = False
        for sid in sts:
            s = smeta.get(sid)
            if not s:
                errors.append(("UNSERVICEABLE", tid, sid, "承接工位不存在"))
                continue
            need = t.get("res") or {}
            gpu = (s.get("gpu") or {})
            vram = gpu.get("usable_gb") or gpu.get("vram_gb") or 0
            if need.get("gpu_gb", 0) > vram:
                errors.append(("HARDWARE", tid, sid,
                               "需要显存 %sGB > 本机 %sGB" % (need.get("gpu_gb"), vram)))
                continue
            if need.get("ram_gb", 0) > (s.get("ram_gb") or 0):
                errors.append(("HARDWARE", tid, sid,
                               "需要内存 %sGB > 本机 %sGB" % (need.get("ram_gb"), s.get("ram_gb"))))
                continue
            if need.get("cores", 0) > (s.get("cpu_cores") or 0):
                errors.append(("HARDWARE", tid, sid,
                               "需要核心 %s > 本机 %s" % (need.get("cores"), s.get("cpu_cores"))))
                continue
            # blocked_scope=gpu 的机器：ComfyUI 挂了只影响 GPU 活，剪辑/字幕/清单照跑
            if (s.get("status") or "") in READY or (
                    s.get("blocked_scope") == "gpu" and need.get("gpu_gb", 0) == 0):
                ok_any = True
        if not ok_any:
            warnings.append(("BOTTLENECK", tid, ",".join(sts),
                             "承接工位全部不在线（有活没人干）"))

    # 每台机的负载面（按能承接的任务类型反查被需求的工序数）
    load = {}
    for sid, s in smeta.items():
        tids = [tid for tid, t in types.items() if sid in (t.get("stations") or [])]
        need_stages = sum(len(demand.get(tid) or []) for tid in tids)
        load[sid] = {"machine": s.get("machine"), "status": s.get("status"),
                     "slots": s.get("slots"), "task_types": len(tids),
                     "demanded_stages": need_stages,
                     "shifts": s.get("shifts")}
        if need_stages and (s.get("status") or "") not in READY:
            warnings.append(("IDLE-DEMAND", sid, "-",
                             "%d 道在册工序要这台机，但它当前是 %s" % (need_stages, s.get("status"))))
        if need_stages == 0:
            warnings.append(("NO-DEMAND", sid, "-", "没有任何在册工序需要这台机"))
    # 模型依赖：这些工序要靠算力大脑（MODEL-COMPUTE 的 primary 端点）出文本
    model_stages = sum(1 for rows in matrix.values() for _, tid, _ in rows
                       if str(types[tid].get("model") or "none").startswith("local"))

    # 产物契约覆盖率：没写 outputs 的工序，自驱无从下手（UNKNOWN-OUTPUT）
    tot = sum(len(p.get("stages") or []) for p in products)
    with_out = sum(1 for p in products for st in (p.get("stages") or [])
                   if (p.get("outputs") or {}).get(st))
    coverage = {"total": tot, "with_outputs": with_out, "missing": tot - with_out}
    return errors, warnings, {"products": matrix, "load": load,
                              "model_dependent_stages": model_stages,
                              "outputs_coverage": coverage}


def selftest():
    good_tax = {"task_types": [
        {"id": "T-A", "name": "a", "res": {"gpu_gb": 0, "ram_gb": 4, "cores": 2}, "stations": ["s1"]},
        {"id": "T-CEO", "name": "ceo", "res": {}, "stations": [], "human": True},
    ], "stage_map": {"P": {"步骤1": "T-A", "发送": "T-CEO"}}}
    good_p = [{"id": "P", "stages": ["步骤1", "发送"]}]
    good_s = [{"id": "s1", "machine": "m1", "status": "ready", "cpu_cores": 8, "ram_gb": 32,
               "gpu": {"vram_gb": 8}, "slots": 4, "shifts": ["00-24"]}]

    cases = []
    e, w, _ = evaluate(good_tax, good_p, good_s)
    cases.append(("正例：映射齐全+硬件够", not e, True))
    cases.append(("正例：CEO 物理件不判 UNSERVICEABLE", not any(x[0] == "UNSERVICEABLE" for x in e), True))

    bad = json.loads(json.dumps(good_tax)); bad["stage_map"]["P"].pop("步骤1")
    e, _, _ = evaluate(bad, good_p, good_s)
    cases.append(("反例：漏映射必须报 UNMAPPED", any(x[0] == "UNMAPPED" for x in e), True))

    bad = json.loads(json.dumps(good_tax)); bad["stage_map"]["P"]["步骤1"] = "T-NOT-EXIST"
    e, _, _ = evaluate(bad, good_p, good_s)
    cases.append(("反例：映射到不存在的类型必须报 UNKNOWN_TYPE",
                  any(x[0] == "UNKNOWN_TYPE" for x in e), True))

    bad = json.loads(json.dumps(good_tax)); bad["task_types"][0]["stations"] = []
    e, _, _ = evaluate(bad, good_p, good_s)
    cases.append(("反例：无承接工位必须报 UNSERVICEABLE",
                  any(x[0] == "UNSERVICEABLE" for x in e), True))

    bad = json.loads(json.dumps(good_tax)); bad["task_types"][0]["res"]["gpu_gb"] = 24
    e, _, _ = evaluate(bad, good_p, good_s)
    cases.append(("反例：显存不够必须报 HARDWARE（擦边 8G 机型要 24G）",
                  any(x[0] == "HARDWARE" for x in e), True))

    bad_s = json.loads(json.dumps(good_s)); bad_s[0]["status"] = "offline"
    e, w, _ = evaluate(good_tax, good_p, bad_s)
    cases.append(("反例：工位全离线必须报 BOTTLENECK",
                  any(x[0] == "BOTTLENECK" for x in w), True))

    ok = 0
    for name, got, want in cases:
        good = (got == want)
        ok += 1 if good else 0
        print("%s %s" % ("ok  " if good else "FAIL", name))
    print("[work_matrix] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    tax = _load("TAXONOMY-v1.json")
    products = _load("PRODUCTS.json")["products"]
    stations = _load("STATIONS.json")["stations"]
    errors, warnings, matrix = evaluate(tax, products, stations)

    if a.json:
        print(json.dumps({"errors": errors, "warnings": warnings, "matrix": matrix},
                         ensure_ascii=False, indent=1))
    else:
        print("== 五台机 · 能力与负载 ==")
        for sid, r in matrix["load"].items():
            print("%-9s %-6s %-28s slots=%-2s 可接类型=%-2s 在册工序=%-3s 时段=%s" % (
                sid, r["machine"], r["status"], r["slots"], r["task_types"],
                r["demanded_stages"], ",".join(r["shifts"] or []) or "未定义"))
        print("\n== 产品工序 → 任务类型 → 承接工位 ==")
        for pid, rows in matrix["products"].items():
            for stage, tid, sts in rows:
                print("%-22s %-12s -> %-22s %s" % (pid, stage, tid, ",".join(sts) or "CEO"))
        print("\n== 缺陷 ==")
        for kind, a1, a2, why in errors:
            print("ERROR   %-13s %s/%s  %s" % (kind, a1, a2, why))
        for kind, a1, a2, why in warnings:
            print("WARN    %-13s %s/%s  %s" % (kind, a1, a2, why))
        if not errors and not warnings:
            print("（无）")
        oc = matrix.get("outputs_coverage") or {}
        print("\n产物契约覆盖：%d/%d 道工序有 outputs（缺 %d 道，自驱无从下手）" % (
            oc.get("with_outputs", 0), oc.get("total", 0), oc.get("missing", 0)))
        print("模型依赖工序（需算力大脑出文本）= %d 道" % matrix.get("model_dependent_stages", 0))
        print("[work_matrix] errors=%d warnings=%d" % (len(errors), len(warnings)))
    return 0 if not errors and not warnings else (2 if errors else 1)


if __name__ == "__main__":
    sys.exit(main())
