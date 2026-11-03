# -*- coding: utf-8 -*-
"""backlog_fill.py - deterministic real-backlog -> production-queue filler.

Why this exists: the queue had 3 jobs total (all DONE), so the claim loop exited
QUEUE-EMPTY every 5 minutes and every supervisor read that exit 0 as "healthy".
This script looks for work that is physically ready on the machine it runs on and
enqueues only jobs whose inputs exist. No LLM, no network, no invented tasks.

First rule: drama episodes whose three-layer mix is already on disk but whose final
video still has no audio track. The mix materials are the expensive part and already
exist; the remux is a one-minute CPU job that turns a silent episode into a deliverable.

Usage: py backlog_fill.py [--root PATH]
"""
import argparse
import json
import os
import re
import sys
import time


def _load(path):
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
    return rows


def _save(path, rows):
    # 队列只有一个写入口（2026-11-02）：交给 fleet_lane 加锁按 id 合并。
    # 这里原来自己写 .tmp 再 os.replace 整表——而 lane_agent 每个周期都会调 fill()，
    # 于是它是第七条隐式写入口：与主控/补料同轮时，谁后写谁把对方的行抹掉。
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "Tools", "fleet"))
    import fleet_lane as _fl
    return _fl.merge_jsonl(path, rows)


def _ep(name):
    m = re.search(r"(EP\d{3})", name, re.I)
    return m.group(1).upper() if m else None


_GIT = {"loaded": False, "paths": set()}


def _git_paths(root):
    """Repo truth for tool existence: bm-m runs a SPARSE checkout, so os.path.exists()
    on Tools/*.py is routinely False for files that do exist on the worker boxes."""
    if not _GIT["loaded"]:
        import subprocess
        try:
            r = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", "HEAD"],
                               capture_output=True, text=True, timeout=40)
            if r.returncode == 0:
                _GIT["paths"] = {x.strip() for x in r.stdout.splitlines() if x.strip()}
        except Exception:
            pass
        _GIT["loaded"] = True
    return _GIT["paths"]


def _checkable(p):
    """Can THIS machine even look at this path? Drive letters only exist on Windows;
    /paths only on POSIX. The master (macOS) must not judge a worker's C-drive data."""
    pp = (p or "").replace("\\", "/")
    if re.match(r"^[A-Za-z]:", pp):
        return os.name == "nt"
    return True


def _tool_ok(cmd, root):
    """Every repo-relative script referenced by cmd must exist in the repo."""
    for tok in (cmd or "").replace('"', " ").replace("'", " ").split():
        t = tok.strip("\\/").replace("\\", "/")
        if t.startswith(("Tools/", "media/", "cph4/")) and t.endswith((".py", ".cmd", ".ps1", ".sh")):
            if t not in _git_paths(root) and not os.path.exists(os.path.join(root, t.replace("/", os.sep))):
                return False, t
    return True, ""


