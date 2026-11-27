#!/usr/bin/env python3
"""Repeatable local-LLM benchmark for the Mac control plane (bm-m).

Why: model choice on a 32 GB unified-memory box is decided by memory footprint
and decode throughput, not by parameter count. Guessing wasted half a day once;
this tool makes the numbers reproducible.

Measures per (model, num_ctx) config via the Ollama HTTP API:
  - load time (s)
  - resident size while loaded (GB, from /api/ps size_vram)
  - prefill throughput (prompt tokens/s)
  - decode throughput (generated tokens/s)
  - system swap-in-use delta (GB)

Usage:
  python3 Tools/fleet/local_llm_bench.py
  python3 Tools/fleet/local_llm_bench.py --models qwen3:4b-instruct --ctx 8192,16384
  python3 Tools/fleet/local_llm_bench.py --runs 3 --out cph4/fleet/dispatcher/LLM-BENCH.json
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import time
import urllib.request
from datetime import datetime, timezone

HOST = "http://127.0.0.1:11434"
PROMPT = "用三句话说明本地大模型解码速度由哪些硬件因素决定。"
NUM_PREDICT = 96


def post(path: str, payload: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(
        HOST + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get(path: str) -> dict:
    with urllib.request.urlopen(HOST + path, timeout=30) as r:
        return json.load(r)


def swap_used_gb() -> float:
    out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
    m = re.search(r"used = ([\d.]+)M", out)
    return round(float(m.group(1)) / 1024, 2) if m else -1.0


def loaded() -> list[dict]:
    return [
        {
            "name": m.get("name") or m.get("model", ""),
            "size_gb": round((m.get("size_vram") or m.get("size") or 0) / 1e9, 1),
            "ctx": m.get("context_length"),
            "until": m.get("expires_at"),
        }
        for m in get("/api/ps").get("models", [])
    ]


def stop(model: str) -> None:
    subprocess.run(["ollama", "stop", model], capture_output=True, text=True)


def wait_gone(model: str, timeout_s: float = 20.0) -> bool:
    """Model eviction is asynchronous; a residual instance would poison load time."""
    end = time.time() + timeout_s
    while time.time() < end:
        if not any(m["name"].split(":")[0] == model.split(":")[0] for m in loaded()):
            return True
        time.sleep(0.5)
    return False


def unload_all() -> None:
    for m in loaded():
        stop(m["name"])


def unload(model: str) -> None:
    stop(model)
    wait_gone(model)


def one_run(model: str, num_ctx: int) -> dict:
    # Ollama reuses a cached prefix for identical prompts, which reports absurd
    # prefill rates; a per-run nonce keeps every prefill cold and comparable.
    nonce = f"{time.time_ns()}"
    r = post(
        "/api/generate",
        {
            "model": model,
            "prompt": f"{PROMPT}\n\n[run {nonce}]",
            "stream": False,
            "keep_alive": "5m",
            "options": {"num_predict": NUM_PREDICT, "temperature": 0, "seed": 0, "num_ctx": num_ctx},
        },
    )
    prefill_n = r.get("prompt_eval_count") or 0
    prefill_t = (r.get("prompt_eval_duration") or 0) / 1e9
    dec_n = r.get("eval_count") or 0
    dec_t = (r.get("eval_duration") or 0) / 1e9
    return {
        "load_s": round((r.get("load_duration") or 0) / 1e9, 2),
        "prefill_tok_s": round(prefill_n / prefill_t, 1) if prefill_t else 0.0,
        "decode_tok_s": round(dec_n / dec_t, 1) if dec_t else 0.0,
        "prompt_tokens": prefill_n,
        "gen_tokens": dec_n,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="qwen3:4b-instruct,qwen3.5:35b-a3b")
    ap.add_argument("--ctx", default="8192,32768")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    ctxs = [int(c) for c in args.ctx.split(",") if c.strip()]

    meta = {
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "chip": platform.processor() or subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True
        ).stdout.strip(),
        "env": {
            k: v
            for k, v in (
                line.split("=", 1)
                for line in subprocess.run(
                    ["launchctl", "getenv", "OLLAMA_KV_CACHE_TYPE"], capture_output=True, text=True
                ).stdout.splitlines()
                if "=" in line
            )
        },
        "swap_before_gb": swap_used_gb(),
    }
    results = []

    print(f"swap before: {meta['swap_before_gb']} GB")
    for model in models:
        unload(model)
        for ctx in ctxs:
            runs = []
            for _ in range(args.runs):
                unload(model)
                time.sleep(1.0)
                runs.append(one_run(model, ctx))
            cur = loaded()
            size = next((m["size_gb"] for m in cur if m["name"] == model), None)
            ctx_seen = next((m["ctx"] for m in cur if m["name"] == model), None)
            best = {
                "load_s": min(r["load_s"] for r in runs),
                "prefill_tok_s": max(r["prefill_tok_s"] for r in runs),
                "decode_tok_s": max(r["decode_tok_s"] for r in runs),
            }
            row = {
                "model": model,
                "num_ctx": ctx,
                "ctx_reported": ctx_seen,
                "resident_gb": size,
                "runs": runs,
                **best,
                "swap_after_gb": swap_used_gb(),
            }
            results.append(row)
            print(
                f"{model:22s} ctx={ctx:6d} seen={ctx_seen} size={size} GB  "
                f"load={row['load_s']:5.1f}s  prefill={row['prefill_tok_s']:6.1f}  decode={row['decode_tok_s']:6.1f}  "
                f"swap={row['swap_after_gb']} GB"
            )

    unload_all()
    payload = {**meta, "results": results, "swap_after_all_gb": swap_used_gb()}
    print(f"swap after unload: {payload['swap_after_all_gb']} GB")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()