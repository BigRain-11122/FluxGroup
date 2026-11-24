# -*- coding: utf-8 -*-
"""S3 retry: the first attempt ran 23 minutes without finishing (GPU pinned at 100%,
11.7/12.3 GB VRAM). The prompt asked for a chin tremble on top of a swallow and a lip
press - three micro-events in one 5s shot, the same overload that made tests #1/#2 drop
the acting. One event only this time, and the wording matches what already worked in S2
(a concrete physical action, no chain of beats).
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

PROMPT = ("Close-up on her lips and chin, 85mm, locked camera. She presses her lips "
          "together, swallows once, then breathes out slowly. Same face, cool museum light.")


def main():
    print("words:", len(PROMPT.split()), flush=True)
    spec = importlib.util.spec_from_file_location("h3", CLIENT)
    h3 = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    spec.loader.exec_module(h3)
    os.makedirs(OUT, exist_ok=True)
    h3.run_shot("S3_cu_lips", KF, PROMPT, 9403, OUT, length=124)
    print("S3 RETRY DONE", flush=True)


if __name__ == "__main__":
    main()