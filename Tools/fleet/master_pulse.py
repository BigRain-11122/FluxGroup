#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""master_pulse.py - the single pulse of the bm-m control plane.

Why this exists (2026-10-30 measured, not guessed):
  * three schedulers fired the same tick (member 60s, master 120s, dashboard 20s), so
    two writers raced on the same state files and the contingency engine died with
    FileNotFoundError on its temp rename;
  * a master_agent run could hang indefinitely, holding the pulse silent while launchd
    kept "succeeding";
  * `git pull --rebase --autostash` swallowed uncommitted hand edits into a stash.

Design:
  one lock (nothing runs twice), pull only on a clean tree, every stage bounded by a
  timeout, and PULSE.json as a heartbeat any other program can read to prove liveness.

Cadence: dispatch-critical stages run every pulse (60s); the heavier maintenance stages
(health/contingency/inventory/judge/brain) run at most once per SLOW_EVERY seconds, so a
slow disk or a busy model can never make the 60s tick overlap with itself.

Usage:
  python3 Tools/fleet/master_pulse.py            # one pulse
  python3 Tools/fleet/master_pulse.py --no-pull  # skip git
  python3 Tools/fleet/master_pulse.py --force-slow  # run maintenance stages now
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NODE = os.environ.get("NODE", "bm-m")
PY = sys.executable or "/usr/bin/python3"
LOCK = "/tmp/fluxgroup-pulse.lock"
LOG = "/tmp/fluxgroup-pulse.log"
STATE_REL = "cph4/fleet/dispatcher/PULSE.json"
SLOW_EVERY = 240

# (name, argv, timeout_s, ok_rc, slow)
STAGES = [
    ("hb", ["Tools/fleet/fleet_hb.py", "--node", NODE, "--root", ROOT], 60, {0}, False),
    ("master", ["Tools/fleet/master_agent.py", "--node", NODE, "--root", ROOT], 240, {0}, False),
    ("lane", ["Tools/fleet/lane_agent.py", "--node", NODE, "--root", ROOT, "--no-fetch"], 300, {0}, False),
    # inventory exits 1 to say "a lane is STARVED"; that is an alert, not a tool failure.
    ("inventory", ["Tools/fleet/inventory_guard.py"], 120, {0, 1}, True),
    ("health", ["Tools/fleet/fleet_health.py"], 90, {0}, True),
    ("contingency", ["Tools/fleet/fleet_contingency.py"], 120, {0}, True),
    ("judge", ["Tools/fleet/local_judge.py"], 180, {0}, True),
    ("brain", ["Tools/fleet/brain_service.py"], 240, {0}, True),
]


