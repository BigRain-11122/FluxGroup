"""C2179: re-burn manifest for KN units whose camera move was never rendered.

Why this file exists
--------------------
The framing gate now reports three units as FLAT: KN03, KN11 and KN21 all
declared a push and measured exactly 1.00x on 100% of samples.  They share one
authored clause, "eases in from almost still on a slow floor dolly" - the same
"dolly" noun the C2178 hygiene gate warns about, which the model reads as a rig
standing in the scene rather than as camera travel.  KN17 with the identical
clause did move (1.16x), so this is a 3-in-5 clause weakness, not a certainty.

C2178 already rewrote that macro to "eases in from almost still on a slow level
move" (motion only, no equipment noun), but the in-flight wave had already read
its manifest into memory, so every flat unit on disk was burned from the old
sentence.  This builder re-derives the units' prompts from the authored shot
file as it stands now, so the re-burn rides the fixed clause instead of the
legacy copy - and it refuses to emit a manifest whose prompts still carry rig
nouns, by calling the same hygiene classifier that gates the authored layer.

Usage
-----
    python kn_reburn_manifest_c2179.py            # writes the 480P manifest
    python kn_reburn_manifest_c2179.py --check    # classify prompts, write nothing

The 480P slice is verification, not production: lane bmcverify, 672x384 int4,
output to clips-verify-480.  768P is only burned after the verification clip
passes the same framing gate.
"""
import argparse
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "可爱女人-shots-v2.py")
OUT = os.path.join(HERE, "local-i2v", "run-bmc-kn-reburn480-c2179.json")
FRAMES = "media/mv-album-001-jay/frames/%s.png"

# shot -> why it is being re-burned (kept in the manifest so the next session
# does not have to reconstruct the reason from a board image)
REBURN = {
    "KN03": "declared push measured 1.00x on 100% of samples (framing gate C2179 FLAT)",
    "KN11": "declared push measured 1.00x on 100% of samples (framing gate C2179 FLAT)",
    "KN21": "declared push measured 1.00x on 100% of samples (framing gate C2179 FLAT)",
    "KN15": "rendered as a built set (paper plane on a rig behind an airliner window) - C2178 set-dressing drift, re-burn on the rig-free clause",
}


def load_shots():
    spec = importlib.util.spec_from_file_location("kn_shots", SHOTS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def new_rows(mod):
    rows = {}
    for row in mod.NEW:
        rows[row[0]] = row
    return rows


def unit_from_row(row, shot_id):
    sid, t0, t1, speed, note, _kf, i2v_prompt = row[:7]
    win_s = round(t1 - t0, 3)
    src_s = round(win_s / speed, 3) if speed else win_s
    return {
        "id": "KN_R1-" + sid,
        "shot": sid,
        "track": "KN",
        "win_s": win_s,
        "speed": speed,
        "src_s": src_s,
        "policy_band": "8-15s" if win_s >= 8 else "short",
        "move_raw": "reburn",
        "frame": FRAMES % ("KN_" + sid),
        "lyric_anchor": "instrumental intro (0.00-30.14)" if sid < "KN23" else "reburn",
        "note": REBURN[sid],
        "i2v_prompt": i2v_prompt,
        "prompt_words": len(i2v_prompt.split()),
        "guard": ["kf_verified=True"],
        "prompt_rev": "v3.2-C2179-reburn480",
    }


def hygiene():
    """Same term lists as kn_prompt_hygiene_gate: rig nouns FAIL, verbs WARN."""
    spec = importlib.util.spec_from_file_location(
        "kn_hyg", os.path.join(HERE, "kn_prompt_hygiene_gate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.audit_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

    mod = load_shots()
    rows = new_rows(mod)
    missing = [s for s in REBURN if s not in rows]
    if missing:
        print("MISSING shots: %s" % ",".join(missing))
        return 1

    units = [unit_from_row(rows[s], s) for s in sorted(REBURN)]

    # authored-layer contract: no rig/crew noun may reach a manifest
    classify = hygiene()
    bad = []
    for u in units:
        fails, warns = classify(u["i2v_prompt"])
        print("%-14s %-6s %s%s" % (u["id"], "FAIL" if fails else "PASS",
                                   ",".join(fails) or "-",
                                   (" warn=" + ",".join(warns)) if warns else ""))
        if fails:
            bad.append(u["id"])
    if bad:
        print("REFUSE: prompts still carry rig nouns: %s" % ",".join(bad))
        return 1

    doc = {
        "policy": ("C2179 KN re-burn, 480P verification first: KN03/KN11/KN21 rendered their "
                   "declared push at 1.00x (framing gate FLAT, all samples), KN15 rendered as a "
                   "built set. Prompts re-derived from the authored shot file so the re-burn rides "
                   "C2178's rig-free macros. 672x384 int4, clips-verify-480, never production. "
                   "Fire only after the 30-unit 768P wave exits - a second runner mid-wave evicts "
                   "the resident int8 model under the in-flight unit."),
        "gate": ("framing gate C2179 (push FLAT on >=90% of samples) + kn_prompt_hygiene_gate "
                 "FAIL=0 on the re-derived prompts + PROMPT-GATE 可爱女人-i2v-PACK-A-v1 SIGN"),
        "wave": "kn-reburn480-c2179",
        "total": len(units),
        "total_win_s": round(sum(u["win_s"] for u in units), 2),
        "units": units,
    }
    for u in units:
        print("%-14s win=%.2fs src=%.2fs words=%d" % (u["id"], u["win_s"], u["src_s"], u["prompt_words"]))
    if a.check:
        print("CHECK-ONLY, nothing written")
        return 0
    d = os.path.dirname(a.out)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print("WROTE %s units=%d" % (a.out, len(units)))
    return 0


if __name__ == "__main__":
    sys.exit(main())