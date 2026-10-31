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
from concurrent.futures import ThreadPoolExecutor
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
SLOW_EVERY = 300   # maintenance batch runs in parallel now, so 5 min is affordable

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
    # Business production (2026-10-31 CEO: 本地 AI 赋能业务). Biz drafts one deliverable per
    # job per day; social only drafts replies (never posts); supervisor writes the one-screen
    # verdict. All are maintenance cadence so they cannot delay dispatch.
    ("social", ["Tools/fleet/social_drafts.py"], 180, {0}, True),
    ("biz", ["Tools/fleet/local_ai_business.py", "--due-only"], 600, {0, 1}, True),
    # Output timeliness + direction alignment, computed on git receipts/globs (the only
    # surface the Mac can always see), then the supervisor's one-screen verdict.
    # Unified-memory budget: decide, every cycle, whether a heavier local model may load at
    # all. 32GB is shared with the CEO's apps; the answer must be measured, not assumed.
    ("mem", ["Tools/fleet/mem_gate.py", "--need-gb", "22"], 30, {0}, True),
    ("autowork", ["Tools/fleet/autowork.py"], 240, {0}, True),
    ("deadline", ["Tools/fleet/fleet_deadline.py"], 120, {0}, True),
    ("supervisor", ["Tools/fleet/fleet_supervisor.py"], 60, {0}, True),
    # Aggregator: turns receipts+queue+verdicts into one screen for the CEO.
    ("digest", ["Tools/fleet/digest_agent.py"], 200, {0}, True),
    # Solve leg: requeues failed cards (capped), warns on starvation, and coordinates the
    # only remote channel we have. Serial with the other queue writers.
    ("solver", ["Tools/fleet/master_solver.py"], 120, {0}, True),
    ("line_agents", ["Tools/fleet/line_agents.py"], 120, {0}, True),
]


def log(line: str) -> None:
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def _one_line(s: str, limit: int = 140) -> str:
    # git errors arrive multi-line; a newline in the log/state breaks every reader.
    return " ".join(str(s or "").split())[:limit]


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


def tree_state() -> tuple[list[str], list[str]]:
    """Return (tracked_dirty, untracked). Rebases only ever choke on tracked edits, but
    untracked state files (PULSE.json, brain receipts) should still ride along so the repo
    stays one coherent snapshot."""
    r = git(["status", "--porcelain"])
    tracked, untracked = [], []
    for ln in (r.stdout or "").splitlines():
        if not ln.strip():
            continue
        if ln.startswith("??"):
            untracked.append(ln[3:].strip())
        else:
            tracked.append(ln[3:].strip())
    return tracked, untracked


def commit_state(tracked: list[str], untracked: list[str]) -> str:
    """Commit the plane's own state files so a rebase never has to stash them.

    Hand edits under Tools/ are deliberately NOT committed here: if one is dirty the pulse
    refuses to pull instead of inventing a commit for someone else's work.
    """
    hand = [p for p in tracked if not p.startswith(STATE_PREFIXES)]
    if hand:
        return "skipped:dirty(hand-edit %s)" % _one_line(hand[0], 60)
    todo = [p for p in tracked + untracked if p.startswith(STATE_PREFIXES)]
    if not todo:
        return "ok (no state changes)"
    git(["add"] + todo)
    r = git(["commit", "-q", "-m", "pulse: state snapshot [via bm-m]"])
    return "ok" if r.returncode == 0 else "commit-failed:%s" % _one_line(r.stderr, 80)


