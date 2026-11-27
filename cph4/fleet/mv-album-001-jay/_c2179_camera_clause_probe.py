"""C2179: which camera macro each landed KN unit used, next to its measured motion.

Why this file exists
--------------------
The framing gate flagged KN11 (1.00x) and KN21 (1.00x) as declared push that
rendered static, and KN08 as 1.09x.  Three of five push units are flat or nearly
flat while KN17's push rendered 1.16x.  The question is whether the flat ones
share a macro: if they do, the defect is in the authored clause, not in the
renderer, and the fix belongs in the shot file (birth station), not in a re-burn
queue that keeps paying for the same sentence.

Read-only.  Prints unit | intent | camera clause, and optionally joins the
framing-gate evidence so the clause sits next to the number.
"""
import io
import json
import re
import sys

HERE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
MANIFEST = HERE + r"\local-i2v\run-bmc-kn-i2v.json"


def camera_clause(prompt):
    m = re.search(r"(A [a-z-]+ (?:shot|take)[^.]*\.)", prompt or "")
    if m:
        return m.group(1)
    m = re.search(r"(camera[^.]*\.)", prompt or "")
    return m.group(1) if m else "(no camera clause)"


def main():
    evidence = sys.argv[1] if len(sys.argv) > 1 else ""
    zoom = {}
    if evidence:
        with io.open(evidence, encoding="utf-8") as fh:
            for r in json.load(fh).get("rows", []):
                stem = re.sub(r"\.mp4$", "", r["clip"])
                zoom[stem] = (r.get("verdict"), r.get("max_zoom"))

    with io.open(MANIFEST, encoding="utf-8") as fh:
        units = json.load(fh)["units"]
    for u in units:
        uid = u["id"]
        if uid not in zoom:
            continue
        verdict, mz = zoom[uid]
        print("%-15s %-9s %-9s %s" % (uid, verdict, "%.2fx" % mz, camera_clause(u.get("i2v_prompt"))))
    print("\ncounting clauses among push units")
    clauses = {}
    for u in units:
        uid = u["id"]
        if uid not in zoom:
            continue
        if zoom[uid][0] not in ("PASS", "FLAT", "UNDECIDED"):
            continue
        c = camera_clause(u.get("i2v_prompt"))
        clauses.setdefault(c, []).append((uid, zoom[uid][1]))
    for c, rows in clauses.items():
        print("\n%s" % c)
        for uid, mz in rows:
            print("   %-15s %.2fx" % (uid, mz))


if __name__ == "__main__":
    main()