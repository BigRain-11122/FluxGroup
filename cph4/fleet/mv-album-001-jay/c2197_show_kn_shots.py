"""C2197 probe: print the KN17/KN18 shot tuples so the shot re-spec is grounded in
the storyboard rather than in the render's failure alone.
"""

import importlib.util
import os
import sys

HERE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
SRC = os.path.join(HERE, "\u53ef\u7231\u5973\u4eba-shots-v2.py")

spec = importlib.util.spec_from_file_location("kn_shots", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

for shot in mod.NEW:
    if shot[0] in ("KN16", "KN17", "KN18", "KN19"):
        print("===", shot[0], "start", shot[1], "end", shot[2])
        for i, val in enumerate(shot):
            print("  [%d] %s" % (i, str(val)[:900]))