# -*- coding: utf-8 -*-
# C2142 follow-up: packA-conform-v2-reverify-after-push ran green at 12:21:17 under IdleGuard
# but the bank entry stayed "claimed". Flip it done from the log evidence (no re-run needed).
import json, io

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
raw = io.open(BANK, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
d = json.loads(raw.decode("utf-8-sig"))
jobs = d["jobs"] if isinstance(d, dict) else d
for j in jobs:
    if j.get("id") == "packA-conform-v2-reverify-after-push":
        j["status"] = "done"
        j["done_ts"] = "2026-10-20T12:21:17"
        j["claimed_by"] = j.get("claimed_by") or "IdleGuard"
        j["done_note"] = (
            "ORIGIN-VERIFY-V2-END ok=1 mismatches=0 eol_only=5 at 12:21:17 (media/mv-album-001-jay/"
            "log-packa-originverify-v2.out.txt): 4710 frames as expected, I=-14.2 LUFS / TP=-2.3 dBTP, run "
            "after the C2140 push landed. The IdleGuard fire never flipped the bank entry, so C2142 closed it "
            "from the log face instead of re-burning it."
        )
        break
io.open(BANK, "w", encoding="utf-8-sig" if bom else "utf-8", newline="").write(
    json.dumps(d, ensure_ascii=False, indent=1) + "\n")
chk = json.loads(io.open(BANK, encoding="utf-8-sig").read())
print("BANK_OK", [x["status"] for x in (chk["jobs"] if isinstance(chk, dict) else chk)][-3:])