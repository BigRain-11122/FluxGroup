# -*- coding: utf-8 -*-
r"""r1552 (bm-c): pin the mv rebuild card to the only box that holds its media.

Evidence, all measured this round:
  * bm-a ran this exact card at 2026-11-09T00:30:45 -> rc=0, 61.3s, frames=5623/5623
    (receipt cph4/fleet/queue-receipts/R-NEXT-BIGSTREAMM-REBUILD-20261109-bm-a.json).
  * bm-c `Tools/mv_rebuild_from_edl.py ... --dry` -> 14 of 73 rows have no source here
    (KF1..KF10 + SING3b + SIL4 + Z02 live in media/MV/mv0001/cloud-v4, which is per-node).
  * Until this round the tool also could not even import off bm-a (paths baked to
    C:\Users\sjs20\Desktop\FluxGroup), which is why every claim died in 0.1s and got
    booked E-INPUT, five generations running.

So: hard-pin to bm-a (hard_nodes never falls back), leave the card OPEN, and say why on
the row itself. Written through fleet_lane.merge_jsonl -- the single queue write path.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
import fleet_lane as fl  # noqa: E402

CARD = "R-NEXT-BIGSTREAMM-REBUILD-20261109"
Q = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")

rows = fl.read_jsonl(Q)
row = None
for r in rows:
    if isinstance(r, dict) and r.get("id") == CARD:
        row = r
        break
if row is None:
    raise SystemExit("card not found: %s" % CARD)

row = dict(row)
row["state"] = "OPEN"
row["nodes"] = ["bm-a"]
row["hard_nodes"] = ["bm-a"]
row["owner"] = None
row["pin_reason"] = (
    "bm-c dry audit 2026-11-11: 14/73 rows have no source on this box "
    "(KF1..KF10/SING3b/SIL4/Z02 live in media/MV/mv0001/cloud-v4, per-node). "
    "bm-a ran this card 2026-11-09 rc=0 in 61.3s (frames 5623/5623). "
    "Tool paths are now repo-relative (fix 2026-11-11) so the dry audit works on any node."
)
row["card_edit_ts"] = "2026-11-11T13:45:00"
row["card_edit_by"] = "bm-c-lane"
row["requeued_by"] = "bm-c-lane"  # explicit re-queue: this is a deliberate routing edit
fl.merge_jsonl(Q, [row])
print("PATCHED %s -> state=%s nodes=%s hard_nodes=%s"
      % (CARD, row["state"], row["nodes"], row["hard_nodes"]))
