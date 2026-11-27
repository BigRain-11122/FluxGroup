# KN 768P birth-gate findings (C2176, 2026-10-24 10:0x)

Scope: the 7 units that landed **after** the C2172 sample — KN11..KN17. Both mechanical
birth gates had last run on KN01-KN10, so these seven were about to reach assembly
ungated. The wave is still burning (KN18 in flight at round time, 17/30 landed).

## Gates read back from disk (not re-judged)

| unit | pseudo-text | framing (intent) | zoom | verdict |
|---|---|---|---|---|
| KN_A-KN11 | PASS (cov 0.74) | push | 1.00x @0.5s | **FLAT** |
| KN_A-KN12 | PASS | mobile | 1.15x @2.5s | not judged |
| KN_A-KN13 | PASS | locked | 1.00x | PASS |
| KN_A-KN14 | PASS | mobile | 1.00x | not judged |
| KN_A-KN15 | PASS (cov 0.46) | locked | 1.00x | PASS |
| KN_A-KN16 | PASS | pull | 1.00x | not judged |
| KN_A-KN17 | PASS | push | 2.30x @10.0s | PASS |

Products: `evidence-c2176/pseudotext-c2176.json`, `evidence-c2176/framing-drift-c2176.json`,
`evidence-c2176/gate-board.json`, `KN-768P-GATE-BOARD-1/-2-c2176.jpg`, frames `evidence-c2176/*.png`.

## Eye pass on the boards (three findings)

1. **KN11 is mechanically FLAT.** Authored as a push, rendered with zero shot-size change
   (1.00x at every sampled frame). It is burned once as an authored unit and replayed in the
   last-chorus reprise, so the dead beat is paid twice. Re-burn candidate, same class as the
   C2171 KN02 DRIFT flag. Not fired this round: GPU is owned by the 30/30 wave.
2. **KN12/KN13/KN14 read as the same photograph.** Same oversized paper plane, same left-of-centre
   placement, same night-city bokeh behind, across four consecutive reprise slots (195.6-218.18s).
   This is what the C2175 worst-40s-window number (100% plane at 189.0s) looks like with eyes: not a
   prop-share statistic but a visible reuse of one composition. The C2175 inserts (KN31/KN32) fix
   37.22-78.50s and do not touch this block, so the C2175 "next coverage target" pointer stays open.
3. **KN17's push lands on an empty sky.** The plane has left frame by ~5.4s and the 2.30x push
   arrives at 10.48s with only stars and warm nebula haze. Advisory, not a gate failure — if the
   beat is "the plane becomes starlight" it is on intent; if the last chorus needs the plane present,
   this take ends without a subject.
4. Advisory on KN16: the concentric rainbow halo around the orb reads as a generator flourish rather
   than an optical event (two perfect rings, lens-like orb). Flagged for the director's eye, not a gate.

## Disposition

- KN11 FLAT -> re-burn candidate, queue behind the running wave; do not burn 768P before the 480P
  pitch check used for every other KN unit.
- KN12/13/14 sameness -> the 189.0s window stays the open coverage target; any fix must be
  span-preserving and must not disturb windows that are already burned and locked.
- No unit is rejected this round. The wave continues; gates run per landing, not per round.