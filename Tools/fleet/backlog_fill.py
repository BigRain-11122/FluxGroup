# -*- coding: utf-8 -*-
"""backlog_fill.py - promote READY backlog cards into the dispatch queue.

Why this file exists (bm-m master, 2026-10-30): master_agent.supply() has called
`from backlog_fill import fill` every cycle since the master moved here, but the
module was NEVER committed. Result: every backlog card stayed stuck in
PRODUCTION-BACKLOG.jsonl and no worker lane could ever see it -> fleet idle while
the master believed it was dispatching. This closes that hole.

Cross-host rule: requires/cwd paths belong to the *assignee's* machine (C:/ K:/),
not the master's (bm-m is macOS). Local os.path.exists() on such paths always
fails -- that is exactly why cards died at the gate before. Master-side validation
here is structural (fields present, tools referenced exist in the REPO), and path
existence is the lane's own duty at claim time (lane_agent re-checks on its box).
"""
import json
import os

import fleet_lane as fl

BACKLOG_REL = "cph4/fleet/PRODUCTION-BACKLOG.jsonl"


def _repo_has(root, rel):
    """True if rel is a path inside the repo that exists (repo-relative check)."""
    return os.path.exists(os.path.join(root, rel.replace("/", os.sep)))


def _structural_ok(card, root):
    if not card.get("id") or not card.get("cmd"):
        return False, "no id/cmd"
    # referenced repo-relative tool paths (e.g. Tools/x.py, media/y/z.cmd) must exist
    cmd = card.get("cmd") or ""
    for token in cmd.replace('"', " ").replace("'", " ").split():
        t = token.strip("\\/").replace("\\", "/")
        if t.startswith(("Tools/", "media/", "cph4/")) and t.endswith((".py", ".cmd", ".ps1", ".sh")):
            if not _repo_has(root, t):
                return False, "tool missing in repo: %s" % t
    return True, ""


def fill(root):
    """Promote READY cards that pass the structural gate. Returns count added."""
    bpath = os.path.join(root, BACKLOG_REL.replace("/", os.sep))
    qpath = os.path.join(root, fl.QUEUE_REL.replace("/", os.sep))
    backlog = fl.read_jsonl(bpath)
    rows = fl.read_jsonl(qpath)
    have = {r.get("id") for r in rows}
    added = 0
    for b in backlog:
        jid = b.get("id")
        if not jid or jid in have:
            continue
        if b.get("state") != "READY":
            continue
        ok, why = _structural_ok(b, root)
        if not ok:
            b["state"] = "INVALID"
            b["invalid_reason"] = why
            continue
        rows.append({
            "id": jid, "title": b.get("title"), "cmd": b.get("cmd"),
            "cwd": b.get("cwd"), "needs": b.get("needs") or "cpu",
            "deliverable": b.get("deliverable"), "nodes": b.get("nodes") or [],
            "model": b.get("model") or "none", "prompt": b.get("prompt") or "",
            "when_all": b.get("when_all") or [], "llm": b.get("llm") or {},
            "prio": b.get("prio") or "P2", "why": b.get("why"),
            "cloud_ok": bool(b.get("cloud_ok")), "heavy": bool(b.get("heavy")),
            "timeout_s": b.get("timeout_s"), "day_ok": bool(b.get("day_ok")),
            "state": "OPEN", "route": "local",
            "created_by": "backlog_fill", "created_at": fl.now_iso(),
        })
        b["state"] = "PROMOTED"
        b["promoted_at"] = fl.now_iso()
        have.add(jid)
        added += 1
    if added:
        fl.write_jsonl(qpath, rows)
        fl.write_jsonl(bpath, backlog)
    else:
        # persist INVALID marks even when nothing was promoted
        if any(b.get("state") == "INVALID" for b in backlog):
            fl.write_jsonl(bpath, backlog)
    return added


if __name__ == "__main__":
    print("promoted:", fill(fl.ROOT_DEFAULT))
