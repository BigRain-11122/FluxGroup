# -*- coding: utf-8 -*-
# c2143_bank_prestow.py -- append the re-anchored B-EX2 verdict job to the bm-c GPU bank.
# Bank law: never empty after a round closes a job. No-op if the id already exists (idempotent).
import io, json, time

P = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
RAW = io.open(P, encoding="utf-8", newline="").read()
J = json.loads(RAW)
now = time.strftime("%Y-%m-%dT%H:%M:%S")
NEW = {
    "id": "kfpb-bex2-occl-verdict-c2143",
    "status": "pending",
    "priority": 43,
    "auth": ("C2143 fired the re-anchored B-EX2 (occluded-hand composition per verdict c2136 sec-5, "
             "1344x768, 3 seeds). The frames exist but nobody has read them at native size, so no seed "
             "is locked for the main pass yet."),
    "require": {
        "files_at_least": [
            ["media/MV/mv0001/xingqing/xq-kfpb-bex2-occl-c2143", "", 2]
        ]
    },
    "cmd": [],
    "log_out": "media/MV/mv0001/logs/kfpb_bex2_occl.out.log",
    "log_err": "media/MV/mv0001/logs/kfpb_bex2_occl.err.log",
    "note": ("Zero GPU review job. Read each PNG at native resolution: is the hand actually hidden behind "
             "the hem (no fingers poking through), does his eyeline read as a single believable line to her "
             "face, does her arm angle carry the gesture, and is the skin free of the glossy waxy face. "
             "PASS gate = a written verdict in done_note naming either the locked seed for the 1344x768 "
             "main pass or a further anchor change with the reason."),
    "prestow_ts": now,
    "prestow_note": "C2143 pre-stow (bank law: never empty) right after firing the re-anchored burn.",
}
if any(j.get("id") == NEW["id"] for j in J["jobs"]):
    print("BANK-ALREADY", NEW["id"])
else:
    J["jobs"].append(NEW)
    io.open(P, "w", encoding="utf-8", newline="").write(
        json.dumps(J, ensure_ascii=False, indent=1))
    print("BANK-APPENDED", NEW["id"], "jobs=%d" % len(J["jobs"]))
print("pending=%d" % len([j for j in J["jobs"] if j.get("status") != "done"]))