"""C2191 state surgery: record the harvest round result and move the snapshot pointer.

Touches only last_round (ts/result/build_ok), current_snapshot_id and current_snapshot.
Writes with indent=1 / LF and no BOM to match the existing file lineage (C1864 rule:
probe the original indent before dumping, otherwise the whole file shows as churn).
"""

import io
import json

P = r'K:\Fluxgroup\MiniGame\state-c.json'
SNAP = "tick-20261024-1705@C2191"

result = (
    "C2191 harvest round on the C2190 KN17 768P production burn (wave flag adopted and "
    "rewritten for the new assembly wave). KN17 768P: GREEN - blurred-sky p99 32/31/32 at "
    "t=1.5/5.0/9.0s against a threshold of 47, the coolest KN17 reading across every pass "
    "(the rejected 768P v3.4 burn was 43/44/47), and the 1:1 native sky strip shows no "
    "vertical shard striations and no hard torn edge, so the C2189 geometry reject does not "
    "reproduce. Keyframe check: KN_KN17.png is p99 37 / med 18 and the clip tracks one point "
    "cooler, i.e. the model is faithful and adds no glow of its own. Promoted "
    "clips-local-768/KN_G5-KN17.mp4 to KN_A-KN17.mp4 (2,591,996B). KN18: the amber nebula was "
    "re-traced to its light block rather than its wording - the 85mm close-up was lighting "
    "itself with galaxy_gold, an establishing-shot description (broad band, thick dust), so "
    "the glow was baked in at frame generation. Added a close-up-only block galaxy_dust_cu "
    "(even round points, clean dark between them, no band, no thick dust), repointed the KN18 "
    "keyframe to it and bumped the shot table to v3.1 (commit 2e773bcf, hygiene gate fail 0 / "
    "warn 3 pre-existing). Re-assembly fired detached with KN17 in place and completed: "
    "assembly-packA-KN/KN-FULL-v1-C2183.mp4, 1344x768, 239.0417s, 5737 frames @24fps, 88.7MB, "
    "audio intact - the first watchable whole-film cut with the galaxy band resolved. "
    "Remaining red is KN18's keyframe: re-burn it (kn_reroll_c2166.py --only KN18) against the "
    "KN17 anchor, then a fresh 480P probe, before it may enter a cut."
)

raw = open(P, 'rb').read()
assert b'\r\n' not in raw, 'unexpected CRLF lineage'
d = json.loads(raw.decode('utf-8'))
d['last_round'] = {"ts": "2026-10-24 17:05", "result": result, "build_ok": True}
d['current_snapshot_id'] = SNAP
if isinstance(d.get('current_snapshot'), dict):
    d['current_snapshot'].update({"id": SNAP, "ts": "2026-10-24 17:05", "batch": "C2191"})
else:
    d['current_snapshot'] = {"id": SNAP, "ts": "2026-10-24 17:05", "batch": "C2191"}

with io.open(P, 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(d, fh, indent=1, ensure_ascii=False)
    fh.write('\n')
print('state written:', SNAP)