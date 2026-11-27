# Xingqing PACK-B - assembly index v2 (C2156)

> Built 2026-10-20T19:29:51+08:00. Frame-exact cut of the whole film on EDL v5.

- slots: **33** / units: **40**
- cut: **5712 frames = 238.000s** of 5712 frames (238.000s) / drift: **0 frames**

## What changed from v1
- every slot boundary is snapped with round(t*24); no boundary can drift.
- every segment is rendered with trim=end_frame=N, so its length is N frames, not a rounded second value.
- the 41 segments are joined with the concat filter in one graph, so the outer container no longer lands on 238.083s.

## Cut table (frames are authoritative)
| # | shot | src frames | cut frames | timeline (s) | file |
|---|---|---|---|---|---|
| 1 | F0-01a | 56 | 48 | 0.000-2.000 | clips-packA-768/XQ_F0-01a.mp4 |
| 2 | F0-01b | 56 | 48 | 2.000-4.000 | clips-packA-768/XQ_F0-01b.mp4 |
| 3 | S0-02 | 56 | 48 | 4.000-6.000 | clips-packA-768/XQ_S0-02.mp4 |
| 4 | S0-03 | 175 | 144 | 6.000-12.000 | clips-packA-768/XQ_S0-03.mp4 |
| 5 | S0-04 | 175 | 144 | 12.000-18.000 | clips-packA-768/XQ_S0-04.mp4 |
| 6 | S0-05 | 175 | 144 | 18.000-24.000 | clips-packA-768/XQ_S0-05.mp4 |
| 7 | S0-06 | 175 | 144 | 24.000-30.000 | clips-packA-768/XQ_S0-06.mp4 |
| 8 | S1-07 | 226 | 195 | 30.000-38.125 | clips-packA-768/XQ_S1-07.mp4 |
| 9 | S1-08 | 141 | 141 | 38.125-44.000 | clips-local-768/XQ_B-S1-08.mp4 |
| 10 | S1-09 | 226 | 226 | 44.000-53.417 | clips-packA-768/XQ_S1-09.mp4 |
| 11 | S2-10 | 226 | 206 | 53.417-62.000 | clips-packA-768/XQ_S2-10.mp4 |
| 12 | S2-11 | 56 | 40 | 62.000-63.667 | clips-packA-768/XQ_S2-11.mp4 |
| 13 | S2-12 | 56 | 40 | 63.667-65.333 | clips-packA-768/XQ_S2-12.mp4 |
| 14 | S2-13 | 56 | 40 | 65.333-67.000 | clips-packA-768/XQ_S2-13.mp4 |
| 15 | S2-14 | 243 | 216 | 67.000-76.000 | clips-packA-redo-r1/XQ_S2-14-redo-r1.mp4 |
| 16 | S2-15 | 226 | 192 | 76.000-84.000 | clips-packA-768/XQ_S2-15.mp4 |
| 17 | S2-16 | 328 | 288 | 84.000-96.000 | clips-packA-768/XQ_S2-16.mp4 |
| 18 | S3-18 | 226 | 216 | 96.000-105.000 | clips-packA-768/XQ_S3-18.mp4 |
| 19 | S3-18cont | 124 | 120 | 105.000-110.000 | clips-local-768/XQ_B-S3-18cont.mp4 |
| 20 | S3-19 | 277 | 240 | 110.000-120.000 | clips-packA-redo-r1/XQ_S3-19-redo-r1.mp4 |
| 21 | S3-20 | 328 | 288 | 120.000-132.000 | clips-packA-redo-r1/XQ_S3-20-redo-r1.mp4 |
| 22 | S3-21 | 226 | 210 | 132.000-140.750 | clips-local-768/XQ_B-S3-21.mp4 |
| 23 | S4-22 | 141 | 126 | 140.750-146.000 | clips-packA-redo-r1/XQ_S4-22-redo-r1.mp4 |
| 24 | S4-23 | 328 | 288 | 146.000-158.000 | clips-packA-768/XQ_S4-23.mp4 |
| 25 | S4-24 | 141 | 116 | 158.000-162.833 | clips-packA-redo-r1/XQ_S4-24-redo-r1.mp4 |
| 26 | S5-25 | 260 | 220 | 162.833-172.000 | clips-packA-768/XQ_S5-25.mp4 |
| 27 | S5-26 | 56 | 56 | 172.000-174.333 | clips-packA-768/XQ_S5-26.mp4 |
| 28 | S5-27 | 56 | 56 | 174.333-176.667 | clips-packA-768/XQ_S5-27.mp4 |
| 29 | S5-28 | 56 | 56 | 176.667-179.000 | clips-packA-768/XQ_S5-28.mp4 |
| 30 | S5-26 | 56 | 56 | 179.000-181.333 | clips-packA-768/XQ_S5-26.mp4 |
| 31 | S5-27 | 56 | 56 | 181.333-183.667 | clips-packA-768/XQ_S5-27.mp4 |
| 32 | S5-28 | 56 | 56 | 183.667-186.000 | clips-packA-768/XQ_S5-28.mp4 |
| 33 | S5-29 | 277 | 240 | 186.000-196.000 | clips-packA-768/XQ_S5-29.mp4 |
| 34 | S5-30 | 175 | 144 | 196.000-202.000 | clips-packA-768/XQ_S5-30.mp4 |
| 35 | S5-31 | 277 | 240 | 202.000-212.000 | clips-local-768/XQ_B-S5-31.mp4 |
| 36 | S5-32 | 175 | 144 | 212.000-218.000 | clips-packA-768/XQ_S5-32.mp4 |
| 37 | F5-33a | 107 | 96 | 218.000-222.000 | clips-packA-redo-r1/XQ_F5-33a-redo-r1.mp4 |
| 38 | F5-33b | 107 | 96 | 222.000-226.000 | clips-packA-768/XQ_F5-33b.mp4 |
| 39 | F5-33c | 158 | 144 | 226.000-232.000 | clips-packA-768/XQ_F5-33c.mp4 |
| 40 | F5-34 | 175 | 144 | 232.000-238.000 | clips-packA-768/XQ_F5-34.mp4 |

## Honest notes
- all picture is real takes; each span is cut from its source clip only.
- one scale pass and one encode for the whole cut; straight cuts only.
- the 172-186s window is six whole 56f takes of the sanctioned montage cycle.
