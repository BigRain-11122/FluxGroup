#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_capacity_bench.py - 本机模型容量标定：在不触发 swap 的前提下能常驻什么。

为什么（2026-11-11 CEO 令「测一下我本地再不触发 swap 的极限，能常驻什么模型，
兼顾质量和并发效率」）：常驻模型不是越大越好——一驻留就换页，主控判读会从秒级
变成几十秒。必须用实测换页速率，而不是看 models 的大小估计。

判据（硬）：
  1. 每个配置前后读 vm.swapusage；swap 增长 > SWAP_LIMIT_MB 判 FAIL 并中止该档。
  2. 记录 ollama /api/ps 的 size（模型驻留字节）与解码 tok/s、首字延迟。
  3. 并发档记录墙钟与聚合吞吐。

用法：
    python3 Tools/fleet/local_capacity_bench.py --quick
    python3 Tools/fleet/local_capacity_bench.py --full
    python3 Tools/fleet/local_capacity_bench.py --matrix qwen3.5:4b:8192:1,qwen3.5:4b:8192:2
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

OLLAMA = os.environ.get("OLLAMA_HOST_URL", "http://127.0.0.1:11434")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "local-bench.json")
SWAP_LIMIT_MB = 128
PROMPT = ("你是机队主控的判读助手。下面是一张卡的描述："
          "卡 id=MV-KF-0007，工位=视觉，状态=OPEN，已 42 小时无人认领，"
          "产物=media/mv/clip_0007.mp4，验收=关键帧 1080x1920 且人脸一致。"
          "请用三句中文说明：该先做什么、为什么、做完怎么验。不要复述原文。")


def post(path, payload, timeout=180):
    req = urllib.request.Request(OLLAMA + path,
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def swap_used_mb():
    try:
        out = subprocess.check_output(["sysctl", "-n", "vm.swapusage"], text=True)
        m = re.search(r"used\s*=\s*([\d.]+)([MG])", out)
        if not m:
            return None
        v = float(m.group(1))
        return v * 1024 if m.group(2) == "G" else v
    except Exception:
        return None


def ps_models():
    try:
        d = post("/api/ps", {}) if False else json.loads(
            urllib.request.urlopen(OLLAMA + "/api/ps", timeout=10).read().decode())
        return d.get("models") or []
    except Exception:
        return []


def unload_all():
    for m in ps_models():
        try:
            post("/api/generate", {"model": m.get("name"), "keep_alive": 0, "prompt": ""}, 30)
        except Exception:
            pass
    time.sleep(1.0)


def run_one(model, ctx, parallel, n_predict=96, timeout=240):
    """单档：加载 → 一次顺序请求测首字与解码 → parallel 路并发测吞吐。"""
    t0 = time.time()
    payload = {"model": model, "prompt": PROMPT, "stream": False, "think": False,
               "keep_alive": "10m",
               "options": {"num_ctx": ctx, "temperature": 0,
                           "num_predict": n_predict, "num_parallel": parallel}}
    try:
        d = post("/api/generate", payload, timeout)
    except Exception as e:
        return {"model": model, "ctx": ctx, "parallel": parallel, "error": str(e)[:120]}
    total = (d.get("total_duration") or 0) / 1e9
    load = (d.get("load_duration") or 0) / 1e9
    ev = d.get("eval_count") or 0
    evd = (d.get("eval_duration") or 0) / 1e9
    pe = d.get("prompt_eval_count") or 0
    ped = (d.get("prompt_eval_duration") or 0) / 1e9
    size = 0
    for m in ps_models():
        if str(m.get("name")) == model or str(m.get("model")) == model:
            size = m.get("size") or 0
            break
    # 并发：parallel 路同时请求，同一模型已驻留
    results = []
    lock = threading.Lock()

    def worker():
        try:
            dd = post("/api/generate", dict(payload, options=dict(payload["options"],
                                                                  num_predict=64)), timeout)
            with lock:
                results.append(dd)
        except Exception as e:
            with lock:
                results.append({"error": str(e)[:80]})

    t1 = time.time()
    ths = [threading.Thread(target=worker) for _ in range(max(1, parallel))]
    [t.start() for t in ths]
    [t.join() for t in ths]
    wall = time.time() - t1
    agg_tokens = sum((x.get("eval_count") or 0) for x in results)
    return {
        "model": model, "ctx": ctx, "parallel": parallel,
        "size_gb": round(size / 2**30, 2) if size else None,
        "load_s": round(load, 2), "total_s": round(total, 2),
        "prompt_tok_s": round(pe / ped, 1) if ped else None,
        "decode_tok_s": round(ev / evd, 1) if evd else None,
        "tokens": ev,
        "conc_wall_s": round(wall, 2),
        "conc_tokens": agg_tokens,
        "conc_tok_s": round(agg_tokens / wall, 1) if wall else None,
        "sample": (d.get("response") or "")[:120].replace("\n", " "),
        "wall_s": round(time.time() - t0, 1),
    }


def matrix(quick=True):
    m = [
        ("qwen3.5:4b", 8192, 1), ("qwen3.5:4b", 8192, 2), ("qwen3.5:4b", 8192, 3),
        ("qwen3.5:4b", 16384, 2),
        ("qwen3.5:2b", 8192, 2),
        ("qwen3:8b", 8192, 1),
        ("qwen3.5:9b-mlx", 8192, 1),
    ]
    if not quick:
        m += [("qwen3.5:4b", 32768, 2), ("qwen3:8b", 8192, 2),
              ("qwen3.5:9b-mlx", 16384, 2), ("deepseek-r1:14b", 8192, 1)]
    return m


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--matrix", default="")
    a = ap.parse_args(argv)
    rows = []
    if a.matrix:
        for item in a.matrix.split(","):
            mo, ctx, par = item.rsplit(":", 2)   # 模型名自带冒号（qwen3.5:4b）
            rows.append((mo, int(ctx), int(par)))
    else:
        rows = matrix(quick=not a.full)

    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "swap_limit_mb": SWAP_LIMIT_MB,
           "runs": [], "notes": []}
    for model, ctx, par in rows:
        unload_all()
        before = swap_used_mb()
        r = run_one(model, ctx, par)
        after = swap_used_mb()
        r["swap_before_mb"] = round(before, 1) if before is not None else None
        r["swap_after_mb"] = round(after, 1) if after is not None else None
        r["swap_delta_mb"] = round((after or 0) - (before or 0), 1) if None not in (before, after) else None
        r["verdict"] = "FAIL-SWAP" if (r.get("swap_delta_mb") or 0) > SWAP_LIMIT_MB else "OK"
        out["runs"].append(r)
        print(json.dumps({k: r.get(k) for k in
                          ("model", "ctx", "parallel", "size_gb", "decode_tok_s",
                           "conc_tok_s", "swap_delta_mb", "verdict", "error")},
                         ensure_ascii=False))
        if r["verdict"] == "FAIL-SWAP":
            out["notes"].append("%s ctx=%s par=%d 触发换页，后续同尺寸档位不再尝试"
                                % (model, ctx, par))
            break
    unload_all()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n写入 %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
