#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gpu_squeeze.py - 本机算力上限实测：在"swap 零增"约束下找吞吐最高的搭配。

为什么要有它：`resident_gb_limit=16GB` 是人猜的，不是测出来的；而"并发不增吞吐"
也不是一条普适真理——2026-11-17 实测是「同一模型多发请求不涨（GPU 排队），
不同模型同驻会涨（解码是带宽饥饿的，交错能填满空闲带宽）」。所以上限必须用
矩阵测出来，不能靠调参口诀。

判据（缺一不可，任一不满足即判 SWAPPING，不进候选）：
  1) 跑完后 swap 用量不比跑前高（允许回落，>8MB 增长即判负）
  2) 整个窗口内换出页数变化 = 0（换出就是真换页，慢不慢都算违约）
  3) 过程中空闲内存最低值 > 512MB（留一点给控制面，不许贴地飞行）

每条配置的测法（控制变量）：
  · 先把无关模型 ollama stop 掉，再逐车道预热钉住 ctx（warmup 用同一 ctx，
    否则 ollama 会因为你换了 num_ctx 悄悄重载模型，把装载时间算进吞吐）
  · 后台 0.25s 采一次内存，抓瞬时尖峰（只看首尾会漏掉中间那一下换页）
  · 每条配置跑 reps 轮，每轮 = 每车道一个并发请求，取聚合中位
  · 聚合 tok/s = 本轮总输出 token / 墙钟，这才是"榨干"要看的口径

用法：
  python3 Tools/fleet/gpu_squeeze.py --self-test
  python3 Tools/fleet/gpu_squeeze.py --matrix            # 全矩阵（约 8-12 分钟）
  python3 Tools/fleet/gpu_squeeze.py --matrix --quick    # 1 轮，先看形状
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_MD = os.path.join(ROOT, "cph4", "fleet", "SQUEEZE-MATRIX.md")
OUT_JSON = os.path.join(ROOT, "cph4", "fleet", "state", "gpu-squeeze.json")
HIST = os.path.join(ROOT, "cph4", "fleet", "state", "gpu-squeeze-history.jsonl")
OLLAMA = "http://127.0.0.1:11434"
LORA = "http://127.0.0.1:8788"

# 车道目录：一条车道 = 一个可独立接收请求的推理端点。
# lora = 8788 上的 mlx_lm.server（4B-4bit + 养号适配器），协议与 ollama 不同。
LANES = {
    "lora": {"kind": "lora", "label": "8788-LoRA"},
    "4b": {"kind": "ollama", "model": "qwen3.5:4b-mlx", "label": "4B"},
    "9b": {"kind": "ollama", "model": "qwen3.5:9b-mlx", "label": "9B"},
    "2b": {"kind": "ollama", "model": "qwen3.5:2b", "label": "2B"},
    "8b": {"kind": "ollama", "model": "qwen3:8b", "label": "8B-dense"},
    "4bd": {"kind": "ollama", "model": "qwen3:4b", "label": "4B-dense"},
}

# 所有车道用**同一段长输出**工作负载：短回复（十几 token）会让墙钟被预填充和首字
# 延迟吃掉，算出"5 tok/s"这种假数（2026-11-18 实锚：8788 短回复 5.2，长输出 25.8，
# 差 5 倍全是量法错，不是模型慢）。长输出让解码段占满窗口。
PROMPT = ("请写一段 250 字的中文短文，介绍冬天海边清晨的景象：光线、风、声音、"
          "人的动作都要写到。")

MIN_FREE_MB = 512
SWAP_GROWTH_MAX_MB = 8.0


