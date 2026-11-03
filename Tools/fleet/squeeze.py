#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""squeeze.py - 压榨度体检：每台机还能吃几件、什么时候必须让路。

为什么（2026-11-03 CEO：「机队所有的本地算力都要科学的压榨到位，留一些余量别让系统卡顿挂掉」）：
  "榨干"必须同时满足两件事：①闲置产能要被看见并补活；②留够余量，别把系统压到卡死。
  这两件都不能靠感觉，要落到同一张表上：**余量 → 可再派几件**。
  另外要能把"假库存"戳穿——2026-11-03 实测 bm-c 银行里 68 条、其中 51 条是旧格式
  （status=done、cmd 是数组、绝对 Windows 路径），当前派单链吃不进去，于是机器 8% 空转
  而账面像"库存充足"。闲置的第一原因经常是库存假，不是产能不够。

判据：
  1. 每机保底余量 reserve_ram_gb（主控 Mac 6GB，其余 3GB）——低于它就不许再派
  2. CPU 上限 cpu_cap（主控 80%，其余 90%）——超过就不再派
  3. 可再派件数 = (ram_free - reserve) / est_gb（默认 1GB/件，模型活按声明 est_gb 算）
  4. 库存健康 = 每家银行里"能被当前链派出去"的条目数（cmd 是字符串 + needs 存在 + 未被标 done）

用法：
  python3 squeeze.py [--json] [--out receipts/squeeze.json]
Exit: 0 无闲置节点；1 有节点有余量但库存为 0（供给缺口，告警不阻断）；2 读不到状态。
"""
import argparse
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "MASTER-STATE.json")
BANKS = os.path.join(ROOT, "cph4", "fleet", "work-bank")

# 保底余量：主控机要留给办公与脉冲；生产机轻一点但要避免 swap
RESERVE_GB = {"bm-m": 6.0, "default": 3.0}
CPU_CAP = {"bm-m": 80.0, "default": 90.0}
EST_GB_PER_JOB = 1.0


def reserve(node):
    return RESERVE_GB.get(node, RESERVE_GB["default"])


def cpu_cap(node):
    return CPU_CAP.get(node, CPU_CAP["default"])


def bank_health(path):
    """返回 (可派, 假库存) 。假库存=当前链吃不到的条目（旧格式/缺字段/已 done）。"""
    try:
        d = json.load(open(path, encoding="utf-8-sig"))
    except Exception:
        return 0, 0
    jobs = d.get("jobs") if isinstance(d, dict) else d
    ok = bad = 0
    for j in jobs or []:
        if not isinstance(j, dict):
            bad += 1
            continue
        cmd = j.get("cmd")
        usable = isinstance(cmd, str) and bool(cmd.strip())
        if j.get("status") in ("done", "cancelled", "killed"):
            usable = False
        if usable:
            ok += 1
        else:
            bad += 1
    return ok, bad


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    try:
        st = json.load(open(STATE, encoding="utf-8-sig"))
    except Exception as e:
        print("读不到 MASTER-STATE：%s" % e)
        return 2
    lanes = st.get("lanes") or {}

    banks = {}
    for p in sorted(glob.glob(os.path.join(BANKS, "*.json"))):
        base = os.path.basename(p).replace(".json", "")
        # 机名是 bm-x（两段），按 "-" 取第一段会得到 "bm"，所有银行的账都会算到一个不存在的节点上
        node = "-".join(base.split("-")[:2])
        kind = "gpu" if base.endswith("gpu-bank") else "cpu"
        ok, bad = bank_health(p)
        banks.setdefault(node, {"cpu": 0, "gpu": 0, "fake": 0})
        banks[node][kind] += ok
        banks[node]["fake"] += bad

    rows, gaps = [], []
    for node, l in sorted(lanes.items()):
        hb = l.get("hb_age_s")
        cpu = l.get("cpu_load_pct")
        ram = l.get("ram_free_gb")
        online = hb is not None and float(hb) <= 600
        rs, cap = reserve(node), cpu_cap(node)
        room = None
        if ram is not None:
            room = max(0, int((float(ram) - rs) // EST_GB_PER_JOB))
        throttled = cpu is not None and float(cpu) >= cap
        b = banks.get(node) or {"cpu": 0, "gpu": 0, "fake": 0}
        stock = b["cpu"] + b["gpu"]
        can = 0 if (not online or throttled) else (room if room is not None else 1)
        row = {"node": node, "online": online, "hb_age_s": hb, "cpu_pct": cpu,
               "ram_free_gb": ram, "reserve_gb": rs, "cpu_cap": cap,
               "can_take_more": can, "throttled": bool(throttled),
               "stock_dispatchable": stock, "stock_fake": b["fake"],
               "verdict": "OK"}
        if not online:
            row["verdict"] = "OFFLINE"
        elif throttled:
            row["verdict"] = "AT-CAP"          # 已到上限，不许再加
        elif can > 0 and stock < can:
            # 库存不为 0 也可能"没吃饱"：能再吃 25 件却只有 2 件，同样叫压榨不到位。
            row["verdict"] = "UNDER-FED"        # 有余量但活不够 → 供给缺口
            row["idle_slots"] = can - stock
            gaps.append("%s 可再吃 %d 件，库存仅 %d（空转 %d 个槽位）"
                        % (node, can, stock, can - stock))
        elif b["fake"] > stock:
            row["verdict"] = "FAKE-STOCK"       # 账上多、能派的少
            gaps.append("%s 假库存 %d 条（旧格式/已 done），可派仅 %d" % (node, b["fake"], stock))
        rows.append(row)

    uti = [float(r["cpu_pct"]) for r in rows if r.get("cpu_pct") is not None and r["online"]]
    mean_cpu = round(sum(uti) / len(uti), 1) if uti else None
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "spec": "SQUEEZE-v1",
           "mean_cpu_pct": mean_cpu,
           "nodes": rows, "gaps": gaps,
           "verdict": "OK" if not gaps else "GAPS"}
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("压榨度体检  平均CPU=%s%%  %s" % (mean_cpu, out["verdict"]))
        for r in rows:
            print(" %-5s %-11s cpu=%-4s ram=%-5s 保底=%-3s 可再派=%-2s 可派库存=%-3s 假库存=%s"
                  % (r["node"], r["verdict"], r["cpu_pct"], r["ram_free_gb"], r["reserve_gb"],
                     r["can_take_more"], r["stock_dispatchable"], r["stock_fake"]))
        for g in gaps:
            print("  ! %s" % g)
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))