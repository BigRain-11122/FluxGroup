# -*- coding: utf-8 -*-
# C2142 closeout surgery: state-c.json (BOM + indent 1) last_round + bank successor verdict.
import json, io, time

STATE = r"K:\Fluxgroup\MiniGame\state-c.json"
BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"

# ---- state ----
raw = io.open(STATE, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
st = json.loads(raw.decode("utf-8-sig"))
now = time.strftime("%Y-%m-%d %H:%M:%S")
st["last_round"] = {
    "ts": now,
    "result": (
        "C2142 M1 round. Step0 merged the two pending lane inboxes (M2 radar + M5 audit/findings) with a "
        "4-key patch at 46+/28- diff, state encoding preserved (BOM + indent 1). Line taken: the banked "
        "kfpb-bex2-reroll-c2140 job - B-EX2 was the only MINOR frame from this morning's KF-PACK-B probe. "
        "Authored the missing single-frame variant runner (idle-guard-kit/kfpb_bex2_reroll_c2140.py: one "
        "anchor, deterministic seeds, explicit hand-geometry + eyeline repair clause, env overrides for "
        "tag/res/seed list). Probe-res sweep 3/3 burned at 672x384 in 98s (PNG 297-315KB, board 73626B, "
        "receipt xq-KFPB-BEX2-RECEIPT-c2140.json). The JPEG board read picked r2, but the NATIVE PNG read "
        "overturned it: r1/r2/r3 all render 3-4 fused finger shapes with no readable thumb = hand clause "
        "0/3. Because that looked like a pixel-budget limit rather than a seed problem, the same prompt was "
        "fired at the real main-pass size (1344x768, seeds 206038+207158, tag xq-kfpb-bex2-hd-c2142): 2/2 "
        "burned, 1.13MB each, and both FAIL the same way at native size (fused mitten hand, no plausible "
        "thumb; eyeline heights also do not match; skin glossy with no pores). Verdict recorded rather than "
        "papering over it: the ANCHOR is unrenderable, not the seeds - a hand close-up hooking a jacket hem "
        "puts the hand in a few dozen pixels. Ruling written into xq-CASTING-VERDICT-c2136-full.md sec-5 as "
        "a mechanical birth gate (hand close-ups occupying >8% of frame are rejected at birth; B-EX2 becomes "
        "an occluded-hand composition shot from behind her shoulder) with both receipts as evidence. Bank: "
        "job closed done + successor kfpb-bex2-hd-verdict-c2142 pre-stowed (bank never empty)."
    ),
    "build_ok": True,
    "changes_count": 0,
}
st["next_round_at"] = "2026-10-20 12:50"
io.open(STATE, "w", encoding="utf-8-sig" if bom else "utf-8", newline="").write(
    json.dumps(st, ensure_ascii=False, indent=1) + "\n")
chk = json.loads(io.open(STATE, encoding="utf-8-sig").read())
assert chk["last_round"]["ts"] == now
print("STATE_OK", now)

# ---- bank successor verdict ----
braw = io.open(BANK, "rb").read()
bbom = braw.startswith(b"\xef\xbb\xbf")
bd = json.loads(braw.decode("utf-8-sig"))
jobs = bd["jobs"] if isinstance(bd, dict) else bd
for j in jobs:
    if j.get("id") == "kfpb-bex2-hd-verdict-c2142":
        j["status"] = "done"
        j["done_ts"] = now.replace(" ", "T")
        j["done_note"] = (
            "VERDICT: B-EX2 anchor is unrenderable, not seed-dependent. 5 frames total - 3 at 672x384 "
            "(204921/206038/207158) and 2 at 1344x768 (206038/207158) - all read at native size show 3-4 "
            "fused finger shapes, no plausible thumb (hand clause 0/5). Eyeline heights also mismatch and "
            "skin is glossy with no pores at both sizes. No B-EX2 seed is locked for the main pass. Ruling "
            "landed in xq-CASTING-VERDICT-c2136-full.md sec-5: hand close-ups occupying >8% of frame are "
            "rejected at birth; B-EX2 is re-anchored as an occluded-hand composition (her hand disappears "
            "behind the jacket hem, camera from behind her shoulder, gesture read from the arm angle). "
            "Next: re-shoot B-EX2 on the new anchor, then the 1344x768 main pass over approved frames."
        )
        break
io.open(BANK, "w", encoding="utf-8-sig" if bbom else "utf-8", newline="").write(
    json.dumps(bd, ensure_ascii=False, indent=1) + "\n")
print("BANK_OK successor closed")