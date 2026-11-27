#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compute_meter.py - 本机算力到底用了几成（可核对读数，不是感觉）。

CEO 2026-11-19「把算力利用到极致」。要先能测，才谈得上榨干：
  GPU   ioreg AGXAccelerator 的 "Device Utilization %"（真读数，不是猜）
  CPU   1 - 空闲率（ps 采样两次）
  车道   当前驻留模型与 8788 是否有适配器
  产出   近 1 小时是否有真活（新语料行数 / 训练步 / 出稿条数）
最后给一句判词：是先"没活"还是"活没排上"——这两种空转的修法完全不同。

用法：
  .venv-housing/bin/python Tools/fleet/compute_meter.py            # 打一行 + 写 state
  .venv-housing/bin/python Tools/fleet/compute_meter.py --json
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state")
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")


BASE_TOK_S = 41.0     # 2026-11-18 实测：单条 4B@8k 解码 41.0 tok/s（两批 41.0/41.2）


def gpu_util():
    """GPU 负载用**吞吐探针**量，不用 ioreg 的 Device Utilization。

    为什么换：ioreg 那个 "Device Utilization %" 实测三次读 97/97/98 纹丝不动——
    它是开机以来的平均，不是实时负载（拿它当"利用率"就是假读数）。
    吞吐会随争用下降，所以"基准 tok/s ÷ 实测 tok/s"才是能用的负载证据。
    """
    import urllib.request
    body = json.dumps({"model": "qwen3.5:4b-mlx", "prompt": "数到十：1 2 3",
                       "stream": False, "keep_alive": "2m",
                       "options": {"num_predict": 24, "temperature": 0}}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read().decode() or "{}")
        wall = max(1e-6, time.time() - t0)
        n = int(d.get("eval_count") or 0)
        ed = float(d.get("eval_duration") or 0) / 1e9
        tok_s = (n / ed) if (n and ed) else (n / wall if n else 0)
        if not tok_s:
            return None
        return {"tok_s": round(tok_s, 1),
                "ratio": round(tok_s / BASE_TOK_S, 2),
                "note": "基准 %.0f tok/s；比值越低说明 GPU 被别的活占着" % BASE_TOK_S}
    except Exception:
        return None


def cpu_busy():
    """CPU 忙的百分比：ps 的 %cpu 是"单进程单核百分比"，全机累加后除以核数。

    不要用"两次采样相减"——那两个数都是瞬时值，相减是噪声（第一版就这么错，
    跑出"CPU 忙 100%"的假读数）。
    """
    try:
        o = subprocess.run(["ps", "-A", "-o", "%cpu="], capture_output=True,
                           text=True, timeout=10).stdout
        total = sum(float(x) for x in o.split() if x.strip())
        cores = os.cpu_count() or 1
        return round(min(100.0, total / cores), 1)
    except Exception:
        return None


def lanes():
    try:
        out = subprocess.run(["/Users/junsheng.sun/.homebrew/bin/ollama", "ps"],
                             capture_output=True, text=True, timeout=10).stdout
        rows = [l.split()[0] for l in out.splitlines()[1:] if l.strip()]
    except Exception:
        rows = []
    lora = ""
    try:
        sys.path.insert(0, HERE)
        import llm_client as lc
        lora = (lc.probe_lora() or {}).get("verdict", "")
    except Exception:
        pass
    return rows, lora


def recent_work(minutes=60):
    """近 N 分钟的真实产出：语料增行 / 训练步 / 出稿条。空转的判据要用产出，不用进程。"""
    cut = time.time() - minutes * 60
    out = {"corpus_new": 0, "trained": 0, "posted": 0}
    p = os.path.join(SOCIAL, "corpus", "human", "own_collected.jsonl")
    try:
        if os.path.getmtime(p) > cut:
            out["corpus_mtime"] = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%H:%M")
    except Exception:
        pass
    try:
        rd = os.path.join(SOCIAL, "train", "RUNS")
        for d in os.listdir(rd):
            p2 = os.path.join(rd, d)
            if os.path.getmtime(p2) <= cut:
                continue
            try:
                j = json.load(open(os.path.join(p2, "RUN.json"), encoding="utf-8"))
            except Exception:
                continue
            if j.get("plumbing_only") or int(j.get("iters") or 0) < 100:
                continue          # 压测/管路件不算产出
            out["trained"] += 1
    except Exception:
        pass
    try:
        import practice_tick as pt
        out["posted"] = len([r for r in pt.rows_today() if r.get("action") == "post"])
    except Exception:
        pass
    return out


def verdict(g, c, lr, work):
    if not g:
        return "GPU 吞吐探针失败（不要用别的数冒充利用率）"
    r = g.get("ratio") or 0
    if r >= 0.85:
        return "GPU 未被争用（%.0f tok/s ≈ 基准，%.0f%%）——空着就是没活" % (
            g["tok_s"], 100 * r)
    if r >= 0.5:
        return "GPU 中等争用（%.0f tok/s，%.0f%% 基准）" % (g["tok_s"], 100 * r)
    return "GPU 被重压（%.0f tok/s，仅 %.0f%% 基准）：正在算重活" % (g["tok_s"], 100 * r)
    if c is not None and c >= 70 and (g.get("ratio") or 0) >= 0.85:
        return "CPU 忙而 GPU 空：有 CPU 活没排到 GPU 上"
    if work.get("trained", 0) or work.get("corpus_new", 0) or work.get("posted", 0):
        return "GPU 空闲但近 1h 有产出（训练%d/出稿%d）：属正常起伏" % (
            work.get("trained", 0), work.get("posted", 0))
    return "GPU 空闲且近 1h 无新语料/训练/出稿：是**没活**，不是没榨"


def main():
    as_json = "--json" in sys.argv
    g = gpu_util()
    c = cpu_busy()
    ls, lr = lanes()
    work = recent_work()
    v = verdict(g, c, lr, work)
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "gpu_util": g, "cpu_busy": c,
           "lanes": ls, "lora": lr, "work": work, "verdict": v}
    os.makedirs(STATE, exist_ok=True)
    json.dump(rec, open(os.path.join(STATE, "compute-meter.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if as_json:
        print(json.dumps(rec, ensure_ascii=False))
    else:
        print("[meter] GPU %s ｜ CPU 忙 %s%% ｜ 驻留 %s ｜ 8788 %s ｜ 产出 %s ｜ %s"
              % ("?" if not g else "%.0f tok/s" % g["tok_s"],
                 "?" if c is None else "%.0f" % c, ",".join(ls) or "无", lr or "?",
                 "训练%d/出稿%d/语料%s" % (work.get("trained", 0), work.get("posted", 0),
                                          work.get("corpus_mtime") or "-"), v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