# ---------------------------------------------------------------- 机器事实
def sh(cmd, timeout=20):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def swap_state():
    """(swap 已用 MB, 换出页数, 换入页数)。换出页是累计值，只看变化量。"""
    used = 0.0
    m = re.search(r"used\s*=\s*([\d.]+)([MG])", sh(["sysctl", "-n", "vm.swapusage"]) or "")
    if m:
        used = float(m.group(1)) * (1024 if m.group(2) == "G" else 1)
    vm = sh(["vm_stat"])
    po = pi = 0
    for line in (vm or "").splitlines():
        if line.startswith("Swapouts"):
            po = int(re.sub(r"[^0-9]", "", line.split(":")[1] or "0") or 0)
        elif line.startswith("Swapins"):
            pi = int(re.sub(r"[^0-9]", "", line.split(":")[1] or "0") or 0)
    return round(used, 1), po, pi


def free_mb():
    vm = sh(["vm_stat"])
    ps = 4096
    m = re.search(r"page size of (\d+) bytes", vm or "")
    if m:
        ps = int(m.group(1))
    tot = 0
    for line in (vm or "").splitlines():
        if line.startswith("Pages free") or line.startswith("Pages inactive"):
            tot += int(re.sub(r"[^0-9]", "", line.split(":")[1] or "0") or 0)
    return round(tot * ps / 1048576.0, 1)


def loaded_models():
    """{模型名: 常驻GB}，来自 ollama ps。"""
    out = {}
    for line in (sh(["ollama", "ps"]) or "").splitlines()[1:]:
        f = line.split()
        if not f:
            continue
        m = re.search(r"(\d+(?:\.\d+)?)\s*GB", line)
        if m:
            out[f[0]] = float(m.group(1))
    return out


def lora_model_id():
    with urllib.request.urlopen(LORA + "/v1/models", timeout=6) as r:
        d = json.loads(r.read().decode() or "{}")
    data = d.get("data") or []
    return data[0]["id"] if data else ""


# ---------------------------------------------------------------- 单次请求
def hit_ollama(model, ctx, maxtok, timeout=300):
    body = json.dumps({"model": model, "prompt": PROMPT, "stream": False, "think": False,
                       "keep_alive": "20m",
                       "options": {"num_ctx": ctx, "num_predict": maxtok,
                                   "temperature": 0.2}}).encode()
    req = urllib.request.Request(OLLAMA + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode() or "{}")
    wall = time.time() - t0
    ec = d.get("eval_count") or 0
    ed = (d.get("eval_duration") or 0) / 1e9
    return {"tok": ec, "wall": wall, "decode_tps": (ec / ed) if ed else 0.0}


