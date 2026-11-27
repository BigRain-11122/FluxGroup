# -*- coding: utf-8 -*-
"""mv_workorder.py - deterministic defect workorder + cut consensus for mv0001.

Why: the v717 delivery gate, the shot audit and the outlier scan each produce their own
JSON, and the director had to cross-read four files by hand before a repair plan could be
written. This tool only merges existing evidence - no video decode, no LLM, no new
judgement: it assigns every already-measured defect to a shot and a fix class, and it
expands the reconcile report into a per-cut consensus table.

Fix classes are mechanical label mappings (see FIX_CLASS); the *choice* which shot to
reburn stays with the director seat.

Usage:
  python Tools/mv_workorder.py workorder --gate-in D:/FleetWorker/review/delivery_gate_v717_wl.json \
      --shots-in D:/FleetWorker/review/shot_audit_v717.json \
      --outliers-in D:/FleetWorker/review/outliers_v717.json \
      --json-out D:/FleetWorker/review/v718_workorder.json \
      --md-out D:/FleetWorker/review/v718_workorder.md
  python Tools/mv_workorder.py cuts --reconcile-in D:/FleetWorker/review/reconcile_v717.json \
      --shots-in D:/FleetWorker/review/shot_audit_v717.json \
      --csv-out D:/FleetWorker/review/v717_cut_consensus.csv
"""
import argparse
import csv
import json
import os

# defect kind -> candidate fix class (mechanical mapping, not a creative decision)
FIX_CLASS = {
    "FLICKER": "regrade-or-interp",
    "FREEZE": "trim-or-insert-motion",
    "JERK": "retime-or-interp",
    "FLOW": "retime",
    "POP": "reburn-shot",
    "JUMP": "reburn-or-retime",
    "CUT": "planned-cut-verify",
    "FLASH": "trim-flash-frame",
    "DUP": "trim-tail-frame",
    "STATIC": "trim-or-insert-motion",
}


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _shot_at(shots, t):
    """Return (name, t0, t1) of the shot containing t, else ('unassigned', None, None)."""
    best = None
    for s in shots:
        try:
            t0, t1 = float(s["t0"]), float(s["t1"])
        except Exception:
            continue
        if t0 <= t <= t1:
            if best is None or (t1 - t0) < (float(best["t1"]) - float(best["t0"])):
                best = s
    if best is None:
        return "unassigned", None, None
    return str(best.get("shot")), float(best["t0"]), float(best["t1"])


def build_workorder(gate, shots, outliers):
    items = []
    for e in outliers.get("events") or []:
        kind = str(e.get("kind") or "").upper()
        t = float(e.get("t") or 0.0)
        name, t0, t1 = _shot_at(shots, t)
        items.append({
            "t": round(t, 3),
            "frame": e.get("frame"),
            "kind": kind,
            "score": e.get("score"),
            "shot": name,
            "shot_t0": t0,
            "shot_t1": t1,
            "fix_class": FIX_CLASS.get(kind, "manual-review"),
            "evidence": "outliers",
        })

    fps = float(gate.get("fps") or 24.0) or 24.0

    def _add(t, frame, kind, score, evidence):
        name, t0, t1 = _shot_at(shots, t)
        items.append({
            "t": round(t, 3),
            "frame": frame,
            "kind": kind,
            "score": score,
            "shot": name,
            "shot_t0": t0,
            "shot_t1": t1,
            "fix_class": FIX_CLASS.get(kind, "manual-review"),
            "evidence": evidence,
        })

    # delivery_gate.flicker = [[frame, delta], ...]
    for f in gate.get("flicker") or []:
        if isinstance(f, dict):
            fr = f.get("frame")
            delta = f.get("delta")
        elif isinstance(f, (list, tuple)) and len(f) >= 2:
            fr, delta = f[0], f[1]
        else:
            continue
        try:
            fr = int(fr)
        except Exception:
            continue
        _add(fr / fps, fr, "FLICKER", delta, "delivery_gate.flicker")

    # delivery_gate.static_shots = [[frame_from, frame_to, mean_mad, shift], ...]
    for s in gate.get("static_shots") or []:
        if not (isinstance(s, (list, tuple)) and len(s) >= 3):
            continue
        f0, f1, mad = int(s[0]), int(s[1]), s[2]
        _add(f0 / fps, f0, "STATIC", mad, "delivery_gate.static_shots[%d-%d mad=%s]" % (f0, f1, mad))

    # exact duplicate frames are only reported inside the free-text fail lines
    import re as _re
    for line in gate.get("fails") or []:
        for m in _re.finditer(r"frame (\d+) \(([\d.]+)s\)", str(line)):
            _add(float(m.group(2)), int(m.group(1)), "DUP", None, "delivery_gate.fails")

    items.sort(key=lambda r: (r["t"], r["kind"]))

    by_kind = {}
    for r in items:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
    by_shot = {}
    for r in items:
        by_shot.setdefault(r["shot"], []).append(r["kind"])

    return {
        "generated_by": "Tools/mv_workorder.py",
        "gate_verdict": gate.get("verdict"),
        "gate_fails": gate.get("fails"),
        "gate_frames": gate.get("frames"),
        "gate_fps": gate.get("fps"),
        "gate_shots": gate.get("shots"),
        "stability": gate.get("stability"),
        "defect_counts": dict(sorted(by_kind.items(), key=lambda kv: -kv[1])),
        "item_count": len(items),
        "shots_with_defects": {k: sorted(set(v)) for k, v in sorted(by_shot.items())},
        "items": items,
    }


