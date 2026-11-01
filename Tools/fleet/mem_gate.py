#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mem_gate.py - what a 32GB unified-memory Mac may actually load, measured not guessed.

Unified memory is one pool: the CEO's apps (Doubao/Feishu/Claude/Safari/Tuanjie) are part of
the same 32GB the model would take. So the budget is not "how big is the model" but
"how much is left after the human".

  available = free + inactive + speculative + purgeable   (macOS reclaimables)
  reserve   = 6GB   (apps + kernel + compressor headroom; swap was already 5GB at 0GB free)
  model_max = clamp(available - reserve, 0, 12GB)

Verdicts:
  OK      model_max >= requested footprint
  DOWNGRADE  fits a smaller tier (4B) but not the requested one
  WAIT    below even the resident tier -> do not load anything now

Usage: python3 Tools/fleet/mem_gate.py [--need-gb 22] [--json]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

RESERVE_GB = 6.0
CAP_GB = 12.0          # never let one model hold more than ~1/3 of the pool
RESIDENT_GB = 3.3      # qwen3:4b-instruct @8k, measured
# CEO 2026-11-01: 不要频繁触发硬盘交换，合理使用 MacBook 的算力. Swap already in use means
# the box is under pressure BEFORE the model loads; counting only "free" RAM would invite
# a load that thrashes. Every GB of live swap is subtracted from what a model may claim.
SWAP_SOFT_GB = 1.0     # above this: be conservative
SWAP_HARD_GB = 2.0     # above this: no new large model, period


def available_gb() -> float:
    vm = subprocess.check_output(["vm_stat"], text=True)
    page = 16384
    vals = {}
    for ln in vm.splitlines():
        if "page size of" in ln:
            page = int(ln.split("page size of")[1].split()[0])
        if ":" in ln:
            k, v = ln.split(":", 1)
            try:
                vals[k.strip()] = int(v.strip().rstrip("."))
            except ValueError:
                pass
    return round(sum(vals.get(k, 0) for k in
                     ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable"))
                 * page / 1e9, 1)


def swap_used_gb() -> float:
    out = subprocess.check_output(["sysctl", "-n", "vm.swapusage"], text=True)
    m = re.search(r"used = ([\d.]+)M", out)
    return round(float(m.group(1)) / 1024, 1) if m else -1.0


def decide(need_gb: float) -> dict:
    avail = available_gb()
    swap = swap_used_gb()
    model_max = max(0.0, min(CAP_GB, avail - RESERVE_GB))
    note = ""
    if swap >= SWAP_HARD_GB:
        # Hard stop: the machine is already paging. Anything bigger than the resident seat
        # would move more hot pages to disk, which is exactly what the CEO forbade.
        model_max = min(model_max, RESIDENT_GB)
        note = "swap hard cap (%.1fGB live) - no model larger than the resident seat" % swap
    elif swap >= SWAP_SOFT_GB:
        model_max = max(0.0, model_max - (swap - SWAP_SOFT_GB))
        note = "swap soft cap (%.1fGB live subtracted from the budget)" % swap
    if need_gb >= model_max:
        verdict = "OK" if need_gb <= model_max else (
            "DOWNGRADE" if model_max >= RESIDENT_GB else "WAIT")
    else:
        verdict = "OK"
    return {"available_gb": avail, "reserve_gb": RESERVE_GB, "cap_gb": CAP_GB,
            "model_max_gb": round(model_max, 1), "need_gb": need_gb,
            "swap_used_gb": swap, "verdict": verdict, "note": note}


def main() -> int:
    need = 22.0
    if "--need-gb" in sys.argv:
        need = float(sys.argv[sys.argv.index("--need-gb") + 1])
    d = decide(need)
    if "--json" in sys.argv:
        print(json.dumps(d, ensure_ascii=False))
    else:
        print("[mem] avail=%.1fGB max_model=%.1fGB need=%.1fGB swap=%.1fGB -> %s%s"
              % (d["available_gb"], d["model_max_gb"], d["need_gb"], d["swap_used_gb"],
                 d["verdict"], (" | " + d["note"]) if d.get("note") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())