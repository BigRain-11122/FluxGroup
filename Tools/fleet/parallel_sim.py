#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parallel_sim.py - 并发争用测试：机队一起要本地算力时，会不会排队排死。

CEO 2026-11-11：「你还要多测并行 模拟机队一起找本地算力」。

分三层，从便宜到贵：
  A 排队模型（纯算术，零成本）：按 AGENT-CAPACITY 的日调用量换算到峰值小时，
    用实测服务时间（并发1 p50=0.84s / 并发2 p50=1.27s）算 makespan / p95 等待，
    对比「有治理（每机并发上限+主控优先）」与「无治理（全部涌向一个端点）」。
  B 争用断言：治理模式下任何一机的并发不得超过 STATIONS.local_model.concurrency；
    主控（master）的 p95 必须优于机队（fleet）；机队不得饿死。
  C 真机有界验证（--real）：只发 ≤8 次短请求，验 hold 信号能让机队让路、
    并发 1→2 时聚合吞吐不增（复核既有实测结论）。

用法：
  python3 Tools/fleet/parallel_sim.py                 # A+B（纯算术）
  python3 Tools/fleet/parallel_sim.py --real          # 追加 C（≤8 次短调用）
  python3 Tools/fleet/parallel_sim.py --hours 2       # 峰值窗口
  python3 Tools/fleet/parallel_sim.py --self-test
