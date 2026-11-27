# -*- coding: utf-8 -*-
# bmc_c07fix_r955.py -- r955 C07_stele_sink_v3 re-burn (CRITICAL fix).
# Incident: v2 judged 3.0 FAIL CRITICAL by full-res quantitative base-line
# audit -- stele width shrank 0.54x across the take (dolly-out signature),
# zero swallowing-line advance, zero medium displacement: the engine read
# "sink" as camera pull-back. v3 fix: explicit locked-off camera anchor +
# constant-size/constant-place stele anchor + object-down physical
# scheduling (sand level climbs the stone, top edge drops, sand slides off
# shoulders, ripples at contact) + ease-in settle curve. Positive phrasing
# only (negation law). Enters shared 8188 FIFO behind R02_v3 (running) and
# C04_v2 (pending) -- third sequential job, ETA ~06:35.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

JOBS = [
    ("C07_stele_sink", "C07_stele_sink_v3", 9223,
     "Single continuous take at 24fps, 16:9. A wide shot at eye level; the "
     "camera stays locked-off with the framing holding exactly the same from "
     "the first frame to the last, the tall basalt stele keeping its same "
     "width and its same place in the frame through the whole take. The stele "
     "standing in a field of rippled wind-blown sand slowly settles into the "
     "ground, its base going under grain by grain, the sand level climbing "
     "quietly up the stone face as the top edge of the stele sinks a small "
     "even depth lower through the whole take, the sinking starting very slow "
     "and settling deeper toward the end, loose sand sliding off the shoulders "
     "of the stone and spreading soft slow ripples around the base where the "
     "stone meets the ground, a low drift of pale sand dust breathing along "
     "the contact line. The dusk horizon behind holds three small steady "
     "fires, their flames keeping one constant size and one constant place "
     "in the frame. Warm amber monochrome grade with deep crushed shadows, "
     "visible 35mm film grain. Restrained continuous motion: the slow sink "
     "of the stele and the sand response only."),
]

if __name__ == "__main__":
    results = []
    for base, tag, seed, prompt in JOBS:
        frame = os.path.join(F.ARCH_FRAMES, base + ".png")
        out = os.path.join(F.ARCH_OUT, tag + ".mp4")
        if not os.path.isfile(frame):
            F.log("[%s] FRAME MISSING %s" % (tag, frame))
            results.append((tag, "FRAME_MISSING"))
            continue
        ok = F.run_i2v(frame, prompt, seed, out, tag)
        if ok:
            F.cdn_upload(out, tag)
        results.append((tag, "DONE" if ok else "FAILED"))
        F.log("C07FIX-R955 %s %s" % (tag, results[-1][1]))
    F.log("C07FIX-R955 RIDER COMPLETE %s" % results)
    sys.exit(0)
