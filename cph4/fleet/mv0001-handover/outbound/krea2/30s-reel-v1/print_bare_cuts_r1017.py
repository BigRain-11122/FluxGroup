# -*- coding: utf-8 -*-
"""Print bare-hard cuts with spacing analysis for V5.3 FX placement (E1 fix)."""
import json
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
TL = json.load(open(HERE + r"\timeline_v52.json", encoding="utf-8"))
FX = [38.62, 40.02, 47.30, 77.30, 80.05, 91.02, 93.05, 102.80, 110.42, 110.62,
      131.62, 141.72, 168.30, 187.24, 212.62, 219.80, 231.90]
cuts = TL["cuts"]
bare = [c for c in cuts if c["type"] == "hard" and not any(abs(f - c["win_b"]) <= 0.35 for f in FX)]
print("BARE=%d" % len(bare))
for c in bare:
    dmin = min(abs(f - c["win_b"]) for f in FX)
    print("#%02d %-22s > %-22s @%6.2f  nearestFX=%4.1fs" % (c["k"], c["prev"], c["next"], c["win_b"], dmin))
