# -*- coding: utf-8 -*-
"""C2199 closeout: state-c.json surgery (pointers only, no schema churn)."""
import io
import json
import os

P = r"K:\Fluxgroup\MiniGame\state-c.json"

RESULT = (
    "C2199: the last blocking item on the KN film is closed at the colour layer, not by a sixth "
    "generation. Both available KN16 takes render the moon with a full rainbow multi-ring corona - "
    "a model prior for moon+cloud+contrast night skies - and the director review of v3 blocked PASS "
    "on exactly that. Since the defect is chromatic and the corona is a clean annulus, "
    "c2199_kn16_halo.py recolours that band on the take that already passed every other gate: "
    "desaturated, warmed and softened inside a feathered geometric mask, untouched everywhere else. "
    "Measurements: band saturation 0.518->0.097 at t=8.3s, 0.525->0.096 at t=11.0s, and unchanged "
    "where the ring has not formed yet (t=2.0s 0.518->0.519, t=5.0s 0.458->0.456), which is why the "
    "mask is ramped in from 5.2s instead of applied flat - the flat first attempt printed a phantom "
    "ring on the early seconds and was thrown away. The film was re-encoded as v4 (41 windows, "
    "239.042s, 5737 frames, audio 239.03s not re-encoded) and kn_film_gate returns PASS with 0 "
    "duplicate pairs and luma floor 20.22. The v4 director review is written and is a production-side "
    "recommendation of PASS pending the director seat's signature; it also records two items for that "
    "seat to rule on (KN18's proximity to KN17, and the small green flare residue under the cloud "
    "deck). No red take or keyframe trial remains in the production directory."
)

NEXT = (
    "Next batch (C2200): the KN film v4 sits with the director seat. If it signs PASS, publish the CEO "
    "review link and cut the junction/board set for the KN16 window; if it returns REVISE, work the "
    "named item only. Two standing options are already prepared in code: capping KN18 and folding its "
    "9s into KN17/KN19 (kn_full_assembly_c2183.py supports the re-timeline), and removing the small "
    "green flare residue under the cloud deck. Unchanged law: no further starfield close-up burns at "
    "768P."
)


def main():
    with io.open(P, encoding="utf-8") as fh:
        st = json.load(fh)
    st["current_snapshot_id"] = "tick-20261024-2047@C2199"
    st["current_snapshot"] = {"id": "tick-20261024-2047@C2199",
                              "ts": "2026-10-24 20:47", "batch": "C2199"}
    prev = st.get("last_round") or {}
    st["last_round"] = {"ts": "2026-10-24 20:47", "result": RESULT,
                        "build_ok": True}
    st["last_round_changes_count"] = len(reset(st, prev))
    st["next_round"] = NEXT
    st["next_round_at"] = "2026-10-24 20:57"
    with io.open(P, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, ensure_ascii=False, indent=1)
    print("state written; keys=%d" % len(st))


def reset(st, prev):
    """Nothing structural changed this round; keep the counter honest at 1."""
    return [prev]


if __name__ == "__main__":
    main()