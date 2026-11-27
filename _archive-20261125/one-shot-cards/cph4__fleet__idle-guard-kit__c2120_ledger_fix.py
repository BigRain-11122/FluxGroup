# -*- coding: utf-8 -*-
"""C2120: re-append the round's ledger rows WITHOUT truncating existing content."""
import os

LEDGER = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\tick-ledger.txt"
now = "2026-10-20 04:42"
rows = [
    "[%s] [Step0 完成] preflight 23 areas PASS zero FLAG; bank 1 pending (grain A/B claimed 04:00:59) -> harvest round; RAM 18.6%% IDLE-CLAIM NOT-GREEN-IDLE" % now,
    "[%s] [Step4 完成] line=GPU DI r1017 sec-5 row-1 grain endpoint + sec-8 items 2-5 (no batchmode, no MCP; GPU free 9.5G)" % now,
    "[%s] [Step5 完成] grain A/B harvested (board 223,408B, 0.10 adopted) -> six grids re-burned clean at 0.10 (6x 3840x2194, wall ~59s, deterministic)" % now,
    "[%s] [Step5 完成] sec-8 probes: 2a kite halo_p50 4.23/4.45 clean; 2b knee max step 2.03/1.93/7.44/3.84 clip 0; 3 handheld bright frac 0.0000; 4 dark-block entropy 4.901/5.17 refuted 93%%; 5 butterfly IoU 0.779 -> director" % now,
    "[%s] [Step6 完成] state three-field surgery kept + snapshot vC2120 prepended + bank p27 done, successor s527-grain-007-vs-010 prestowed" % now,
    "%s TICK_DONE C2120 grain 0.10 endpoint adopted + six 4K re-burn + sec-8 items 2/3/4 closed, 5 to director, 6 deferred; bank 28 done/1 pending" % now,
]

with open(LEDGER, "rb") as f:
    raw = f.read()
before = raw.count(b"\n")
eol = "\r\n" if b"\r\n" in raw[-600:] else "\n"
if not raw.endswith(b"\n"):
    raw += eol.encode()
payload = raw + "".join(r + eol for r in rows).encode("utf-8")
with open(LEDGER, "wb") as f:
    f.write(payload)
with open(LEDGER, "rb") as f:
    after = f.read().count(b"\n")
print("LEDGER-APPEND ok lines_before=%d after=%d added=%d" % (before, after, after - before))