# PROXY-PASS — mv0001 V5.11 GAP batch (540P proxy)

- Date: 2026-10-20 02:05 (verdict written R2404)
- File under review: `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v511_proxy.mp4`
- Build log: `v511_gap_proxy_r2403.log` (launch 22:55, `DONE` 23:06:49, `exit rc=0`)
- Spec: `V511-GAP-ADDENDUM-20261019.md`

## Verdict: **PASS** (proxy), with two notes carried to the final QC

## Machine evidence

| item | measured | expected | result |
|---|---|---|---|
| container duration | 234.253 s | 234.25 s (target) | PASS |
| video stream | h264 960x540 24/1 | 540P proxy | PASS |
| frame count | 5622 | ~5622 (234.25 x 24) | PASS |
| frame PTS continuity | 5622 frames, 0 non-uniform steps, first 0.000, last 234.208 | no duplicate / negative / gap | PASS |
| audio stream | aac, present | song track (no AI ambience) | PASS |
| build asserts | `ASSERT-OK V5.11`, `VIDEO-FRAMES 5622 (expect ~5622)`, `FINAL-LEN 234.25 (target 234.25)` | all green | PASS |

Command used: `ffprobe -show_entries frame=pts_time` piped to a sorted-delta check (tolerance 1/24 s +/- 0.008 s).

## Gap-1 (verse splits) review

| sid | t0 | cut | t1 | halves | beat dev | visual continuity |
|---|---|---|---|---|---|---|
| N05_dead_language | 61.980 | 65.4445 | 68.860 | 3.46 / 3.42 | 0.0000 | clean |
| N06_poem_light | 68.860 | 71.4940 | 74.600 | 2.63 / 3.11 | 0.0000 | clean |
| R05_gold_threads | 126.320 | 129.2392 | 131.720 | 2.92 / 2.48 | 0.0000 | clean |
| R06_museum_verse | 131.720 | 135.1400 | 138.560 | 3.42 / 3.42 | 0.1487 | clean |

Continuity was checked on an 8-cell frame board (`_proxycheck/SPLIT-CONTINUITY.jpg`, +/-0.21 s around each cut) with a multimodal read: all four rows are same source / same subject / same lighting / no framing jump / no garbled face / no doubled subject / no compression block; the "doubled" face in R06 is the intended glass reflection of the display case. Verdict: deliberate in-shot cuts, not broken splices.

Note 1 — R05_gold_threads split measures 5.40 s total (above the addendum's stated <=4.4 s band for non-named verse shots). It is a residual catch from the same CEO clause-1 law, kept because both halves land on the beat grid. Director accepts for this cut; if the next pass touches verse banding, R05 is the first candidate for a third split.

## Gap-2 (beat snap) review

5 of 14 XFS cut points snapped to the 109.1 BPM grid within the 0.10 s window (21.900 / 40.220 / 44.000 / 102.880 / 110.520); the other 9 keep their word-window position because the deviation exceeds 0.10 s (dev 0.11-0.27 s), per the addendum's word-window priority rule. Audit table: `V511-GAP-AUDIT-20261019.md`.

## Carried notes (not blockers)

Note 2 — pre-existing verse band above 3.47 s, all still under the 4.47 s verse ceiling: S5_columns 3.60, N02_crowd_her 3.70, N03_goddess_pass 4.22, N04_river_marks 3.54, R01_war_later 4.16, R02_she_turns 3.76, R03_goddess_dim 4.36. Within the addendum tolerance and out of the named split scope; flagged for the final QC board.

## Disposition

Proxy accepted. Final 1344x768 / crf17 / preset fast render launched detached at 02:04 (pid recorded in `v511_final_r2404.pid`, log `v511_gap_final_r2404.log`), stale pre-gap cache backed up to `_cut/v56_v511_final_bak1658` so every shot is rebuilt with the V5.11 split rows. Post-render chain: three-shot dense frame boards + PTS + transition spot-check + grade reference boards -> dual sign-off -> CEO.

Signed: BigStream OS loop R2404 (machine evidence) / director seat (verdict).