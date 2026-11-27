#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_bench.py - 本地模型形态的实测台（回答"大的串行 vs 小的并行"）。

为什么要它：2026-11-17 CEO「你好好测试，事实说话」。拍脑袋说"并发不增吞吐"没有说服力，
必须控制变量、多次重复取中位、同时记内存与换页，才能分辨"模型慢"和"换页拖慢"。

四组实验（各自独立，可单跑）：
  --suite throughput  同一 prompt，c=1/2/4，各 n 次 → 单条解码 tok/s、聚合 tok/s、P50 墙钟
  --suite residency   4B 单独 vs 4B+9B 同驻（同一 4B 工作负载）→ 量化"两档同驻"的代价
  --suite coldload    卸掉模型后第一次请求 vs 预热后 → 冷加载成本
  --suite quality     黄金集分类题，4B vs 9B → 类别准确率 + 红线安全率（安全比快慢重要）

每条实验都打印过程行（避免被"无输出"判死），最后写 MODEL-BENCH-<日期>.md 与 json。

Usage:
  python3 Tools/fleet/model_bench.py --suite throughput --reps 3
  python3 Tools/fleet/model_bench.py --suite residency
  python3 Tools/fleet/model_bench.py --suite coldload --reps 3
  python3 Tools/fleet/model_bench.py --suite quality --limit 20
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
OUT_MD = os.path.join(ROOT, "cph4", "fleet", "MODEL-BENCH-%s.md" % datetime.now().strftime("%Y%m%d"))
OUT_JSON = os.path.join(ROOT, "cph4", "fleet", "state", "model-bench.json")
API = "http://127.0.0.1:11434/api/generate"

SMALL = "qwen3.5:4b-mlx"
BIG = "qwen3.5:9b-mlx"
# 固定工作负载：约 120 token 输出，避免"输出太短导致 tok/s 噪声大"
PROMPT = ("你在替一个 MV 账号回 B 站评论。写一条回复：12-25 字、口语、不客服腔、"
          "不说感谢支持、不反问。评论：这段剪辑太顺了，剪了好几遍")
MAXTOK = 120


def sh(cmd, timeout=10):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def mem():
    """返回 (swap_used_mb, swapouts_mb, pages_free_mb, loaded_gb)"""
    sw = sh(["sysctl", "-n", "vm.swapusage"])
    used = 0.0
    m = re.search(r"used\s*=\s*([\d.]+)([MG])", sw or "")
    if m:
        used = float(m.group(1)) * (1024 if m.group(2) == "G" else 1)
    vm = sh(["vm_stat"])
    so = free = 0
    for line in (vm or "").splitlines():
        if "Swapouts" in line:
            so = int(re.sub(r"[^0-9]", "", line.split(":")[1] or "0") or 0) * 4096 / 1048576
        if "Pages free" in line:
            free = int(re.sub(r"[^0-9]", "", line.split(":")[1] or "0") or 0) * 4096 / 1048576
    ps = sh(["ollama", "ps"])
    gb = 0.0
    for line in (ps or "").splitlines():
        m2 = re.search(r"(\d+(?:\.\d+)?)\s*GB", line)
        if m2:
            gb += float(m2.group(1))
    return round(used, 1), round(so, 1), round(free, 1), round(gb, 2)


def gen(model, prompt=PROMPT, ctx=8192, maxtok=MAXTOK, keep="5m"):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False,
                       "keep_alive": keep,
                       "options": {"num_ctx": ctx, "num_predict": maxtok,
                                   "temperature": 0.2}}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    dt = time.time() - t0
    ec = d.get("eval_count") or 0
    ed = (d.get("eval_duration") or 0) / 1e9
    pc = d.get("prompt_eval_count") or 0
    pd = (d.get("prompt_eval_duration") or 0) / 1e9
    return {"wall": dt, "tok": ec,
            "decode_tps": (ec / ed) if ed else 0.0,
            "prefill_tps": (pc / pd) if pd else 0.0,
            "text": (d.get("response") or "").strip()[:60]}


def median(xs):
    xs = [x for x in xs if x > 0]
    return round(statistics.median(xs), 1) if xs else 0.0


