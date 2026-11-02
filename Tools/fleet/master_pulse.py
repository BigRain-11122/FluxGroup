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
import re
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
SLOW_EVERY = 300
STATE_SNAPSHOT_S = 1800   # 报告类状态每 30 分钟快照一次（此前每 60 秒，占全部提交 44%）
HOT_PREFIXES = ("cph4/fleet/lanes/", "cph4/fleet/PRODUCTION-QUEUE.jsonl",
                "cph4/fleet/PRODUCTION-BACKLOG.jsonl", "cph4/fleet/dispatcher/MASTER-STATE.json",
                "cph4/fleet/dispatcher/MASTER-TICK.json")   # maintenance batch runs in parallel now, so 5 min is affordable

# (name, argv, timeout_s, ok_rc, slow)
STAGES = [
    ("hb", ["Tools/fleet/fleet_hb.py", "--node", NODE, "--root", ROOT], 60, {0}, False),
    # SUPPLY FIRST (CEO 2026-11-01: 不许因为是"没人宣告"就闲置). Both declare-work seats
    # existed since 10-31 but were never wired into the pulse, so they only ran when a
    # human remembered - boxes idled with an empty backlog while the generators sat idle.
    # They are queue writers, so they run serially before the dispatcher reads the queue.
    ("night_plan", ["Tools/fleet/night_plan.py"], 120, {0}, False),
    ("night_fill", ["Tools/fleet/night_fill.py", "--target", "3"], 90, {0}, False),
    ("workgen", ["Tools/fleet/workgen.py", "--root", ROOT], 180, {0}, False),
    ("master", ["Tools/fleet/master_agent.py", "--node", NODE, "--root", ROOT], 240, {0}, False),
    ("lane", ["Tools/fleet/lane_agent.py", "--node", NODE, "--root", ROOT, "--no-fetch"], 300, {0}, False),
    # inventory exits 1 to say "a lane is STARVED"; that is an alert, not a tool failure.
    ("inventory", ["Tools/fleet/inventory_guard.py"], 120, {0, 1}, True),
    # 事实层（2026-11-02 FLUX OS v2）：先把磁盘事实与结构断言跑一遍，再谈派单。
    # census 写 state/lines.json（I14 与 metrics 都依赖它），因此放在慢批串行最前。
    ("census", ["Tools/fleet/census.py"], 180, {0}, True),
    # 研究创新席（2026-11-02 CEO 令）：体检四席的边界与空转，顺手刷新 PROPOSALS.json
    # 供派单方择取。rc=2 是有违规的告警，不是工具坏，所以计入 ok_rc。
    ("ri", ["Tools/fleet/ri_dept.py", "check"], 60, {0, 2}, True),
    ("gate", ["Tools/fleet/gate_report.py"], 180, {0}, True),
    ("checkups", ["Tools/fleet/checkups.py"], 180, {0, 2}, True),
    ("metrics", ["Tools/fleet/ops_metrics.py"], 90, {0}, True),
    ("showcase", ["Tools/fleet/showcase.py"], 60, {0}, True),
    ("vault", ["Tools/fleet/vault.py", "verify"], 120, {0, 2}, True),
    ("handoff", ["Tools/fleet/handoff.py"], 60, {0}, True),
    ("chief", ["Tools/fleet/chief.py"], 120, {0}, True),
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
    ("closer", ["Tools/fleet/closer.py"], 60, {0}, True),
    ("deadline", ["Tools/fleet/fleet_deadline.py"], 120, {0}, True),
    ("supervisor", ["Tools/fleet/fleet_supervisor.py"], 60, {0}, True),
    # One page that names the single decision that moves the fleet now, from disk facts
    # only (CEO 2026-11-01: 大脑要及时/准确/创新/严格). Read-only, so it cannot stall.
    ("brain", ["Tools/fleet/brain_brief.py", "--root", ROOT], 60, {0}, True),
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


# Files the pulse commits itself so a rebase never has to stash them. CODELY.md and the
# memory folder belong here: agents append memory constantly, and while that file stayed
# dirty the pulse skipped every pull and every push ("non-fast-forward" for hours), so the
# plane kept ticking while the fleet could not see it - the 2026-11-02 overnight vacuum.
# Memory writes are append-only facts, safe to snapshot; hand edits under Tools/ are not.
# 2026-11-02: CODELY.md / 记忆目录**不**由主控自动提交。多个班的会话同时在维护记忆，主控再自动签入就必然撞冲突（本轮连撞四次，写出冲突标记）。记忆由写它的会话自己提交，主控只碰派单通道。
STATE_PREFIXES = ("cph4/fleet/", "fleet-console.html")
# 手写脏件挡住 git 超过这么久就不再算「可以容忍的迟到」，而是主控故障（需人/会话处理）。
GIT_SKIP_ALERT_MIN = 30


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


def last_snapshot_ts() -> float:
    """Wall-clock time of the last commit that touched a cold state file.

    Used to throttle report snapshots. Reading it from git (rather than trusting a field in
    PULSE.json) keeps the throttle honest even after a restart or a reset.
    """
    try:
        r = git(["log", "-1", "--format=%at", "--",
                 "cph4/fleet/dispatcher/PULSE.json"], timeout=20)
        return float((r.stdout or "0").strip() or 0)
    except Exception:
        return 0.0


def commit_state(tracked: list[str], untracked: list[str], force=False, last_ts=0.0) -> str:
    """Commit the plane's own state files, with hot/cold separation.

    Structure fix (2026-11-02): git was being used as a 60-second message bus. 44% of all
    commits were state snapshots, 54% of cycles could not sync because some file was dirty,
    and every second scheduler writing the same files produced rebase conflicts. Git now
    carries (a) the dispatch channel and (b) reports - and reports are snapshotted at most
    every STATE_SNAPSHOT_S, because nobody needs a SUPERVISOR.md per minute in history.
    """
    # 记忆是追加型事实：任何会话随时在写 CODELY.md。把它当成"手写代码"会让同步永久停摆
    # （2026-11-02 实测 322/386 轮因此跳过同步）。记忆单独定向提交，不与派单混在一起。
    MEMORY_PATHS = ("CODELY.md", ".codely-cli/memory/")
    mem = [p for p in tracked if p.startswith(MEMORY_PATHS)]
    if mem:
        try:
            git(["add", "--"] + mem)
            git(["commit", "-q", "-m", "memory: autosave [via %s]"
                 % os.environ.get("NODE", "bm-m")])
        except Exception:
            pass
        tracked = [p for p in tracked if p not in mem]
    hand = [p for p in tracked if not p.startswith(STATE_PREFIXES)]
    if hand:
        return "skipped:dirty(hand-edit %s)" % _one_line(hand[0], 60)
    # Only the dispatch channel is committed from now on. Reports (PULSE/SUPERVISOR/
    # BRAIN/DIGEST...) are gitignored runtime files: they are rewritten every cycle, and a
    # permanently dirty worktree is what blocked every pull (54% of cycles, 2026-11-02).
    todo = [p for p in tracked + untracked
            if p.startswith(STATE_PREFIXES) and any(p.startswith(h) for h in HOT_PREFIXES)]
    if not todo:
        return "ok (no state changes)"
    git(["add", "--"] + todo)
    kind = "dispatch"
    r = git(["commit", "-q", "-m", "pulse: %s snapshot [via bm-m]" % kind])
    return "ok" if r.returncode == 0 else "commit-failed:%s" % _one_line(r.stderr, 80)


def pull_if_clean(last_ts=0.0) -> str:
    """Sync without ever letting a dirty worktree block the plane.

    Two hard-won rules (2026-11-02):
      * never rebase - a rebase over a shared worktree stalls and leaves UU conflicts;
      * generated state (everything under cph4/fleet/) is allowed to be autostashed, but a
        dirty HAND EDIT under Tools/ still blocks the pull, because autostash can silently
        swallow someone's uncommitted work.
    """
    tracked, untracked = tree_state()
    try:
        note = commit_state(tracked, untracked, last_ts=last_ts)
    except Exception as e:
        # A bug in state bookkeeping must never stop the plane from dispatching.
        note = "commit-error:%s" % str(e)[:80]
    if note.startswith("skipped"):
        return note
    tracked2, _ = tree_state()
    # 记忆文件是追加型事实，任何会话随时在写；把它算作「手写代码」会让同步永久停摆
    # （这正是昨夜主控哑巴 8h 的病根）。只有 Tools/ 等真代码脏才拒绝同步。
    IGNORABLE = ("cph4/fleet/", "CODELY.md", ".codely-cli/memory/", "fleet-console.html")
    hand = [p for p in tracked2 if not p.startswith(IGNORABLE)]
    if hand:
        return "skipped:dirty(hand-edit %s)" % _one_line(hand[0], 60)
    args = ["pull", "--ff-only", "--no-rebase", "origin", "main"]
    if tracked2:
        # only generated state is dirty: stash/restore around the fast-forward
        args = ["pull", "--ff-only", "--autostash", "origin", "main"]
    try:
        r = git(args, timeout=120)
    except subprocess.TimeoutExpired:
        return "timeout"
    if r.returncode == 0:
        return "ok"
    msg = _one_line(r.stderr or r.stdout, 120)
    if "Not possible to fast-forward" in msg or "diverg" in msg:
        return "DIVERGED(report-only):%s" % msg
    return "failed:%s" % msg


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


def align_resident() -> str:
    """Keep exactly one brain resident: the policy model. A stray tag means the fleet is
    quietly running on something nobody configured (2026-11-01: policy qwen3.5:4b, resident
    qwen3:4b-instruct). Unload the stranger; never force-load (first caller loads it)."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            models = json.load(r).get("models", [])
    except Exception:
        return "unknown"
    pol = {}
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "MODEL-POLICY.json"), encoding="utf-8-sig") as f:
            pol = json.load(f)
    except Exception:
        pass
    want = ((pol.get("lane_local_llm") or {}).get("model")) or ""
    if not want:
        return "no-policy"
    stray = [m.get("name") or m.get("model") for m in models
             if not (m.get("name") or m.get("model") or "").startswith(want.split(":")[0])]
    for name in stray:
        try:
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({"model": name, "keep_alive": 0}).encode(),
                headers={"Content-Type": "application/json"}), timeout=30).read()
        except Exception:
            pass
    return "ok" if not stray else "unloaded:" + ",".join(stray)


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


def swap_used_gb() -> float:
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True,
                             timeout=10).stdout
        m = re.search(r"used = ([\d.]+)M", out)
        return round(float(m.group(1)) / 1024, 1) if m else -1.0
    except Exception:
        return -1.0


def pageouts() -> int:
    """Cumulative pageouts. Swap *usage* is sticky - it does not shrink when pressure
    goes away - so judging by the number alone would flag the box red for hours after a
    single spike. What matters is whether pages are still going to disk NOW."""
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"Pageouts:\s+(\d+)", out)
        return int(m.group(1)) if m else -1
    except Exception:
        return -1


def relieve_swap() -> str:
    """CEO 2026-11-01: 不要频繁触发硬盘交换. Live swap means pages are already on disk;
    every extra resident model makes it worse. Above 2GB we drop everything except the
    policy seat and say so, instead of quietly paging during the CEO's work."""
    gb = swap_used_gb()
    if gb < 0:
        return "unknown"
    if gb < 2.0:
        return "ok(%.1fGB)" % gb
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            models = json.load(r).get("models", [])
    except Exception:
        return "high(%.1fGB) unload-unknown" % gb
    keep = ""
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "MODEL-POLICY.json"), encoding="utf-8-sig") as f:
            pol = json.load(f)
        keep = ((pol.get("lane_local_llm") or {}).get("model")) or ""
    except Exception:
        pass
    dropped = []
    for m in models:
        name = m.get("name") or m.get("model") or ""
        if keep and name.startswith(keep.split(":")[0]):
            continue
        try:
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({"model": name, "keep_alive": 0}).encode(),
                headers={"Content-Type": "application/json"}), timeout=30).read()
            dropped.append(name)
        except Exception:
            pass
    return "high(%.1fGB)%s" % (gb, (" unloaded:" + ",".join(dropped)) if dropped else " no-extra-model")