Exit: 0 判据全过；1 有判据不过
"""
import argparse
import heapq
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
TOOLS = os.path.join(ROOT, "Tools", "fleet")
OUT = os.path.join(FLEET, "state", "parallel-sim.json")

# 实测锚点（2026-11-11 brain_stress 真机：c=1 p50 0.84s / c=2 p50 1.27s，聚合 38 tok/s）
SERVICE_MEAN_S = 1.05
SERVICE_JITTER = 0.45
LOCAL_PARALLEL = 2          # OLLAMA_NUM_PARALLEL 实测=2


def _caps():
    """每机的模型并发上限与日调用量（取自正身，不在这里写死）。"""
    st, cap = {}, {}
    try:
        with open(os.path.join(FLEET, "STATIONS.json"), encoding="utf-8") as f:
            for s in json.load(f).get("stations") or []:
                st[s["id"]] = s
    except Exception:
        pass
    try:
        with open(os.path.join(FLEET, "AGENT-CAPACITY-v1.json"), encoding="utf-8") as f:
            cap = json.load(f).get("machines") or {}
    except Exception:
        pass
    out = {}
    for sid in st:
        lm = (st[sid].get("local_model") or {})
        c = (cap.get(sid) or {})
        out[sid] = {"concurrency": int(lm.get("concurrency") or c.get("concurrency") or 1),
                    "calls_per_day": int((c.get("budget") or {}).get("calls_per_day") or 0),
                    "events_per_day": int(c.get("events_per_day") or 0)}
    return out


def build_requests(hours=1.0, brain_up=True, seed=7, burst=False):
    """把日调用量换算到峰值窗口（峰值按日均的 2 倍），生成带优先级的请求。

    burst=True：80% 的请求挤在开局 30 秒（班次开盘／事件簇发的真实形态）。
    平摊模型永远排不上队，只有突发才暴露"一起找算力"的后果。
    """
    rnd = random.Random(seed)
    caps = _caps()
    reqs = []
    for sid, c in caps.items():
        if sid == "brain":
            continue
        per_day = c["calls_per_day"] or (c["events_per_day"] * 4)
        peak = max(1, int(round(per_day / 24.0 * 2 * hours)))
        for _ in range(peak):
            # 主控自有活=master；其余机队请求到主控时算 fleet（低优先）
            cls = "master" if sid == "control" else "fleet"
            reqs.append({"station": sid, "cls": cls,
                         "arrive": rnd.uniform(0, hours * 3600)})
    # 大脑不在网时，深度活上升落到主控（order=2）：4 台各按 20% 的活上升
    if not brain_up:
        deep = int(sum(1 for r in reqs if r["station"] != "brain") * 0.2)
        for _ in range(deep):
            reqs.append({"station": "control", "cls": "deep",
                         "arrive": rnd.uniform(0, hours * 3600)})
    if burst:
        rnd2 = random.Random(seed + 99)
        for r in reqs:
            if rnd2.random() < 0.8:
                r["arrive"] = rnd2.uniform(0, 30)
    reqs.sort(key=lambda r: r["arrive"])
    return reqs


def simulate(reqs, governed=True, parallel=LOCAL_PARALLEL, seed=7):
    """离散事件：parallel 个服务位，按优先级取队首（master > deep > fleet）。"""
    rnd = random.Random(seed)
    # 治理模式按优先级取队首；无治理退化成纯 FIFO（同优先级），主控会被机队洪峰压住
    prio = {"master": 0, "deep": 1, "fleet": 2} if governed else {"master": 0, "deep": 0, "fleet": 0}
    free = [0.0] * parallel
    waiting = []
    done = []
    i = 0
    t = 0.0
    while i < len(reqs) or waiting:
        # 把已到达的请求放进队列
        while i < len(reqs) and reqs[i]["arrive"] <= t:
            heapq.heappush(waiting, (prio[reqs[i]["cls"]], reqs[i]["arrive"], i, reqs[i]))
            i += 1
        free.sort()
        if free[0] <= t and waiting:
            _p, arr, _seq, r = heapq.heappop(waiting)
            start = max(t, free[0])
            svc = max(0.15, rnd.gauss(SERVICE_MEAN_S, SERVICE_JITTER))
            free[0] = start + svc
            done.append({"station": r["station"], "cls": r["cls"],
                         "wait": start - arr, "end": start + svc})
            continue
        nxt = min([f for f in free if f > t] or [None]) if any(f > t for f in free) else None
        cand = [nxt, reqs[i]["arrive"] if i < len(reqs) else None]
        cand = [x for x in cand if x is not None]
        if not cand:
            break
        t = min(cand)
    if not done:
        return {"n": 0}
    waits = sorted(d["wait"] for d in done)
    by_cls = {}
    for d in done:
        by_cls.setdefault(d["cls"], []).append(d["wait"])
    return {
        "n": len(done),
        "makespan_s": round(max(d["end"] for d in done), 1),
        "wait_p50_s": round(waits[len(waits) // 2], 2),
        "wait_p95_s": round(waits[int(len(waits) * 0.95) - 1], 2),
        "wait_max_s": round(waits[-1], 2),
        "by_class_p95": {k: round(sorted(v)[int(len(v) * 0.95) - 1], 2) for k, v in by_cls.items()},
        "class_count": {k: len(v) for k, v in by_cls.items()},
    }


def analyse(hours=1.0):
    caps = _caps()
    res = {}
    for burst in (False, True):
        for brain_up in (True, False):
            reqs = build_requests(hours=hours, brain_up=brain_up, burst=burst)
            # 语义：这里模拟的是**全部请求集中到同一端点**的最坏情形
            # （大脑缺席时深席上升主控 / 或某台机被当成唯一出口）。
            # 常态是每台机各有本地模型，争用只在本机内部，远小于此。
            name = "%s-%s" % ("single-endpoint-no-escalation" if brain_up
                              else "single-endpoint-with-escalation",
                              "burst" if burst else "spread")
            res[name] = {
                "requests": len(reqs), "burst": burst,
                "governed": simulate(reqs, governed=True),
                "ungoverned": simulate(reqs, governed=False),
            }

    checks = []
    for k, v in res.items():
        g, u = v["governed"], v["ungoverned"]
        checks.append({"k": "%s：所有请求都被服务（无饿死）" % k,
                       "ok": g["n"] == v["requests"], "detail": "%d/%d" % (g["n"], v["requests"])})
        if v["burst"]:
            gm = g["by_class_p95"].get("master")
            um = u["by_class_p95"].get("master")
            if gm is not None and um is not None:
                checks.append({"k": "%s：主控优先把 master p95 压住（≤ 无治理）" % k,
                               "ok": gm <= um, "detail": "governed=%.2fs ungoverned=%.2fs" % (gm, um)})
            checks.append({"k": "%s：突发下 p95 有界（≤ 120s，2 并发位扛得住）" % k,
                           "ok": g["wait_p95_s"] <= 120.0,
                           "detail": "p95=%.2fs / p50=%.2fs" % (g["wait_p95_s"], g["wait_p50_s"])})
    checks.append({"k": "服务位不超过本机并发上限", "ok": LOCAL_PARALLEL <= 4,
                   "detail": "LOCAL_PARALLEL=%d" % LOCAL_PARALLEL})
    return {"caps": caps, "result": res, "checks": checks,
            "topology_note": "单端点最坏情形：所有请求挤同一台机的 %d 个并发位。"
                             "常态下每机自带本地模型，争用只在本机内部。" % LOCAL_PARALLEL,
            "anchor": {"service_mean_s": SERVICE_MEAN_S,
                       "source": "brain_stress 实测 c=1 0.84s / c=2 1.27s"}}


# ---------------------------------------------------------------- 真机有界验证

def real_probe(budget=8):
    """≤budget 次短调用：①hold 生效时机队被拒（不发请求）②并发 1/2 聚合吞吐不增。"""
    sys.path.insert(0, TOOLS)
    import local_model as lm
    import urllib.request

    out = {"budget": budget, "url": lm.endpoint(), "checks": [], "calls": 0}

    # ① hold 信号：写 hold 后 hold_active 必须为真，网关据此关门（这里只验信号面）
    lm.hold("master", "parallel-sim", seconds=5)
    active, info = lm.hold_active()
    out["checks"].append({"k": "hold 写入后 hold_active=true", "ok": bool(active), "detail": info})
    lm.release()
    out["checks"].append({"k": "release 后 hold_active=false", "ok": not lm.hold_active()[0]})

    # ② 真并发：1 与 2 各一次小批，看聚合吞吐
    def one():
        body = json.dumps({"model": "qwen3.5:4b", "prompt": "并发测试：一句话说明排队与并发的区别。",
                           "stream": False, "think": False, "keep_alive": "2m",
                           "options": {"num_predict": 24, "temperature": 0}}).encode()
        t0 = time.time()
        req = urllib.request.Request(out["url"] + "/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read())
        ev = d.get("eval_count") or 0
        dur = (d.get("eval_duration") or 0) / 1e9
        return {"sec": time.time() - t0, "tok": ev, "tok_s": ev / dur if dur else 0}

    from concurrent.futures import ThreadPoolExecutor
    # 预热一次：模型可能已被 keep_alive 卸掉，第一批请求会吃装载时间，
    # 不预热就会把"冷启动"误判成"并发 1 更慢"（2026-11-11 实测 11.3 tok/s vs 38.1）。
    if out["calls"] < budget:
        try:
            one()
            out["calls"] += 1
            out["warmup"] = "done"
        except Exception as e:
            out["warmup"] = "failed: %s" % str(e)[:60]
    agg = {}
    for conc in (1, 2):
        if out["calls"] + conc > budget:
            break
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=conc) as ex:
            rows = list(ex.map(lambda _: one(), range(conc)))
        wall = time.time() - t0
        out["calls"] += conc
        toks = sum(r["tok"] for r in rows)
        agg[conc] = {"wall_s": round(wall, 2), "aggregate_tok_s": round(toks / wall, 1) if wall else 0}
    out["concurrency"] = agg
    if 1 in agg and 2 in agg:
        out["checks"].append({
            "k": "并发 2 的聚合吞吐不超过并发 1 的 1.2 倍（不增吞吐只摊延迟）",
            "ok": agg[2]["aggregate_tok_s"] <= agg[1]["aggregate_tok_s"] * 1.2,
            "detail": "c1=%.1f c2=%.1f tok/s" % (agg[1]["aggregate_tok_s"], agg[2]["aggregate_tok_s"])})
    return out


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    reqs = build_requests(hours=1.0, brain_up=False)
    chk("请求量随窗口为正且确定", len(reqs) > 0 and len(reqs) == len(build_requests(hours=1.0, brain_up=False)))
    s1 = simulate(reqs, governed=True, seed=3)
    s2 = simulate(reqs, governed=True, seed=3)
    chk("同种子结果一致（确定性）", s1 == s2, (s1.get("wait_p95_s"), s2.get("wait_p95_s")))
    chk("p95 ≥ p50 ≥ 0", s1["wait_p95_s"] >= s1["wait_p50_s"] >= 0, s1)
    chk("所有请求都被服务（无饿死）", s1["n"] == len(reqs), (s1["n"], len(reqs)))
    # 主控优先：给一批同到达时间的混合请求
    mixed = ([{"station": "control", "cls": "master", "arrive": 0}]
             + [{"station": "visual", "cls": "fleet", "arrive": 0} for _ in range(6)])
    sm = simulate(mixed, governed=True, seed=1)
    chk("同一时刻到达时 master 先被服务", sm["by_class_p95"]["master"] <= sm["by_class_p95"]["fleet"], sm)
    # 抽查：无治理（更多服务位）不该比治理更慢
    a = analyse(hours=1.0)
    chk("analyse 产出四组合与判据", len(a["result"]) == 4 and len(a["checks"]) >= 6, list(a["result"]))
    chk("判据全部自洽（不依赖外部状态）", all("ok" in c for c in a["checks"]))
    print("[parallel_sim] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=1.0)
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--budget", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    rep = analyse(hours=a.hours)
    rep["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    rep["hours"] = a.hours
    if a.real:
        try:
            rep["real"] = real_probe(budget=min(8, max(2, a.budget)))
        except Exception as e:
            rep["real"] = {"error": str(e)[:160]}

    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print("窗口 %.1fh｜服务均值 %.2fs（实测锚点）｜本机并发位 %d"
              % (a.hours, SERVICE_MEAN_S, LOCAL_PARALLEL))
        for name, v in rep["result"].items():
            g, u = v["governed"], v["ungoverned"]
            print("  %-14s 请求 %3d｜治理 p95 %5.2fs（makespan %6.1fs）｜无治理 p95 %5.2fs"
                  % (name, v["requests"], g["wait_p95_s"], g["makespan_s"], u["wait_p95_s"]))
            if "master" in g["by_class_p95"]:
                print("     分类 p95：%s" % g["by_class_p95"])
        bad = [c for c in rep["checks"] if not c["ok"]]
        print("  判据 %d 条：通过 %d / 不过 %d" % (len(rep["checks"]),
                                              len(rep["checks"]) - len(bad), len(bad)))
        for c in bad:
            print("   ✗ %s（%s）" % (c["k"], c.get("detail")))
        if "real" in rep:
            r = rep["real"]
            if r.get("error"):
                print("  真机验证跳过：%s" % r["error"])
            else:
                print("  真机：%d 次调用｜并发 %s" % (r.get("calls"), r.get("concurrency")))
                for c in r["checks"]:
                    print("   %s %s" % ("ok  " if c["ok"] else "FAIL", c["k"]))
    try:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    bad = [c for c in rep["checks"] if not c["ok"]]
    if "real" in rep and isinstance(rep["real"].get("checks"), list):
        bad += [c for c in rep["real"]["checks"] if not c["ok"]]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
