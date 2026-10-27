"""C2179: append the round's step lines and TICK_DONE to tick-ledger.txt."""
import io
import time

P = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\tick-ledger.txt"
raw = open(P, "rb").read()
try:
    raw.decode("utf-8")
    enc = "utf-8"
except Exception:
    enc = "gbk"
now = time.strftime("%Y-%m-%d %H:%M")
bodies = [
    "[Step0 完成] C2179 preflight all PASS, INFO only (GPU_COMFY_MISSING / not-green-idle / 35 foreign-guid meta); "
    "KN 768P wave owns the card (PID 29056, 22/30 on disk)",
    "[Step1-3 完成] no project scan or compile batch: CPU lane only, zero GPU, zero cloud; competitor/intel cache fresh",
    "[Step4 完成] line = audit the gate that was supposed to catch the flat renders: KN03/KN11/KN21 declared a push and "
    "measured 1.00x on every sample, yet KN03/KN21 were reported UNDECIDED because a stray correlation spike on a still "
    "frame set the unstable flag",
    "[Step5 完成] shipped the still_frac rule (>=90 pct of samples <=1.005x and max <=1.03x = FLAT, spike ignored) and "
    "rescanned all 23 landed units: flat 1->3, undecided 3->1, no regressions; built the 4-unit 480P re-burn manifest by "
    "re-deriving prompts from the authored shots file (hygiene 4/4 PASS) and armed kn_waveend_chain_c2179.py to fire it "
    "25s after the wave exits",
    "[Step6-7 完成] state/snapshot/ledger updated; evidence framing-all-c2179/b.json + pseudotext-kn21 in media",
    "C2179 TICK_DONE product=framing-gate still_frac fix (3 decided flats) + re-burn 480P manifest + armed wave-end chain | "
    "batch C2179 | next = harvest the 4 verify clips, gate KN22b-30 as they land, then 30/30 -> assembly",
]
lines = ["[" + now + "] " + b for b in bodies]
with io.open(P, "a", encoding=enc, newline="") as fh:
    for ln in lines:
        fh.write(ln + "\r\n")
print("LEDGER_OK enc=%s lines=%d" % (enc, len(lines)))
tail = io.open(P, encoding=enc).read().strip().split("\n")[-1]
print("TAIL:", tail[:140])