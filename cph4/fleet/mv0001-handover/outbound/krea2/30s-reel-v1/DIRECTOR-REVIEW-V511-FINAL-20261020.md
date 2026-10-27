# DIRECTOR-REVIEW — mv0001 V5.11 FINAL (1344x768)

- Date: 2026-10-20 03:1x (BigStream OS loop R2405)
- File under review (production master): `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v511.mp4`
- Delivery variant (AIGC-safe audio, video stream copied): `full_mv_v511_n1.mp4`
- Predecessor: `PROXY-PASS-V511.md` (R2404, 2026-10-20 02:05, proxy 960x540)
- Spec: `V511-GAP-ADDENDUM-20261019.md` + `QC-MASTER-CHECKLIST` + `V5-TYPOGRAPHY-SPEC-20261016.md`

## Verdict: **PASS** (final), with one carried director note

Order chain consumed: orders 2026-10-20 00:32 row 636 (@bm-a BigStream-OSLoop,
lane=hq-central-night-gpu). Proxy re-render had died at 23:06 on the first try;
the re-dispatched detached run completed 02:24 (all segments + 12 G-blocks
rebuilt into `_cut/v56_v511_final`) and the 768P master landed 02:27.

## Machine evidence (measured this round)

| item | measured | expected | result |
|---|---|---|---|
| container | 234.253 s | 234.25 s target | PASS |
| video | h264 1344x768 24/1, 5622 frames | 768P production | PASS |
| frame PTS | 5622 frames, **0** non-uniform steps, first 0.0000 last 234.2083 | no dup/gap/reverse | PASS |
| bitrate / size | 45.70 Mbps / 1338 MB | crf18 per spec | PASS (note 3) |
| platform gate | `platform_spec_check --platform B站` -> aspect 16:9 PASS, duration 234.25 s within 180-900 s | B站 16:9 3-15min | PASS |
| audio true peak (master) | **+0.2 dBTP** | <= -1.0 (N1 gate) | **FAIL as-is** |
| audio true peak (delivery `_n1`) | **-1.1 dBTP** | <= -1.0 | PASS |
| loudness | I = -14.1 LUFS, LRA 5.6 LU | -14 LUFS | PASS |
| boards | XFS-CUT-BOARD (14 cuts), SPLIT-DENSE-BOARD (4 gap-1 splits), GRADE-DUAL-BOARD (6 cells), DENSE-3SHOT (3 shots x 12 consecutive frames) | required by dispatch | PASS |

QC pack: `media/BigStream/qa/mv0001-v511/FINAL-QC-PACK.json` (boards same dir).

## Board reads (multimodal review, this round)

1. **DENSE-3SHOT** (C03_dig_reveal / D06_chisel_fingertip / E03_gaze_meet, 12
   consecutive frames each): rows 1-2 progressive motion every frame, no frozen
   pair, no garbled face/hand, single continuous take. Row 3 (E03 @ 196.9 s)
   crosses the 197.0 s cut into `SING3b_v4@197` at frame 2->3 — that is the
   edit point landing on the beat, not a splice defect.
2. **XFS-CUT-BOARD** (14 cut points, +/-0.21 s): all 14 read as coherent cuts or
   intended dissolves; no ghosted subject except row 12 (187.26 s), which is the
   designed `fx_echo` plate (build table: `fx_echo.png @187.24 s, 0.58 s, 0.60`)
   — confirmed intentional, not a ghost-frame artifact.
3. **SPLIT-DENSE-BOARD**: gap-1 splits unchanged from the signed proxy review
   (same source, same subject, same light; R06 "doubled face" = glass reflection).
4. **GRADE-DUAL-BOARD**: all six sampled frames sit in one warm amber/sepia
   envelope; the "cool museum zone" is not executed in the picture at 40.5 /
   106.0 / 205.0 s. Same finding as the proxy pack. Single-language grade is
   coherent and filmic — **carried as director note, no re-render**.

## Carried notes (not blockers)

- **Note 1** R05_gold_threads verse split stays 5.40 s (above the 4.4 s band for
  non-named verse shots; both halves land on the beat grid). First candidate if
  the verse band is touched again.
- **Note 2** Pre-existing verse band 3.5-4.4 s list unchanged from the proxy
  review (S5 3.60 / N02 3.70 / N03 4.22 / N04 3.54 / R01 4.16 / R02 3.76 /
  R03 4.36 / R04 3.50) — inside addendum tolerance.
- **Note 3** Master is 45.70 Mbps (1.34 GB) because the production path encodes
  intermediates and the final at crf18/fast against heavy grain. Spec-compliant,
  but upload-heavy; a delivery-size encode is a separate decision (would be a
  second generation pass, so it is not done silently here).
- **Note 4** AIGC badge overlay + VideoSeal invisible watermark (「大喵没鱼吃」)
  are NOT yet applied to this master. They belong to the publish-prep step and
  must be applied before any public release (AIGC 显著标识 = 硬法).

## Disposition

Final accepted. Delivery variant for CEO viewing = `full_mv_v511_n1.mp4`
(video stream copied byte-for-byte, audio re-encoded to 256k AAC under a -3.3 dB
limiter so the AAC overshoot still lands under the -1.0 dBTP gate).

Signed: BigStream OS loop R2405 (machine evidence) / director seat (verdict)