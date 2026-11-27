"""C2179 closeout surgery: state-c.json three fields only (indent=1, BOM probed)."""
import json
import os
import time

P = r"K:\Fluxgroup\MiniGame\state-c.json"
raw = open(P, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
enc = "utf-8-sig" if bom else "utf-8"
with open(P, encoding=enc, newline="") as f:
    s = json.load(f)

now = time.strftime("%Y-%m-%d %H:%M")
s["last_round"] = {
    "ts": now,
    "result": "C2179 audited the framing gate itself and found it laundering defects: KN03/KN11/KN21 "
              "declared a push and measured exactly 1.00x at every sampled frame, yet KN03 and KN21 were "
              "reported UNDECIDED ('needs an eye pass') because a stray correlation spike on a still image "
              "raised the unstable flag - the gate handed the clearest static evidence back to a human. "
              "Added a still_frac rule (>=90% of samples at <=1.005x and max <=1.03x = FLAT, spike ignored) "
              "and re-scanned all 23 landed units: flat 1 -> 3, undecided 3 -> 1, no regressions. The shared "
              "cause of the three flats is the authored push macro's 'slow floor dolly' - the same equipment "
              "noun C2178 already rewrote to 'slow level move' (KN17 with the old clause did move, 1.16x, so "
              "this is a 3-in-5 clause weakness rather than a certainty). Because the in-flight wave read its "
              "manifest into memory at start, every landed clip still carries the old sentence, so the fix "
              "reaches the screen only by re-burning. Built the re-burn manifest by re-deriving the four "
              "units' prompts from the authored file (hygiene PASS 4/4), and armed a wave-end chain that "
              "fires the 480P verification slice 25s after the 768P wave exits - a second runner mid-wave "
              "would /free the int8 model out from under the in-flight unit. No 768P burn this round and no "
              "kill of the wave: 21 of 30 units are on disk and the remaining six are still inside it.",
    "build_ok": True,
}
s["current_snapshot_id"] = "tick-20261024-1215@C2179"
s["next_round_at"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 600))

out = json.dumps(s, ensure_ascii=False, indent=1)
data = (b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8")
tmp = P + ".tmp"
with open(tmp, "wb") as f:
    f.write(data)
os.replace(tmp, P)
with open(P, encoding=enc) as f:
    chk = json.load(f)
assert chk["current_snapshot_id"] == s["current_snapshot_id"]
print("STATE_OK snapshot=%s bom=%s bytes=%d" % (chk["current_snapshot_id"], bom, len(data)))