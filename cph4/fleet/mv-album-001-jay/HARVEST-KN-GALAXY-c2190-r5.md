# Harvest — KN17 768P production burn (C2190 wave, harvested this round)

- harvested: 2026-10-24 17:02
- wave: `kn-galaxy-prod-c2190` (1 clip, detached lane bmc int8 1344x768, 1587s wall)
- probe rev: `v4.0-C2189-galaxy480-noband` prompt carried into the 768P lane
- screening aid: blurred-sky p99, threshold **47** (768P family; the 480P 82 line does not carry)
- evidence: `media/mv-album-001-jay/qc-frames-c2190/` (3 native frames + 1:1 native sky strip),
  `qc-boards/KN-GALAXY-PROD-c2190.jpg`, `logs/kn-harvest-c2190.json`

## KN17 — GREEN, promoted

- clip `clips-local-768/KN_G5-KN17.mp4` → copied to `clips-local-768/KN_A-KN17.mp4`
  1344x768, 260 frames, 2,531KB (2,591,996B)
- p99 **32 / 31 / 32** at t = 1.5 / 5.0 / 9.0 s — the coolest KN17 reading across all passes
  (768P v3.4 burned 43/44/47 and still failed geometry; 480P r4 was 36/37/38)
- 1:1 native sky strip: evenly seeded fine round points, **no vertical shard striations**,
  **no hard torn edge**. The warm dust plank reads soft and even, i.e. a Milky Way band,
  not a torn sheet — the C2189 geometry reject does not reproduce at 768P with this prompt.
- keyframe fidelity: `frames/KN_KN17.png` measures p99 37 / med 18, so the clip tracks its
  source frame **one point cooler** instead of adding glow. Model is faithful.

## KN18 — root cause converted into a prompt fix (not yet burned)

The r4 harvest traced KN18's amber nebula to its **keyframe**, not to the motion prompt.
Today's read of the shot table confirms the mechanism: KN18 (85mm close-up) was lighting
itself with `galaxy_gold`, an **establishing-shot** description ("a broad band of warm gold
star dust arched across an ink-blue night sky ... the grain of the night air thick and soft").
Broad band + thick dust at close range is exactly an amber cloud, so the glow was inherited
at frame generation time and no amount of i2v wording could remove it.

Fix committed (`2e773bcf`):

- new light block `galaxy_dust_cu` — closest-grain night air, countless fine round warm
  points spread evenly, darkness between points clean and empty, no band, no thick dust;
- KN18 KF text rewritten off the dust-current wording and repointed to that block;
- `kn_prompt_hygiene_gate.py --shots` = fail 0 warn 3 (the 3 warns are pre-existing
  camera-move wording, untouched);
- `kn_reroll_c2166.py --only KN18 --dry-run` resolves seed 40200018, jman False.

Next KN18 move: **keyframe re-burn** (`--only KN18 --seed-offset 1`), then read its p99
against the KN17 anchor (37/18 → target ≤ 40), then a fresh 480P probe before it joins a cut.

## Actions taken this round

1. Adopted the C2190 harvest flag: read the log to `CHAIN DONE`, screened the clip, promoted it.
2. Harvest tooling generalized for the 768P lane: `c2190_kn_harvest.py` (threshold 47,
   3 native frames + 1:1 strip, board + JSON).
3. KN18 prompt-side fix committed (light block + KF text + changelog v3.1).
4. Film v2 re-assembly fired detached (`c2190e_kn_full_assembly_launch.py`, pid 44332) —
   the video had been blocked on KN17, so the whole 239.03s cut can now be built.
   A new wave-harvest flag points the next round at the encode output.