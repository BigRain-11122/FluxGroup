#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tri_lane_probe.py - 实测"采集 + 训练 + 养号出稿"能不能同时跑。

CEO 2026-11-19「我要求你采集和训练的同时，养号实战」。
现状是三者排队：`train_run.sh` 训练前 bootout sociallearn/socialagentday/modelqueue、
停 8788、`vram_ceiling --apply train`（全部卸载）。理由是 2026-11-18 实锚：
训练跑到一半别处把 9B(9GB)+4B(5GB) 装回来，训练进程 rss 3.9GB→0.43GB 被换出。

但"会不会换页"是能测的，不该靠一刀切。本探针同时拉起三线，按 15 秒采样
swap / pageouts / 空闲内存，并记录训练步速，最后给 SAFE/SLOW/UNSAFE 三态：

  SAFE   swap 增长 < 64MB 且 pageouts < 120/min 且训练步速不低于单跑 70%
  SLOW   不换页但训练明显变慢（说明是 CPU/带宽争用，能并行但要限流）
  UNSAFE 触发换页（按 CEO「不许硬扛 swap」直接否决）

用法：
  .venv-housing/bin/python Tools/fleet/tri_lane_probe.py --iters 60 --data /tmp/ds-probe
  .venv-housing/bin/python Tools/fleet/tri_lane_probe.py --iters 60 --data <ds> --collect-url <BV url>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state")
PY = sys.executable
# 训练必须用 pyenv 3.13（mlx_lm 只装在那里；.venv-housing 里没有——2026-11-19 实锚：
# 用 sys.executable 起训练会立刻 "No module named mlx_lm" 并 rc=1）。
TRAIN_PY = "/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"

sys.path.insert(0, HERE)


def sample():
    import mem_guard as mg
    return {"ts": time.time(), "swap_mb": mg.swap_used_mb(), "pageouts": mg.pageouts(),
            "free_gb": round(mg.free_gb(), 1)}


def load_4b(keep="30m"):
    """把 4B 装进来（模拟"出稿兜底车道"在跑），用 HTTP 而不是 ollama run 防挂住。"""
    import urllib.request
    body = json.dumps({"model": "qwen3.5:4b", "prompt": "hi", "stream": False,
                       "keep_alive": keep, "options": {"num_predict": 4}}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            r.read()
        return True, ""
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, str(e)[:80])


