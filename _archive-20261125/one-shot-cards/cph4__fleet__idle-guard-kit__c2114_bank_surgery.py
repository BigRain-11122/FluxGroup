# -*- coding: utf-8 -*-
# c2114_bank_surgery.py -- flip f533c-i2v-leg done + pre-stow v3 strips + delete wave flag
import json, io, os

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
FLAG = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\wave-harvest-pending.json"

with io.open(BANK, "r", encoding="utf-8") as f:
    b = json.load(f)

hit = 0
for j in b["jobs"]:
    if j.get("id") == "f533c-i2v-leg":
        if j.get("status") == "done":
            print("ALREADY_DONE")
        else:
            j["status"] = "done"
            j["done_ts"] = "2026-10-20 03:23:17"
            j["done_note"] = (
                "HARVEST PASS by tick-C2114: PASS gate 4/4 (ALBUM LANE DONE lane=bmcpackA ok=1 fail=0 in log-f533c-i2v.out tail; "
                "clips-packA-768/XQ_F5-33c.mp4 854,252B >=100KB; ffprobe -count_frames decode-clean 158f @1344x768 24fps 6.58s, 630s burn). "
                "3-frame native strip QC 3/3 PASS: zero readable text in all three samples (tally strokes only), pen paused between strokes at tail with mid-stroke at mid, "
                "small square plain paper label holding its form (frame-0 'second sheet' is the KF's own layered design, confirmed against source KF F5-33c_s502092.png), "
                "clear cassette shell corner present, natural tripod grip, 35mm grain + warm 2001 telecine palette intact. "
                "Board xq-F533C-QC-STRIP-c2114.jpg + receipt qc-f533c-c2114/receipt.json. "
                "PACK-A now 33/33 on disk (incl. F5-33c + S5-27) -> assembly-unlock evidence base complete on the execution seat; "
                "full contact board xq-PACKA-33-FULL-BOARD-c2114.jpg. Remaining = director re-review on 33-unit board + S5-27 reshake counter-sign."
            )
            hit += 1
print("FLIPPED", hit)

ids = set(j.get("id") for j in b["jobs"])
if "packA-qc-strips-v3-33" not in ids:
    b["jobs"].append({
        "id": "packA-qc-strips-v3-33",
        "status": "pending",
        "priority": 26,
        "auth": "X2670 sec-6 assembly unlock: PACK-A complete at 33 units after C2114 F5-33c harvest; v2 board was the 31-unit redo-r1 base plate and is now stale",
        "require": {"files_at_least": [["media/mv-album-001-jay/clips-packA-768", "XQ_F5-33c.mp4", 1]]},
        "cmd": ["D:\\ComfyUI\\python_embeded\\pythonw.exe",
                "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\packA_qc_strips_v3_c2114.py"],
        "log_out": "media/mv-album-001-jay/log-qcstripsv3.out.txt",
        "log_err": "media/mv-album-001-jay/log-qcstripsv3.err.txt",
        "note": (
            "33-unit adjudication board regen (v2 verbatim + count 31->33 + redo-r1 swap kept). "
            "PASS gate = STRIPS-V3 DONE 33 clips in log tail + board xq-PACKA-QC-STRIPS-v3-c2114.jpg >= 1000000B + zero exit. "
            "Harvest = per-unit sec-4 adjudication on the 2 new units (F5-33c pen-pause/label form, S5-27 star three-beat) then "
            "director re-review on the 33-unit board -> assembly unlock."
        ),
        "prestow_ts": "2026-10-20T03:31:00",
        "prestow_note": "C2114 pre-stow immediately after p25 harvest flip (bank must never be empty, O-20261018-2236).",
    })
    print("PRESTOWED packA-qc-strips-v3-33")

data = json.dumps(b, ensure_ascii=False, indent=1) + "\n"
tmp = BANK + ".tmp"
with io.open(tmp, "w", encoding="utf-8", newline="") as f:
    f.write(data)
json.loads(io.open(tmp, "r", encoding="utf-8").read())
os.replace(tmp, BANK)
print("BANK_BYTES", os.path.getsize(BANK))

if os.path.isfile(FLAG):
    os.remove(FLAG)
    print("WAVE_FLAG_DELETED")
else:
    print("WAVE_FLAG_ABSENT")

open_jobs = [j["id"] + ":" + j["status"] for j in b["jobs"] if j.get("status") != "done"]
print("OPEN_JOBS", open_jobs)