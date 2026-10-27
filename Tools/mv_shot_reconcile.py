# -*- coding: utf-8 -*-
"""mv_shot_reconcile.py - align the three shot/cut counts before any sign-off.

Why this exists: the same v717 file is reported as 83 shots (scene scan),
95 shots / 94 cuts (jitter classify) and 118 cuts (transition audit). Two people
signing off on different tables are signing different films. This tool takes the
three already-produced JSON artifacts and answers one question deterministically:
are the counts different because of *thresholds* (same cuts, different sensitivity)
or because one pass actually sees cuts the others miss?

It decodes nothing and invents nothing: input is the JSONs the fleet already wrote.

Usage:
  python Tools/mv_shot_reconcile.py --trans T.json --jitter J.json --audit A.json \
      --fps 24 --out R.json
"""
import argparse
import json
import os


def _load(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _trans_rows(d):
    """transition audit -> [(t, verdict)]"""
    if d is None:
        return None
    out = []
    rows = d if isinstance(d, list) else (d.get("cuts") or d.get("transitions") or [])
    for r in rows:
        if isinstance(r, dict) and "t" in r:
            out.append((float(r["t"]), str(r.get("verdict") or "?")))
        elif isinstance(r, (int, float)):
            out.append((float(r), "?"))
    return out


def _trans_cuts(d):
    """transition audit -> cut times"""
    rows = _trans_rows(d)
    return None if rows is None else [t for t, _ in rows]


def _jitter_cuts(d):
    """jitter classify -> cut times (list of floats or dicts with t)"""
    if d is None:
        return None
    raw = d.get("cuts") if isinstance(d, dict) else None
    if raw is None:
        raw = d.get("events") if isinstance(d, dict) else []
    out = []
    for r in raw or []:
        if isinstance(r, dict):
            if r.get("kind") in ("FLASH", "POP"):
                continue
            if "t" in r:
                out.append(float(r["t"]))
        elif isinstance(r, (int, float)):
            out.append(float(r))
    return out


def _audit_shot_starts(d):
    """full audit -> shot start times (shot boundaries, i>0)"""
    if d is None:
        return None
    rows = d if isinstance(d, list) else (d.get("shots") or [])
    out = []
    for r in rows:
        if isinstance(r, dict) and "t0" in r:
            out.append(float(r["t0"]))
    return sorted(out)


def _cluster(times_by_src, tol):
    """Union cut times, merging entries within `tol` seconds into one cluster."""
    flat = []
    for src, times in times_by_src.items():
        if times is None:
            continue
        for t in times:
            flat.append((t, src))
    flat.sort()
    clusters = []
    cur = []
    for t, src in flat:
        if cur and (t - cur[-1][0]) > tol:
            clusters.append(cur)
            cur = []
        cur.append((t, src))
    if cur:
        clusters.append(cur)
    out = []
    for c in clusters:
        members = {}
        for t, src in c:
            members.setdefault(src, []).append(round(t, 3))
        out.append({
            "t": round(sum(x[0] for x in c) / len(c), 3),
            "sources": sorted(members),
            "n_sources": len(members),
            "detail": members,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trans", default=None, help="transition audit json")
    ap.add_argument("--jitter", default=None, help="jitter classify json")
    ap.add_argument("--audit", default=None, help="full audit json (per-shot)")
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--tol-frames", type=float, default=3.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    tol = a.tol_frames / a.fps
    trans = _trans_cuts(_load(a.trans))
    trans_rows = _trans_rows(_load(a.trans))
    # transition audit mixes real shots with intra-shot jumps; only HARD/MATCH are
    # shot boundaries, so that subset is the one comparable with per-shot tables.
    trans_by_verdict = {}
    for _, v in (trans_rows or []):
        trans_by_verdict[v] = trans_by_verdict.get(v, 0) + 1
    trans_boundaries = None
    if trans_rows is not None:
        trans_boundaries = sum(1 for _, v in trans_rows if v in ("HARD", "MATCH"))
    jitter = _jitter_cuts(_load(a.jitter))
    starts = _audit_shot_starts(_load(a.audit))
    # shot starts exclude t=0, and the last boundary may equal duration: treat as cuts
    audit_cuts = [t for t in (starts or []) if t > 0]

    src = {"trans": trans, "jitter": jitter, "audit": audit_cuts}
    counts = {k: (len(v) if v is not None else None) for k, v in src.items()}
    present = [k for k, v in src.items() if v is not None]
    clusters = _cluster({k: src[k] for k in present}, tol)

    only = {}
    for k in present:
        other = [c for c in clusters if c["sources"] == [k]]
        only[k] = [c["t"] for c in other]

    spread = None
    vals = [counts[k] for k in present]
    if vals:
        spread = max(vals) - min(vals)

    if len(present) < 2:
        verdict = "INSUFFICIENT"
        why = "need at least two artifacts to compare"
    elif spread == 0:
        verdict = "ALIGNED"
        why = "all present passes agree on cut count"
    elif all(len(only[k]) == 0 for k in present):
        verdict = "ALIGNED-BY-TOLERANCE"
        why = "counts differ only because of detection threshold, every cut is seen by >=2 passes"
    else:
        verdict = "MISMATCH"
        why = "at least one pass sees cuts no other pass sees; the union is the honest cut list"

    out = {
        "inputs": {"trans": a.trans, "jitter": a.jitter, "audit": a.audit},
        "fps": a.fps,
        "tolerance_s": round(tol, 4),
        "counts": counts,
        "trans_by_verdict": trans_by_verdict,
        "trans_shot_boundaries": trans_boundaries,
        "spun_from_shots": {k: (counts[k] + 1) if counts[k] is not None else None for k in counts},
        "count_spread": spread,
        "union_cut_count": len(clusters),
        "only_in_one_pass": only,
        "clusters": clusters,
        "verdict": verdict,
        "why": why,
    }

    print("counts   :", counts)
    if trans_by_verdict:
        print("trans    :", trans_by_verdict, "| shot boundaries(HARD+MATCH) =", trans_boundaries)
    print("union    :", len(clusters), "cuts (tol %.3fs)" % tol)
    for k in present:
        print("  only in %-7s: %d" % (k, len(only[k])))
    print("VERDICT  :", verdict, "-", why)

    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
        print("json ->", a.out)


if __name__ == "__main__":
    main()