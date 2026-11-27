# -*- coding: utf-8 -*-
# bmc_reshake_r955.py -- r955 QC-fail reshakes (2 clips, sequential self-interleave)
# R05_gold_threads_v2: v1 6.0 FAIL (material drift threads->ribbed speckled stone
#   under mechanical exposure ramp). Fix: material pin (gold lines keep thread form,
#   stone stays matte dark, light holds one steady level) + canon slow push-in.
# R02_she_turns_v3: v2 6.5 FAIL (turn front-loaded then frozen tail 1.5s + blink
#   absent). Fix: motion distributed evenly across take, ease-to-stillness only at
#   the end, one slow blink pinned near end. Positive phrasing only (negation law).
# Reuses bmc_night_factory.run_i2v/cdn_upload verbatim (anti-duplication law).
# Enters shared 8188 FIFO behind track-2 C09_v2; sequential submission.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

JOBS = [
    ("R05_gold_threads", "R05_gold_threads_v2", 9221,
     "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera "
     "pushes in with small amplitude at very slow speed. Cuneiform registers sunk "
     "in warm darkness, only the thin edges of the carved wedges catching fine "
     "gold lines of light, the glow breathing slowly along the strokes, the gold "
     "lines keeping their fine thread form through the whole take, the stone "
     "staying matte and dark in its warm black setting, the light holding at one "
     "steady warm level from the first frame to the last. Warm amber monochrome "
     "grade with deep crushed shadows, visible 35mm film grain. Restrained "
     "continuous motion: the slow push-in and the breathing glow only."),
    ("R02_she_turns", "R02_she_turns_v3", 9222,
     "Single continuous take at 24fps, 16:9. A medium shot at eye level; the "
     "camera holds locked-off with the framing staying exactly the same from the "
     "first frame to the last. A young woman with long black hair and a full "
     "blunt fringe standing among softly blurred museum visitors in a dim "
     "gallery, her head continuing its slow turn back over her shoulder toward "
     "the dark display cases through the whole take, the motion spread evenly "
     "across the take and easing to stillness only in the final moment, her eyes "
     "finding a far stone in the dark, one slow blink arriving near the end of "
     "the take, the warm gallery light holding her face steady through the turn, "
     "deep shadows around the cases, soft film grain throughout. Warm amber "
     "monochrome grade with deep crushed shadows, visible 35mm film grain. "
     "Restrained continuous motion: her head turn and the single slow blink only."),
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
        F.log("RESHAKE-R955 %s %s" % (tag, results[-1][1]))
    F.log("RESHAKE-R955 RIDER COMPLETE %s" % results)
    sys.exit(0)
