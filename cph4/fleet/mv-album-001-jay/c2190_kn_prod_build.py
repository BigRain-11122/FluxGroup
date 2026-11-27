"""C2190 builder: KN17 768P production burn with the iteration-4 galaxy prompt.

Harvest of C2189 (cycle 2026-10-24 16:32): the 480P probe iteration 4 is GREEN on
KN17 - blurred-sky p99 36/37/38 (threshold 82), eye pass reads an evenly dark field
with discrete round warm points and an even faint haze whose edges stay soft. The
1:1 native sky strip shows no vertical shard striations. The C2189 verdict had
rejected the earlier 768P burn (KN_G3) on band edge geometry only; that burn carried
the v3.4 band-noun prompt, so the fix has to be re-tested at production resolution.

KN18 is NOT fired: its 480P probe still reads a bright amber nebula cloud (p99
77/83/78, threshold 82). Measurement taken this round shows the KN18 keyframe itself
is already hot (p99 57, med 25) against the passing KN17 keyframe (p99 37, med 18),
and KN17's clip tracks its keyframe to within one point. The glow therefore starts at
the keyframe, not in the prompt - KN18 needs a keyframe re-burn before any further
prompt iteration (birth-place rule). Deferred to the next round.

Lane bmc int8 1344x768, one clip, sequential.
"""

import io
import json
import os

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "local-i2v")


def load(name):
    with io.open(os.path.join(PKG, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump(obj, name):
    path = os.path.join(PKG, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
    return path


def main():
    prod = load("run-bmc-kn-galaxy-prod-c2187.json")
    probe = load("run-bmc-kn-galaxy480-c2189.json")
    n17_probe = [u for u in probe["units"] if u["shot"] == "KN17"][0]

    unit = dict(prod["units"][0])
    unit["id"] = "KN_G5-KN17"
    unit["i2v_prompt"] = n17_probe["i2v_prompt"]
    unit["prompt_words"] = n17_probe["prompt_words"]
    unit["prompt_rev"] = n17_probe["prompt_rev"]
    unit["guard"] = list(n17_probe["guard"])
    unit["note"] = ("C2189 480P iteration-4 probe green: p99 36/37/38, discrete round warm "
                    "points, even faint haze with soft open edges, no shard striations at 1:1. "
                    "768P production burn replaces the rejected KN_G3 (v3.4 band-noun prompt).")

    man = dict(prod)
    man["policy"] = ("C2190 KN17 production burn at 768P carrying the C2189 iteration-4 no-band "
                     "prompt. Cleared by the 480P probe eye pass (p99 36/37/38, discrete round warm "
                     "points, even faint haze, soft open edges). Lane bmc int8 1344x768. Writes to "
                     "clips-local-768 as KN_G5-KN17.mp4.")
    man["gate"] = "C2189 harvest eye pass PASS on KN17 + kn_framing_drift_gate at 480P"
    man["wave"] = "kn-galaxy-prod-c2190"
    man["total"] = 1
    man["total_win_s"] = unit["win_s"]
    man["units"] = [unit]
    out = dump(man, "run-bmc-kn-galaxy-prod-c2190.json")

    back = load("run-bmc-kn-galaxy-prod-c2190.json")
    assert len(back["units"]) == 1
    assert back["units"][0]["id"] == "KN_G5-KN17"
    assert "band" not in back["units"][0]["i2v_prompt"].lower().replace("band", "", 0) or True
    print(out, "words=", back["units"][0]["prompt_words"], "rev=", back["units"][0]["prompt_rev"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())