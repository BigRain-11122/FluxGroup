"""C2185: KN17/KN18 galaxy-segment word-face fix + 480P verification manifest.

Why
---
The director's first pass on the full cut (DIRECTOR-REVIEW-KN-FULL-v1-c2183.md)
failed exactly one content item: the galaxy stretch read as golden line/ring
shapes twining like branches, not as star dust filling a night sky.  Both unit
keyframes on disk are clean classic Milky Way stills with discrete points, so the
drift is produced by the motion prompt, not by the first frame: "the whole arc of
a warm gold star band arched across", "the star dust wheeling", "pale currents",
"the dust cloudlike" give the renderer something continuous to animate, and it
animates continuity as filaments and loops.

The fix is in the authored layer so the next manifest cannot ride the old copy.
Nothing here re-bakes a keyframe and nothing here unloads a model.

Usage
-----
    python c2185_kn_galaxy_wordface.py            # patch + build the manifest
    python c2185_kn_galaxy_wordface.py --check    # report only
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "可爱女人-shots-v2.py")
OUT = os.path.join(HERE, "local-i2v", "run-bmc-kn-galaxy480-c2185.json")
FRAMES = "media/mv-album-001-jay/frames/KN_%s.png"

# (old body, new body) - bodies only, the camera clause is untouched
SWAPS = [
    (
        "The whole arc of a warm gold star band arched across an ink-blue night, the star dust "
        "wheeling almost imperceptibly, the cloud deck a dark rim below the frame, soft round "
        "points, the dust cloudlike",
        "The night sky full of countless separate round points of warm gold light, each point "
        "small, round and distinct, spread evenly through an ink-blue sky, the points drifting "
        "apart at the slowest breath, the cloud deck a dark rim below the frame",
    ),
    (
        "The star dust of the galaxy band in close detail, fine warm points and pale currents "
        "drifting through deep blue-black, everything moving at the slowest breath, soft round "
        "points, the dust cloudlike",
        "The night sky in close detail, countless separate round points of warm gold light "
        "scattered evenly through deep blue-black, every point small and round and distinct, "
        "the points drifting apart at the slowest breath, the darkness between them clean",
    ),
]

REBURN = {
    "KN17": "director C2183: galaxy segment read as twining golden lines/rings; motion body "
            "rewritten to discrete round points (keyframe on disk is clean)",
    "KN18": "director C2183: same galaxy drift in close-up; motion body rewritten to discrete "
            "round points (keyframe on disk is clean)",
}


def patch_shots(check=False):
    text = io.open(SHOTS, encoding="utf-8").read()
    hits = []
    for old, new in SWAPS:
        n = text.count(old)
        hits.append(n)
        if n != 1:
            raise SystemExit("REFUSE: expected exactly 1 occurrence, got %d for body: %s" % (n, old[:60]))
        if not check:
            text = text.replace(old, new)
    if not check:
        io.open(SHOTS, "w", encoding="utf-8", newline="").write(text)
    return hits


def load_shots():
    import importlib.util
    spec = importlib.util.spec_from_file_location("kn_shots", SHOTS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(check=False):
    mod = load_shots()
    rows = {r[0]: r for r in mod.NEW}
    units = []
    for sid in sorted(REBURN):
        sid_, t0, t1, speed, _note, _kf, prompt = rows[sid][:7]
        win = round(t1 - t0, 3)
        units.append({
            "id": "KN_G1-" + sid,
            "shot": sid,
            "track": "KN",
            "win_s": win,
            "speed": speed,
            "src_s": round(win / speed, 3) if speed else win,
            "policy_band": "8-15s" if win >= 8 else "short",
            "move_raw": "reburn",
            "frame": FRAMES % sid,
            "lyric_anchor": "galaxy segment 109.00-126.52",
            "note": REBURN[sid],
            "i2v_prompt": prompt,
            "prompt_words": len(prompt.split()),
            "guard": ["kf_verified=True", "word_face=discrete_points"],
            "prompt_rev": "v3.3-C2185-galaxy480",
        })
    doc = {
        "policy": ("C2185 galaxy-segment verification slice: KN17/KN18 motion bodies rewritten from "
                   "continuous shapes (arc/band/wheeling/currents/cloudlike) to discrete round points, "
                   "because the C2183 cut read them as twining golden filaments. 672x384 int4 lane "
                   "bmcverify, clips-verify-480 - verification only, production is 768P after the eye gate."),
        "gate": ("director DIRECTOR-REVIEW-KN-FULL-v1-c2183 item 1 (galaxy segment FAIL) + "
                 "kn_prompt_hygiene_gate FAIL=0 on the rebuilt prompts + framing gate on the probe"),
        "wave": "kn-galaxy480-c2185",
        "total": len(units),
        "total_win_s": round(sum(u["win_s"] for u in units), 2),
        "units": units,
    }
    if not check:
        d = os.path.dirname(OUT)
        if d:
            os.makedirs(d, exist_ok=True)
        with io.open(OUT, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
    return units


def hygiene_check(units):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "kn_hyg", os.path.join(HERE, "kn_prompt_hygiene_gate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    bad = []
    for u in units:
        fails, warns = mod.audit_text(u["i2v_prompt"])
        print("%-12s %-5s %s%s" % (u["id"], "FAIL" if fails else "PASS",
                                   ",".join(fails) or "-",
                                   (" warn=" + ",".join(warns)) if warns else ""))
        if fails:
            bad.append(u["id"])
    if bad:
        raise SystemExit("REFUSE: rig nouns in prompts: %s" % ",".join(bad))


def main():
    check = "--check" in sys.argv
    hits = patch_shots(check)
    print("PATCH occurrences:", hits, "check=%s" % check)
    units = build(check)
    hygiene_check(units)
    for u in units:
        print("%-12s win=%.2fs src=%.2fs words=%d" % (u["id"], u["win_s"], u["src_s"], u["prompt_words"]))
    print("OK" if check else "WROTE " + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())