def suite_throughput(models=(SMALL, BIG), concs=(1, 2, 4), reps=3):
    rows = []
    for model in models:
        gen(model, prompt="说一句话", maxtok=8)          # 预热，避免冷加载算进吞吐
        for c in concs:
            single, agg, walls = [], [], []
            for r in range(reps):
                res = []

                def work():
                    res.append(gen(model))

                th = [threading.Thread(target=work) for _ in range(c)]
                before = mem()
                t0 = time.time()
                [t.start() for t in th]
                [t.join() for t in th]
                wall = time.time() - t0
                after = mem()
                tot = sum(x["tok"] for x in res)
                single += [x["decode_tps"] for x in res]
                agg.append(tot / wall if wall else 0)
                walls.append(wall)
                print("  [%s c=%d rep%d] 墙钟%.1fs 聚合%.1f tok/s 单条均%.1f swap%s→%sGB 常驻%.1f→%.1fGB"
                      % (model, c, r + 1, wall, tot / wall if wall else 0,
                         sum(x["decode_tps"] for x in res) / len(res),
                         before[0], after[0], before[3], after[3]))
            rows.append({"model": model, "concurrency": c,
                         "decode_tps_median": median(single),
                         "aggregate_tps_median": median(agg),
                         "wall_median": median(walls),
                         "swapouts_mb": mem()[1]})
    return rows


def suite_residency(reps=3):
    """同一 4B 工作负载：只驻 4B vs 4B+9B 同驻。差别只能来自换页/内存争用。"""
    out = []
    sh(["ollama", "stop", BIG]); time.sleep(3)
    gen(SMALL, prompt="说一句话", maxtok=8); time.sleep(1)
    alone = [gen(SMALL)["decode_tps"] for _ in range(reps)]
    m1 = mem()
    print("  [4B 单独] %s tok/s 中位%.1f  swap%.0fMB 常驻%.1fGB 空闲%.0fMB"
          % ([round(x, 1) for x in alone], median(alone), m1[0], m1[3], m1[2]))
    gen(BIG, prompt="说一句话", maxtok=8); time.sleep(1)   # 把 9B 拉进常驻
    both = [gen(SMALL)["decode_tps"] for _ in range(reps)]
    m2 = mem()
    print("  [4B+9B 同驻] %s tok/s 中位%.1f  swap%.0fMB 常驻%.1fGB 空闲%.0fMB"
          % ([round(x, 1) for x in both], median(both), m2[0], m2[3], m2[2]))
    out.append({"scenario": "4B_only", "decode_tps_median": median(alone),
                "swap_mb": m1[0], "free_mb": m1[2], "loaded_gb": m1[3]})
    out.append({"scenario": "4B_plus_9B", "decode_tps_median": median(both),
                "swap_mb": m2[0], "free_mb": m2[2], "loaded_gb": m2[3]})
    if median(alone) and median(both):
        out.append({"scenario": "degradation_pct",
                    "pct": round((median(alone) - median(both)) / median(alone) * 100, 1)})
    return out


def suite_coldload(model=BIG, reps=3):
    rows = []
    for i in range(reps):
        sh(["ollama", "stop", model])
        time.sleep(4)
        t0 = time.time()
        r = gen(model, prompt="说一句话", maxtok=8)
        cold = time.time() - t0
        warm = gen(model, prompt="说一句话", maxtok=8)["wall"]
        print("  [%s rep%d] 冷 %.2fs / 热 %.2fs（差 %.2fs）"
              % (model, i + 1, cold, warm, cold - warm))
        rows.append({"model": model, "cold_s": round(cold, 2), "warm_s": round(warm, 2),
                     "cost_s": round(cold - warm, 2)})
    return rows


