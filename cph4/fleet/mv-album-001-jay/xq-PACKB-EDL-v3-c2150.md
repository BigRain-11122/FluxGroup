# Xingqing EDL v3 - PACK-B S3-17 retired (C2150)

> Built 2026-10-20T17:10:14+08:00. Arithmetic only: no new footage is invented here.

## Decision
- **retire** `S3-17` (95.6-102.0s, 6.40s): three burns, plate re-rendered at t~3-5s on r2 and r3.
- **advance** `S3-18` to 95.6s and cut it to the full PASS clip (9.417s).

## Coverage
| metric | before | after |
|---|---|---|
| covered | 236.0s | 231.0s |
| uncovered | 2.0s | 7.0s |

## Holes after the retirement
- 52.00-54.00s (2.00s)
- 105.02-110.00s (4.98s)

## Residual (the honest part)
- the retired slot needs 6.40s from the survivor; the survivor clip is 9.417s, short by **0.00s**.
- close options:
  - a) cut S3-19 in early over the residual tail (star shot arrives before its lyric beat)
  - b) slow the survivor below 0.83x to stretch 9.42s over 14.4s (motion reads as slow-motion)
  - c) one new A-pack frame/burn for the leftover span only (not a re-burn of S3-17)
  - d) accept the residual as a deliberate cut-away and let the audio station decide

## Proof clip
- `media/mv-album-001-jay/assembly-packA/XQ-RETIME-PROOF-S3-18-c2150.mp4` (9.42s, 1094477 B) - the PASS take at the new slot over the real song.

Gate: `EDL-END retired=1 advanced=1 holes=2 proof_ok=1`