def hit_lora(maxtok, timeout=300):
    body = json.dumps({"model": lora_model_id(),
                       "messages": [{"role": "user", "content": PROMPT}],
                       "max_tokens": maxtok, "temperature": 0.2,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(LORA + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode() or "{}")
    wall = time.time() - t0
    ch = (d.get("choices") or [{}])[0]
    text = ((ch.get("message") or {}).get("content") or "")
    us = d.get("usage") or {}
    tok = us.get("completion_tokens") or 0
    if not tok:                       # 服务没回 usage 时按字符估，只用于相对比较
        tok = max(1, len(text) // 2)
    return {"tok": tok, "wall": wall, "decode_tps": tok / wall if wall else 0.0}


def hit(lane, ctx, maxtok):
    spec = LANES[lane]
    if spec["kind"] == "lora":
        return hit_lora(maxtok)
    return hit_ollama(spec["model"], ctx, maxtok)


# ---------------------------------------------------------------- 内存采样
class Sampler(threading.Thread):
    """跑测试时后台采样：抓空闲内存最低点与换出页增量（首尾两次看会漏掉尖峰）。"""

    def __init__(self, interval=0.25):
        super().__init__(daemon=True)
        self.interval = interval
        self.stop_flag = threading.Event()
        self.min_free = 1e9
        self.po0 = swap_state()[1]

    def run(self):
        while not self.stop_flag.is_set():
            try:
                self.min_free = min(self.min_free, free_mb())
            except Exception:
                pass
            self.stop_flag.wait(self.interval)

    def finish(self):
        self.stop_flag.set()
        self.join(timeout=3)
        po1 = swap_state()[1]
        return {"min_free_mb": round(self.min_free, 1) if self.min_free < 1e9 else None,
                "swapouts_delta": po1 - self.po0}


# ---------------------------------------------------------------- 一条配置
def settle(need_mb=4000, max_wait=45):
    """等空闲内存回到 need_mb 以上，或最多等 max_wait 秒（别把时间全花在等上）。"""
    t0 = time.time()
    while time.time() - t0 < max_wait:
        f = free_mb()
        _ = swap_state()[1]
        if f >= need_mb:
            print("    · 内存已回落 %.0fMB（等 %.0fs）" % (f, time.time() - t0))
            return f
        time.sleep(2)
    f = free_mb()
    print("    · 等满 %ds 仍只有 %.0fMB，照测但存疑" % (max_wait, f))
    return f


def prepare(lanes, ctx):
    """卸掉不需要的 ollama 模型，再把要用的逐条预热钉住 ctx。"""
    want = {LANES[x]["model"] for x in lanes if LANES[x]["kind"] == "ollama"}
    for name in loaded_models():
        if name not in want:
            sh(["ollama", "stop", name])
            print("    - 卸载 %s" % name)
    # 卸载后必须等内存真的回到系统：2026-11-18 实锚——刚 ollama stop 掉 9B 就开测，
    # 同一条 4B+2B 在轮1 被判换出 1484 页、轮2 又归零，那是残留压力不是配置问题。
    settle(need_mb=4000, max_wait=45)
    for x in lanes:
        if LANES[x]["kind"] == "ollama":
            hit_ollama(LANES[x]["model"], ctx, 1)      # maxtok=1：只装载+钉 ctx
    time.sleep(3)


def run_config(name, lanes, ctx, maxtok, reps):
    print("\n[%s] 车道=%s ctx=%d" % (name, "+".join(LANES[x]["label"] for x in lanes), ctx))
    prepare(lanes, ctx)
    rows = []
    for r in range(reps):
        before_sw, _, _ = swap_state()
        smp = Sampler()
        smp.start()
        res, lock = {}, threading.Lock()

        def work(lane):
            try:
                out = hit(lane, ctx, maxtok)
            except Exception as e:
                out = {"tok": 0, "wall": 0, "decode_tps": 0.0, "err": str(e)[:60]}
            with lock:
                res[lane] = out

        t0 = time.time()
        th = [threading.Thread(target=work, args=(x,)) for x in lanes]
        [t.start() for t in th]
        [t.join() for t in th]
        wall = time.time() - t0
        mem = smp.finish()
        after_sw, _, _ = swap_state()
        tot = sum(v["tok"] for v in res.values())
        agg = tot / wall if wall else 0.0
        row = {"round": r + 1, "wall": round(wall, 2), "tokens": tot,
               "aggregate_tps": round(agg, 1),
               "per_lane": {k: {"tps": round(v["decode_tps"], 1), "tok": v["tok"],
                                **({"err": v["err"]} if v.get("err") else {})}
                            for k, v in res.items()},
               "swap_used_mb": [before_sw, after_sw],
               "swap_growth_mb": round(max(0.0, after_sw - before_sw), 1),
               **mem}
        rows.append(row)
        print("    轮%d 墙钟%.1fs 聚合%.1f tok/s ｜ %s ｜ swap %+.1fMB 换出 %d 页 空余最低%sMB"
              % (row["round"], wall, agg,
                 " ".join("%s=%.1f" % (LANES[k]["label"], v["decode_tps"])
                          for k, v in res.items()),
                 after_sw - before_sw, mem["swapouts_delta"], mem["min_free_mb"]))

    aggs = [x["aggregate_tps"] for x in rows if x["aggregate_tps"] > 0]
    growth = max(x["swap_growth_mb"] for x in rows)
    outs = max(x["swapouts_delta"] for x in rows)
    minfree = min((x["min_free_mb"] or 1e9) for x in rows)
    zero_swap = growth <= SWAP_GROWTH_MAX_MB and outs == 0 and minfree >= MIN_FREE_MB
    if not aggs:
        zero_swap = False
    sums = [sum(v["tps"] for v in x["per_lane"].values()) for x in rows]
    cfg = {"name": name, "lanes": lanes, "ctx": ctx,
           "aggregate_tps_median": round(statistics.median(aggs), 1) if aggs else 0.0,
           "sum_decode_tps_median": round(statistics.median(sums), 1) if sums else 0.0,
           "swap_growth_mb": growth, "swapouts_delta": outs,
           "min_free_mb": minfree if minfree < 1e9 else None,
           "zero_swap": zero_swap, "rounds": rows}
    print("    → 中位：解码算力 %.1f tok/s（Σ各车道）｜ 墙钟聚合 %.1f tok/s ｜ %s"
          % (cfg["sum_decode_tps_median"], cfg["aggregate_tps_median"],
             "ZERO-SWAP ✓" if zero_swap else "SWAPPING ✗"))
    return cfg


def _default_matrix():
    """从少到多、从纯 ollama 到混合：只增不减，避免反复装载污染对照。"""
    # 第二轮：围绕第一轮胜者加"更多不同的小模型"这一轴，9B 只留一条做对照
    # （第一轮实测 9B 是毒丸：占 8.9GB，把 4B 从 41 拖到 15-20，Σ反而降）。
    # 第三轮（定档）：只跑对照 + 胜者 + 边界，轮次加厚；前面两轮已经筛掉了
    # 9B 与五/六车道（5-6 车道把 swap 顶起来，实测 swap 用了 3870→4292MB）。
    return [
        ("O1-4B基线",     ["4b"],                     8192),
        ("M2-lora+4B+2B", ["lora", "4b", "2b"],       8192),
        ("M4-四车道边界",  ["lora", "4b", "2b", "8b"], 8192),
        ("M2-低ctx",      ["lora", "4b", "2b"],       2048),
        ("O2-4B+9B",      ["4b", "9b"],               8192),
        ("M3-lora+4B+9B", ["lora", "4b", "9b"],       8192),
    ]


LOCK = os.path.join(ROOT, ".codely-cli", "state", "gpu-squeeze.lock")
SWAP_BASE = [None]          # 本次跑批开始时的 swap 用量（门只守增量，基线要如实写进报告）


def take_lock():
    """拿不到锁就退出——两条压测同时跑测出来的数是废的。"""
    import fcntl
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    f = open(LOCK, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("[squeeze] 已有一条压测在跑（%s），本次退出" % LOCK)
        return None
    f.write(str(os.getpid()))
    f.flush()
    return f


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", action="store_true")
    ap.add_argument("--quick", action="store_true", help="每条 1 轮，先看形状")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--maxtok", type=int, default=200)
    ap.add_argument("--ctx", type=int, default=None, help="覆盖矩阵里的 ctx")
    ap.add_argument("--only", default="", help="只跑名字含此串的配置")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report-only", action="store_true",
                    help="只从历史账重建报告，不测（改完表头/口径时用，避免重跑烧时间）")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()

    if not a.matrix and not a.report_only:
        ap.print_help()
        return 0

    if a.report_only:
        hist = [json.loads(x) for x in open(HIST, encoding="utf-8") if x.strip()]
        ok = [c for c in hist if c.get("zero_swap") and c.get("sum_decode_tps_median", 0) > 0]
        ok.sort(key=lambda c: -c["sum_decode_tps_median"])
        rec = {"ts": datetime.now().isoformat(timespec="seconds"), "reps": "-", "maxtok": "-",
               "gate": {"swap_growth_max_mb": SWAP_GROWTH_MAX_MB, "min_free_mb": MIN_FREE_MB},
               "configs": hist, "best": ok[0] if ok else None,
               "history": sorted(hist, key=lambda x: -x.get("sum_decode_tps_median", 0)),
               "agg": aggregate(hist)}
        write_report(rec)
        return 0

    lock = take_lock()
    if lock is None:
        return 2
    reps = 1 if a.quick else a.reps
    SWAP_BASE[0] = swap_state()[0]
    print("[squeeze] 基线 swap=%sMB 常驻=%s 空余=%.0fMB"
          % (swap_state()[0], loaded_models() or "无", free_mb()))
    try:
        print("[squeeze] 8788 模型=%s" % lora_model_id())
        lora_up = True
    except Exception as e:
        print("[squeeze] 8788 不可用（%s），含 lora 的配置跳过" % type(e).__name__)
        lora_up = False

    out = []
    for name, lanes, ctx in _default_matrix():
        if not lora_up and "lora" in lanes:
            print("\n[%s] 跳过（8788 不可用）" % name)
            continue
        if a.only and a.only not in name:
            continue
        try:
            cfg = run_config(name, lanes, a.ctx or ctx, a.maxtok, reps)
            out.append(cfg)
            with open(HIST, "a", encoding="utf-8") as f:      # 逐条落账，断了也不丢
                f.write(json.dumps({k: v for k, v in cfg.items() if k != "rounds"},
                                   ensure_ascii=False) + "\n")
        except Exception as e:
            print("    配置失败：%s: %s" % (type(e).__name__, str(e)[:120]))

    hist = []
    try:
        for line in open(HIST, encoding="utf-8"):
            if line.strip():
                hist.append(json.loads(line))
    except Exception:
        pass
    merged = {(h["name"], h["ctx"]): h for h in hist}
    for c in out:
        merged[(c["name"], c["ctx"])] = {k: v for k, v in c.items() if k != "rounds"}
    ok = [c for c in out if c["zero_swap"] and c["aggregate_tps_median"] > 0]
    ok.sort(key=lambda c: -c["sum_decode_tps_median"])
    best = ok[0] if ok else None
    rec = {"ts": datetime.now().isoformat(timespec="seconds"),
           "swap_baseline_mb": SWAP_BASE[0],
           "reps": reps, "maxtok": a.maxtok,
           "gate": {"swap_growth_max_mb": SWAP_GROWTH_MAX_MB, "min_free_mb": MIN_FREE_MB},
           "configs": out, "best": best,
           "history": sorted(merged.values(), key=lambda x: -x["sum_decode_tps_median"]),
           "agg": aggregate(list(merged.values()))}
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(rec, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_report(rec)
    print("\n[squeeze] 胜出：%s 解码算力 %.1f tok/s（%s）"
          % (best["name"], best["sum_decode_tps_median"], "+".join(best["lanes"]))
          if best else "\n[squeeze] 无零 swap 配置胜出")
    return 0 if best else 1


def aggregate(rows):
    """按 (name, ctx) 聚合多批次：中位、最小值、最大值、批次数。"""
    g = {}
    for r in rows:
        k = (r["name"], r["ctx"])
        g.setdefault(k, []).append(r)
    out = []
    for (name, ctx), vs in g.items():
        vals = [v.get("sum_decode_tps_median", 0) for v in vs]
        walls = [v.get("aggregate_tps_median", 0) for v in vs]
        out.append({
            "name": name, "ctx": ctx, "lanes": vs[0]["lanes"],
            "batches": len(vs),
            "sum_decode_tps_median": round(statistics.median(vals), 1),
            "sum_decode_min": round(min(vals), 1),
            "sum_decode_max": round(max(vals), 1),
            "aggregate_tps_median": round(statistics.median(walls), 1),
            "swap_growth_mb": max(v.get("swap_growth_mb", 0) for v in vs),
            "swapouts_delta": max(v.get("swapouts_delta", 0) for v in vs),
            "min_free_mb": min((v.get("min_free_mb") or 1e9) for v in vs),
            "zero_swap": all(v.get("zero_swap") for v in vs),
        })
    return sorted(out, key=lambda x: -x["sum_decode_tps_median"])


def write_report(rec):
    L = ["# 本机算力上限实测（swap 零增约束）", "",
         "- 时间：%s｜每配置 %s 轮｜每条输出上限 %s token"
         % (rec["ts"], rec["reps"], rec["maxtok"]),
         "- swap：跑批开始时 %sMB ｜ 写报告时 %s"
         % ((rec.get("swap_baseline_mb") or "-"),
            re.search(r"used\s*=\s*([\d.]+)([MG])", sh(["sysctl", "-n", "vm.swapusage"]) or "")
            and sh(["sysctl", "-n", "vm.swapusage"]).strip()),
         "- 判据：swap 增长 ≤%.0fMB 且 换出 0 页 且 空闲内存最低 ≥%dMB"
         % (rec["gate"]["swap_growth_max_mb"], rec["gate"]["min_free_mb"]),
         "", "| 配置 | 车道 | ctx | 解码算力 tok/s（中位/区间） | 批次 | 墙钟聚合 | swap增长 | 换出页 | 空余最低 | 判定 |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for c in rec.get("agg") or aggregate(rec["configs"]):
        L.append("| %s | %s | %d | %.1f（%.1f–%.1f） | %d | %.1f | %+.1fMB | %d | %sMB | %s |"
                 % (c["name"], "+".join(c["lanes"]), c["ctx"],
                    c["sum_decode_tps_median"], c["sum_decode_min"], c["sum_decode_max"],
                    c.get("batches", 1), c.get("aggregate_tps_median", 0),
                    c["swap_growth_mb"], c["swapouts_delta"],
                    ("%.0f" % c["min_free_mb"]) if c["min_free_mb"] else "-",
                    "ZERO-SWAP" if c["zero_swap"] else "SWAPPING"))
    agg = rec.get("agg") or aggregate(rec["configs"])
    if agg:
        b = agg[0]
        L += ["", "## 结论", "",
              "零 swap 下最高解码算力：**%s = %.1f tok/s**（%s，ctx=%d，区间 %.1f–%.1f，%d 批，空余最低 %sMB）"
              % (b["name"], b["sum_decode_tps_median"], "+".join(b["lanes"]), b["ctx"],
                 b["sum_decode_min"], b["sum_decode_max"], b.get("batches", 1),
                 ("%.0f" % b["min_free_mb"]) if b["min_free_mb"] else "-"),
              "", "机读：`cph4/fleet/state/gpu-squeeze.json`"]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("[squeeze] → %s" % os.path.relpath(OUT_MD, ROOT))


def self_test():
    """自检：判据口径必须能用"应通过/应拒绝"两组样例反向验证（不许只看跑通）。"""
    checks = []

    def chk(name, cond):
        checks.append((name, bool(cond)))

    # 1) 判负样例：swap 涨了就一定不是零 swap
    smp_ok = {"min_free_mb": 2000, "swapouts_delta": 0}
    smp_bad = {"min_free_mb": 2000, "swapouts_delta": 120}
    smp_low = {"min_free_mb": 100, "swapouts_delta": 0}

    def gate(growth, s):
        return (growth <= SWAP_GROWTH_MAX_MB and s["swapouts_delta"] == 0
                and s["min_free_mb"] >= MIN_FREE_MB)

    chk("零 swap 应通过", gate(0.0, smp_ok))
    chk("swap 增长超阈应拒绝", not gate(SWAP_GROWTH_MAX_MB + 1, smp_ok))
    chk("有换出页应拒绝", not gate(0.0, smp_bad))
    chk("空闲内存塌到底应拒绝", not gate(0.0, smp_low))
    # 2) swap 回落（负增长）不应被误判为违约
    chk("swap 回落应通过", gate(-50.0, smp_ok))
    # 3) 车道表必须每条都有 kind，避免打到不存在的协议
    chk("车道声明完整", all("kind" in v and v["kind"] in ("ollama", "lora")
                            for v in LANES.values()))
    for n, ok in checks:
        print("  [%s] %s" % ("PASS" if ok else "FAIL", n))
    bad = [n for n, ok in checks if not ok]
    print("[self-test] %d/%d" % (len(checks) - len(bad), len(checks)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
