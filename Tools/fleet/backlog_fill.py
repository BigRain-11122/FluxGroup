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


_GIT_TREE = {"loaded": False, "paths": set()}


def _git_paths(root):
    """Authoritative file list for the whole repo. bm-m runs a SPARSE checkout, so
    os.path.exists() on Tools/*.py is routinely False for files that DO exist on the
    worker boxes (2026-10-30: that mis-lint killed 5 real mv0001 cards as 'phantom').
    git ls-tree is the single source of truth and works regardless of checkout width."""
    if not _GIT_TREE["loaded"]:
        import subprocess
        try:
            r = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", "HEAD"],
                               capture_output=True, text=True, timeout=40)
            if r.returncode == 0:
                _GIT_TREE["paths"] = set(x.strip() for x in r.stdout.splitlines() if x.strip())
        except Exception:
            pass
        _GIT_TREE["loaded"] = True
    return _GIT_TREE["paths"]


def _repo_has(root, rel):
    rel = rel.replace("\\", "/").lstrip("./")
    if rel in _git_paths(root):
        return True
    return os.path.exists(os.path.join(root, rel.replace("/", os.sep)))


def _is_remote(pth):
    import re
    return bool(re.match(r"^[A-Za-z]:", pth.replace("\\\\", "/"))) or pth.startswith("/")


def _structural_ok(card, root):
    if not card.get("id") or not card.get("cmd"):
        return False, "no id/cmd"
    for req in (card.get("requires") or []):
        if _is_remote(req):
            continue          # lives on the assignee box; lane re-checks at claim time
        if not _repo_has(root, req):
            return False, "input missing in repo: %s" % req
    # referenced repo-relative tool paths (e.g. Tools/x.py, media/y/z.cmd) must exist
    cmd = card.get("cmd") or ""
    for token in cmd.replace('"', " ").replace("'", " ").split():
        t = token.strip("\\/").replace("\\", "/")
        if t.startswith(("Tools/", "media/", "cph4/")) and t.endswith((".py", ".cmd", ".ps1", ".sh")):
            if not _repo_has(root, t):
                return False, "tool missing in repo: %s" % t
    return True, ""


def _local_inputs_ok(card, node):
    """For lane self-dispatch: the card is runnable HERE only if its declared inputs
    exist on this machine and its deliverable is not already produced. The master cannot
    know this (different box, sparse checkout) -- the lane does. (2026-10-30: lane_agent
    has called fill(root, node) all along while the signature was fill(root); the
    TypeError was swallowed by the except in self_dispatch, so self-dispatch had been
    silently dead the whole time. This closes that hole properly.)"""
    for req in (card.get("requires") or []) + (card.get("when_all") or []):
        if not os.path.exists(req):
            return False
    out = card.get("deliverable") or ""
    if out and os.path.exists(out):
        return False
    return True


def fill(root, node=None):
    """Promote READY cards that pass the gate. node=None -> master pass (structural
    lint only); node='bm-b' -> lane pass (also require the inputs on THIS machine)."""
    bpath = os.path.join(root, BACKLOG_REL.replace("/", os.sep))
    qpath = os.path.join(root, fl.QUEUE_REL.replace("/", os.sep))
    backlog = fl.read_jsonl(bpath)
    rows = fl.read_jsonl(qpath)
    have = {r.get("id") for r in rows}
    by_id = {r.get("id"): r for r in rows}
    added = 0
    for b in backlog:
        jid = b.get("id")
        if not jid:
            continue
        if jid in have:
            # A dead INVALID row must not permanently block a fixed card, and a FAILED
            # row must not block a card whose tool/env defect has since been solved
            # (2026-10-30: 5 mis-linted mv0001 cards were stuck behind their own corpse).
            cur = by_id.get(jid) or {}
            if cur.get("state") not in ("INVALID", "FAILED"):
                continue
            rows = [r for r in rows if r.get("id") != jid]
            have.discard(jid)
            by_id.pop(jid, None)
        if b.get("state") != "READY":
            continue
        nodes = b.get("nodes") or []
        if node is not None:
            # lane pass: only this node's cards, and they must be runnable on this disk
            if nodes and node not in nodes:
                continue
            if not _local_inputs_ok(b, node):
                continue
            ok, why = (True, "")
        else:
            ok, why = _structural_ok(b, root)
        if not ok:
            b["state"] = "INVALID"
            b["invalid_reason"] = why
            b["invalid_at"] = fl.now_iso()
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
            "created_by": ("backlog_fill:%s" % node) if node else "backlog_fill",
            "created_at": fl.now_iso(),
        })
        b["state"] = "PROMOTED"
        b["promoted_at"] = fl.now_iso()
        have.add(jid)
        added += 1
    if added:
        fl.write_jsonl(qpath, rows)
    fl.write_jsonl(bpath, backlog)
    return added


if __name__ == "__main__":
    print("promoted:", fill(fl.ROOT_DEFAULT))
