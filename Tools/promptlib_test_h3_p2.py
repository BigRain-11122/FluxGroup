# -*- coding: utf-8 -*-
"""Test #2 on the LOCAL H3: same keyframe, same intent, but within the local budget.

Why the rewrite: test #1 was 196 words against a 90-word i2v budget and used 11 `no xxx`
lines the local lint rejects, so the acting instruction was diluted and only the first
sentence (push-in) survived. This version keeps ONE intent sentence plus one acting
sentence, and states constraints positively.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CLIENT = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "outbound", "krea2",
                      "30s-reel-v1", "h3_i2v_client.py")
KF = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "assets", "kf-her-6s.png")
OUT = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "out")

PROMPT = (
    "Slow push-in, 50mm, eye level, chest-up. She holds still, eyes on the carved band "
    "beyond the glass; her gaze fills with longing, then she presses her lips together to "
    "hold it back, and at the end one slow blink lets it show, lashes trembling. "
    "Same face, same hair, same necklace, one person, soft museum room tone."
)


def main():
    print("words:", len(PROMPT.split()), flush=True)
    spec = importlib.util.spec_from_file_location("h3", CLIENT)
    h3 = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    spec.loader.exec_module(h3)
    os.makedirs(OUT, exist_ok=True)
    h3.run_shot("p2_perf_short", KF, PROMPT, 9202, OUT, length=124)
    print("TEST2 DONE ->", OUT, flush=True)


if __name__ == "__main__":
    main()