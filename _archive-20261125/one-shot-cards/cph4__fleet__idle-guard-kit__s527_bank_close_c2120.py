# -*- coding: utf-8 -*-
"""C2120: bank bookkeeping - close s527-4k-grain-ab, pre-stow the grain delta board."""
import json
import os
import time

P = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
with open(P, encoding="utf-8") as f:
    d = json.load(f)

now = time.strftime("%Y-%m-%dT%H:%M:%S")
for j in d["jobs"]:
    if j["id"] == "s527-4k-grain-ab":
        j["status"] = "done"
        j["done_ts"] = now
        j["claimed_by"] = j.get("claimed_by") or "tick-C2120-idleguard"
        j["done_note"] = ("GRAIN-AB-END ok=4 + board 223408B; multimodal read = 0.10 is closer to "
                          "2000s Taiwan film (0.05 dark areas read slightly digital). Endpoint adopted "
                          "and the six grids re-burned clean at 0.10 (xq-S527-4K-GRAIN010-RECEIPT-c2120.json, "
                          "6x 3840x2194, 15.1-15.8MB, s20193/s20202 byte-identical to the A/B endpoint "
                          "plates = deterministic). Monitor recheck: star_retention 1.27-3.50 vs source "
                          "(no faint-star loss), corner_dark 0.995-0.9998.")

if not any(j["id"] == "s527-grain-007-vs-010" for j in d["jobs"]):
    d["jobs"].append({
        "id": "s527-grain-007-vs-010",
        "status": "pending",
        "priority": 28,
        "auth": "r1017 sec-5 row-1 endpoint pick support: director needs the 1:1 delta before ratifying 0.10",
        "require": {"files_at_least": [["media/MV/mv0001/xingqing/s7r-4k",
                                        "_4k_grain010.png", 6]]},
        "cmd": ["D:\\ComfyUI\\python_embeded\\python.exe",
                "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\s527_grain_delta_c2121.py"],
        "log_out": "media/mv-album-001-jay/log-s527-graindelta.out.txt",
        "log_err": "media/mv-album-001-jay/log-s527-graindelta.err.txt",
        "note": ("Side-by-side 1:1 of grain 0.07 vs 0.10 for the six grids + measured high-frequency sigma "
                 "per level. PASS gate = GRAIN-DELTA-END ok=6 in log tail + board >= 300KB. Reads plates "
                 "already on disk; zero re-burn."),
        "prestow_ts": now,
        "prestow_note": "C2120 pre-stow after adopting the 0.10 endpoint (bank law: never empty).",
    })

with open(P, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print("BANK-END jobs=%d done=%d pending=%d" % (
    len(d["jobs"]),
    sum(1 for j in d["jobs"] if j["status"] == "done"),
    sum(1 for j in d["jobs"] if j["status"] in ("pending", "claimed"))))