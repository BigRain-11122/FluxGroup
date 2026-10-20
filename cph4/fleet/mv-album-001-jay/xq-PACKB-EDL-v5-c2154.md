# Xingqing EDL v5 - the last hole closed by one continuation take (C2154)

> Built 2026-10-20T18:17:42+08:00. All 238.0s of the timeline are now backed by picture.

## Edit
- `S3-18cont` inserted at 105.017-110.000s - continuation seeded with the last frame of `S3-18`, 4.983s used of 5.167s, 0.184s trimmed

## Coverage
| metric | C2145 | v3 | v4 | v5 |
|---|---|---|---|---|
| covered | 236.00s | 231.02s | 233.017s | 238.000s |
| uncovered | 2.00s | 6.98s | 4.983s | 0.000s |

## Holes after v5
- none

## Plate lock at the seam
- last frame of S3-18 mean RGB [91.0, 80.2, 63.0] vs continuation first frame [89.1, 77.6, 60.7]
- mean absolute pixel difference 3.57 (per channel [3.57, 3.66, 3.49]), threshold 12.0 -> **PASS**

## Review
- stills: plate matches frame-for-frame; same wardrobe, scale and rim light; no duplicated limbs, no third figure, no grade step
- motion: 15s proof read in real time: no cut, jump, stutter or flash at the 5.0s join; camera locked off; S3-19 head lands as a deliberate hard cut in the same dusk light
- caveat: the painted road line reads on opposite sides of the pair early vs late in the take; subtle at dusk silhouette contrast, watch it at assembly

## Proof clip
- `media/mv-album-001-jay/assembly-packA/XQ-CONT-PROOF-105-c2154.mp4` (15.00s, 1862720 B) - seam at 105.017s over the real song; segments {'s3_18_tail': 5.017, 's3_18cont': 4.983, 's3_19_head': 5.0}
- strip `media/mv-album-001-jay/assembly-packA/XQ-CONT-PROOF-105-c2154-strip.jpg` (S3-18 tail / just after the seam / S3-19 head)

Gate: `EDL-CONT closed=1 covered_delta=+4.983 holes=0 seam_ok=1 proof_ok=1`
