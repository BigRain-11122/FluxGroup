# KN 768P wave — mid-wave QC (C2172)

Author: bm-c tick round C2172 — 2026-10-24 08:0x — repo FluxGroup
Wave: `local-i2v/run-bmc-kn-i2v.json` (30 units, 可爱女人 PACK-A 768P), in flight since 05:50.
Sample: the 10 units landed when this round started (KN01..KN10), judged while the wave keeps burning.

## 1. What this round adds

The wave's two automated gates (C2170 pseudo-text, C2171 framing drift) answer narrow
questions. They cannot answer "does this look like the shot I wrote". This round adds the
missing read, cheaply enough to run mid-wave instead of after the drain:

| item | path |
|---|---|
| sampled contact boards (native 1344x768, 3 frames per unit) | `cph4/fleet/mv-album-001-jay/KN-768P-BOARD-{1,2}-c2172.jpg` |
| board builder + per-unit facts | `cph4/fleet/mv-album-001-jay/kn_768p_sampled_board_c2172.py` |
| board verdict JSON (duration vs authored window, intent, gate columns) | `media/mv-album-001-jay/evidence-c2172/sampled-board.json` |
| repetition probe (frozen clips + composition overlap) | `cph4/fleet/mv-album-001-jay/kn_wave_repeat_probe_c2172.py` → `evidence-c2172/repeat-probe.json` |

Both scripts are CPU-only and never touch the burn. The board reads its gate columns out of
`evidence-c2170/pseudotext-guard.json`, so a picture and its verdict cannot drift apart.

## 2. Landing facts (10/30)

Decoded duration matches the authored `src_s` window on every unit; the differences below are
the H3 frame-grid quantisation (17k+5), not truncation — the shortest unit, KN09, is 73 frames
for an authored 2.59 s.

| unit | authored src_s | decoded s | authored move | gate | note |
|---|---|---|---|---|---|
| KN01 | 7.22 | 7.29 | mobile | PASS | hands folding the crane, rooftop bokeh; holds |
| KN02 | 6.84 | 7.29 | locked | **SUSPECT + DRIFT** | caption strip burned bottom-centre; pushed to 1.80x by 5.0 s. Re-burn staged (not fired: the wave owns the GPU) |
| KN03 | 9.00 | 9.42 | push | PASS | push lands 1.80x at 8.5 s, as authored |
| KN04 | 6.78 | 7.29 | mobile | PASS | plane leaves frame, hand stays; water tower reads 2000s Taipei |
| KN05 | 6.73 | 7.29 | mobile | PASS | searchlight beams behind the plane — the C1958 night-city idea survived |
| KN06 | 6.42 | 6.58 | mobile | PASS | plane over the twilight alley |
| KN07 | 7.20 | 7.29 | locked | PASS | plane holds over the night city, 1.00x |
| KN08 | 5.76 | 5.88 | push | PASS | girl at the window, plane on the sill, 1.30x |
| KN09 | 2.59 | 3.04 | locked | PASS | rooftop sit, 1.00x |
| KN10 | 3.20 | 3.75 | mobile | PASS | plane over the city, 1.15x |

## 3. The repetition question — measured, cleared

The board put three plane-over-the-city units next to each other (KN06/KN07/KN10), which is
exactly the shape that reads as a replay in a cut. Both faces measured, zero GPU:

- **Frozen clips (framemd5, the method that caught the 3.208 s replay in the XQ pack):** 0
  duplicate frame pairs in all 10 units — 158/175/226/73/90-frame clips, every frame unique.
  Nothing here is a still.
- **Composition overlap (84x48 grey MAD on the mid frame):** the closest pair in the whole
  sample is KN07 vs KN09 at 0.133 (13 %) — the same idea of "wide night city" with a different
  subject and lighting. Same-picture (<0.5 %) pairs: 0. Suspect (<2 %) pairs: 0.

Verdict: the three plane shots are distinct frames, and the wave is not producing stills. No
re-burn on this account. The motif repetition stays an editorial call at assembly (they read
as a progression, dusk → night → high city), not a defect.

## 4. Editorial notes carried to assembly (not repairs)

1. **KN03 ends on a face that fills the frame** (1.80x push over 9.4 s). Cutting straight into
   a wide is a hard jolt; the edit needs either the next unit already moving closer or a beat.
2. **KN08's girl reads 15-17** — the known casting-side read, unchanged by this batch; worth
   one line at the director pass, not a re-burn.
3. **KN02 is the only unit this sample would stop** — both its defects are the same clip, and
   the staged re-burn (prompt v2.0, 165 words, bare concrete band described, shot size held
   end to end) already targets both.

## 5. Halt decision

`landed=10 pseudo=1 framing=1 defects=1` → no halt (the rule fires at 40 % with ≥5 landed).
One unit in ten is defective, and it is the unit already staged for a re-burn. **The wave keeps
burning.** Remaining 20 units get the same two gate faces automatically at birth; the board
and the repetition probe are re-run at the harvest round rather than every tick.

## 6. Next

1. Wave continues to 30/30 (last unit ~2-3 h at the observed 6-16 min per unit).
2. KN02 re-burn fires after the wave releases the GPU — it must not pre-empt a unit, and the
   runner unloads models at start, which would evict the resident int8 model mid-unit.
3. Harvest round: re-run both probes over all 30, then the 480P-free full landing verdict.