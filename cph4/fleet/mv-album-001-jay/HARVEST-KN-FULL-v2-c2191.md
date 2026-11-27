# Harvest — KN PACK-A whole film v2 (C2190 wave) + KN18 keyframe re-burn (C2191)

- harvested: 2026-10-24 17:12–17:24
- flag adopted: `wave-harvest-pending.json` batch C2190 → verdict path
  `assembly-packA-KN/KN-FULL-v1-C2183.mp4`
- upstream: C2190 harvested KN17 768P GREEN (p99 32/31/32) and fired the full-film
  re-assembly detached (`c2190e_kn_full_assembly_launch.py`, pid 44332)

## 1. Film v2 adopted — assembly complete and screened

| check | reading | verdict |
|---|---|---|
| file | `assembly-packA-KN/KN-FULL-v1-C2183.mp4`, 88,671,159 B | present |
| duration / frames | 239.042 s / 5737 frames @ 24 fps | matches song length 239.03 |
| resolution | 1344x768 | 768P production |
| windows | 41 / 41 `present=true`, `film_end` 239.03 | complete cut |
| audio | aac 48 kHz stereo, 239.030 s | full-length song track |
| **duplicate frames** | **0 identical pairs across 5737 frames, longest repeat run 0** | no pixel-level freeze / loop |

Duplicate scan method: `ffmpeg -f framemd5` over the whole cut (no sampling), frame
hashes compared pairwise (`knfull-c2191.md5`).  The 172–186 s repeat class that
needed a punch-in fix in PACK-B does **not** occur in this cut.

Boundary frames pulled natively: 108.9 / 109.1 (KN17 in), 113.2 (KN17 mid),
117.4 (KN17 out), 117.7 (KN18 in), 126.6 (KN18 out), 239.0 (last frame).
Board: `qc-boards/KN-FULL-C2191-BOARD.jpg`; frames in `qc-frames-c2191/`.

- **KN17 in-film**: sky band p99 36, med 0 — fine round points, even seeding, no
  striations, no torn edge.  Consistent with the harvested clip; the C2189 geometry
  reject does not reproduce.
- **KN18 in-film (pre-fix clip)**: amber dust cloud visible at 117.7 — the known RED.
  The cut keeps the old clip until the keyframe fix lands.
- Observation for the director pass: at 108.9/109.1 the cloud deck frame carries a
  pronounced multi-ring rainbow halo around the moon (KN16 tail).  Possible "generated"
  read at the moon; flag for the eye gate, no action taken this round.

## 2. KN18 keyframe re-burn — GREEN on the screening metric

`kn_reroll_c2166.py --only KN18 --seed-offset 1` (previous frame archived to
`frames/_reroll-c2166/KN_KN18_prev.png`, burned 106 s).

The r4 root cause was the **keyframe**: `galaxy_gold` is an establishing-shot block
("broad band ... grain of the night air thick and soft") hanging on an 85 mm close-up,
so an amber cloud was baked at frame generation.  C2191 added `galaxy_dust_cu`
(nearest grain, countless fine round warm points, darkness between them clean and empty,
nothing else in frame) and repointed KN18 to it.

Measurement (sky band = top 35 %, grayscale; blurred r6 for p99 so single star pixels do
not masquerade as glow):

| frame | blur p99 | blur p95 | raw p99 | hot(>60) share |
|---|---|---|---|---|
| KN_KN17.png (anchor) | 38 | 30 | 40 | 0.14 % |
| **KN_KN18.png (new)** | **35** | **26** | 64 | 1.05 % |

- blur p99 **35 ≤ 47 threshold** and **below the KN17 anchor 38** → GREEN.
- raw p99 64 is the discrete bright star points themselves (hot share 1.05 % vs KN17
  0.14 %): visual read confirms evenly spread round points on a clean dark field, no
  band, no thick dust, no nebula — the intended `galaxy_dust_cu` face.
- old KF measured p99 57 / med 25; new KF med 14 matches the KN17 anchor med 14.

## 3. Fired this round (detached, harvest next round)

`c2192_kn18_probe_launch.py` → `local-i2v/run-bmc-kn-galaxy480-c2192.json`,
lane bmcverify 672x384 int4, 1 unit `KN_G6-KN18`, 260 frames.  The motion prompt is
carried **verbatim from C2189 r4** so the keyframe is the only variable under test
(isolation discipline).  Log `logs/kn-galaxy480-c2192.log`, submitted 17:22:57,
submission seed 102675.

Screen when it lands: blurred-sky p99 ≤ 47 at 1.5 / 5.0 / 9.0 s, plus a 1:1 native strip
for striations and torn edges.  Green → 768P production burn for KN18 → replace
`clips-local-768/KN_A-KN18.mp4` → re-assemble film v2 → director pass.
Red → next lever is the haze sentence in the motion prompt (drop the "fine dust haze"
clause so nothing can thicken), not another keyframe pass.

## 4. KN18 480P probe — GREEN, and the 768P burn is away

The probe finished inside the same round (`clips-verify-480/KN_G6-KN18.mp4`, 672x384,
260 frames, 10.833 s, 690,892 B).

| t | blur p99 | blur p95 | raw p99 | med | hot(>60) share |
|---|---|---|---|---|---|
| 1.5 s | 22 | 19 | 100 | 10 | 1.48 % |
| 5.0 s | 25 | 21 | 141 | 10 | 1.94 % |
| 9.0 s | **28** | 23 | 161 | 9 | 2.24 % |

Against the r4 RED (77/83/78) this is a **36-point drop**, and it is cooler than the KN17
480P r4 clip (36/37/38).  Native 1:1 sky strip read: discrete small round points, even
seeding, clean dark ground, **no vertical shard striations, no torn edge, no amber
nebula**.  The raw p99 values are the star points themselves (hot share 1.5-2.2 %), not a
cloud — the keyframe fix propagated through the motion pass exactly as predicted.

Fired on the back of that verdict, lane bmc int8 1344x768, 17:27:43:
`c2192_kn18_prod_launch.py` → `run-bmc-kn-galaxy-prod-c2192.json`, log
`logs/kn-galaxy-prod-c2192.log`.  The wave flag now points the next round at
`clips-local-768/KN_G6-KN18.mp4`: screen it, promote to `KN_A-KN18.mp4`, rebuild the whole
film, then the director pass.

## Actions taken this round

1. Adopted the C2190 wave flag: film v2 read, screened, duplicate-free, adopted.
2. Built the boundary QC board and pulled 7 native frames for the director pass.
3. Re-burned the KN18 keyframe on the fixed `galaxy_dust_cu` prompt; screened GREEN.
4. Fired the KN18 480P probe detached, harvested it GREEN the same round, and fired the
   768P production burn; the flag now points at that burn.