def pull_if_clean() -> str:
    tracked, untracked = tree_state()
    # Two attempts: the dashboard rewrites its html every 20s and the master rewrites its
    # state every cycle, so a rebase can find the tree dirty again between commit and pull.
    # Committing our own state twice is cheap; rebasing over hand edits is not.
    for attempt in (0, 1):
        tracked, untracked = tree_state()
        note = commit_state(tracked, untracked)
        if note.startswith("skipped"):
            return note
        try:
            r = git(["pull", "--rebase", "--no-autostash", "origin", "main"], timeout=120)
        except subprocess.TimeoutExpired:
            return "timeout"
        if r.returncode == 0:
            return "ok" + ("(committed-state)" if "no state" not in note else "")
        msg = _one_line(r.stderr or r.stdout, 120)
        if "unstaged" not in msg and "not concluded" not in msg:
            git(["rebase", "--abort"])
            return "failed:%s" % msg
    return "skipped:dirty-race(%s)" % _one_line(msg, 80)


def push_if_ahead() -> str:
    """Other nodes read lanes from origin, so an unpushed dispatch is a silent no-op.
    Pushing does not need a clean tree (unlike rebase) - no stash, no loss."""
    try:
        r = git(["rev-list", "--count", "origin/main..HEAD"], timeout=20)
        ahead = int((r.stdout or "0").strip() or 0)
    except Exception:
        return "count-failed"
    if ahead == 0:
        return "up-to-date"
    try:
        r = git(["push", "origin", "HEAD:main"], timeout=90)
        if r.returncode != 0:
            # Another node (bm-b/bm-c) pushes between our pull and push; rebase once, retry.
            msg = _one_line(r.stderr, 120)
            if "fetch first" in msg or "rejected" in msg:
                pull_note = pull_if_clean()
                if pull_note.startswith("ok"):
                    r = git(["push", "origin", "HEAD:main"], timeout=90)
                    if r.returncode == 0:
                        return "ok+%d(after-rebase)" % ahead
                return "rejected:%s | pull=%s" % (msg, pull_note)
            return "failed:%s" % msg
    except subprocess.TimeoutExpired:
        return "timeout"
    return "ok+%d" % ahead


def ollama_ok() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


MAX_RESIDENT_GB = 8.0


