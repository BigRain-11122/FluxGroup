"""C2122 bank surgery: flip p28 (grain delta) to done and pre-stow p29 successor."""
import io
import json
import time

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"

d = json.load(io.open(BANK, encoding="utf-8"))
jobs = d["jobs"]

p28 = [j for j in jobs if j.get("id") == "s527-grain-007-vs-010"]
assert len(p28) == 1, "p28 anchor count=%d" % len(p28)
p28 = p28[0]
assert p28["status"] == "claimed", "p28 status=%s" % p28["status"]
p28["status"] = "done"
p28["done_ts"] = "2026-10-20 05:19"
p28["done_note"] = (
    "HARVEST PASS by tick-C2122. First fire 04:40:59 died ok=0: the base-plate anchor was built with a "
    "doubled shot prefix (S5-26_S5-26_..._4k.png) so all six 0.07 plates read MISSING while only the "
    "grain010 side resolved. Fixed PAIRS to the real single-prefix base plates after confirming GRAIN=0.07 "
    "in s527_4k_esrgan_c2119.py, re-ran: GRAIN-DELTA-END ok=6 board_bytes=1,091,355 (>=300KB gate). "
    "Measured high-frequency sigma in the dark-sky patch: 0.07 = 3.188-3.195, 0.10 = 4.653-4.663, "
    "delta +1.459..+1.471 (~+46%) identical across all six = deterministic. Eye gate on the 1:1 two-column "
    "board: the delta is visible only in sky/shadow regions; 0.10 reads closer to 2000s Taiwan 35mm while "
    "0.07 leans low-noise digital; no blocky compression, no colour shift, no halo, no crushed blacks on "
    "either side; star field stays tight on 0.10 (no smear, no noise clusters). => grain 0.10 endpoint "
    "endorsed on the execution seat; director counter-sign still open."
)

existing = [j for j in jobs if j.get("id") == "s527-4kraw-locate"]
assert not existing, "p29 already present"
jobs.append({
    "id": "s527-4kraw-locate",
    "status": "pending",
    "priority": 29,
    "auth": "r1017 sec-8 item-1 pre-condition 1 (fine-line hallucination / dot-matrix cleanup) is open; "
            "C2121 established that locating artifacts on the grain plates is unusable (130-357 false "
            "candidates per plate because the new grain occupies the same high-frequency band). "
            "C2122 pre-stow: rebuild the six 4K plates with ZERO grain so the locator gets a clean substrate.",
    "require": {
        "files_at_least": [
            ["media/MV/mv0001/xingqing/abatch_s7r", "_s7rC.png", 6]
        ]
    },
    "cmd": [
        "D:\\ComfyUI\\python_embeded\\python.exe",
        "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\s527_4kraw_c2122.py"
    ],
    "log_out": "media/mv-album-001-jay/log-s527-4kraw-c2122.out.txt",
    "log_err": "media/mv-album-001-jay/log-s527-4kraw-c2122.err.txt",
    "note": "Six-grid ESRGAN x4 + LANCZOS 3840 wide with GRAIN=0.0 (no grain), then the C2121 scorer runs on "
            "those raw plates and emits trustworthy coordinates + a 1:1 zoom board. PASS gate = "
            "S527-4KRAW-BURN-END ok=6 in log tail + 6 PNG *_4kraw.png >=8MB + RAW-LOCATE-END with "
            "board_bytes >= 300000 + S527-4KRAW-END line. Existing grained plates are never touched. "
            "Harvest = next round: compare candidate counts raw vs grain (expect a large drop = locator "
            "usable), pick the real phantom-stroke addresses, then a targeted repair leg on the raw plate "
            "before the final grain pass.",
    "prestow_ts": "2026-10-20T05:20:00",
    "prestow_note": "C2122 pre-stow right after the grain-delta harvest (bank law: never empty).",
})

io.open(BANK, "w", encoding="utf-8", newline="\n").write(
    json.dumps(d, ensure_ascii=False, indent=1))
print("BANK_OK jobs=%d" % len(jobs))