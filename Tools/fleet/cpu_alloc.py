#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cpu_alloc.py - CPU 算力分配执行体（数据正身=cph4/fleet/CPU-PLAN-v1.json）。

CEO 2026-11-11：「我每个机器都有强大的 CPU，尤其是算力大脑，规划好 CPU 的算力」。

它只回答三个问题，全部可算：
  1) 这台机现在能给这类活几个并行？（留核律 + 白天律 + 内存卡）
  2) 这类活该排哪几台、每台几并行、为什么（含禁区：无 AVX2 的大脑禁 CPU 推理）
  3) 排不下时缺多少核（缺口要报数，不许"看着能跑"）

用法：
  python3 Tools/fleet/cpu_alloc.py plan                    # 全表：每机每类并行度
  python3 Tools/fleet/cpu_alloc.py assign --class transcode --tasks 4
  python3 Tools/fleet/cpu_alloc.py status                  # 本机核数/负载 vs 计划
  python3 Tools/fleet/cpu_alloc.py --self-test
Exit: 0 正常；1 判据不过；2 配置异常
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
PLAN = os.path.join(FLEET, "CPU-PLAN-v1.json")
OUT = os.path.join(FLEET, "state", "cpu-plan.json")
RAM_HEADROOM = 0.8          # 单机同时占用不超过内存 80%
MEM_RESERVED_GB = 8.0       # 系统与 GPU 喂数据的常驻内存


def load_plan(path=PLAN):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def night_now(ts=None):
    h = time.localtime(ts or time.time()).tm_hour
    return h >= 20 or h < 8


def share(machine, night=None):
    night = night_now() if night is None else night
    return float(machine.get("night_share" if night else "day_share") or 0)


def forbidden(plan, mid, cls):
    for f in plan.get("forbid") or []:
        if f.get("machine") != mid:
            continue
        pat = f.get("class") or ""
        if pat == cls or (pat.startswith("*") and pat.strip("*") in cls):
            return f.get("why")
    return None


