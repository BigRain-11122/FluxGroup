# -*- coding: utf-8 -*-
# bmc_reshake_c02_v3.py -- r951 QC patrol re-shake rider (3rd attempt)
# C02_sand_bury v2 verdict 5.5/10 FAIL (r951 patrol, threshold 7.5):
#   fix1 black lower-right block HEALED (10/10), fix3 relief crispness HEALED (9/10),
#   fix2 sand physics STILL 3/10 -- the wide drape over the stele top renders as
#   solid sheet/taffy (model capability boundary: narrow falling streams ARE
#   granular per same QC -- STRENGTH-MAP-v1 W-region state-transition boundary).
# v3 fix (positive phrasing only, negation-wall law): redesign the motion to the
# model's proven granular zone -- narrow ribbon of sand pouring down ONE carved
# edge in a falling stream breaking into individual grains + settled sand bank
# (end-state pre-set in frame) + light wind drift across a continuous sunlit
# field. Zero wide-surface drowning language. Frame unchanged (r840 frame passed
# script/cuneiform QC; base ~10% buried = early-stage composition on-model).
# Reuses bmc_night_factory.run_i2v/cdn_upload verbatim (anti-duplication law).
# Output tag C02_sand_bury_v3 (v1/v2 rows kept as ledger).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

PROMPT_V3 = (
    "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera "
    "holds locked-off. A tall black basalt stele with crisp chisel-cut relief figures "
    "on the upper registers, its base resting in a settled bank of soft sand, and a "
    "thin ribbon of loose sand pouring down one carved edge in a narrow falling "
    "stream, the stream breaking into individual tumbling grains that catch the "
    "amber light one by one, fine grains drifting sideways on a light wind across a "
    "sunlit sand field that runs continuous from frame edge to edge, warm light "
    "wrapping every corner, shadows soft and full of film grain. Warm amber "
    "monochrome grade with deep crushed shadows, visible 35mm film grain. "
    "Restrained continuous motion, camera and subject motion only."
)

FRAME = os.path.join(F.ARCH_FRAMES, "C02_sand_bury.png")
OUT = os.path.join(F.ARCH_OUT, "C02_sand_bury_v3.mp4")
TAG = "C02_sand_bury_v3"
SEED = 9208

if __name__ == "__main__":
    if not os.path.isfile(FRAME):
        F.log("[%s] FRAME MISSING %s" % (TAG, FRAME))
        sys.exit(2)
    ok = F.run_i2v(FRAME, PROMPT_V3, SEED, OUT, TAG)
    if ok:
        F.cdn_upload(OUT, TAG)
    F.log("RESHAKE C02 v3 RESULT %s" % ("DONE" if ok else "FAILED"))
    sys.exit(0 if ok else 1)
