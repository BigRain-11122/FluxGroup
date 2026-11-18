# -*- coding: utf-8 -*-
"""Test #3 - the director's answer to limited conditions.

Local H3 gives us 480p, ~5s and a 90-word budget. One shot cannot carry a three-beat
performance at that size (tests #1/#2 proved it). So build the performance in the CUT:
three micro-shots, one beat each, each readable at 480p because the frame is a detail
(eyes / fingertip / lips) rather than a full face. The beat is triggered by a physical
event (a tap on the glass) so the model has something to react to instead of "acting".
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CLIENT = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "outbound", "krea2",
                      "30s-reel-v1", "h3_i2v_client.py")
KF = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "assets", "kf-her-6s.png")
OUT = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "out", "p3_three_shot")

SHOTS = [
    ("S1_ecu_eyes",
     "Extreme close-up on her eyes, 85mm, locked camera. A fingertip taps the glass just "
     "off frame; her pupils widen a little, her lower lids tense, and she blinks once, "
     "slowly. Same face, same hair, soft museum tone.",
     9301),
    ("S2_ecu_fingertip",
     "Extreme close-up on her fingertip resting on the cold glass, 85mm, locked camera. "
     "The finger slides down two centimetres and leaves a faint print; her breath fogs a "
     "small patch of glass. One hand, one person, cool museum light.",
     9302),
    ("S3_cu_lips",
     "Close-up on her lips and chin, 85mm, locked camera. She presses her lips together, "
     "swallows once, her chin trembles slightly, then her lips part and she breathes out. "
     "Same face, same hair, cool museum light.",
     9303),
]


def main():
    spec = importlib.util.spec_from_file_location("h3", CLIENT)
    h3 = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    spec.loader.exec_module(h3)
    os.makedirs(OUT, exist_ok=True)
    for tag, prompt, seed in SHOTS:
        print("[%s] words=%d" % (tag, len(prompt.split())), flush=True)
        h3.run_shot(tag, KF, prompt, seed, OUT, length=124)
    print("TEST3 DONE ->", OUT, flush=True)


if __name__ == "__main__":
    main()