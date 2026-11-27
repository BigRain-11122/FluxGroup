# -*- coding: utf-8 -*-
# bmc_reshake_n02.py -- r949 QC patrol re-shake rider
# N02_crowd_her v1 FAILED frame-level QC 6.5/10 (<7.5 threshold, r949 patrol):
#   dead-fish static subject (zero blink/breathing) + smeared crowd blur + plastic face.
# Fix per STRENGTH-MAP + ghost-audit life-pulse law: one slow blink + quiet breathing +
# hair sway + soft-focus slow crowd + natural skin texture. Positive phrasing only
# (prompt-writing-spec negation-wall law). Reuses bmc_night_factory.run_i2v/cdn_upload
# verbatim (anti-duplication law); queues into shared 8188 FIFO behind the currently
# burning factory shot. Output tag N02_crowd_her_v2 (v1 row kept as ledger).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

PROMPT_V2 = (
    "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera pushes in "
    "with small amplitude at slow speed past the blurred passers-by. A young woman with long "
    "black hair and a full blunt fringe standing still in a dim museum crowd, her calm gaze "
    "resting on the glass display case, she blinks slowly once, her chest rising and falling "
    "with quiet breathing, a few loose strands of her hair swaying gently, blurred visitors "
    "drifting past slowly in soft focus in the foreground. Warm amber monochrome grade with "
    "deep crushed shadows, visible 35mm film grain, natural skin texture with fine pores. "
    "Restrained continuous motion, camera and subject motion only."
)

FRAME = os.path.join(F.ARCH_FRAMES, "N02_crowd_her.png")
OUT = os.path.join(F.ARCH_OUT, "N02_crowd_her_v2.mp4")
TAG = "N02_crowd_her_v2"
SEED = 9202

if __name__ == "__main__":
    if not os.path.isfile(FRAME):
        F.log("[%s] FRAME MISSING %s" % (TAG, FRAME))
        sys.exit(2)
    ok = F.run_i2v(FRAME, PROMPT_V2, SEED, OUT, TAG)
    if ok:
        F.cdn_upload(OUT, TAG)
    F.log("RESHAKE N02 v2 RESULT %s" % ("DONE" if ok else "FAILED"))
    sys.exit(0 if ok else 1)
