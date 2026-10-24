# -*- coding: utf-8 -*-
"""mv_emit_prompts.py - dump a shot script's KF prompts plus the structured tokens the
preflight gate needs (shot / angle / grade / texture / scene / light).

The shot scripts call kf(...) and embed the tokens as prose, so we reverse-map the lexicon
instead of guessing: scene comes from the light keyword the shot used (each LIGHT block in the
script is written for one place), and shot/angle/grade/texture are matched against the lexicon.

Usage:
  py mv_emit_prompts.py --script "C:\\...\\星晴-shots-v2.py" --out prompts.json --scene-map roof_dusk=rooftop
"""
import argparse
import json
import os
import runpy
import sys

LEXICON_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..",
    "cph4", "fleet", "mv0001-handover", "outbound", "krea2",
    "prompt-writing-spec-v1", "patched-scripts")
sys.path.insert(0, os.path.normpath(LEXICON_DIR))
import prompt_lexicon as LX  # noqa: E402


def reverse(mapdict, phrase):
    for k, v in mapdict.items():
        if v.lower() and v.lower() in phrase.lower():
            return k
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scene-map", default="",
                    help="light_key=scene pairs, comma separated")
    a = ap.parse_args()

    scene_map = {}
    for pair in [p for p in a.scene_map.split(",") if "=" in p]:
        k, v = pair.split("=", 1)
        scene_map[k.strip()] = v.strip()

    m = runpy.run_path(a.script)
    NEW = m["NEW"]
    lx = m.get("LX", LX)

    rows = []
    for row in NEW:
        sid, t0, t1, speed, note, kf_prompt = row[0], row[1], row[2], row[3], row[4], row[5]
        shot = reverse(lx.SHOT_SIZE, kf_prompt.split(",")[0])
        angle = reverse(lx.CAM_ANGLE, kf_prompt)
        grade = reverse({k: v for k, v in lx.GRADE.items() if k in ("tw2001", "mono")}, kf_prompt)
        texture = reverse({k: v for k, v in lx.TEXTURE.items()
                           if k in ("film_night", "film_day", "mist", "soft")}, kf_prompt)
        light_key = ""
        for k in lx.LIGHT:
            if lx.LIGHT[k] and lx.LIGHT[k].split(",")[0].lower() in kf_prompt.lower():
                light_key = k
                break
        rows.append({
            "id": sid, "t0": t0, "t1": t1, "note": note,
            "prompt": kf_prompt,
            "shot": shot or "med", "angle": angle or "eye", "move": "static",
            "grade": grade or "tw2001", "texture": texture or "film_night",
            "scene": scene_map.get(light_key, "rooftop"),
            "light": light_key or "roof_dusk",
        })

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("wrote %d prompts -> %s" % (len(rows), a.out))
    for r in rows[:3]:
        print("  %s scene=%s light=%s shot=%s angle=%s" % (r["id"], r["scene"], r["light"], r["shot"], r["angle"]))


if __name__ == "__main__":
    main()