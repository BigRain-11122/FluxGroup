#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resource_governor.py - 把本机 CPU/GPU/内存用到极致，但守住 swap 红线。

CEO 2026-11-09：「CPU GPU 内存应用到极致，不要触发 swap」。
做法（每 60s）：
  1. 读 swap 用量、可用内存、已加载模型；
  2. swap 已用 > 2.2GB 或可用 < 1.5GB → 卸掉"非主力"模型（embedding / 8B），
     只保留 4B 主力；写状态并记日志；
  3. 其余情况不动手（激进用，不提前降级）；
  4. 输出 state/resource-governor.json 供日报/看板读。

用法：python3 Tools/fleet/resource_governor.py [--apply]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
OUT = os.path.join(STATE, "resource-governor.json")
LOG = os.path.join(STATE, "resource-governor.log")
OLLAMA = "http://127.0.0.1:11434"
KEEP = ("qwen3.5:4b-mlx",)


def swap_used_mb():
    try:
        t = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
        m = re.search(r"used = ([0-9.]+)M", t)
        return float(m.group(1)) if m else -1
    except Exception:
        return -1


def free_gb():
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    vals = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            try:
                vals[k.strip()] = int(v.strip().rstrip("."))
            except ValueError:
                pass
    return round((vals.get("Pages free", 0) + vals.get("Pages inactive", 0)
                  + vals.get("Pages speculative", 0)) * 16384 / 1024 ** 3, 1)


def loaded():
    try:
        d = json.loads(urllib.request.urlopen(OLLAMA + "/api/ps", timeout=5).read())
        return [(m["name"], round(m.get("size_vram", 0) / 1e9, 1)) for m in d.get("models", [])]
    except Exception:
        return []


def unload(model):
    try:
        req = urllib.request.Request(OLLAMA + "/api/generate",
                                     data=json.dumps({"model": model, "keep_alive": 0}).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=60).read()
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sw, free = swap_used_mb(), free_gb()
    models = loaded()
    act = []
    red = sw > 2200 or free < 1.5
    if red and a.apply:
        for name, _gb in models:
            if name in KEEP:
                continue
            if unload(name):
                act.append("unloaded %s" % name)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "swap_used_mb": sw, "free_gb": free,
           "models": models, "red": red, "actions": act}
    os.makedirs(STATE, exist_ok=True)
    json.dump(rec, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if red:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s swap=%.0fMB free=%.1fGB actions=%s\n" % (rec["ts"], sw, free, act))
    print(json.dumps(rec, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