def _fill_manifest(root, rows, have, node=None):
    """Generic declarative rule.

    Why: the drama rule below only fires where drama-eps/ exists (bm-b). On bm-a every
    claim round returned QUEUE-EMPTY and the supervisor read exit 0 as healthy, while the
    machine sat idle with a real, already-declared backlog. So the backlog itself is now a
    file: a row is enqueued only when every path in `requires` exists and its `deliverable`
    does not -- no LLM, no guessing, nothing invented.
    """
    man = os.path.join(root, "cph4", "fleet", "PRODUCTION-BACKLOG.jsonl")
    queue_path = os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    rows_by_id = {x.get("id"): x for x in rows}
    backlog = _load(man)
    touched = False
    added = 0
    # 2026-11-03：语义判重（向量）。真事故：同一个配音质检活同时存在 3 张卡（2 跑 1 待）。
    # 在这里按标题相似度挡一次。任何异常都让 _sd 为 None → 不做判重 → 照常派活，
    # 绝不因为"判重工具坏了"把真活挡在门外。
    _sd = None
    try:
        import importlib.util as _ilu
        _sp = _ilu.spec_from_file_location(
            "_sd_block", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "fleet", "semantic_dupes.py"))
        _sd = _ilu.module_from_spec(_sp)
        _sp.loader.exec_module(_sd)
    except Exception:
        _sd = None
    for r in backlog:
        jid = r.get("id")
        if not jid:
            continue
        if r.get("state") not in (None, "READY"):
            continue
        nodes = r.get("nodes")
        if node and nodes and node not in nodes:
            continue
        if jid in have:
            cur = rows_by_id.get(jid) or {}
            # A corpse (INVALID/FAILED) must not block a card whose defect is now fixed.
            if cur.get("state") not in ("INVALID", "FAILED"):
                continue
            rows[:] = [x for x in rows if x.get("id") != jid]
            rows_by_id.pop(jid, None)
            have.discard(jid)
        # 2026-11 调研：无人值守工厂的第一教训不是"要更自主"，而是"没有书面规格→瓶颈转到
        # 评审队列"。所以卡必须自带交付物与验收口径，否则拒绝入队（SPEC-REQUIRED）。
        if not (r.get("deliverable") or r.get("accept") or r.get("when_none")):
            r["invalid_reason"] = "SPEC-REQUIRED: 无交付物/验收口径"
            r["state"] = "INVALID"
            touched = True
            continue
        cmd = r.get("cmd") or ""
        ok, bad = _tool_ok(cmd, root)
        if not ok:
            r["state"] = "INVALID"
            r["invalid_reason"] = "tool not in repo: %s" % bad
            r["invalid_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            touched = True
            continue
        req = r.get("requires") or []
        wa = r.get("when_all") or []
        if node is not None:
            # lane pass: THIS box must really have every declared input (strict)
            if req and not all(os.path.exists(p) for p in req):
                continue
            if wa and not all(os.path.exists(p) for p in wa):
                continue
        elif not r.get("verify_on_node"):
            # master pass: verify only what this OS can see; the rest the lane re-checks.
            # verify_on_node=true exists because the control plane (Mac) never holds the
            # production media: a card for bm-a whose input is a 2GB master would otherwise
            # be unpromotable forever. The lane pass below stays strict.
            if any(_checkable(p) and not os.path.exists(p) for p in req + wa):
                continue
        out = r.get("deliverable")
        if out and _checkable(out) and os.path.exists(out):
            # Already produced. Leaving such a row at READY/None made it look like pending
            # work for ever (2026-11-01: 22 rows read as inventory while every box idled).
            if r.get("state") is None:
                r["state"] = "DONE"
                r["closed_by"] = "backlog_fill: deliverable already on disk"
                touched = True
            continue
        if node is not None:
            r["state"] = "PROMOTED"
            r["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            touched = True
        # 2026-10-30 bm-m master: fields must survive promotion or the card is crippled --
        # day_ok lost = bm-a daytime cards never claimable; heavy lost = work-hour yield
        # bypassed; when_all lost = input gate gone; model/prompt lost = every text job
        # became "empty job" (that is why local lanes looked permanently idle).
        job = {k: r.get(k) for k in ("id", "title", "cmd", "cwd", "needs", "deliverable",
                                     "nodes", "day_ok", "heavy", "when_all", "when_none",
                                     "model", "prompt", "llm", "prio", "why", "timeout_s",
                                     "cloud_ok", "need_mb", "est_gb", "verify_on_node", "accept", "line",
                                     # requires 漏拷是 2026-11-03 实测事故：量化卡被派到没有量化仓的
                                     # 本机，rc=2 E-INPUT。输入门禁必须随卡进队列，否则形同虚设。
                                     "requires", "ok_rc", "minutes", "rescue")}
        job["state"] = "OPEN"
        if _sd is not None:
            try:
                _live = [(x.get("id"), x.get("title")) for x in rows
                         if x.get("state") in ("OPEN", "RUNNING", "READY") and x.get("id") != jid]
                _dup = _sd.duplicate_of(r.get("title") or "", _live)
                if _dup:
                    r["state"] = "DUP-SKIP"
                    r["dup_of"] = _dup[0]
                    r["dup_score"] = _dup[1]
                    r["dup_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    touched = True
                    continue
            except Exception:
                pass
        job["route"] = "local"
        job["created_by"] = "backlog_fill.py:manifest"
        job["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        rows.append(job)
        have.add(jid)
        rows_by_id[jid] = job
        added += 1
    if touched:
        _save(man, backlog)
    return added


def fill(root=None, node=None):
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    queue = os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    rows = _load(queue)
    have = {r.get("id") for r in rows}

    added = _fill_manifest(root, rows, have, node)
    if added:
        _save(queue, rows)

    eps_dir = os.path.join(root, "media", "drama-eps")
    mix_dir = os.path.join(root, "media", "drama-mix-out", "r1003_3layer")
    out_dir = os.path.join(root, "media", "drama-eps-audio")
    if not (os.path.isdir(eps_dir) and os.path.isdir(mix_dir)):
        return added

    done = set()
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            e = _ep(f)
            if e and f.lower().endswith(".mp4"):
                done.add(e)

    audio = {}
    for f in os.listdir(mix_dir):
        if f.lower().endswith((".wav", ".mp3", ".m4a", ".aac", ".flac")):
            e = _ep(f)
            if e:
                audio.setdefault(e, os.path.join(mix_dir, f))

    for f in sorted(os.listdir(eps_dir)):
        if not f.lower().endswith(".mp4") or f.lower().startswith(("tmp_", "diag_")):
            continue
        e = _ep(f)
        if not e or e in done or e not in audio:
            continue
        jid = "Q-DRAMA-AUDIO-" + e
        if jid in have:
            continue
        video = os.path.join(eps_dir, f)
        out = os.path.join(out_dir, e + "_AUDIO.mp4")
        cmd = (
            'ffmpeg -y -i "{v}" -i "{a}" -map 0:v -map 1:a -c:v copy '
            '-af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -shortest "{o}"'
        ).format(v=video, a=audio[e], o=out)
        rows.append({
            "id": jid,
            "title": "drama audio remux " + e,
            "cmd": cmd,
            "cwd": root,
            "needs": "cpu",
            "deliverable": out,
            "state": "OPEN",
            "created_by": "backlog_fill.py",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })
        have.add(jid)
        added += 1

    if added:
        os.makedirs(out_dir, exist_ok=True)
        _save(queue, rows)
    return added


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    a = ap.parse_args()
    print("BACKLOG-ADDED", fill(a.root))