def write_md(wo, path):
    lines = []
    lines.append("# v718 defect workorder (generated, deterministic)")
    lines.append("")
    lines.append("- gate verdict: **%s**" % wo.get("gate_verdict"))
    lines.append("- frames/shots: %s / %s @ %sfps" % (wo.get("gate_frames"), wo.get("gate_shots"), wo.get("gate_fps")))
    lines.append("- stability: %s" % json.dumps(wo.get("stability"), ensure_ascii=False))
    lines.append("- gate fails:")
    for f in wo.get("gate_fails") or []:
        lines.append("  - %s" % f)
    lines.append("")
    lines.append("## defect counts")
    lines.append("")
    lines.append("| kind | count | fix class |")
    lines.append("|---|---|---|")
    for k, v in wo["defect_counts"].items():
        lines.append("| %s | %d | %s |" % (k, v, FIX_CLASS.get(k, "manual-review")))
    lines.append("")
    lines.append("## items (%d)" % wo["item_count"])
    lines.append("")
    lines.append("| t (s) | frame | kind | score | shot | window | fix class |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in wo["items"]:
        win = "" if r["shot_t0"] is None else "%.2f-%.2f" % (r["shot_t0"], r["shot_t1"])
        lines.append("| %.3f | %s | %s | %s | %s | %s | %s |" % (
            r["t"], r["frame"], r["kind"], r["score"], r["shot"], win, r["fix_class"]))
    lines.append("")
    lines.append("> Per-shot repair decision belongs to the director seat; this file only")
    lines.append("> aggregates already-measured defects and labels a candidate fix class.")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_cuts(rec, shots):
    rows = []
    for c in rec.get("clusters") or []:
        t = float(c.get("t") or 0.0)
        srcs = list(c.get("sources") or [])
        name, t0, t1 = _shot_at(shots, t)
        verdict = "BOTH" if len(srcs) >= 2 else ("TRANS-ONLY" if srcs == ["trans"] else "AUDIT-ONLY")
        rows.append({
            "t": round(t, 3),
            "sources": "+".join(srcs),
            "n_sources": len(srcs),
            "verdict": verdict,
            "shot": name,
            "shot_t0": t0,
            "shot_t1": t1,
            "detail": json.dumps(c.get("detail") or {}, ensure_ascii=False),
        })
    rows.sort(key=lambda r: r["t"])
    return {
        "generated_by": "Tools/mv_workorder.py",
        "tolerance_s": rec.get("tolerance_s"),
        "declared_counts": rec.get("declared_counts"),
        "counts": rec.get("counts"),
        "union_cut_count": rec.get("union_cut_count"),
        "only_in_one_pass": rec.get("only_in_one_pass"),
        "rows": rows,
    }


def write_csv(cut, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "frame_est", "sources", "n_sources", "verdict", "shot", "shot_t0", "shot_t1", "detail"])
        for r in cut["rows"]:
            w.writerow([r["t"], int(round(r["t"] * 24)), r["sources"], r["n_sources"], r["verdict"],
                        r["shot"], r["shot_t0"], r["shot_t1"], r["detail"]])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("workorder")
    w.add_argument("--gate-in", required=True)
    w.add_argument("--shots-in", required=True)
    w.add_argument("--outliers-in", required=True)
    w.add_argument("--json-out", required=True)
    w.add_argument("--md-out", required=True)

    c = sub.add_parser("cuts")
    c.add_argument("--reconcile-in", required=True)
    c.add_argument("--shots-in", required=True)
    c.add_argument("--csv-out", required=True)

    a = ap.parse_args()

    if a.cmd == "workorder":
        gate = _load(a.gate_in)
        shots = _load(a.shots_in)
        outliers = _load(a.outliers_in)
        wo = build_workorder(gate, shots, outliers)
        os.makedirs(os.path.dirname(a.json_out), exist_ok=True)
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(wo, f, ensure_ascii=False, indent=1)
        write_md(wo, a.md_out)
        print("WORKORDER items=%d counts=%s" % (wo["item_count"], json.dumps(wo["defect_counts"], ensure_ascii=False)))
        inner = [r for r in wo["items"] if r["shot"] != "unassigned"]
        print("assigned_to_shot=%d unassigned=%d" % (len(inner), wo["item_count"] - len(inner)))
    else:
        rec = _load(a.reconcile_in)
        shots = _load(a.shots_in)
        cut = build_cuts(rec, shots)
        os.makedirs(os.path.dirname(a.csv_out), exist_ok=True)
        write_csv(cut, a.csv_out)
        ver = {}
        for r in cut["rows"]:
            ver[r["verdict"]] = ver.get(r["verdict"], 0) + 1
        print("CUTS rows=%d verdict=%s" % (len(cut["rows"]), json.dumps(ver, ensure_ascii=False)))


if __name__ == "__main__":
    main()