def log(line: str) -> None:
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_state() -> dict:
    try:
        with open(os.path.join(ROOT, STATE_REL.replace("/", os.sep)), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def git(args, timeout=90):
    return subprocess.run(["git", "-C", ROOT] + args, capture_output=True, text=True, timeout=timeout)


STATE_PREFIXES = ("cph4/fleet/", "fleet-console.html")


def tree_is_clean() -> tuple[bool, list[str]]:
    # Only tracked changes count: the master rewrites its own state files constantly, and
    # rebasing on top of that is what produced the autostash losses.
    r = git(["status", "--porcelain", "--untracked-files=no"])
    dirty = [ln[3:].strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
    return (not dirty), dirty


def commit_state(dirty: list[str]) -> str:
    """Commit the plane's own state files so a rebase never has to stash them.

    Hand edits under Tools/ are deliberately NOT committed here: if one is dirty the pulse
    refuses to pull instead of inventing a commit for someone else's work.
    """
    if any(not p.startswith(STATE_PREFIXES) for p in dirty):
        return "skipped:dirty(hand-edit %s)" % next(
            p for p in dirty if not p.startswith(STATE_PREFIXES))[:60]
    git(["add"] + dirty)
    r = git(["commit", "-q", "-m", "pulse: state snapshot [via bm-m]"])
    return "ok" if r.returncode == 0 else "commit-failed:%s" % (r.stderr or "").strip()[:80]


def pull_if_clean() -> str:
    clean, dirty = tree_is_clean()
    note = ""
    if not clean:
        note = commit_state(dirty)
        if not note.startswith("ok"):
            return note
        clean, dirty = tree_is_clean()
        if not clean:
            return "still-dirty:%s" % (dirty[0] if dirty else "")
    try:
        r = git(["pull", "--rebase", "--no-autostash", "origin", "main"], timeout=120)
    except subprocess.TimeoutExpired:
        return "timeout"
    if r.returncode != 0:
        git(["rebase", "--abort"])       # never leave a half-finished rebase behind
        return "failed:%s" % (r.stderr or r.stdout or "").strip()[:120]
    return "ok" + ("(committed-state)" if note else "")


def ollama_ok() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def checks() -> list[dict]:
    out = [{"name": "ollama", "ok": ollama_ok(), "detail": "http://127.0.0.1:11434/api/tags"}]
    caf = subprocess.run(["pgrep", "-f", "caffeinate"], capture_output=True, text=True)
    out.append({"name": "caffeinate", "ok": bool(caf.stdout.strip()),
                "detail": "keeps the plane awake on AC power"})
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    for label in ("com.fluxgroup.pulse", "com.fluxgroup.dashboard", "com.fluxgroup.ollama"):
        line = next((ln for ln in r.stdout.splitlines() if ln.endswith(label)), "")
        parts = line.split()
        # "-" in the PID column just means "between interval runs" for StartInterval jobs.
        out.append({"name": label, "ok": bool(line) and len(parts) >= 2 and parts[1] == "0",
                    "detail": line.strip()})
    return out


def run_stage(argv, timeout_s):
    t0 = time.time()
    try:
        r = subprocess.run([PY] + argv, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout_s)
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        tail = (out.splitlines() or err.splitlines() or [""])[-1][:160]
        return r.returncode, round(time.time() - t0, 1), tail
    except subprocess.TimeoutExpired:
        return 124, round(time.time() - t0, 1), "timeout after %ss" % timeout_s


def main() -> int:
    no_pull = "--no-pull" in sys.argv
    force_slow = "--force-slow" in sys.argv

    lock_fd = open(LOCK, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("%s skip: previous pulse still running" % now())
        return 0

    started = time.time()
    prev = read_state()
    slow_due = force_slow or (time.time() - float(prev.get("slow_ts") or 0) > SLOW_EVERY)
    git_note = "skipped" if no_pull else pull_if_clean()

    stages, alerts, failed = {}, [], []
    for name, argv, timeout_s, ok_rc, slow in STAGES:
        if slow and not slow_due:
            stages[name] = {"rc": None, "sec": 0, "tail": "deferred (runs every %ds)" % SLOW_EVERY}
            continue
        rc, sec, tail = run_stage(argv, timeout_s)
        stages[name] = {"rc": rc, "sec": sec, "tail": tail}
        if rc not in ok_rc:
            failed.append(name)
        elif rc != 0:
            alerts.append("%s:%s" % (name, tail[-80:]))

    chk = checks()
    blockers = [c["name"] for c in chk if not c["ok"]] + ["stage:" + n for n in failed]
    pulse = {
        "ts": now(),
        "node": NODE,
        "sec": round(time.time() - started, 1),
        "slow_ts": time.time() if slow_due else float(prev.get("slow_ts") or 0),
        "git": git_note,
        "stages": stages,
        "checks": chk,
        "alerts": alerts,
        "blockers": blockers,
        "ok": not blockers,
    }
    path = os.path.join(ROOT, STATE_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pulse, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)

    summary = " ".join("%s=%s/%ss" % (k, v["rc"], v["sec"]) for k, v in stages.items()
                       if v.get("rc") is not None)
    log("%s pulse %s git=%s blockers=%s alerts=%s | %s"
        % (now(), "OK" if pulse["ok"] else "DEGRADED", git_note,
           ",".join(blockers) or "-", ",".join(alerts) or "-", summary))
    print("pulse %s git=%s blockers=%s%s"
          % ("OK" if pulse["ok"] else "DEGRADED", git_note,
             ",".join(blockers) or "-", (" alerts:" + ",".join(alerts)) if alerts else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())