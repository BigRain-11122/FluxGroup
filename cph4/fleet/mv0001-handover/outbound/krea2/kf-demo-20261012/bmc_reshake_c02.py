# -*- coding: utf-8 -*-
# bmc_reshake_c02.py -- r950 QC patrol re-shake rider
# C02_sand_bury v1 FAILED frame-level QC 5.5/10 (<7.5 threshold, r950 patrol):
#   (a) large pitch-black flat-edged block materialized lower-right 00:03-04 (ghost 3/10),
#   (b) sand cascade rendered as uniform stationary sheet (physics 5/10),
#   (c) top-register carved figures melted/mushy limbs (material 7/10).
# Fix (positive phrasing only, prompt-writing-spec negation-wall law):
#   granular tumbling sand stream + continuous sunlit sand field edge-to-edge with
#   warm light wrapping every corner + crisp chisel-cut relief figures with clean
#   limb boundaries. Reuses bmc_night_factory.run_i2v/cdn_upload verbatim
#   (anti-duplication law); queues into shared 8188 FIFO behind the burning
#   factory shot. Output tag C02_sand_bury_v2 (v1 row kept as ledger).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

PROMPT_V2 = (
    "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera holds "
    "locked-off as fine sand drifts steadily across the stone. A tall black basalt stele "
    "half-buried under drifting wind-blown sand, loose sand grains pouring over the stele "
    "top in a fine tumbling stream, each grain catching the amber light separately, the "
    "upper carved registers with crisp chisel-cut relief figures and clean limb boundaries "
    "drowning grain by grain while the lowest fresh band holds the last amber light. The "
    "sunlit sand field runs continuous from frame edge to edge, warm light wrapping every "
    "corner, shadows soft and full of film grain. Warm amber monochrome grade with deep "
    "crushed shadows, visible 35mm film grain. Restrained continuous motion, camera and "
    "subject motion only."
)

FRAME = os.path.join(F.ARCH_FRAMES, "C02_sand_bury.png")
OUT = os.path.join(F.ARCH_OUT, "C02_sand_bury_v2.mp4")
TAG = "C02_sand_bury_v2"
SEED = 9207

if __name__ == "__main__":
    if not os.path.isfile(FRAME):
        F.log("[%s] FRAME MISSING %s" % (TAG, FRAME))
        sys.exit(2)
    ok = F.run_i2v(FRAME, PROMPT_V2, SEED, OUT, TAG)
    if ok:
        F.cdn_upload(OUT, TAG)
    F.log("RESHAKE C02 v2 RESULT %s" % ("DONE" if ok else "FAILED"))
    sys.exit(0 if ok else 1)