def capacity(plan, mid, cls, night=None):
    """单机单类的并行上限 = min(核数份额÷单任务线程, 内存份额÷单任务内存)。"""
    m = (plan.get("machines") or {}).get(mid)
    c = (plan.get("classes") or {}).get(cls)
    if not m or not c:
        return {"machine": mid, "class": cls, "parallel": 0, "why": "未定义"}
    why = forbidden(plan, mid, cls)
    if why:
        return {"machine": mid, "class": cls, "parallel": 0, "why": "禁区：" + why}
    if mid not in (c.get("machines") or []):
        return {"machine": mid, "class": cls, "parallel": 0, "why": "不在该活允许的机器里"}
    degraded = ""
    threads = max(1, c.get("threads", 1))
    if c.get("needs_avx2") and not m.get("avx2"):
        fb = c.get("no_avx2_fallback")
        if not fb:
            return {"machine": mid, "class": cls, "parallel": 0,
                    "why": "该机无 AVX2，此活需要 AVX2"}
        threads = max(1, int(fb.get("threads") or threads))
        degraded = fb.get("why") or "无 AVX2 降速档"
    usable_cores = max(0.0, m.get("cores", 0) * share(m, night) - m.get("reserve_cores", 0))
    by_core = int(usable_cores // threads)
    mem_budget = m.get("ram_gb", 0) * RAM_HEADROOM - MEM_RESERVED_GB
    by_mem = int(mem_budget // max(0.1, c.get("mem_gb", 1)))
    parallel = max(0, min(by_core, by_mem))
    limiter = "核数" if by_core <= by_mem else "内存"
    return {"machine": mid, "class": cls, "parallel": parallel, "threads": threads,
            "usable_cores": round(usable_cores, 1), "by_core": by_core, "by_mem": by_mem,
            "limited_by": limiter, "degraded": degraded or None,
            "why": "%s 份额 %.2f，留 %s 核 → 可用 %.1f 核；内存 %.1fG 预算"
                   % ("夜窗" if (night if night is not None else night_now()) else "白天",
                      share(m, night), m.get("reserve_cores"), usable_cores, mem_budget)}


def assign(plan, cls, tasks, night=None):
    if cls not in (plan.get("classes") or {}):
        return {"ok": False, "why": "未定义的活类：%s（现有：%s）"
                % (cls, ",".join(sorted((plan.get("classes") or {}).keys())))}
    rows = [capacity(plan, mid, cls, night) for mid in sorted((plan.get("machines") or {}).keys())]
    total = sum(r["parallel"] for r in rows)
    left = int(tasks)
    for r in rows:
        r["take"] = min(r["parallel"], left) if r["parallel"] else 0
        left -= r["take"]
    return {"ok": True, "class": cls, "tasks": tasks, "capacity": total,
            "assigned": tasks - max(0, left), "short": max(0, left), "rows": rows,
            "note": "排不下就先报缺口，不许硬塞（塞进去只会互相拖慢）" if left > 0 else ""}


def local_machine(plan):
    try:
        sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
        import local_model as lm
        return lm.local_station()
    except Exception:
        return None


def local_cores():
    try:
        if sys.platform == "darwin":
            return int(subprocess.run(["sysctl", "-n", "hw.ncpu"], capture_output=True,
                                      text=True, timeout=5).stdout.strip())
        return os.cpu_count() or 0
    except Exception:
        return os.cpu_count() or 0


def local_load():
    try:
        if sys.platform == "darwin":
            out = subprocess.run(["sysctl", "-n", "vm.loadavg"], capture_output=True,
                                 text=True, timeout=5).stdout
            return float(out.split("{")[1].split()[0])
        return os.getloadavg()[0]
    except Exception:
        return -1.0


def status(plan):
    mid = local_machine(plan)
    cores = local_cores()
    load = local_load()
    rows = []
    if mid:
        for cls in sorted((plan.get("classes") or {}).keys()):
            rows.append(capacity(plan, mid, cls))
    return {"station": mid, "cores": cores, "load1": round(load, 2),
            "busy_pct": round(load / cores * 100, 1) if cores and load >= 0 else None,
            "night": night_now(), "classes": rows}


# ---------------------------------------------------------------- 有界实测锚点

BENCH_FILE = os.path.join(FLEET, "state", "cpu-bench.json")


def bench(seconds=3, workers=8):
    """有界 CPU 锚点：sha256 吃满单核/多核，各跑 seconds 秒（默认合计 6 秒）。
    只用来横向比各机核力（E5-2695v2 与 9950X 差一个档），不做绝对跑分。"""
    import hashlib
    import threading
    block = os.urandom(1 << 20)          # 1MB 定长块，避免内存带宽干扰

    def _run(nthreads):
        counts = [0] * nthreads
        deadline = time.time() + seconds

        def work(i):
            n = 0
            while time.time() < deadline:
                hashlib.sha256(block).digest()
                n += 1
            counts[i] = n

        ts = [threading.Thread(target=work, args=(i,)) for i in range(nthreads)]
        t0 = time.time()
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        wall = time.time() - t0
        return round(sum(counts) / wall, 1)          # MB/s

    one = _run(1)
    many = _run(max(1, min(workers, local_cores() or 2)))
    st = None
    try:
        sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
        import local_model as lm
        st = lm.local_station()
    except Exception:
        pass
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "station": st or "unknown",
           "cores": local_cores(), "workers": max(1, min(workers, local_cores() or 2)),
           "single_mb_s": one, "multi_mb_s": many,
           "scale": round(many / one, 2) if one else None, "seconds": seconds}
    try:
        data = {}
        if os.path.exists(BENCH_FILE):
            with open(BENCH_FILE, encoding="utf-8") as f:
                data = json.load(f)
        data[row["station"]] = row
        os.makedirs(os.path.dirname(BENCH_FILE), exist_ok=True)
        with open(BENCH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return row


def self_test():
    plan = load_plan()
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    # 1) 无 AVX2 的大脑绝不接需要 AVX2 的活
    r = capacity(plan, "brain", "asr-post")
    chk("大脑(无 AVX2) 不接 asr-post", r["parallel"] == 0, r)
    r = capacity(plan, "brain", "transcode")
    chk("大脑可接 transcode（但注明 veryfast 限制）", r["parallel"] >= 1, r)

    # 2) 留核律：并行×线程 + 留核 ≤ 核数
    bad = []
    for mid, m in (plan.get("machines") or {}).items():
        for cls, c in (plan.get("classes") or {}).items():
            cap = capacity(plan, mid, cls, night=True)
            if cap["parallel"] > 0:
                need = cap["parallel"] * c["threads"] + m["reserve_cores"]
                if need > m["cores"]:
                    bad.append((mid, cls, need, m["cores"]))
    chk("留核律：并行×线程+留核 从不超核数", not bad, bad)

    # 3) 白天份额更严：白天并行 ≤ 夜窗并行
    worse = []
    for mid in (plan.get("machines") or {}):
        for cls in (plan.get("classes") or {}):
            d = capacity(plan, mid, cls, night=False)["parallel"]
            n = capacity(plan, mid, cls, night=True)["parallel"]
            if d > n:
                worse.append((mid, cls, d, n))
    chk("白天律：白天并行不超过夜窗", not worse, worse)

    # 4) 内存卡：回测只在大脑（256G），别的机排不下
    others = [mid for mid in (plan.get("machines") or {})
              if mid != "brain" and capacity(plan, mid, "backtest")["parallel"] > 0]
    chk("回测只排内存够的机（其他机 0）", not others, others)

    # 5) 未定义活类要明确拒绝而不是瞎猜
    r = assign(plan, "no-such-class", 1)
    chk("未定义活类 -> 拒绝并列出可选项", r["ok"] is False and "现有" in r["why"], r)

    # 6) 排不下要报缺口
    r = assign(plan, "backtest", 999, night=True)
    chk("任务超容量 -> short>0 且不硬塞", r["ok"] and r["short"] > 0 and r["assigned"] <= r["capacity"], r)

    # 7) 有活且有容量时能给到并行度
    r = assign(plan, "rule-check", 3, night=True)
    chk("rule-check 可分配", r["ok"] and r["assigned"] == 3, r)

    # 8) 禁区配置自身要么指向存在的机，要么是全通配
    bad_f = [f for f in (plan.get("forbid") or []) if f.get("machine") not in (plan.get("machines") or {})]
    chk("forbid 里的机器名都存在", not bad_f, bad_f)

    print("[cpu_alloc] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="plan",
                    choices=["plan", "assign", "status", "bench"])
    ap.add_argument("--class", dest="cls", default="rule-check")
    ap.add_argument("--tasks", type=int, default=1)
    ap.add_argument("--night", action="store_true", help="按夜窗份额算")
    ap.add_argument("--seconds", type=int, default=3, help="bench 每档秒数（有界）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()
    try:
        plan = load_plan()
    except Exception as e:
        print("配置读不了：%s" % e)
        return 2

    night = True if a.night else None
    if a.cmd == "plan":
        print("时刻：%s" % ("夜窗份额" if (night if night is not None else night_now()) else "白天份额"))
        classes = sorted((plan.get("classes") or {}).keys())
        machines = sorted((plan.get("machines") or {}).keys())
        print("%-12s %s" % ("活类", " ".join("%-8s" % m for m in machines)))
        for cls in classes:
            cells = []
            for mid in machines:
                cap = capacity(plan, mid, cls, night)
                cells.append("%-8s" % ("-" if cap["parallel"] == 0 else cap["parallel"]))
            print("%-12s %s" % (cls, " ".join(cells)))
        try:
            with open(BENCH_FILE, encoding="utf-8") as f:
                b = json.load(f)
            print("\n实测锚点（sha256 MB/s，只比核力不比跑分）：")
            for mid, r in sorted(b.items()):
                print("  %-10s 单核 %6.1f  多核 %7.1f  ×%s" % (mid, r["single_mb_s"],
                                                             r["multi_mb_s"], r["scale"]))
        except Exception:
            print("\n实测锚点：尚未测（各机跑 `cpu_alloc.py bench` 自报）")
        print("\n合计核心：%d 核 / %d 线程"
              % (sum(m["cores"] for m in plan["machines"].values()),
                 sum(m["threads"] for m in plan["machines"].values())))
        for cls in classes:
            tot = sum(capacity(plan, mid, cls, night)["parallel"] for mid in machines)
            print("  %-12s 全队并行上限 %d" % (cls, tot))
    elif a.cmd == "assign":
        r = assign(plan, a.cls, a.tasks, night)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        if not r["ok"]:
            return 1
    elif a.cmd == "bench":
        r = bench(seconds=max(1, min(a.seconds, 8)))
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        st = status(plan)
        print("本机 %s：%d 核，load1=%.2f（%.1f%%），%s"
              % (st["station"], st["cores"], st["load1"], st["busy_pct"] or 0,
                 "夜窗" if st["night"] else "白天"))
        for c in st["classes"]:
            print("  %-12s 可并行 %-2d %s" % (c["class"], c["parallel"], c["why"]))

    try:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "cmd": a.cmd,
                       "plan": {"machines": sorted((plan.get("machines") or {})),
                                "classes": sorted((plan.get("classes") or {}))},
                       "assign": assign(plan, a.cls, a.tasks, night) if a.cmd == "assign" else None},
                      f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