def evict_heavy_models() -> str:
    """bm-m is the control plane (CEO 2026-10-31): resident models must stay light.
    A 22GB model here starves the 32GB box and swaps the whole machine."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            models = json.load(r).get("models", [])
    except Exception:
        return "unknown"
    heavy = [(m.get("name") or m.get("model"), (m.get("size_vram") or 0) / 1e9)
             for m in models if (m.get("size_vram") or 0) / 1e9 > MAX_RESIDENT_GB]
    if not heavy:
        return "ok"
    for name, _ in heavy:
        try:
            body = json.dumps({"model": name, "keep_alive": 0}).encode()
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:11434/api/generate", data=body,
                headers={"Content-Type": "application/json"}), timeout=30).read()
        except Exception:
            pass
    return "evicted:" + ",".join(n for n, _ in heavy)


def checks() -> list[dict]:
    out = []
    ev = evict_heavy_models()
    out.append({"name": "resident-model-size", "ok": ev in ("ok", "unknown"),
                "detail": "limit %.0fGB (control plane, not a production box): %s"
                          % (MAX_RESIDENT_GB, ev)})
    ok = ollama_ok()
    detail = "http://127.0.0.1:11434/api/tags"
    if not ok:
        # The judgement seat is dead if Ollama is down; repair it before reporting.
        subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/com.fluxgroup.ollama" % os.getuid()],
                       capture_output=True, text=True)
        for _ in range(20):
            time.sleep(1)
            if ollama_ok():
                ok, detail = True, "restarted by pulse after failing a health check"
                break
    out.append({"name": "ollama", "ok": ok, "detail": detail})

    caf = subprocess.run(["pgrep", "-f", "caffeinate"], capture_output=True, text=True)
    caf_ok = bool(caf.stdout.strip())
    if not caf_ok:
        subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/com.fluxgroup.caffeinate" % os.getuid()],
                       capture_output=True, text=True)
        time.sleep(2)
        caf = subprocess.run(["pgrep", "-f", "caffeinate"], capture_output=True, text=True)
        caf_ok = bool(caf.stdout.strip())
    out.append({"name": "caffeinate", "ok": caf_ok,
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
    git_note = "skipped" if no_pull else _one_line(pull_if_clean(), 120)

    stages, alerts, failed = {}, [], []

    def record(name, rc, sec, tail, ok_rc):
        stages[name] = {"rc": rc, "sec": sec, "tail": tail}
        if rc not in ok_rc:
            failed.append(name)
        elif rc != 0:
            alerts.append("%s:%s" % (name, tail[-80:]))

    # Dispatch-critical stages stay serial and ordered; maintenance stages are independent
    # and are run concurrently (2026-10-31: 4B handles 3 parallel calls at ~41 tok/s each
    # with no extra memory, so the slow batch is latency-bound on nothing but serialisation).
    # Queue writers (master, contingency, inventory) must never run concurrently or they
    # clobber each other's rows; everything else is read-mostly and model-bound.
    SLOW_SERIAL = {"inventory", "contingency", "solver", "line_agents"}
    serial = [s for s in STAGES if not s[4]]
    slow_serial = [s for s in STAGES if s[4] and s[0] in SLOW_SERIAL]
    parallel = [s for s in STAGES if s[4] and s[0] not in SLOW_SERIAL]
    # Two pools by resource, not by "more workers = faster":
    #   MODEL_STAGES share Ollama's 3 slots; giving them 6 threads only queues work.
    #   IO stages are pure python (files/git) and are cheap to run wide.
    MODEL_STAGES = {"judge", "brain", "social", "biz", "autowork", "digest"}
    pool_model = ThreadPoolExecutor(max_workers=3)
    pool_io = ThreadPoolExecutor(max_workers=8)
    pool = pool_model
    futs = {}
    if slow_due:
        # Start the read-mostly/model-bound batch BEFORE the dispatch trio: they do not read
        # queue state, so waiting for hb+master first would just serialise the whole cycle.
        futs = {}
        for name, argv, timeout_s, _, _ in parallel:
            target = pool_model if name in MODEL_STAGES else pool_io
            futs[name] = target.submit(run_stage, argv, timeout_s)

    for name, argv, timeout_s, ok_rc, _ in serial:
        rc, sec, tail = run_stage(argv, timeout_s)
        record(name, rc, sec, tail, ok_rc)

    if slow_due:
        for name, argv, timeout_s, ok_rc, _ in slow_serial:
            rc, sec, tail = run_stage(argv, timeout_s)
            record(name, rc, sec, tail, ok_rc)
        for name, _argv, _t, ok_rc, _ in parallel:
            rc, sec, tail = futs[name].result()
            record(name, rc, sec, tail, ok_rc)
        pool_model.shutdown()
        pool_io.shutdown()
    else:
        pool_model.shutdown()
        pool_io.shutdown()
        for name, _argv, _t, _ok, _ in slow_serial + parallel:
            stages[name] = {"rc": None, "sec": 0,
                            "tail": "deferred (runs every %ds)" % SLOW_EVERY}

    git_push = "skipped" if no_pull else push_if_ahead()
    chk = checks()
    blockers = [c["name"] for c in chk if not c["ok"]] + ["stage:" + n for n in failed]
    pulse = {
        "ts": now(),
        "node": NODE,
        "sec": round(time.time() - started, 1),
        "slow_ts": time.time() if slow_due else float(prev.get("slow_ts") or 0),
        "git": git_note,
        "push": git_push,
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
    log("%s pulse %s git=%s push=%s blockers=%s alerts=%s | %s"
        % (now(), "OK" if pulse["ok"] else "DEGRADED", git_note, git_push,
           ",".join(blockers) or "-", ",".join(alerts) or "-", summary))
    print("pulse %s git=%s blockers=%s%s"
          % ("OK" if pulse["ok"] else "DEGRADED", git_note,
             ",".join(blockers) or "-", (" alerts:" + ",".join(alerts)) if alerts else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())