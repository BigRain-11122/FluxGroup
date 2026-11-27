"""Camera-clause hygiene gate for the authored i2v prompts (zero GPU).

Why this file exists
--------------------
KN15 landed at 768P as a built set: the paper plane sits on a rig in front of an
airliner window with drawn curtains, looking out over a cloud deck.  Its keyframe
was correct (a white paper plane above clouds), and every mechanical gate passed
it: framing is locked (1.00x PASS, it is a still frame), the pseudo-text probe is
clean, the coverage gate sees the declared plane.  So the cost of that unit was
already sunk before any gate could say anything.

The authored prompt for that unit was:

    ... the camera holds a locked-off tripod frame, everything still ...
    A paper plane holding its line just above a moving cloud deck, thin mist
    lifting from its wings, the blue opening ahead.

The render kept the paper plane but built the place it was standing in, and the
words that put a rig and a window on set are the camera-hardware nouns: a
"tripod" is a physical object, and "the blue opening ahead" gave it something to
be an opening of.  The identical clause on KN13 rendered cleanly (plane over a
night city), so this is a risk, not a certainty - which is exactly what a lint is
for: it removes the avoidable half of the risk before the burn, instead of asking
the eye board to catch it afterwards.

Rule
----
The camera sentence may describe what the viewpoint does.  It may not name
physical rig or crew: those are objects and people the renderer can fabricate and
place in frame.  Motion verbs that happen to be equipment-derived ("cranes down",
"dollies in") are reported at WARN level, because the verb reads as movement far
more often than the noun reads as a prop.

Two audit targets
-----------------
    --shots      the authored camera macros (the source every future manifest is
                 built from) - must be clean, so new waves are born clean
    --manifest   one built i2v manifest - units already fired keep the words they
                 were built with; the report marks them LEGACY so the gap between
                 authored-now and already-burned-on-disk stays visible

Exit 0 = clean (or only WARN), 1 = any FAIL hit.

Usage
-----
    python kn_prompt_hygiene_gate.py --shots
    python kn_prompt_hygiene_gate.py --manifest \
        cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-kn-i2v.json --out <json>
"""
import argparse
import glob
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Nouns that name a physical rig or a crew member.  A renderer that receives one
# of these can decide it is set dressing.
FAIL_TERMS = (
    "tripod",
    "floor dolly",
    "steadicam",
    "jib arm",
    "gimbal",
    "slider rail",
    "boom pole",
    "operator",
    "camera crew",
    "cameraman",
)

# Equipment-derived verbs: movement when read as a verb, a prop when read as a
# noun.  Keep them visible in the report, do not fail the build on them.
WARN_TERMS = (
    "dollies",
    "cranes",
    "craning",
)

CAM_SENTENCE = re.compile(r"(camera[^.]*\.)", re.I)


def camera_sentence(prompt):
    """The camera clause of an authored prompt, or the prompt head if unlabelled."""
    m = CAM_SENTENCE.search(prompt or "")
    if m:
        return m.group(1)
    head = (prompt or "").split(";")
    return head[0] if len(head) > 1 else (prompt or "")[:200]


def audit_text(text):
    low = (text or "").lower()
    fails = [t for t in FAIL_TERMS if t in low]
    warns = [t for t in WARN_TERMS if t in low]
    return fails, warns


def load_shots():
    f = None
    for p in glob.glob(os.path.join(HERE, "*-shots-v2.py")):
        if os.path.basename(p).startswith("\u53ef\u7231"):
            f = p
    if not f:
        raise SystemExit("FATAL: KN shots file not found")
    spec = importlib.util.spec_from_file_location("kn_shots", f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    macros = dict(mod.CM)
    macros["slide"] = mod.CM_SLIDE_EASED
    return os.path.basename(f), macros


def rows_for_shots():
    name, macros = load_shots()
    rows = []
    for key in sorted(macros):
        clause = macros[key]
        fails, warns = audit_text(clause)
        rows.append({"unit": "CM." + key, "clause": clause,
                     "fail": fails, "warn": warns,
                     "verdict": "FAIL" if fails else ("WARN" if warns else "PASS")})
    return name, rows


def rows_for_manifest(path):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    units = doc["units"] if isinstance(doc, dict) else doc
    rows = []
    for u in units:
        clause = camera_sentence(u.get("i2v_prompt", ""))
        fails, warns = audit_text(clause)
        rows.append({"unit": u.get("id"), "clause": clause,
                     "fail": fails, "warn": warns,
                     "verdict": "FAIL" if fails else ("WARN" if warns else "PASS")})
    return path, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", action="store_true", help="audit the authored macros")
    ap.add_argument("--manifest", help="audit one built i2v manifest")
    ap.add_argument("--out")
    ap.add_argument("--batch", default="C2178")
    a = ap.parse_args()

    if a.shots:
        target, rows = rows_for_shots()
        mode = "shots"
    elif a.manifest:
        target, rows = rows_for_manifest(a.manifest)
        mode = "manifest"
    else:
        ap.error("need --shots or --manifest")

    fails = [r for r in rows if r["verdict"] == "FAIL"]
    warns = [r for r in rows if r["verdict"] == "WARN"]
    for r in rows:
        if r["verdict"] == "PASS":
            continue
        print("%-12s %-5s %s | %s" % (r["unit"], r["verdict"],
                                      ",".join(r["fail"] + r["warn"]),
                                      r["clause"].encode("ascii", "replace").decode()))

    if a.out:
        doc = {
            "batch": a.batch,
            "mode": mode,
            "target": target,
            "rule": ("camera sentence may describe viewpoint motion only; physical rig "
                     "or crew nouns are FAIL (the renderer can fabricate them as set "
                     "dressing, see KN15), equipment-derived verbs are WARN"),
            "fail_terms": list(FAIL_TERMS),
            "warn_terms": list(WARN_TERMS),
            "units": len(rows),
            "fail": len(fails),
            "warn": len(warns),
            "rows": rows,
        }
        d = os.path.dirname(os.path.abspath(a.out))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        print("VERDICT ->", a.out)

    print("HYGIENE-END mode=%s units=%d fail=%d warn=%d"
          % (mode, len(rows), len(fails), len(warns)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())