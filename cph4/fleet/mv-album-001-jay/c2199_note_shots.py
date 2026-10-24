# -*- coding: utf-8 -*-
"""One-shot: add the C2199 recolour note to the KN16 shot entry."""
import io
import os

MV = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
P = os.path.join(MV, "\u53ef\u7231\u5973\u4eba-shots-v2.py")
ANCHOR = '    ("KN16", 99.00, 109.00, 0.84,'
NOTE = (
    "    # v7.1=C2199: the take is recoloured, not regenerated. Both available KN16\n"
    "    # takes render the moon with a full rainbow multi-ring corona (the model prior\n"
    "    # for moon+cloud+contrast night skies); the director review of film v3 blocked\n"
    "    # PASS on exactly that. The ring is chromatic and geometric, so c2199_kn16_halo.py\n"
    "    # recolours the corona annulus to a soft warm-white halo and leaves every other\n"
    "    # pixel alone. Window, speed and grade are unchanged.\n"
)

s = io.open(P, encoding="utf-8").read()
assert s.count(ANCHOR) == 1, "anchor count %d" % s.count(ANCHOR)
if "v7.1=C2199" in s:
    print("note already present")
else:
    io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(ANCHOR, NOTE + ANCHOR))
    print("note inserted")