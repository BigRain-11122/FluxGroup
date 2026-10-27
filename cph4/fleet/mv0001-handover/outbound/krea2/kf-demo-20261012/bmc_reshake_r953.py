# -*- coding: utf-8 -*-
# bmc_reshake_r953.py -- r953 QC patrol re-shake rider (1 clip, sequential self-interleave)
# Verdicts (r953 patrol, threshold 7.5):
#   R02_she_turns 5.5 FAIL -- model drifted full-body wide -> closeup mid-take,
#     composition morph left a translucent second-face residue at t=2.1 (ghost-face law),
#     scale jump reads as a cut inside the shot. Turn direction itself matches canon
#     (head back over shoulder toward the dark display cases -- museum reprise shot,
#     source frame canon-verified clean, modern gallery setting is CORRECT per
#     mv_full_shots.py R02 definition).
#     v2 fix: composition hard-locked (fixed medium framing start-to-end, head-and-
#     shoulders occupy the same region of frame throughout), motion = head turn only,
#     one slow blink life-pulse, camera locked-off.
#   (C04_words_alive_v2 3.5 FAIL CRITICAL -> NOT reshaken here: source frame itself
#     carries the radial hub-wheel disc + sandy-clay material病灶, prompt-level
#     reshake futile -> joins track-2 frame regen batch with C03/C09, disclosed at
#     closeout per deathline discipline.)
# Positive phrasing only (negation-wall law). Frame unchanged (r840 archive).
# Reuses bmc_night_factory.run_i2v/cdn_upload verbatim (anti-duplication law).
# Sequential submission: enters the shared 8188 FIFO behind current burns
# (factory R04 / r951b C06_v2 / addon D02), FIFO co-serve law: new items only.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

JOBS = [
    ("R02_she_turns", "R02_she_turns_v2", 9217,
     "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera "
     "holds locked-off at a fixed distance and the framing stays exactly the same "
     "from the first frame to the last, her head and shoulders filling the same part "
     "of the frame through the whole take. A young woman with long black hair and a "
     "full blunt fringe standing among softly blurred museum visitors in a dim "
     "gallery, her head the only thing moving as it turns slowly back over her "
     "shoulder toward the dark display cases behind her, her eyes finding a far "
     "stone in the dark, one slow blink near the end of the take, the warm gallery "
     "light holding her face steady through the turn, deep shadows around the "
     "cases, soft film grain throughout. Warm amber monochrome grade with deep "
     "crushed shadows, visible 35mm film grain. Restrained continuous motion, her "
     "head turn only."),
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
        F.log("RESHAKE-R953 %s %s" % (tag, results[-1][1]))
    F.log("RESHAKE-R953 RIDER COMPLETE %s" % results)
    sys.exit(0)
