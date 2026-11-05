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


def _load_cfg():
    try:
        with open(os.path.join(FLEET, "AUTONOMY-CONFIG.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


CFG = _load_cfg()


def book_prefixes():
    """记账目录（state/receipts/dispatcher）由配置给出，算在用到时，避免模块加载顺序问题。"""
    raw = ((CFG.get("truth") or {}).get("bookkeeping_prefixes") or
           ["cph4/fleet/state/", "cph4/fleet/queue-receipts/", "cph4/fleet/dispatcher/"])
    return tuple(norm(p).rstrip("/") for p in raw)


def norm(p):
    return p.replace("\\", "/")


def is_bookkeeping(p):
    q = norm(p)
    if os.path.isabs(q):
        try:
            q = norm(os.path.relpath(q, ROOT))
        except ValueError:
            return False
    # 目录本身不带结尾斜杠（cph4/fleet/queue-receipts）也必须算进记账，
    # 否则证据里一条目录路径就能把整条线判成"刚产出"。
    return any(q == pref or q.startswith(pref + "/") for pref in book_prefixes())


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
    book = is_bookkeeping(p)
    files = 0
    total = 0
    newest = 0.0
    if os.path.isfile(path):
        st = os.stat(path)
        return {"kind": "bookkeeping" if book else "local", "files": 1, "bytes": st.st_size,
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
    return {"kind": "bookkeeping" if book else "local", "files": files, "bytes": total,
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
    """What the disk says, independent of the declaration.

    2026-11-05: ONLY real artifacts count as output. A path under state/ or
    queue-receipts/ is bookkeeping written by the loop itself; counting it made every
    line look fresh (fluxverse/biglife showed 0.1h off state/city-state.json).
    """
    local = [e for e in evidence if e["stat"]["kind"] == "local"]
    remote = [e for e in evidence if e["stat"]["kind"] == "remote"]
    missing = [e for e in evidence if e["stat"]["kind"] == "missing"]
    book = [e for e in evidence if e["stat"]["kind"] == "bookkeeping"]
    live = [e for e in local if (e["stat"]["files"] or 0) > 0]
    newest = max([e["stat"]["newest"] for e in live if e["stat"]["newest"]] or [""])
    if live:
        return "OBSERVED", age_h(newest), newest
    if book and not remote and not missing:
        return "BOOKKEEPING", None, ""
    if remote:
        return "REMOTE", None, ""
    if missing and len(missing) == len(evidence):
        return "NO-DISK", None, ""
    return "EMPTY", None, ""


def group_rollup(rows, reg):
    """把 13 条工段线折成产品组的实况（2026-11-02 组织定案：中枢 + 三产品组 + 三职能）。

    组级只回答一件事：这一组今天有没有产物、最老的一件多旧。
    线仍是工段登记（派卡与证据目录按线走），组是给一屏与配额看的层。
    """
    org = {l.get("id"): (l.get("org") or "platform") for l in (reg.get("lines") or [])}
    prio = {l.get("id"): str(l.get("priority") or "P2") for l in (reg.get("lines") or [])}
    groups = {}
    for r in rows:
        g = org.get(r.get("id")) or "platform"
        e = groups.setdefault(g, {"group": g, "lines": [], "priority": None,
                                  "ages": [], "observed": 0, "stale": 0})
        e["lines"].append({"id": r.get("id"), "observed": r.get("observed"),
                           "age_h": r.get("age_h")})
        if r.get("age_h") is not None:
            e["ages"].append(r["age_h"])
        if r.get("observed") == "OBSERVED":
            e["observed"] += 1
        p = prio.get(r.get("id")) or "P2"
        if e["priority"] is None or p < e["priority"]:
            e["priority"] = p
    for g, e in groups.items():
        e["newest_age_h"] = min(e["ages"]) if e["ages"] else None
        e["oldest_age_h"] = max(e["ages"]) if e["ages"] else None
        # 本机没有证据目录 ≠ 没产出（跨机产物只认回执，2026-11-02 判例）。
        # 所以只有在"看得到证据且确实旧了"时才算 STALE；一条都看不到记 UNSEEN。
        if e["observed"] == 0:
            e["status"] = "UNSEEN"
        elif e["newest_age_h"] is None or e["newest_age_h"] > 24:
            e["status"] = "STALE"
        else:
            e["status"] = "OK"
        e["stale"] = 1 if e["status"] == "STALE" else 0
        e.pop("ages", None)
    return sorted(groups.values(), key=lambda x: (x["priority"] or "P9", x["group"]))


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
            "drift": (declared_status(line) == "ACTIVE" and obs in ("NO-DISK", "EMPTY", "BOOKKEEPING")),
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
           "groups": group_rollup(rows, reg),
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
    print("\n组级（一屏看的层）")
    for g in out["groups"]:
        print("  %-10s %-3s lines=%-2d 有产物=%-2d 最新产出=%s  %s" % (
            g["group"], g["priority"] or "-", len(g["lines"]), g["observed"],
            ("%.1fh 前" % g["newest_age_h"]) if g["newest_age_h"] is not None else "-",
            g["status"]))
    print("\ndeclared ACTIVE but no disk: %d | observed on disk: %d | remote-only: %d"
          % (s["declared_active_no_disk"], s["observed"], s["remote"]))
    print("queue: %d cards %s" % (len(q), states))
    print("-> cph4/fleet/state/lines.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))