def checks(prev: dict | None = None) -> list[dict]:
    out = []
    sw = relieve_swap()
    po = pageouts()
    prev_po = int((prev or {}).get("swap_pageouts") or 0)
    growing = prev_po > 0 and po > prev_po
    out.append({"name": "swap", "ok": not growing,
                "detail": "live swap %s%s (2GB line unloads extra models; red only while "
                          "pageouts still grow: %s->%s)"
                          % (sw, " GROWING" if growing else "",
                             prev_po or "-", po if po >= 0 else "-")})
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
        # A live PID in column 1 already proves the job is up. The status column is the
        # LAST exit code and keeps reporting a SIGTERM/previous failure after a deliberate
        # restart, which used to make a healthy plane look broken (2026-11-01).
        running = len(parts) >= 2 and parts[0].isdigit()
        clean_exit = len(parts) >= 2 and parts[1] == "0"
        out.append({"name": label, "ok": bool(line) and (running or clean_exit),
                    "detail": line.strip()})
    return out


def run_stage(argv, timeout_s):
    t0 = time.time()
    try:
        # 周期件禁云（CEO 2026-11-02）：给每个阶段打标记，router 见到就拒绝升云。
        _env = dict(os.environ, FLUX_AUTOMATION="1")
        r = subprocess.run([PY] + argv, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout_s, env=_env)
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
    resident_note = align_resident()
    prev = read_state()
    slow_due = force_slow or (time.time() - float(prev.get("slow_ts") or 0) > SLOW_EVERY)
    git_note = "skipped" if no_pull else _one_line(
        pull_if_clean(last_snapshot_ts()), 120)

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
    SLOW_SERIAL = {"census", "inventory", "contingency", "solver", "line_agents"}
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

    # EARLY HEARTBEAT. The dispatch trio above is what liveness depends on; the maintenance
    # batch below can take minutes (autowork and digest both wait on the 4B). With a single
    # write at the very end, a 4-minute cycle looked like a dead plane from every other node
    # - that is how bm-a spent a whole night believing the master was vacuum and took over.
    try:
        _early = {"ts": now(), "node": NODE, "sec": round(time.time() - started, 1),
                  "git": git_note, "stages": dict(stages),
                  "slow": "running" if slow_due else "deferred", "phase": "dispatch-done"}
        _p = os.path.join(ROOT, STATE_REL.replace("/", os.sep))
        _tmp = "%s.%d.early" % (_p, os.getpid())
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(_early, f, ensure_ascii=False, indent=1)
        os.replace(_tmp, _p)
    except Exception:
        pass

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
    chk = checks(prev)
    # 同步停摆必须可见（2026-11-02）：commit_state 遇手写脏件就整体跳过 git，
    # 而 PULSE 过去仍报 ok=true —— 与昨夜主控哑巴 8h 同一类「假绿」。
    skip_since = prev.get("git_skip_since")
    if str(git_note).startswith("skipped"):
        skip_since = skip_since or time.time()
        stuck_min = int((time.time() - float(skip_since)) / 60)
        chk.append({"name": "git-sync", "ok": stuck_min < GIT_SKIP_ALERT_MIN,
                    "detail": "%s; stuck %dmin (commit or clean it: uncommitted hand edits "
                              "stop fleet-wide sync)" % (_one_line(git_note, 90), stuck_min)})
    else:
        skip_since = None
        chk.append({"name": "git-sync", "ok": True, "detail": _one_line(git_note, 90)})
    blockers = [c["name"] for c in chk if not c["ok"]] + ["stage:" + n for n in failed]
    pulse = {
        "ts": now(),
        "node": NODE,
        "sec": round(time.time() - started, 1),
        "slow_ts": time.time() if slow_due else float(prev.get("slow_ts") or 0),
        "git": git_note,
        "git_skip_since": skip_since,
        "push": git_push,
        "stages": stages,
        "checks": chk,
        "swap_pageouts": pageouts(),
        "swap_used_gb": swap_used_gb(),
        "alerts": alerts,
        "blockers": blockers,
        "ok": not blockers,
    }
    pulse["resident"] = resident_note
    path = os.path.join(ROOT, STATE_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pulse, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)

    # Append-only event stream: every pulse leaves one immutable fact so dispatch/claim/
    # result can be replayed later instead of argued about.
    try:
        import collections
        qp = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
        cnt = collections.Counter()
        if os.path.exists(qp):
            for ln in open(qp, encoding="utf-8"):
                ln = ln.strip()
                if ln:
                    try:
                        cnt[json.loads(ln).get("state")] += 1
                    except Exception:
                        pass
        ev = {"ts": now(), "node": NODE, "sec": pulse["sec"], "ok": pulse["ok"],
              "git": git_note, "push": git_push, "queue": dict(cnt),
              "blockers": blockers, "alerts": alerts}
        with open(os.path.join(ROOT, "cph4", "fleet", "dispatcher", "events.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass


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
    # --loop N = resident mode: launchd KeepAlive then keeps ONE process alive instead of
    # waking a new one every minute (the 12:21 stall was a missed wake-up, not a crash).
    if "--loop" in sys.argv:
        every = int(sys.argv[sys.argv.index("--loop") + 1])
        while True:
            try:
                main()
            except Exception as e:
                log("%s loop-error: %s" % (now(), str(e)[:160]))
            time.sleep(every)
    sys.exit(main())