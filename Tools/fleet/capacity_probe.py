#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capacity_probe.py - 实测本机可持续算力上限（不换页、不降频）。

CEO 2026-11-05：「本机算力利用的极限就是不要进行 swap 硬盘交换，不要过热，好好测这个度」。

为什么要用吞吐衰减当温度信号：
  无 sudo 读不到 SMC 温度（powermetrics 需 root，pmset -g therm 无数据）。
  但过热降频的**后果**可测：同等工作量耗时变长。所以持续压测并分段测吞吐，
  吞吐掉 >15% 即判「已降频」，这是比温度读数更贴近实际的判据。

两项实验：
  1) --mode cpu ：并发 1/2/4/6/8 各压一段，量聚合吞吐与 swap 增量，找拐点。
  2) --mode mem ：按 1GB 阶梯吃内存并触碰页面，量 swap 增量，找「不换页的最大可用内存」。

产物：cph4/fleet/state/capacity-probe.json
Exit: 0 测完；2 环境异常
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "capacity-probe.json")
PAGE = 16384


def swap_mb():
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                             text=True, timeout=5).stdout
        for part in out.split():
            pass
        # "total = 4096.00M used = 2987.12M free = 1108.88M"
        used = out.split("used =")[1].split("M")[0].strip()
        return float(used)
    except Exception:
        return -1.0


def vm():
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return {}
    d = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.rsplit(":", 1)
            v = v.strip().replace(".", "")
            if v.isdigit():
                d[k.strip()] = int(v) * PAGE / 1e9
    return d


def therm():
    try:
        out = subprocess.run(["pmset", "-g", "therm"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""
    lim = None
    for line in out.splitlines():
        low = line.lower()
        if "cpu_speed_limit" in low or "cpu speed limit" in low:
            try:
                lim = int(line.split("=")[-1].strip().rstrip("%"))
            except Exception:
                pass
    return lim


def burn(seconds, acc):
    """固定量的纯计算，用来测「同样工作要多久」。"""
    t0 = time.time()
    x = 0.0
    n = 0
    while time.time() - t0 < seconds:
        for i in range(200000):
            x += (i * 1.0000001) ** 0.5
        n += 1
    acc.append((n, round(time.time() - t0, 3)))


def burn_units(seconds):
    """单进程固定时长计算，返回完成的工作单元数（供跨进程汇总）。"""
    t0 = time.time()
    x = 0.0
    n = 0
    while time.time() - t0 < seconds:
        for i in range(200000):
            x += (i * 1.0000001) ** 0.5
        n += 1
    return n


def run_concurrency(level, seconds):
    # 必须用多进程：Python 线程受 GIL 限制，压不出真并发（否则会得出"加核无用"的假结论）。
    from concurrent.futures import ProcessPoolExecutor
    sw0, m0 = swap_mb(), vm()
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=level) as ex:
        futs = [ex.submit(burn_units, seconds) for _ in range(level)]
        acc = [(f.result(), seconds) for f in futs]
    wall = time.time() - t0
    sw1, m1 = swap_mb(), vm()
    work = sum(n for n, _ in acc)
    return {
        "concurrency": level,
        "wall_s": round(wall, 1),
        "units": work,
        "units_per_s": round(work / wall, 1) if wall else 0,
        "swap_mb_before": sw0,
        "swap_mb_after": sw1,
        "swap_delta_mb": round(sw1 - sw0, 1),
        "avail_gb_before": round((m0.get("Pages free", 0) + m0.get("Pages inactive", 0)
                                  + m0.get("Pages purgeable", 0)), 2),
        "therm_limit": therm(),
    }


def mem_probe(step_gb=1.0, max_gb=26.0):
    rows = []
    held = []
    sw0 = swap_mb()
    comp0 = vm().get("Pages occupied by compressor", 0)
    gb = 0.0
    while gb < max_gb:
        try:
            # 真触碰页面，避免"虚拟分配"骗人
            # 必须填不可压缩数据：零页会被 macOS 压缩器吃掉，
            # 实测用零页能"分配 26GB 而 swap 不变"，那是假象（compressor 偷偷涨到 5.17GB）。
            size = int(step_gb * (1 << 30))
            buf = bytearray(size)
            rnd = os.urandom(4096)
            for i in range(0, size, 4096):
                buf[i:i + 512] = rnd[:512]
            held.append(buf)
        except MemoryError:
            rows.append({"allocated_gb": round(gb, 1), "event": "MemoryError"})
            break
        gb += step_gb
        sw = swap_mb()
        v = vm()
        rows.append({
            "allocated_gb": round(gb, 1),
            "swap_mb": sw,
            "swap_delta_mb": round(sw - sw0, 1),
            "free_gb": round(v.get("Pages free", 0), 2),
            "compressor_gb": round(v.get("Pages occupied by compressor", 0), 2),
        })
        # swap 明显上涨即到界，立刻收手
        comp = v.get("Pages occupied by compressor", 0)
        rows[-1]["compressor_delta_gb"] = round(comp - comp0, 2)
        # 判据看增量：基线 compressor 可能本来就高（实测 4.7GB），绝对值会误判。
        if sw - sw0 > 256 or (comp - comp0) > 1.5:
            break
    del held
    time.sleep(2)
    return {"start_swap_mb": sw0, "start_compressor_gb": round(comp0, 2), "steps": rows,
            "max_no_swap_gb": max([r["allocated_gb"] for r in rows
                                   if r.get("swap_delta_mb", 999) <= 256] or [0])}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["cpu", "mem", "both"], default="both")
    ap.add_argument("--seconds", type=int, default=45)
    ap.add_argument("--levels", default="1,2,4,6,8,10")
    a = ap.parse_args(argv)

    res = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": a.mode,
           "baseline": {"swap_mb": swap_mb(), "vm": vm(), "therm_limit": therm()}}
    if a.mode in ("cpu", "both"):
        rows = []
        for lv in [int(x) for x in a.levels.split(",")]:
            r = run_concurrency(lv, a.seconds)
            rows.append(r)
            print("[probe] 并发 %-2d  吞吐 %8.1f u/s  swap +%.0fMB  限频 %s"
                  % (lv, r["units_per_s"], r["swap_delta_mb"], r["therm_limit"]))
            time.sleep(3)
        best = max(rows, key=lambda r: r["units_per_s"])
        # 拐点：吞吐不再随并发上升（<前一级的 110%）
        knee = rows[0]["concurrency"]
        for prev, cur in zip(rows, rows[1:]):
            if cur["units_per_s"] < prev["units_per_s"] * 1.10:
                break
            knee = cur["concurrency"]
        res["cpu"] = {"rows": rows, "best_concurrency": best["concurrency"],
                      "knee_concurrency": knee,
                      "note": "knee=吞吐不再随并发提升的第一级，超过它只是加热不增产"}
    if a.mode in ("mem", "both"):
        res["mem"] = mem_probe()
        print("[probe] 不换页最大可用内存 ≈ %.1f GB" % res["mem"]["max_no_swap_gb"])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("[probe] 结果 -> %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())