def inference_loop(n, out):
    """养号出稿车道：对 8788 发 n 次短请求，记录成功与耗时。"""
    import llm_client as lc
    ok = 0
    t0 = time.time()
    for i in range(n):
        try:
            r = lc.generate_lora("只写一句话：收到。", max_tokens=24, timeout=90)
            ok += 1 if r.get("ok") else 0
        except Exception:
            pass
    out.update({"n": n, "ok": ok, "sec": round(time.time() - t0, 1)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=60)
    ap.add_argument("--data", required=True)
    ap.add_argument("--collect-url", default="")
    ap.add_argument("--infer-n", type=int, default=10)
    ap.add_argument("--single-baseline-ms", type=float, default=0.0,
                    help="单跑时每步毫秒（有值就用来判 SLOW）")
    a = ap.parse_args()

    os.makedirs(STATE, exist_ok=True)
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "iters": a.iters,
           "data": a.data, "collect": bool(a.collect_url), "samples": []}
    t_start = time.time()

    ok4, why4 = load_4b()
    rec["loaded_4b"] = [ok4, why4]

    inf = {}
    th = threading.Thread(target=inference_loop, args=(a.infer_n, inf), daemon=True)
    th.start()

    col = None
    if a.collect_url:
        col = subprocess.Popen([PY, os.path.join(HERE, "social_collect.py"),
                                "--url", a.collect_url, "--limit", "60",
                                "--min", "1", "--scrolls", "3"],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)

    log = os.path.join(STATE, "tri-lane-train.log")
    tr = subprocess.Popen([TRAIN_PY, "-u", os.path.join(HERE, "train_lora.py"),
                           "--data", a.data, "--iters", str(a.iters),
                           "--num-layers", "16", "--max-seq-length", "224",
                           "--steps-per-eval", str(max(10, a.iters // 2)),
                           "--grad-checkpoint", "--keep-models"],
                          cwd=ROOT, stdout=open(log, "w"), stderr=subprocess.STDOUT, text=True)

    t_train_start = time.time()
    base = sample()
    while tr.poll() is None:
        time.sleep(15)
        s = sample()
        rec["samples"].append({"t": round(s["ts"] - base["ts"], 0), "swap_mb": s["swap_mb"],
                               "free_gb": s["free_gb"], "pageouts": s["pageouts"]})
    rec["train_rc"] = tr.returncode
    train_wall = time.time() - t_train_start
    th.join(timeout=5)
    rec["infer"] = inf
    col_rc = None
    if col is not None:
        try:
            col.wait(timeout=180)
            col_rc = col.returncode
        except Exception:
            col.kill()
            col_rc = "killed-timeout"
    rec["collect_rc"] = col_rc

    # 训练步速：从日志里取最后两行 step 的墙钟差
    step_ms = None
    try:
        txt = open(log, encoding="utf-8", errors="replace").read()
        its = re.findall(r"Iter (\d+):.*?Val loss", txt)
        times = re.findall(r"(\d{2}:\d{2}:\d{2}),\d+ - INFO - Iter (\d+)", txt)
        if len(times) >= 2:
            def secs(h):
                hh, mm, ss = (int(x) for x in h.split(":"))
                return hh * 3600 + mm * 60 + ss
            d = secs(times[-1][0]) - secs(times[0][0])
            n = int(times[-1][1]) - int(times[0][1])
            if n > 0 and d >= 0:
                step_ms = round(1000.0 * d / n, 1)
    except Exception:
        pass
    # 步速按墙钟算（训练日志的进度行格式不稳，正则容易落空＝假 None）
    rec["step_ms"] = step_ms or round(train_wall * 1000.0 / max(1, a.iters), 1)

    first, last = (rec["samples"][0], rec["samples"][-1]) if rec["samples"] else (base, base)
    swap_growth = last["swap_mb"] - first["swap_mb"]
    elapsed_min = max(1e-6, (time.time() - t_start) / 60.0)
    pageouts_rate = max(0, last["pageouts"] - first["pageouts"]) / elapsed_min
    rec.update({"swap_growth_mb": swap_growth, "pageouts_per_min": round(pageouts_rate, 1),
                "elapsed_min": round(elapsed_min, 1)})

    verdict = "SAFE"
    why = []
    if swap_growth > 64 or pageouts_rate > 120:
        verdict = "UNSAFE"
        why.append("触发换页：swap %+dMB / pageouts %.0f/min" % (swap_growth, pageouts_rate))
    if a.single_baseline_ms and step_ms and step_ms > a.single_baseline_ms * 1.43:
        verdict = "UNSAFE" if verdict == "UNSAFE" else "SLOW"
        why.append("训练变慢：%.0fms/步 vs 单跑 %.0fms" % (step_ms, a.single_baseline_ms))
    if rec["train_rc"] != 0:
        verdict = "UNSAFE"
        why.append("训练 rc=%s" % rec["train_rc"])
    rec["verdict"] = verdict
    rec["why"] = why or ["swap 与 pageouts 均在阈值内"]

    out = os.path.join(STATE, "tri-lane-%s.json" % datetime.now().strftime("%Y%m%d-%H%M%S"))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[probe] %s ｜ swap %+dMB ｜ pageouts %.0f/min ｜ 步速 %s ms ｜ 出稿 %s ｜ 采集 rc=%s"
          % (verdict, swap_growth, pageouts_rate, step_ms, inf or "-", col_rc))
    print("[probe] 报告 %s" % os.path.relpath(out, ROOT))
    return 0 if verdict == "SAFE" else 1


if __name__ == "__main__":
    sys.exit(main())
