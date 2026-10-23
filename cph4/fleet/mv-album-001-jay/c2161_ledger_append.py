"""Append C2161 closeout lines to tick-ledger.txt (bytes-safe, idempotent)."""
import os
import time

P = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\tick-ledger.txt"
now = time.strftime("%Y-%m-%d %H:%M")
lines = [
    "[%s] [Step0 done] preflight all PASS; WAVE-PENDING FLAG=C2160 - r4a still running in "
    "the ComfyUI queue (226 frames), harvest flag kept, not deleted" % now,
    "[%s] [Step2 done] stage card: Xingqing PACK-B sits at director REVISE; R4 is the only "
    "hard blocker and it is burning; R6-1/R6-3 are assembly-layer items that need no GPU" % now,
    "[%s] [Step4 done] target: land R6-1 + R6-3 at the assembly layer with machine "
    "acceptance - zero GPU, zero timeline change, no half-built film" % now,
    "[%s] [Step5 done] c2161_r6_patch.py probe mode; three butterfly grades tried - gblur "
    "replaced the unsharp spec (it sharpened) and a warm tint replaced pure grey (palette "
    "coherence); montage lift self-calibrated in whole code steps" % now,
    "[%s] [Step5 done] acceptance: butterfly sat proxy ratio 0.218 (line <=0.22); montage "
    "dup frames 81->0, YAVG 40.14 in 37.5-42.5, min 32.27 >=32, frames 336=336" % now,
    "[%s] [Step6 done] state-c last_round/current_snapshot/next_round rewritten (indent=1, "
    "no BOM, 5/5 line diff); snapshot-c overwritten to vC2161" % now,
    "%s TICK_DONE C2161 | target=land R6-1/R6-3 at the assembly layer without GPU | "
    "landed=window-level graded clips + before/after boards + probe numbers + receipt with "
    "the three v6 wiring points | gate=both acceptance sets pass mechanically, no PASS "
    "self-signed, no v6 film | next=harvest r4a/r4b, pick the take whose cloud separates, "
    "assemble v6, director pass" % now,
]

raw = open(P, "rb").read()
tail = raw[-4096:].decode("utf-8", "replace")
todo = [ln for ln in lines if ln.split("] ")[0] not in tail or ln not in tail]
todo = [ln for ln in lines if ln not in tail]
if not todo:
    print("LEDGER_SKIP already present")
    raise SystemExit(0)
eol = b"\r\n" if raw.endswith(b"\r\n") else b"\n"
if not raw.endswith(b"\n"):
    raw += eol
add = eol.join(ln.encode("utf-8") for ln in todo) + eol
with open(P, "ab") as f:
    f.write(add)
chk = open(P, "rb").read()
assert add in chk, "append not found after write"
print("LEDGER_OK +%d lines, %d bytes" % (len(todo), len(add)))