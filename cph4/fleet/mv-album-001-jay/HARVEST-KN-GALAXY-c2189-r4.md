# Harvest — KN galaxy probe iteration 4 (C2189 wave, harvested by C2190)

- harvested: 2026-10-24 16:33
- wave: `kn-galaxy480-c2189` (2 clips, sequential lane bmcverify, 672x384 int4)
- probe rev: `v4.0-C2189-galaxy480-noband` (band noun dropped, one flat even dust haze)
- screening aid: blurred-sky p99, threshold 82. Calibration carried from C2186/C2187:
  KN17 63/66/76 good, KN18 88/95/102 bad.

## KN17 — GREEN

- clip `clips-verify-480/KN_G4-KN17.mp4`, 672x384, 260 frames, 10.5s, 617KB
- p99 **36 / 37 / 38** (t = 1.5 / 5.0 / 9.0) — the coolest KN17 reading so far
  (768P v3.4 burn was 43/44/47)
- eye pass: evenly dark ink-blue field, discrete round warm points, faint even haze,
  edges soft and open. The 1:1 native sky strip shows **no vertical shard striations**
  and no hard torn edge — the C2189 geometry reject does not reproduce with this prompt.
- keyframe check: `frames/KN_KN17.png` p99 37 / med 18; the clip tracks it within one
  point, so the model is faithful rather than adding glow.

## KN18 — RED (still)

- clip `clips-verify-480/KN_G4-KN18.mp4`, 672x384, 260 frames, 10.6s, 908KB
- p99 **77 / 83 / 78** — improved from iteration 3 (89/110/114) but sits on the line,
  and the board still shows an amber nebula cloud where the star field should be.
- **root cause moved to the keyframe**: `frames/KN_KN18.png` measures p99 57 / med 25
  against the passing KN17 keyframe at p99 37 / med 18, and this clip open (t=1.5, p99 77)
  is already hot before the model has had time to drift. The glow is inherited from the
  source frame, so further prompt iteration is wasted work.

## Actions taken this round

1. KN17 cleared for 768P: built `local-i2v/run-bmc-kn-galaxy-prod-c2190.json`
   (id `KN_G5-KN17`, iteration-4 prompt, lane bmc int8 1344x768) and fired it detached
   via `c2190_kn_prod_launch.py` at 16:34:15.
2. KN18 held back from the production burn; the next KN18 move is a **keyframe re-burn**
   (cooler, no warm dust lane; target p99 <= 40 / med ~18 to match KN17), not another
   prompt rewrite. Logged as the next-round head item.
3. Evidence: `media/mv-album-001-jay/qc-frames-c2189-r4/` (3 native frames + 1:1 sky strip
   per clip), `media/mv-album-001-jay/qc-boards/KN-GALAXY-R4-c2189.jpg`,
   `media/mv-album-001-jay/logs/kn-harvest-c2189.json`.

## Next (harvest of C2190)

1. Screen `clips-local-768/KN_G5-KN17.mp4` with the same p99 + 1:1 strip check. Target
   <= 47 (the 480P pass is not automatically a 768P pass — the v3.4 burn passed brightness
   and still failed geometry).
2. Green -> copy to `clips-local-768/KN_A-KN17.mp4`, rerun `kn_full_assembly_c2183.py --encode`
   for film v2.
3. KN18 keyframe re-burn, then a fresh 480P probe before it joins the assembly.
4. Director re-pass on film v2 after both galaxy shots are in place.