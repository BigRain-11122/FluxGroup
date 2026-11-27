# -*- coding: utf-8 -*-
# bmc_track2_r955.py -- r955 track-2 i2v rider (3 clips, sequential self-interleave)
# Frames: bm-a Krea2 regen v2 (MSG-20261013-0455-bma receipt, QC 8/9/9) landed in
#   bmc/i2v_frames/<tag>_v2.png via group-tree origin cat-file extraction.
# Motion law: C03/C04 canon i2v from mv_full_shots.py verbatim + composition
#   hard-lock prefix (r953 lesson: composition morph = ghost-face class risk);
#   C09 motion REWRITTEN per MSG-0430 prescription (canon weathered-band object
#   sweep retired with the old frame): two-figure still side-profiles + dust
#   lifting in the wind + brazier flame leaning/swelling (oath->heaven-change
#   slow shot). Positive phrasing only (negation-wall law).
# Reuses bmc_night_factory.run_i2v/cdn_upload verbatim (anti-duplication law).
# Sequential submission: enters the shared 8188 FIFO behind current burns
# (factory R06 / addon E03), FIFO co-serve law: new items only.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

JOBS = [
    ("C03_dig_reveal_v2", 9218,
     "Single continuous take at 24fps, 16:9. A close-up from a high angle; the "
     "camera holds locked-off with the framing staying exactly the same from the "
     "first frame to the last. A soft brush sweeping dusty sand off a buried "
     "cuneiform band stroke by stroke, pale dust lifting through a warm amber "
     "glow, the carved wedges surfacing one by one, the brush head the only thing "
     "crossing the frame, deep crushed shadows around the work-lamp pool, soft "
     "film grain throughout. Warm amber monochrome grade with visible 35mm film "
     "grain. Restrained continuous motion: brush sweep, dust lift only."),
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
    ("C09_oath_weather_v2", 9220,
     "Single continuous take at 24fps, 16:9. A medium shot at eye level; the "
     "camera holds locked-off at a fixed distance with the framing staying "
     "exactly the same from the first frame to the last. Two figures standing in "
     "profile facing each other in a quiet oath moment, a young Babylonian woman "
     "with deep-set eyes and long straight black hair facing a young scribe with "
     "a blunt fringe, both figures holding still as their extended hands rest "
     "over the small brazier flame between them, thin dust lifting and drifting "
     "across the frame as the wind grows, the amber flame leaning and swelling "
     "slowly as if the oath were being heard, the carved meander wall resting "
     "low in the background, deep crushed shadows, soft film grain throughout. "
     "Warm amber monochrome grade with visible 35mm film grain. Restrained "
     "continuous motion: dust drift, flame sway only, figures hold still."),
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
        F.log("TRACK2-R955 %s %s" % (tag, results[-1][1]))
    F.log("TRACK2-R955 RIDER COMPLETE %s" % results)
    sys.exit(0)
