# -*- coding: utf-8 -*-
# bmc_c04fix_r955.py -- r955 C04_words_alive_v2 re-burn from the NEW bm-a frame.
# Incident: track2 rider hit its idempotent "SKIP (exists)" guard on the stale
# C04_words_alive_v2.mp4 (the r953-era FAIL 3.5 burn from the OLD bad frame
# with radial hub-wheel + sandy material), so the new bm-a regen frame
# (bmc/i2v_frames/C04_words_alive_v2.png, MSG-0455 QC 9) was never i2v'd.
# Stale clip quarantined as C04_words_alive_v2_STALE_r953fail.mp4; index row
# marked STALE. This rider burns the new frame with the same canon prompt
# (seed 9219) as the third sequential job behind reshake R05_v2/R02_v3.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

JOBS = [
    ("C04_words_alive_v2", 9219,
     "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera "
     "pushes in dead-straight along its own axis at very slow speed, the frame "
     "center holding on the same wedge band through the whole take. A single "
     "horizontal register of large crisp triangular cuneiform wedges cut into "
     "matte black basalt, every stroke clean and legible in the still warm amber "
     "light, the glow breathing slowly over the pale cuts, deep crushed shadows "
     "in the stone grain, soft film grain throughout. Warm amber monochrome "
     "grade with visible 35mm film grain. Restrained continuous motion: slow "
     "straight push-in, glow breath only."),
]

if __name__ == "__main__":
    results = []
    for tag, seed, prompt in JOBS:
        frame = os.path.join(F.FRAMES, tag + ".png")
        out = os.path.join(F.ARCH_OUT, tag + ".mp4")
        if not os.path.isfile(frame):
            F.log("[%s] FRAME MISSING %s" % (tag, frame))
            results.append((tag, "FRAME_MISSING"))
            continue
        ok = F.run_i2v(frame, prompt, seed, out, tag)
        if ok:
            F.cdn_upload(out, tag)
        results.append((tag, "DONE" if ok else "FAILED"))
        F.log("C04FIX-R955 %s %s" % (tag, results[-1][1]))
    F.log("C04FIX-R955 RIDER COMPLETE %s" % results)
    sys.exit(0)
