#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""census.py - generate the truth about business lines from the disk, not from memory.

Why: on 2026-11-02 the registry said 13 lines were ACTIVE while 9 of their repos did
not exist on the control machine at all. Hand-written status is a wish; only the disk
is evidence. This script scans every declared evidence path, records file count, bytes
and newest mtime, and reports the difference between "declared" and "observed".

Output: cph4/fleet/state/lines.json  (generated, gitignored)
Rules: never invent a status. A path that lives on another machine is reported as
REMOTE (not as missing) so that cross-machine absence is not mistaken for a dead line.

Usage: python3 census.py [--json]
"""
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
REG = os.path.join(FLEET, "LINE-REGISTRY.json")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
WD_DRIVE = ("D:", "K:", "C:", "E:", "F:")


def norm(p):
    return p.replace("\\", "/")


def classify(p):
    """local | remote | missing. Remote = a path rooted on another OS/drive."""
    if not p:
        return "missing"
    q = norm(p)
    if q.startswith(WD_DRIVE) or q.startswith("\\\\"):
        return "remote"
    if q.startswith("/") and not q.startswith(ROOT):
        return "remote" if os.path.exists(q) is False else "local"
    path = q if os.path.isabs(q) else os.path.join(ROOT, q)
    return "local" if os.path.exists(path) else "missing"


def stat_path(p):
    kind = classify(p)
    if kind != "local":
        return {"kind": kind, "files": None, "bytes": None, "newest": None}
    q = norm(p)
    path = q if os.path.isabs(q) else os.path.join(ROOT, q)
    files = 0
    total = 0
    newest = 0.0
    if os.path.isfile(path):
        st = os.stat(path)
        return {"kind": "local", "files": 1, "bytes": st.st_size,
                "newest": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")}
    for dirpath, dirs, names in os.walk(path):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
        for n in names:
            fp = os.path.join(dirpath, n)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            files += 1
            total += st.st_size
            if st.st_mtime > newest:
                newest = st.st_mtime
    return {"kind": "local", "files": files, "bytes": total,
            "newest": datetime.fromtimestamp(newest).isoformat(timespec="seconds") if newest else None}


def age_h(iso):
    if not iso:
        return None
    try:
        return round((time.time() - datetime.fromisoformat(iso).timestamp()) / 3600.0, 1)
    except Exception:
        return None


def declared_status(line):
    return (line.get("status") or "UNKNOWN").upper()


def observed_status(evidence):
    """What the disk says, independent of the declaration."""
    local = [e for e in evidence if e["stat"]["kind"] == "local"]
    remote = [e for e in evidence if e["stat"]["kind"] == "remote"]
    missing = [e for e in evidence if e["stat"]["kind"] == "missing"]
    live = [e for e in local if (e["stat"]["files"] or 0) > 0]
    newest = max([e["stat"]["newest"] for e in live if e["stat"]["newest"]] or [""])
    if live:
        return "OBSERVED", age_h(newest), newest
    if remote:
        return "REMOTE", None, ""
    if missing and len(missing) == len(evidence):
        return "NO-DISK", None, ""
    return "EMPTY", None, ""


def main(argv):
    reg = json.load(open(REG, encoding="utf-8-sig"))
    os.makedirs(STATE, exist_ok=True)
    rows = []
    for line in reg.get("lines") or []:
        ev = []
        seen = set()
        paths = list(line.get("evidence") or [])
        for st in line.get("stages") or []:
            paths.extend(st.get("evidence") or [])
        for p in paths:
            if norm(p) in seen:
                continue
            seen.add(norm(p))
            ev.append({"path": norm(p), "stat": stat_path(p)})
        for r in line.get("repos") or []:
            if norm(r) in seen:
                continue
            seen.add(norm(r))
            ev.append({"path": norm(r), "stat": stat_path(r), "is_repo": True})
        obs, age, newest = observed_status(ev)
        rows.append({
            "id": line.get("id"),
            "name": line.get("name"),
            "declared": declared_status(line),
            "observed": obs,
            "age_h": age,
            "newest": newest,
            "evidence": ev,
            "drift": (declared_status(line) == "ACTIVE" and obs in ("NO-DISK", "EMPTY")),
        })

    # queue reality, same idea: count what the books say vs what is on disk
    q = []
    try:
        for l in open(QUEUE, encoding="utf-8"):
            l = l.strip()
            if l:
                q.append(json.loads(l))
    except FileNotFoundError:
        pass
    states = {}
    for r in q:
        states[r.get("state") or "NONE"] = states.get(r.get("state") or "NONE", 0) + 1

    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "source": "census.py - generated from disk; never hand-edit",
           "lines": rows,
           "queue": {"total": len(q), "by_state": states},
           "summary": {
               "declared_active_no_disk": sum(1 for r in rows if r["drift"]),
               "observed": sum(1 for r in rows if r["observed"] == "OBSERVED"),
               "remote": sum(1 for r in rows if r["observed"] == "REMOTE"),
           }}
    with open(os.path.join(STATE, "lines.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    print("line                 declared   observed   age_h   newest")
    for r in rows:
        print("%-20s %-10s %-10s %-7s %s %s" % (
            (r["id"] or "")[:20], r["declared"], r["observed"],
            "-" if r["age_h"] is None else r["age_h"],
            (r["newest"] or "")[:19], "<- DRIFT" if r["drift"] else ""))
    s = out["summary"]
    print("\ndeclared ACTIVE but no disk: %d | observed on disk: %d | remote-only: %d"
          % (s["declared_active_no_disk"], s["observed"], s["remote"]))
    print("queue: %d cards %s" % (len(q), states))
    print("-> cph4/fleet/state/lines.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))