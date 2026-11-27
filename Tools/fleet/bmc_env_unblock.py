#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bmc_env_unblock.py — bm-c 环境解锁取证（撤 ollama 驻留 + ComfyUI 可达探测）。

为什么存在（2026-11-10 CEO-PROXY 事件班实测）：
  bm-c 名下 3 张 asset-gen 卡（需 ComfyUI 出图）被 route=queue 扣留，
  本机状态面写的是「no local GPU lane free」，但实测是
  verdict=GPU_COMFY_MISSING|RAM_LOW（RAM free 1.4G/23.9G、ComfyUI 未起、VRAM 15.1G 空闲）。
  即：不是没卡位，是缺环境。派卡之前必须先有这份回执证明环境可跑。

做法（全部确定性、可逆、不碰生产进程）：
  1) 调 Tools/fleet/free_mem.py --apply 撤掉 ollama 常驻模型（free_mem 自带 NEVER 白名单保护）
  2) 探 http://127.0.0.1:8188/system_stats 判断 ComfyUI 是否就位
  3) 回执写 RAM before/after + ComfyUI 结论；RAM>=4G 且 COMFY-UP 判解锁成功

用法：python Tools/fleet/bmc_env_unblock.py --receipt <path> [--apply]
      默认 dry-run（不真撤驻留），加 --apply 才执行。
退出码：0=解锁成功；3=如实 BLOCKED（RAM 或 ComfyUI 未达标）；1=用法错误
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
COMFY = "http://127.0.0.1:8188/system_stats"
STATUS_FILES = [
    os.path.join(ROOT, "gaming", "MiniGame", "Design", "configs", "GLOBAL", "fleet", "c.json"),
]


def read_ram():
    """优先读本机 fleet 状态面（c.json ram.free_gb），退回 Win32 全局内存。"""
    for p in STATUS_FILES:
        try:
            with open(p, encoding="utf-8-sig") as f:
                d = json.load(f)
            g = (d.get("ram") or {}).get("free_gb")
            if g is not None:
                return float(g), p
        except Exception:
            continue
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$o=Get-CimInstance Win32_OperatingSystem;"
             "[math]::Round($o.FreePhysicalMemory/1MB,2)"],
            capture_output=True, text=True, timeout=25)
        return float((out.stdout or "0").strip() or 0), "Win32_OperatingSystem"
    except Exception:
        return -1.0, "unavailable"


def probe_comfy():
    try:
        with urllib.request.urlopen(COMFY, timeout=4) as r:
            return "COMFY-UP http=%d" % r.status
    except Exception as e:
        return "COMFY-DOWN %s" % str(e)[:80]


def unload_ollama(apply_it):
    script = os.path.join(HERE, "free_mem.py")
    if not os.path.exists(script):
        return "free_mem.py MISSING (skip)"
    cmd = [sys.executable, script] + (["--apply"] if apply_it else [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return ((r.stdout or "") + (r.stderr or ""))[-2000:]
    except Exception as e:
        return "free_mem error: %s" % str(e)[:120]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--ram-gate-gb", type=float, default=4.0)
    a = ap.parse_args()

    before, src = read_ram()
    freemem_out = unload_ollama(a.apply)
    after, _ = read_ram()
    comfy = probe_comfy()

    ok = (after >= a.ram_gate_gb) and comfy.startswith("COMFY-UP")
    lines = [
        "bmc_env_unblock receipt",
        "mode=%s" % ("APPLY" if a.apply else "DRY-RUN"),
        "ram_before_gb=%.2f (src=%s)" % (before, src),
        "ram_after_gb=%.2f" % after,
        "ram_gate_gb=%.2f" % a.ram_gate_gb,
        "comfy=%s" % comfy,
        "verdict=%s" % ("UNBLOCKED" if ok else "BLOCKED"),
        "== free_mem output ==",
        freemem_out,
    ]
    path = a.receipt if os.path.isabs(a.receipt) else os.path.join(ROOT, a.receipt.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())