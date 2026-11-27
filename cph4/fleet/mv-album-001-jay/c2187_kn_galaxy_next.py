"""C2187 builder: KN17 768P production burn manifest + KN18 480P probe iteration 3.

Harvest of C2186 (cycle 2026-10-24 ~16:00): KN17 G2 eye pass = PASS on the band
criteria (dim low-contrast dust, unlit cloud rim, discrete round warm points, no
twining rings/branches) -> cleared for 768P production. KN18 G2 eye pass = FAIL:
the band still animates into a bright glowing orange nebula (much brighter than
its own keyframe).

Root cause for KN18 is prompt conditioning, not the keyframe: the KN18 keyframe
is exactly what the director asked for (faint low-contrast dust lane, pinpoint
stars), but the prompt stated the band with negations ("no glowing nebula, no
bright orange clouds"). Naming a defect in the positive prompt conditions the
model toward it. Iteration 3 therefore describes only what must exist, with no
negation and no colour words for the band.

Prompt text stays ASCII by house rule (source strings are English only).
"""

import io
import json
import os

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "local-i2v")
SRC = os.path.join(PKG, "run-bmc-kn-galaxy480-c2186.json")


def load(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump(obj, name):
    path = os.path.join(PKG, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
    return path


def build_prod(src):
    unit = dict(src["units"][0])  # KN17
    unit["id"] = "KN_G3-KN17"
    unit["note"] = ("C2186 eye pass green: band reads dim low-contrast dust, cloud "
                    "rim unlit, points discrete round warm and countable. 768P production burn.")
    unit["prompt_rev"] = "v3.4-C2186-galaxy480 (prompt carried over unchanged)"
    man = {
        "policy": ("C2187 KN17 production burn at 768P. Cleared by the C2186 480P probe eye "
                   "pass (dim low-contrast dust, unlit cloud rim, discrete round warm points). "
                   "Lane bmc int8 1344x768. Writes to clips-local-768 as KN_G3-KN17.mp4."),
        "gate": "C2186 harvest eye pass PASS on KN17 band criteria + kn_framing_drift_gate",
        "wave": "kn-galaxy-prod-c2187",
        "total": 1,
        "total_win_s": unit["win_s"],
        "units": [unit],
    }
    return dump(man, "run-bmc-kn-galaxy-prod-c2187.json")


KN18_PROMPT = (
    "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera slides "
    "laterally with small amplitude in shallow focus, easing in at the start and settling to "
    "a stop at the end. The night sky in close detail: countless round pin-points of pale warm "
    "light, all the same tiny size, spread evenly through deep blue-black, the darkness between "
    "them clean and even. Across the upper frame a wide lane of the same tiny pin-points sits "
    "slightly denser, its brightness almost identical to the sky beside it, its edges soft and "
    "open, each speck resolvable on its own. Warm 2000 Taiwanese telecine grade, milky lifted "
    "blacks. Visible 35mm film grain. Restrained continuous motion, camera and subject motion only."
)


def build_probe(src):
    unit = dict(src["units"][1])  # KN18
    unit["id"] = "KN_G3-KN18"
    unit["note"] = ("C2186 eye pass FAIL: band still animates into a bright glowing orange nebula. "
                    "Iteration 3 drops every negation and colour word from the band description and "
                    "binds the lane to the same pin-point specks at almost the same brightness as the sky.")
    unit["i2v_prompt"] = KN18_PROMPT
    unit["prompt_words"] = len(KN18_PROMPT.split())
    unit["prompt_rev"] = "v3.5-C2187-galaxy480-ng3"
    unit["guard"] = ["kf_verified=True", "word_face=discrete_points", "band=same_specks_barely_brighter"]
    man = dict(src)
    man["policy"] = ("C2187 KN18 probe iteration 3. C2186 residual: the dust band animated into a bright "
                     "glowing orange nebula although the keyframe is correct. The prompt previously named "
                     "the defect in the positive text; iteration 3 uses positive-only wording and binds the "
                     "lane to the same pin-point specks at almost the same brightness as the sky. "
                     "672x384 int4 lane bmcverify - verification only, production is 768P after the eye gate.")
    man["gate"] = "director DIRECTOR-REVIEW-KN-FULL-v1-c2183 item 1 + C2186 eye pass KN18 FAIL"
    man["wave"] = "kn-galaxy480-c2187"
    man["total"] = 1
    man["total_win_s"] = unit["win_s"]
    man["units"] = [unit]
    return dump(man, "run-bmc-kn-galaxy480-c2187.json")


if __name__ == "__main__":
    src = load(SRC)
    print("PROD ", build_prod(src))
    print("PROBE", build_probe(src))
    for name in ("run-bmc-kn-galaxy-prod-c2187.json", "run-bmc-kn-galaxy480-c2187.json"):
        data = load(os.path.join(PKG, name))
        assert len(data["units"]) == 1
        print(name, "words=", data["units"][0].get("prompt_words"), "id=", data["units"][0]["id"])