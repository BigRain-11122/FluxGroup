# KN A-pack 768P harvest — station-3 gate, first completed pass

Face: `KN-PA768-HARVEST-c2169.json` | script: `kn_pa768_harvest_c2169.py`
Run: 2026-10-28 15:26 (bm-c) | wave: `kn-i2v-packA-768` | 30 units in `clips-local-768`

**Result: 30/30 PASS, 0 CHECK.** Two prior CHECK rows cleared, and the reason they
appeared at all was a gate defect, not a clip defect.

## What the harvest measures (zero GPU)

Per unit: ffprobe (resolution / fps / frames / bytes), frame-hash duplicate-run scan
(the "tape repeat" class), the C2170 subtitle-band pseudo-text probe, three native
frames and two 15-tile contact boards.

## The two CHECK rows and how they were resolved

The first pass used global floors — `MIN_FRAMES = 80` and `MIN_BYTES = 400000` — and
flagged two clips:

| unit | flag | what it actually is |
|---|---|---|
| KN_A-KN09 | `frames=73` | a **2.2 s window** (`win_s 2.2`, speed 0.85, `src_s 2.59`). 73 frames at 24 fps = 3.04 s of playback, i.e. the clip is *longer* than its window, not short. Read at native size at 1.67 s: clean rooftop-medium, denim, starry sky, city bokeh, no artifact, no pseudo-text. |
| KN_A-KN25 | `bytes=349022` | a **dark locked-off establishing plate** (city bowl, 5.4 s window, 141 frames). The clip passes probe/dup/pseudo-text; 349 KB over 5.9 s is ~0.47 Mbps and is what a night city with crushed blacks costs. Read at native size at 3.23 s: dense low-rise night blocks, street lamp right, lit alley — no artifact, no pseudo-text. Flagged for grade (it is deliberately underexposed), not for re-burn. |

## Fix landed (root cause, not the symptom)

`MIN_FRAMES` is now per unit, derived from the pack manifest (`src_s × fps`, 85% tail
tolerance), and `MIN_BYTES` drops to a 120,000-byte corruption floor. The log line now
prints `frames=<n> need=<m>` so a short clip and a deliberately short window can be told
apart without a re-read. Same defect family as r1292/r1315: a global constant pretending
to be a per-unit judgement.

## Also fixed in the same pass

`board()` raised `KeyError: 'id'` — `tiles.append(frames[1])` passed a frame row
`{t, path, bytes}` into a board that labels tiles by unit. The whole board stage (and
therefore the verdict JSON) died on it, leaving 30 verified clips with no machine-readable
verdict. Tiles now carry `{id, path}` and the labeler falls back to the timestamp.

## Gate state for the next station

`KN-PA768-HARVEST-c2169.json` → `pass == units`, so bank job
`kn-pa-station4-conform-author-c2169` has its prerequisite satisfied. Its `cmd` is still
empty (script not authored) — authoring it is the next station, not this one.
Boards: `media/mv-album-001-jay/evidence-c2169/KN-PA768-BOARD-{1,2}-c2169.jpg` (gitignored media).