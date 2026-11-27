# -*- coding: utf-8 -*-
# c2143_bank_close.py -- close the re-anchor verdict job and pre-stow the KF-PACK-B main pass.
import io, json, time

P = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
J = json.loads(io.open(P, encoding="utf-8", newline="").read())
now = time.strftime("%Y-%m-%dT%H:%M:%S")

DONE_NOTE = (
    "VERDICT: the occluded-hand anchor works and B-EX2 is unlocked. 3/3 frames burned at 1344x768 in "
    "284s and were read at native size (not on the board). o1 (seed 204921): her hand is fully hidden "
    "behind the jacket hem, nothing to miscount, eyeline single-source and readable, skin acceptable "
    "under the dusk key - LOCKED as the B-EX2 main-pass seed. o2 (209030) and o3 (211892): the gesture "
    "turned into a grip on his forearm; four fingers read cleanly, the thumb sits on the far side of the "
    "arm (legitimate occlusion), eyelines connect, no melted anatomy - both usable, so B-EX2 now has a "
    "primary plus two alternates. This closes the C2142 dead end: the defect was the anchor's hand "
    "close-up, exactly as the birth gate said, and removing the close-up removed the failure."
)

for j in J["jobs"]:
    if j.get("id") == "kfpb-bex2-occl-verdict-c2143":
        j["status"] = "done"
        j["done_ts"] = now
        j["claimed_by"] = "tick-C2143"
        j["done_note"] = DONE_NOTE

NEW = {
    "id": "kfpb-mainpass-author-c2144",
    "status": "pending",
    "priority": 44,
    "auth": ("B-EX2 is unlocked (seed 204921 primary, 209030/211892 alternates). KF-PACK-B still owes the "
             "1344x768 main pass on all six frames; kfpb_probe_c2139.py only knows how to fire at probe "
             "size with probe seeds, so the main-pass runner does not exist yet."),
    "require": {"files_at_least": []},
    "cmd": [],
    "log_out": "media/MV/mv0001/logs/kfpb_mainpass.out.log",
    "log_err": "media/MV/mv0001/logs/kfpb_mainpass.err.log",
    "note": ("Author kfpb_mainpass_c2144.py from kfpb_probe_c2139.py: all six KF-PACK-B frames at 1344x768, "
             "one seed each (A/B faces as canonised, B-EX2 = 204921), lint gate + dry-run before firing, "
             "board + receipt. Fire detached and arm wave-harvest-pending.json. PASS gate = "
             "KFPB-MAINPASS-END ok=6/6 + 6 PNG >=900KB + board + receipt."),
    "prestow_ts": now,
    "prestow_note": "C2143 pre-stow (bank law: never empty) right after locking the B-EX2 seed.",
}
if not any(j.get("id") == NEW["id"] for j in J["jobs"]):
    J["jobs"].append(NEW)

io.open(P, "w", encoding="utf-8", newline="").write(json.dumps(J, ensure_ascii=False, indent=1))
print("BANK-CLOSED + PRESTOWED jobs=%d pending=%d" % (
    len(J["jobs"]), len([j for j in J["jobs"] if j.get("status") != "done"])))