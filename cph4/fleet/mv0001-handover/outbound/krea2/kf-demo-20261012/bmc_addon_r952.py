# -*- coding: utf-8 -*-
# bmc_addon_r952.py -- r952 add-on rider: 4 face-close-up clips local INT8 re-burn
# Per orders row 10-13 03:4x (@bm-c append): Seedance wave-4 rejected 4 face-detail
# close-ups via content_moderation (D02/E03/B01/D03) -> cloud face shots dead-end,
# local INT8 = only lane (engine-matrix new row). Deadline: landed by 07:45.
# i2v prompt bodies = mv_full_shots.py rows verbatim (three-field canonical);
# composed in single-take format with grade tail + restraint clause (rider format);
# face shots carry minimal life-pulse in positive phrasing (life-pulse law).
# Tags = FULL mv_full_shots.py row names (collection-naming law: find_src resolves
# full names; short names break assembly).
# Reuses bmc_night_factory.run_i2v/cdn_upload verbatim (anti-duplication law).
# Sequential self-interleave behind factory R-series + r951b rider (FIFO co-serve
# law: new items only, he-window queue items untouched).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as F

JOBS = [
    ("D02_she_reads", 9213,
     "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera "
     "pushes in with small amplitude at slow speed. A young woman's face close to "
     "museum glass, reading a low carved register intently, the warm amber case "
     "glow on her profile, her faint reflection resting over the blurred words, "
     "her eyes moving slowly along the carved lines and closing once in a slow "
     "blink, her breathing gentle in the still air. Warm amber monochrome grade "
     "with deep crushed shadows, visible 35mm film grain. Restrained continuous "
     "motion, one slow camera push and her quiet reading only."),
    ("D03_two_worlds", 9214,
     "Single continuous take at 24fps, 16:9. A medium shot at eye level; the "
     "camera pushes in with small amplitude at very slow speed. A museum display "
     "case glass holding two worlds: a young woman's dark reflected profile in "
     "the foreground, and behind the glass the carved slab wrapped in drifting "
     "amber firelight and smoke, the two lights slowly breathing toward each "
     "other, her reflected profile holding still with a slow gentle breath, the "
     "firelight drifting softly behind the glass. Warm amber monochrome grade "
     "with deep crushed shadows, visible 35mm film grain. Restrained continuous "
     "motion, one very slow camera push and the breathing lights only."),
    ("B01_weary", 9215,
     "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera "
     "holds locked-off. A young scribe sunk onto his stool before an unfinished "
     "row of cuneiform wedges, his tools down at his side, his heavy-lidded eyes "
     "low and easing to one slow blink, his shoulders settling lower as the thin "
     "torch flame slowly fails in its bronze bowl, the warm light dimming by a "
     "breath around him. Warm amber monochrome grade with deep crushed shadows, "
     "visible 35mm film grain. Restrained continuous motion, his settling and "
     "the failing flame only."),
    ("E03_gaze_meet", 9216,
     "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera "
     "holds a near-static shot. Dark museum glass carrying a young woman's "
     "warm-lit profile in the foreground, and behind it a faint male silhouette "
     "in rough linen surfacing in the amber firelight, his gaze finding hers "
     "across the glass, both reflections breathing toward each other and "
     "settling together, the firelight drifting softly between them. Warm amber "
     "monochrome grade with deep crushed shadows, visible 35mm film grain. "
     "Restrained continuous motion, the two reflections settling only."),
]

if __name__ == "__main__":
    results = []
    for tag, seed, prompt in JOBS:
        frame = os.path.join(F.ARCH_FRAMES, tag + ".png")
        out = os.path.join(F.ARCH_OUT, tag + ".mp4")
        if not os.path.isfile(frame):
            F.log("[%s] FRAME MISSING %s" % (tag, frame))
            results.append((tag, "FRAME_MISSING"))
            continue
        ok = F.run_i2v(frame, prompt, seed, out, tag)
        if ok:
            F.cdn_upload(out, tag)
        results.append((tag, "DONE" if ok else "FAILED"))
        F.log("ADDON-R952 %s %s" % (tag, results[-1][1]))
    F.log("ADDON-R952 RIDER COMPLETE %s" % results)
    sys.exit(0)