def suite_quality(limit=20, models=(SMALL, BIG)):
    sys.path.insert(0, HERE)
    import social_drafts as sd
    golden = os.path.join(ROOT, "cph4", "fleet", "social", "golden.jsonl")
    cases = [json.loads(l) for l in open(golden, encoding="utf-8") if l.strip()][:limit]
    out = []
    for model in models:
        old = sd.MODEL
        sd.MODEL = model
        ok = safe = red = 0
        fails = []
        for c in cases:
            face = c.get("face") or "comment"
            faq = None
            if c.get("faq"):
                faq = next((r for r in sd._load_jsonl(sd.FAQ) if r.get("id") == c["faq"]), None)
            k, d, h, n = sd.classify_and_draft(c["text"], face=face, faq=faq)
            good_kind = k in (c.get("kind") or [])
            if good_kind and h == bool(c.get("human")):
                ok += 1
            else:
                fails.append((c["id"], k, h))
            if c.get("redline"):
                red += 1
                if d == "" and h:
                    safe += 1
        sd.MODEL = old
        out.append({"model": model, "cases": len(cases), "pass": ok,
                    "pass_rate": round(ok / max(len(cases), 1) * 100, 1),
                    "redline_total": red, "redline_safe": safe,
                    "redline_rate": round(safe / red * 100, 1) if red else None,
                    "fails": fails[:8]})
        print("  [%s] 通过 %d/%d = %.0f%% · 红线 %d/%d" % (model, ok, len(cases),
                                                          ok / max(len(cases), 1) * 100, safe, red))
    return out


def write_report(suites):
    lines = ["# 本地模型实测报告 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), "",
             "本机 %s · 判据=同一 prompt/同一 ctx、多次重复取中位、只算解码段" %
             (sh(["sysctl", "-n", "hw.memsize"]).strip() and
              "%.0fGB 内存" % (int(sh(["sysctl", "-n", "hw.memsize"]).strip() or 0) / 1073741824)), ""]
    if "throughput" in suites:
        lines += ["## 吞吐（decode tok/s）", "",
                  "| 模型 | 并发 | 单条中位 | 聚合中位 | 墙钟中位 |", "|---|---|---|---|---|"]
        for r in suites["throughput"]:
            lines.append("| %s | %d | %.1f | %.1f | %.1fs |"
                         % (r["model"], r["concurrency"], r["decode_tps_median"],
                            r["aggregate_tps_median"], r["wall_median"]))
        lines.append("")
    if "residency" in suites:
        lines += ["## 两档同驻的代价（同一 4B 负载）", ""]
        for r in suites["residency"]:
            lines.append("- %s: %s" % (r["scenario"], json.dumps({k: v for k, v in r.items()
                                                                  if k != "scenario"}, ensure_ascii=False)))
        lines.append("")
    if "coldload" in suites:
        lines += ["## 冷加载成本", ""]
        for r in suites["coldload"]:
            lines.append("- %s: 冷 %.2fs / 热 %.2fs → 每次换入代价 %.2fs"
                         % (r["model"], r["cold_s"], r["warm_s"], r["cost_s"]))
        lines.append("")
    if "quality" in suites:
        lines += ["## 质量（黄金集分类题）", "",
                  "| 模型 | 通过 | 通过率 | 红线安全 |", "|---|---|---|---|"]
        for r in suites["quality"]:
            lines.append("| %s | %d/%d | %.0f%% | %s/%s |"
                         % (r["model"], r["pass"], r["cases"], r["pass_rate"],
                            r["redline_safe"], r["redline_total"]))
        lines.append("")
    md = "\n".join(lines) + "\n"
    open(OUT_MD, "w", encoding="utf-8").write(md)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump({"ts": datetime.now().isoformat(timespec="seconds"), "suites": suites},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[bench] -> %s" % OUT_MD)
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True,
                    choices=["throughput", "residency", "coldload", "quality"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()
    suites = {}
    if os.path.exists(OUT_JSON):
        try:
            suites = json.load(open(OUT_JSON, encoding="utf-8")).get("suites") or {}
        except Exception:
            suites = {}
    print("[bench] 开始 %s（swap=%.0fMB 常驻=%.1fGB）" % (a.suite, mem()[0], mem()[3]))
    if a.suite == "throughput":
        suites["throughput"] = suite_throughput(reps=a.reps)
    elif a.suite == "residency":
        suites["residency"] = suite_residency(reps=a.reps)
    elif a.suite == "coldload":
        suites["coldload"] = suite_coldload(reps=a.reps)
    else:
        suites["quality"] = suite_quality(limit=a.limit)
    write_report(suites)
    return 0


if __name__ == "__main__":
    sys.exit(main())
