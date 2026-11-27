# Xingqing EDL v4 - 52.00-54.00s script gap closed (C2151)

> Built 2026-10-20T17:53:32+08:00. Arithmetic only: no new footage is invented here.

## Edits
- `S1-09` 44.000-52.000s -> 44.000-53.417s - clip is 9.417s, the EDL used 8.0s; the +1.417s surplus reaches into the gap
- `S2-10` 54.000-62.000s -> 53.417-62.000s - starts 0.583s before its lyric beat; 8.583s used of 9.417s, 0.834s trimmed

## Coverage
| metric | C2145 | v3 | v4 |
|---|---|---|---|
| covered | 236.00s | 231.02s | 233.017s |
| uncovered | 2.00s | 6.98s | 4.983s |

## Holes after v4
- 105.017-110.000s (4.983s)

## Residual 105.017-110.00s (still open)
- 4.983s, decision: option c) one new burn for the leftover span only: an S3-18 continuation (couple silhouette on the white line, dusk), 5.0s, first_frame from the S3-18 keyframe. Not fired this round.
- why not (a)/(b): (a) pulls the star reveal 5s before its lyric beat and only moves the hole downstream; (b) 0.65x reads as slow motion.

## Proof clip
- `media/mv-album-001-jay/assembly-packA/XQ-GAP-PROOF-52-54-c2151.mp4` (12.00s, 4424498 B) - seam at 53.417s over the real song.
- strip `media/mv-album-001-jay/assembly-packA/XQ-GAP-PROOF-52-54-c2151-strip.jpg`

Gate: `EDL-GAP closed=1 covered_delta=+2.000 holes=1 proof_ok=1`
