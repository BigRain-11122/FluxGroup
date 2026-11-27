# -*- coding: utf-8 -*-
"""Prompt-library test #1 on the LOCAL H3 (480p, free).

Tests performance.micro-expression + camera.slow-push-in + the timecode骨架 against the
same keyframe used for the blocked cloud attempt, so the cloud and local runs stay
comparable. Runs through the existing h3_i2v_client (official I2VA structure, audio chain
already stripped per the CEO audio ban).
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

PROMPT = """integrated_multimodal_description:
4 seconds, 16:9, realistic cinematic image-to-video, I2VA. Use <Picture 1> as the exact first frame and the only reference for the woman.
subject_definitions:
<Subject 1> is the adult woman from <Picture 1>, preserving facial identity, long dark hair, black knit sweater, thin gold necklace, skin texture and the cool blue-grey museum light on her face.
retention_analysis:
<Subject 1>: fully_preserved - retain face, hair, wardrobe, necklace, light direction.
<Picture 1> (museum case behind her): partially_preserved - keep the carved stone band out of focus behind the glass.
detailed_description:
Camera: 50mm equivalent, eye level, chest-up close. One continuous slow push-in, simulated handheld breathing motion of very small amplitude, no shake, no zoom, no cuts.
Performance: she keeps still, gaze fixed on the carved band beyond the glass. Longing held in the eyes; then she suppresses it by pressing her lips together; finally one small leak - a single slow blink with the lashes trembling.
Hard negative constraints: no identity drift, no face deformation, no extra people, no extra limbs, no warped mouth, no cartoon expression, no subtitles, no watermark.
overall_soundscape:
Quiet museum room tone, distant ventilation hum, her single soft breath.
non_diegetic_music:
N/A (song laid in post).
"""


def main():
    spec = importlib.util.spec_from_file_location("h3", CLIENT)
    h3 = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    spec.loader.exec_module(h3)
    os.makedirs(OUT, exist_ok=True)
    print("KF exists:", os.path.exists(KF), flush=True)
    h3.run_shot("p1_perf_pushin", KF, PROMPT, 9101, OUT, length=124)
    print("TEST DONE -> ", OUT, flush=True)


if __name__ == "__main__":
    main()