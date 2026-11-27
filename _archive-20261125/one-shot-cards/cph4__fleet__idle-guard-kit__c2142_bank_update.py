# -*- coding: utf-8 -*-
# C2142 bank surgery: close kfpb-bex2-reroll-c2140 with its real verdict, and pre-stow a
# successor job (bank law: never empty). Reads the bank, edits only the two entries.
import json, io, os, time

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
raw = io.open(BANK, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
d = json.loads(raw.decode("utf-8-sig"))
jobs = d["jobs"] if isinstance(d, dict) and "jobs" in d else d

idx = {j.get("id"): j for j in jobs}
j = idx["kfpb-bex2-reroll-c2140"]
j["status"] = "done"
j["claimed_ts"] = "2026-10-20T12:25:00"
j["claimed_by"] = "tick-C2142"
j["done_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
j["done_note"] = (
    "Authored the blocked runner (idle-guard-kit/kfpb_bex2_reroll_c2140.py: one frame, hand-geometry + "
    "eyeline repair clause, deterministic seeds, env overrides for tag/res/seed list). Probe-res sweep "
    "3/3 burned at 672x384 (seeds 204921 / 206038 / 207158, PNG 297-315KB, board 73626B, receipt "
    "xq-KFPB-BEX2-RECEIPT-c2140.json). Board read picked r2; NATIVE PNG read overturned it: r1/r2/r3 all "
    "show 3-4 fused finger shapes with no readable thumb at probe resolution = hand clause FAIL 0/3. "
    "Verdict: this is a resolution limit, not a seed problem - the hand occupies too few pixels at 672x384. "
    "Escalation fired in the same round at the real main-pass size (1344x768, seeds 206038+207158, tag "
    "xq-kfpb-bex2-hd-c2142)."
)

succ = {
    "id": "kfpb-bex2-hd-verdict-c2142",
    "status": "pending",
    "priority": 41,
    "auth": ("C2142 native read: the B-EX2 hand stays fused at probe resolution (672x384) across three seeds, "
             "so the frame cannot be judged there. The 1344x768 test frames exist on disk and need a native "
             "verdict before the main pass commits a B-EX2 seed."),
    "require": {"files_at_least": [["media/MV/mv0001/xingqing/xq-kfpb-bex2-hd-c2142", "", 2]]},
    "cmd": [],
    "log_out": "media/MV/mv0001/logs/kfpb_bex2_reroll.out.log",
    "log_err": "media/MV/mv0001/logs/kfpb_bex2_reroll.err.log",
    "note": ("Zero GPU review job: read the 1344x768 PNGs at native size, count fingers and check the thumb, "
             "then either lock a B-EX2 seed for the main pass or record that the anchor must change "
             "(crop the hand to the frame edge / shift the gesture to the sleeve cuff). PASS gate = a written "
             "verdict in the bank done_note naming the locked seed or the redesigned anchor."),
    "prestow_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "prestow_note": "C2142 pre-stow (bank law: never empty) after closing the probe-res re-roll."
}
if "kfpb-bex2-hd-verdict-c2142" not in idx:
    jobs.append(succ)
else:
    idx["kfpb-bex2-hd-verdict-c2142"].update(succ)

out = json.dumps(d, ensure_ascii=False, indent=1)
io.open(BANK, "w", encoding="utf-8-sig" if bom else "utf-8", newline="").write(out + "\n")
chk = json.loads(io.open(BANK, encoding="utf-8-sig").read())
ids = [x["id"] for x in (chk["jobs"] if isinstance(chk, dict) and "jobs" in chk else chk)]
print("BANK_OK jobs=%d closed=%s successor=%s" % (
    len(ids),
    [x["id"] for x in (chk["jobs"] if isinstance(chk, dict) else chk) if x.get("status") == "done"][-1],
    "kfpb-bex2-hd-verdict-c2142" in ids))