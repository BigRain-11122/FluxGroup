# -*- coding: utf-8 -*-
# bmc_reshake_r951b.py -- r951b QC patrol re-shake rider (4 clips, sequential self-interleave)
# Verdicts (r951b patrol, threshold 7.5):
#   C02_sand_bury_v3 6.4 FAIL -- stream fans to translucent liquid curtain mid-clip
#     v4 fix: single narrow bead-ribbon stream, SAME width top-to-bottom whole take,
#     opaque distinct grains, landing bounce, mound grows ONLY at the foot.
#   C04_words_alive 7.0 FAIL -- motion reads as camera drift/rotate, wedges morph at hub
#     v2 fix: camera locked-off, stone motionless, light sweep ONLY, wedges hold exact shape.
#   C06_forever_cut 6.5 FAIL -- chip at chisel tip stretches like wet putty (3.2s),
#     dark mass intrudes bottom-left (4.4s)
#     v2 fix: one strike early, dust as separate solid specks each on own arc,
#     lower frame edge clean unlit stone.
#   C07_stele_sink 7.1 FAIL -- sink motion undelivered (locked), blown-out white
#     horizon breaks amber/deep-black monochrome
#     v2 fix: camera pull-back+crane-up carries the motion, stele shrinks in frame,
#     horizon dim ember glow deep in shadow, sky near-black.
# Positive phrasing only (negation-wall law). Frames unchanged (r840 archive).
# Reuses bmc_night_factory.run_i2v/cdn_upload verbatim (anti-duplication law).
# Sequential submission: each next reshake enters the shared 8188 FIFO only after
# the previous finishes, self-interleaving behind the factory's R-series progress
# (FIFO co-serve law: new items only, he-window queue items untouched).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

JOBS = [
    ("C02_sand_bury", "C02_sand_bury_v4", 9209,
     "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera "
     "holds locked-off. A tall black basalt stele with crisp chisel-cut relief figures "
     "on the upper registers, its foot set in a low settled bank of soft sand. A "
     "single narrow stream of dense opaque sand pours down one carved edge, thin as a "
     "ribbon of beads from top to bottom and keeping the same narrow width through the "
     "whole take, each grain a distinct dark speck catching the amber light one by "
     "one, the grains landing at the foot with a light scattered bounce and settling "
     "into the bank so the mound grows only there, fine loose grains drifting "
     "sideways on a light wind across a sunlit sand field that runs continuous from "
     "frame edge to edge, warm light wrapping every corner, shadows soft and full of "
     "film grain. Warm amber monochrome grade with deep crushed shadows, visible "
     "35mm film grain. Restrained continuous motion, camera and subject motion only."),
    ("C04_words_alive", "C04_words_alive_v2", 9210,
     "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera "
     "holds locked-off and the stone stays perfectly still. A single band of large "
     "crisp cuneiform wedges cut into black basalt, every wedge holding its exact "
     "shape and position throughout the take, the warm amber glow slowly breathing "
     "and sliding across the carved strokes as a torch passes off-frame, pale cut "
     "edges brightening wedge by wedge then easing back into shadow, fine stone "
     "texture and film grain throughout. Warm amber monochrome grade with deep "
     "crushed shadows, visible 35mm film grain. Restrained continuous motion, light "
     "motion only, the carved surface motionless."),
    ("C06_forever_cut", "C06_forever_cut_v2", 9211,
     "Single continuous take at 24fps, 16:9. An extreme close-up at eye level; the "
     "camera holds locked-off. A bronze chisel seated at the head of the last large "
     "wedge in a fresh row on black basalt, the wooden mallet landing the strike "
     "early in the take, pale stone dust bursting upward in fine separate specks, "
     "each chip a small solid fleck breaking clear of the cut and falling away on "
     "its own arc, the specks drifting and settling one by one in the torchlight, "
     "the chisel then resting still in the finished groove, the lower frame edge "
     "holding clean unlit stone in deep shadow. Warm amber monochrome grade with "
     "deep crushed shadows, visible 35mm film grain. Restrained continuous motion, "
     "one strike and its dust only."),
    ("C07_stele_sink", "C07_stele_sink_v2", 9212,
     "Single continuous take at 24fps, 16:9. A wide shot from a low angle; the camera "
     "pulls back and cranes up with steady amplitude at slow speed. A tall black "
     "basalt stele standing alone on a dark alluvial plain, the stone shrinking "
     "smaller in the frame as the camera retreats and rises, the plain's darkness "
     "rising up the frame, a low dim ember-amber glow resting at the horizon deep "
     "inside the shadow gradation, the sky above near-black, warm light wrapping the "
     "stele's carved edge as it recedes, soft film grain throughout. Warm amber "
     "monochrome grade with deep crushed shadows, visible 35mm film grain. "
     "Restrained continuous motion, one slow camera move only."),
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
        F.log("RESHAKE-R951B %s %s" % (tag, results[-1][1]))
    F.log("RESHAKE-R951B RIDER COMPLETE %s" % results)
    sys.exit(0)
