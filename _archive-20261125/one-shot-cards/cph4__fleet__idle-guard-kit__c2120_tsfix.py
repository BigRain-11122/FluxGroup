# -*- coding: utf-8 -*-
"""C2120: correct timestamps to the measured wall clock (04:42, not the guessed 05:31)."""
import json
import os

ROOT = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(ROOT, "state-c.json")
SNAP = os.path.join(ROOT, "自动化快照-c.md")
LEDGER = os.path.join(ROOT, ".codely-cli", "engine-tick", "tick-ledger.txt")
RATIFY = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\xq-AB-DIRECTOR-RATIFY-r1017.md"

OLD_ID, NEW_ID = "tick-20261020-0531@c2120-grain010-s08", "tick-20261020-0442@c2120-grain010-s08"

d = json.load(open(STATE, encoding="utf-8"))
d["current_snapshot_id"] = NEW_ID
d["current_snapshot"] = NEW_ID
d["next_round_at"] = "2026-10-20 04:57"
with open(STATE, "wb") as f:
    f.write(json.dumps(d, ensure_ascii=False, indent=1).encode("utf-8"))
print("state fixed ->", NEW_ID)

subs = [("2026-10-20 05:31", "2026-10-20 04:42"),
        ("tick = 2026-10-20 05:31", "tick = 2026-10-20 04:42"),
        ("`tick-20261020-0531@c2120-grain010-s08`", "`tick-20261020-0442@c2120-grain010-s08`"),
        ("next_round_at 05:47", "next_round_at 04:57"),
        ("vC2120）2026-10-20 05:31", "vC2120）2026-10-20 04:42")]
for path in (SNAP, RATIFY):
    raw = open(path, "rb").read()
    txt = raw.decode("utf-8")
    n = 0
    for a, b in subs:
        if a in txt:
            n += txt.count(a)
            txt = txt.replace(a, b)
    txt = txt.replace("2026-10-20 05:2x", "2026-10-20 04:4x")
    open(path, "wb").write(txt.encode("utf-8"))
    print(os.path.basename(path), "subs", n)

raw = open(LEDGER, "rb").read().decode("utf-8")
raw = raw.replace("[2026-10-20 04:41]", "[2026-10-20 04:42]").replace("2026-10-20 04:41 TICK_DONE",
                                                                    "2026-10-20 04:42 TICK_DONE")
open(LEDGER, "wb").write(raw.encode("utf-8"))
print("ledger ts aligned")