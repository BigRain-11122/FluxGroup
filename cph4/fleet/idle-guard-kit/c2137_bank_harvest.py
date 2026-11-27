# -*- coding: utf-8 -*-
# c2137_bank_harvest.py -- harvest the casting full-res job from its runner receipt and pre-stow
# the successor: KF-PACK-B composition probe (6 frames, 672x384, 1 seed per shot).
import io
import json
import os
import time

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
RUNNER = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit\kfpb_probe_c2139.py"
PY = r"D:\ComfyUI\python_embeded\python.exe"
TS = time.strftime("%Y-%m-%d %H:%M")

d = json.load(io.open(BANK, encoding="utf-8-sig"))
jobs = d["jobs"]
by_id = {j.get("id"): j for j in jobs}

closed = 0
j = by_id.get("casting-ab-full-c2136")
if j and j.get("status") == "claimed":
    j["status"] = "done"
    j["done_ts"] = TS
    j["done_note"] = (
        "CASTING-FULL-END ok=12/12 fails=none (idle guard fired 09:32:43, harvested by tick-C2137 "
        "from the receipt). 12 native 1344x768 PNGs, board xq-CASTING-BOARD-c2136-full.jpg 230,093B. "
        "Frame QC at native res: 12/12 in 7.5-9.0, zero eliminate-grade defects; top three 8.9/9.0/9.0. "
        "Director-seat verdict xq-CASTING-VERDICT-c2136-full.md fixes B (seed 578950 dusk + 514974 "
        "night) as the canonical face and A (439906) as the alternate plus cross-hair consistency "
        "anchor. Receipt out_dir field corrected to the -full directory on harvest.")
    closed = 1

new_id = "kf-packb-probe-c2139"
if new_id not in by_id:
    jobs.append({
        "id": new_id,
        "status": "pending",
        "priority": 41,
        "auth": (
            "xq-CASTING-VERDICT-c2136-full.md sec-4 step-2: the canonical B face is fixed, which "
            "unblocks KF-PACK-B (S1-08 / S3-17 / S3-21 / S5-31 plus the two B extras). "
            "KF-PACK-A-v1 sec-2 probe law requires 672x384 one seed per shot before the 1344x768 pass."),
        "require": {"files_at_least": [
            ["cph4/fleet/mv-album-001-jay", "xq-CASTING-VERDICT-c2136-full.md", 3000]]},
        "cmd": [PY, RUNNER],
        "log_out": "media/MV/mv0001/logs/kfpb_probe_c2139.out.log",
        "log_err": "media/MV/mv0001/logs/kfpb_probe_c2139.err.log",
        "note": (
            "6 frames at 672x384, one derived seed each, 8 steps: S1-08 hands, S3-17 feet, S3-21 "
            "look-up, S5-31 two-shot, B-EX1 kite spool, B-EX2 jacket hem. Prompts = KF-PACK-A shared "
            "blocks (world + light family + closing) around the SHOTLIST v3 KF anchors; female block = "
            "the canonical B face, male block = ID_M_2001 with jman LoRA 0.6 on the two frames that "
            "show him. PASS gate = KFPB-PROBE-END ok=6 in the log tail plus 6 PNGs >=50KB, the strip "
            "board xq-KFPB-BOARD-c2139-probe.jpg and the receipt. GPU lanes only, resumes on partial "
            "runs, aborts if the ComfyUI queue is not empty."),
        "prestow_ts": TS,
    })

raw = io.open(BANK, encoding="utf-8-sig").read()
indent = 1 if raw.split("\n", 3)[1].startswith(" ") and not raw.split("\n", 3)[1].startswith("  ") else 2
tmp = BANK + ".tmp"
io.open(tmp, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=indent))
os.replace(tmp, BANK)

chk = json.load(io.open(BANK, encoding="utf-8-sig"))
pend = [x["id"] for x in chk["jobs"] if x.get("status") == "pending"]
print("BANK-HARVEST-END closed=%d jobs=%d pending=%s indent=%d" % (closed, len(chk["jobs"]), ",".join(pend) or "none", indent))