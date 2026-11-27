# Xingqing PACK-B - edit grammar (C2167)

> CHK-E1 program count from the assembly index. No hand counting.

| class | joins | share |
|---|---|---|
| cut | 26 | 66.7% |
| motion | 3 | 7.7% |
| dissolve | 6 | 15.4% |
| blur | 4 | 10.3% |

- classes present: **4** (need >= 4)
- hard cuts: **66.7%** (need <= 70%)
- verdict: **PASS**

## Join table
| n | at (s) | from -> to | class | mechanism |
|---|---|---|---|---|
| 1 | 2.000 | F0-01a -> F0-01b | cut | straight cut |
| 2 | 4.000 | F0-01b -> S0-02 | dissolve | xfade fade 6 frames (0.250s) |
| 3 | 6.000 | S0-02 -> S0-03 | cut | straight cut |
| 4 | 12.000 | S0-03 -> S0-04 | cut | straight cut |
| 5 | 18.000 | S0-04 -> S0-05 | cut | straight cut |
| 6 | 24.000 | S0-05 -> S0-06 | cut | straight cut |
| 7 | 30.000 | S0-06 -> S1-07 | cut | straight cut |
| 8 | 38.125 | S1-07 -> S1-08 | motion | hard cut on matched movement direction |
| 9 | 44.000 | S1-08 -> S1-09 | blur | defocus out/in over 8 frames (0.333s) then cut |
| 10 | 53.417 | S1-09 -> S2-10 | cut | straight cut |
| 11 | 62.000 | S2-10 -> S2-11 | motion | hard cut on matched movement direction |
| 12 | 63.667 | S2-11 -> S2-12 | cut | straight cut |
| 13 | 65.333 | S2-12 -> S2-13 | cut | straight cut |
| 14 | 67.000 | S2-13 -> S2-14 | cut | straight cut |
| 15 | 76.000 | S2-14 -> S2-15 | cut | straight cut |
| 16 | 84.000 | S2-15 -> S2-16 | cut | straight cut |
| 17 | 96.000 | S2-16 -> S3-18 | dissolve | xfade fade 8 frames (0.333s) |
| 18 | 105.000 | S3-18 -> S3-18cont | cut | straight cut |
| 19 | 110.000 | S3-18cont -> S3-19 | cut | straight cut |
| 20 | 120.000 | S3-19 -> S3-20 | blur | defocus out/in over 8 frames (0.333s) then cut |
| 21 | 132.000 | S3-20 -> S3-21 | blur | defocus out/in over 8 frames (0.333s) then cut |
| 22 | 140.750 | S3-21 -> S4-22 | dissolve | xfade fade 8 frames (0.333s) |
| 23 | 146.000 | S4-22 -> S4-23 | cut | straight cut |
| 24 | 158.000 | S4-23 -> S4-24 | cut | straight cut |
| 25 | 162.833 | S4-24 -> S5-25 | dissolve | xfade fade 8 frames (0.333s) |
| 26 | 172.000 | S5-25 -> S5-26 | dissolve | xfade fade 10 frames (0.417s) |
| 27 | 174.333 | S5-26 -> S5-27 | cut | straight cut |
| 28 | 176.667 | S5-27 -> S5-28 | cut | straight cut |
| 29 | 179.000 | S5-28 -> S5-26 | cut | straight cut |
| 30 | 181.333 | S5-26 -> S5-27 | cut | straight cut |
| 31 | 183.667 | S5-27 -> S5-28 | cut | straight cut |
| 32 | 186.000 | S5-28 -> S5-29 | cut | straight cut |
| 33 | 196.000 | S5-29 -> S5-30 | motion | hard cut on matched movement direction |
| 34 | 202.000 | S5-30 -> S5-31 | blur | defocus out/in over 8 frames (0.333s) then cut |
| 35 | 212.000 | S5-31 -> S5-32 | cut | straight cut |
| 36 | 218.000 | S5-32 -> F5-33a | cut | straight cut |
| 37 | 222.000 | F5-33a -> F5-33b | cut | straight cut |
| 38 | 226.000 | F5-33b -> F5-33c | cut | straight cut |
| 39 | 232.000 | F5-33c -> F5-34 | dissolve | xfade fade 10 frames (0.417s) |
