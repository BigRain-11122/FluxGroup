# -*- coding: utf-8 -*-
# c2136_bank_surgery.py -- (1) close the stuck "claimed" v2 origin-verify job, (2) pre-stow the
# successor: Xingqing casting full-res A/B stage (1344x768 x3 seeds per light).
import io
import json
import os
import time

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
LAUNCH = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit\casting_full_c2136_launch.py"
PY = r"D:\ComfyUI\python_embeded\python.exe"
TS = time.strftime("%Y-%m-%d %H:%M")

d = json.load(io.open(BANK, encoding="utf-8-sig"))
jobs = d["jobs"]
by_id = {j.get("id"): j for j in jobs}

closed = 0
j = by_id.get("packA-conform-v2-origin-verify-v1")
if j and j.get("status") == "claimed":
    j["status"] = "done"
    j["done_ts"] = TS
    j["done_note"] = (
        "ORIGIN-VERIFY-V2-END ok=1 mismatches=0 (C2135 addendum, verifier run of "
        "xq_packa_v2_origin_verify_c2135.py: five receipts read back from origin, v2 film 4710/4710 "
        "frames, -14.2 LUFS / -2.3 dBTP). The guard never flipped the claim; closed from the runner "
        "receipt instead of re-running.")
    closed = 1

new_id = "casting-ab-full-c2136"
if new_id not in by_id:
    jobs.append({
        "id": new_id,
        "status": "pending",
        "priority": 40,
        "auth": (
            "xq-CASTING-READ-c2136.md sec-5: the v2 board passed the casting gates (A 8.0 / B 8.0, "
            "C 7.5, D 6.5); the next station is the full-res face-id stage for the two leading types "
            "so KF-PACK-B (6 face-dependent frames) can be unblocked."),
        "require": {"files_at_least": [
            ["cph4/fleet/mv-album-001-jay", "xq-CASTING-BOARD-c2136-v2.jpg", 100000]]},
        "cmd": [PY, LAUNCH],
        "log_out": "media/MV/mv0001/logs/xq_casting_c2136.out.log",
        "log_err": "media/MV/mv0001/logs/xq_casting_c2136.err.log",
        "note": (
            "12 frames at 1344x768 (types A and B, dusk + night, 3 seeds each) using the v2 age/skin "
            "fix blocks. PASS gate = CASTING-FULL-END ok=12 in the log tail plus 12 PNGs >=50KB and the "
            "board xq-CASTING-BOARD-c2136-full.jpg. GPU lanes only; resumes on partial runs."),
        "prestow_ts": TS,
    })

# keep the file's own indentation style exactly as found (probe first, then dump)
raw = io.open(BANK, encoding="utf-8-sig").read()
indent = 1 if raw.split("\n", 3)[1].startswith(" ") and not raw.split("\n", 3)[1].startswith("  ") else 2
tmp = BANK + ".tmp"
io.open(tmp, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=indent))
os.replace(tmp, BANK)

chk = json.load(io.open(BANK, encoding="utf-8-sig"))
pend = [x["id"] for x in chk["jobs"] if x.get("status") == "pending"]
print("BANK-SURGERY-END closed=%d jobs=%d pending=%s indent=%d" % (closed, len(chk["jobs"]), ",".join(pend) or "none", indent))