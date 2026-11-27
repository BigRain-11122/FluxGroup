# KN 768P BIRTH GATE — C2171 (framing-drift face)

Author: bm-c tick round C2171 · 2026-10-24 07:2x · repo FluxGroup
Predecessor: C2170 (pseudo-text face, `KN-PSEUDOTEXT-VERDICT-c2170.md`)

## 1. Why this round exists

C2170 caught KN02 carrying a generated caption strip. Watching the same clip frame by
frame turned up a second, independent defect: KN02 was authored as

> *"the camera holds a locked-off tripod frame, everything still except the living light and air"*

but the render pushes in to a medium close-up. Measured 1.8x by 5.0 s (evidence frame
`KN02-f66.png`), and it starts early: `KN02-f10.png` is still the wide keyframe, the
caption strip is already burned in there, and by 5 s the boy fills the frame.

Consequence: the clip cannot cut with the rooftop block even if the caption strip were
cropped away. The C2170 probe reads text only, so the defect passed it.

## 2. What landed

| item | path |
|---|---|
| probe | `cph4/fleet/mv-album-001-jay/local-i2v/kn_framing_drift_probe.py` |
| wired into the per-cycle gate | `cph4/fleet/idle-guard-kit/kn_pseudo_guard_c2170.py` (now two faces) |
| verdict JSON | `media/mv-album-001-jay/evidence-c2170/pseudotext-guard.json` |
| standalone calibration JSON | `media/mv-album-001-jay/evidence-c2171/framing-drift-kn.json` |
| staged re-burn spec | `cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-kn-reburn-kn02.json` |

## 3. The rule (deterministic, zero GPU, zero model)

If the model pushed in, a later frame is approximately a centre crop of frame 0
magnified. For every sampled frame the probe searches scale `s ∈ {1.0 … 2.3}`, crops
the centre of frame 0 to `1/s`, resamples back to an 84x48 grey grid and keeps the `s`
with the smallest mean absolute difference. Frame 0 is the i2v output's own first
frame, so nothing external is read.

The **declared** move is parsed out of the authored i2v sentence and gates the reading:

| declared | wording | rule |
|---|---|---|
| locked | tripod / locked-off / handheld hold | zoom must stay **≤ 1.15x** else DRIFT |
| push | eases in / dolly | zoom must reach **≥ 1.10x** else FLAT |
| mobile | slides / travels / pans / tilts / cranes / rises | not judged |
| pull | eases back | not judged (centre-crop search cannot see a widening) |

Wave-wide intent coverage of the 30 KN units: **12 locked · 6 push · 11 mobile · 1 pull
· 0 unclassified**. The locked class is the one that matters and it is fully covered.

## 4. Calibration on the 6 units landed so far

| unit | intent | max zoom | verdict | note |
|---|---|---|---|---|
| KN_A-KN01 | mobile | 2.00 | not judged | lateral slide; zoom unreadable |
| KN_A-KN02 | **locked** | **1.80** | **DRIFT** | the confirmed defect; eye-checked at f10/f66 |
| KN_A-KN03 | push | 1.80 | PASS | authored dolly-in, rendered dolly-in |
| KN_A-KN04 | mobile | 2.30 | not judged | rise with the paper plane |
| KN_A-KN05 | mobile | 1.30 | not judged | travels alongside the subject |
| KN_A-KN06 | mobile | 1.00 | not judged | tilt up |

One flag, and it is the one a human eye confirmed. Gate result:
`landed=6 pseudo=1 framing=1 defects=1 halt=no`.

**Rejected first attempt, same round.** The initial version measured skin-tone share
and flagged KN03 + KN05 — both authored pushes/travels — while reading 19-20% "skin"
on the *wide* KN01/KN02 frame 0 because the warm dusk sky matches any RGB skin rule.
That is a self-constructed probe (B1145 family); it was killed before it could be
committed as a gate. Kept in the file header as a warning.

## 5. KN02 fix (staged, not fired)

`run-bmc-kn-reburn-kn02.json` carries the corrected unit. Two changes against the
original prompt:

1. **Shot size held positively**, not by negation (the prompt lint forbids negatives):
   *"the camera holds the same wide framing from the first frame to the last, the whole
   rooftop and the boy small and centred in the frame"*.
2. **The bare bottom band is described** instead of left as an unexplained dark strip —
   a flat dark band at the bottom of frame is exactly the attractor that produced the
   caption strip: *"the bare concrete rooftop floor along the bottom of the frame
   carries only worn grey concrete and its stains"*.

Fire order: the running 768P wave owns the GPU (30 units, ~13 min each). When it ends,
move `KN_A-KN02.mp4` to `clips-local-768/_rejects/` first — the runner skips existing
output — then run the staged manifest. Never start a second runner while the wave is
burning: `h3_i2v_album.py` calls `/free {unload_models:true}` at start, which would
evict the resident int8 model under the in-flight unit.

## 6. Standing rule for the lane

A clip must satisfy both faces of the birth gate before it may enter assembly.
`pseudotext-guard.json` is the single machine-readable verdict; `halting_units` lists
every unit that cannot be signed in. The gate runs between burns as a work-bank job, so
a defect is flagged the moment the unit lands instead of after all 30 have burned.