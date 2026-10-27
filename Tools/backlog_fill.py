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
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def _ep(name):
    m = re.search(r"(EP\d{3})", name, re.I)
    return m.group(1).upper() if m else None


def fill(root=None):
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    queue = os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    rows = _load(queue)
    have = {r.get("id") for r in rows}

    eps_dir = os.path.join(root, "media", "drama-eps")
    mix_dir = os.path.join(root, "media", "drama-mix-out", "r1003_3layer")
    out_dir = os.path.join(root, "media", "drama-eps-audio")
    if not (os.path.isdir(eps_dir) and os.path.isdir(mix_dir)):
        return 0

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

    added = 0
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