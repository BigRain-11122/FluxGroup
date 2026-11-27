#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent.py - the ONE resident agent each fleet node runs.

Why this replaces "hb task + claim task" (2026-10-31 root cause): the heartbeat task was
alive while the executor task was dead, so the master saw a healthy machine and an empty
execution log all night. Two tasks = two failure modes = a control plane that lies to
itself. This is one task, one process, one chain:

    pull -> heartbeat -> self-check own scheduled task -> claim from lane -> run -> report

Every step is idempotent and writes evidence, so the master can judge four separate
signals instead of one: machine hb, agent report, claim, receipt.

Usage (on the node, once, then register as a scheduled task):
    python Tools/fleet/agent.py --node bm-b
    python Tools/fleet/agent.py --node bm-b --loop 60     # stay resident
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PY = sys.executable or "python"

# 提交前兜底只许收自己的状态件（见 commit_state_before_rebase 注释）
# 2026-11-04: lanes/ REMOVED - the lane file is the master's pen, nodes only read it.
# Snapshotting lanes (including OTHER machines' lanes) re-published stale/merged lane
# versions after every rebase - that is how conflict-marker poison survived 5 straight
# commits and blocked all dispatch on 2026-11-04.
STATE_PREFIXES = ("cph4/fleet/state/", "cph4/fleet/dispatcher/")
STATE_FILES = ("cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/PRODUCTION-BACKLOG.jsonl")


def run(argv, timeout):
    try:
        # 2026-11-05: git output carries UTF-8 Chinese (queue/lanes/receipts); the GBK
        # default on Windows raised UnicodeDecodeError in the reader threads.
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        tail = ((r.stdout or "").strip().splitlines() or [""])[-1][:160]
        return r.returncode, tail
    except subprocess.TimeoutExpired:
        return 124, "timeout after %ss" % timeout
    except Exception as e:
        return 1, str(e)[:160]


# Machine-generated state files that the master republishes on every pulse. A node's own
# copy of these is disposable: dropping it costs at most one sensor cycle. Anything outside
# this list (ledgers, orders, logs written by humans or shifts) must never be discarded.
GEN_STATE = [
    "cph4/fleet/dispatcher/SUPERVISOR.md",
    "cph4/fleet/dispatcher/CLOCK-SKEW.json",
    "cph4/fleet/dispatcher/NEED-JUDGMENT.md",
    "docs/audits/selfaudit-report.md",
    # R2.59: lane writes this pointer every round and it is tracked, so the tree was
    # permanently dirty and every ff-only/rebase refused -- the same class of bug as
    # R2.57's SUPERVISOR.md. Regenerated on the next lane round, so dropping it is free.
    "cph4/fleet/queue-receipts/_last_lane_*.json",
    # R2.60: the R2.57/R2.59 lists named four files, but the master republishes a wider set
    # of derived state and each local sensor rewrites its own copy. On 11-01 13:5x the tree
    # carried 22 dirty tracked files, so the clear step freed 5 of them and the fast-forward
    # still refused for hours -- the node sat 23 commits behind and every local writer landed
    # on a stale base. Only derived state belongs here: the authoritative copy is on origin,
    # written by the master, and a node's own copy costs at most one sensor cycle to rebuild.
    # Human/shift ledgers (DISPATCH-LOG, DEADLINES, MASTER-LOG, PATROL-FLEET/*) and the queue
    # itself (PRODUCTION-QUEUE/BACKLOG, queue-receipts) are deliberately NOT listed: those
    # carry work that exists nowhere else, so they must block the pull and be resolved.
    "cph4/fleet/dispatcher/MASTER-STATE.json",
    "cph4/fleet/dispatcher/MASTER-TICK.json",
    "cph4/fleet/dispatcher/PULSE.json",
    "cph4/fleet/dispatcher/SOLVER.md",
    "cph4/fleet/dispatcher/DIGEST.md",
    "cph4/fleet/dispatcher/digest-cache.json",
    "cph4/fleet/dispatcher/CONTINGENCY-STATE.json",
    "cph4/fleet/dispatcher/NEED-SUPPLY.md",
    "cph4/fleet/dispatcher/AUTOWORK.md",
    "cph4/fleet/dispatcher/ROUTED-WORK.jsonl",
    "cph4/fleet/dispatcher/events.jsonl",
    "cph4/fleet/social/DIGEST.md",
    "cph4/fleet/lanes/*.json",
]


def run_msg(argv, timeout):
    """Like run(), but keeps git's stderr -- merge/checkout refusals are reported there."""
    try:
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        msg = ((r.stderr or "") + " " + (r.stdout or "")).strip().replace("\n", " | ")
        return r.returncode, msg[:240]
    except subprocess.TimeoutExpired:
        return 124, "timeout after %ss" % timeout
    except Exception as e:
        return 1, str(e)[:240]


def heal_deleted():
    """Materialise tracked files that HEAD has but the worktree lacks.

    2026-11-01 measured: after a `git reset --mixed origin/main` convergence, HEAD equalled
    origin while 26 files the master had committed (including Tools/voicebank/
    vb_discover.py) were never written to disk. `merge --ff-only` then answers "Already up
    to date" forever, so the node silently ran a stale tree and the master's card
    C-VB-DISCOVER-V02 died rc=2 in 0.1s on a script that "should" have existed. Only files
    that are MISSING are restored, so local edits and working-tree changes are untouched.
    """
    rc, out = run_msg(["git", "ls-files", "-d"], 60)
    paths = [p.strip() for p in out.replace(" | ", "\n").splitlines() if p.strip()]
    healed = 0
    for p in paths:
        r, _ = run_msg(["git", "checkout", "--", p], 60)
        healed += 1 if r == 0 else 0
    if healed:
        note("healed %d missing tracked file(s)" % healed)
    return healed


def commit_state():
    """Snapshot the fleet state this node itself rewrote, so the rebase can actually run.

    Why (2026-11-02): the lane's workgen/backlog_fill steps rewrite the shared backlog and queue
    every cycle. Those are real state transitions (cards promoted, archived, closed) and must not
    be dropped by GEN_STATE -- but while they sit unstaged, the rebase that a diverged node needs
    refuses on "unstaged changes" and the node stays behind. bm-c sat at ahead/behind 1/2 and
    kept re-running stale code for exactly this reason. Commit them under a pathspec limited to
    fleet state; shift ledgers (dispatcher logs, orders) are deliberately left alone.
    """
    # Full output, not run_msg: it truncates to 240 chars, which would silently commit only the
    # first one or two paths and leave the rest to block the next rebase.
    try:
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                               capture_output=True, text=True, timeout=60,
                               encoding="utf-8", errors="replace").stdout or ""
    except Exception:
        return 1
    paths = []
    for ln in dirty.splitlines():
        if not ln.strip():
            continue
        p = ln[3:].strip()
        # 只归自己的状态件（2026-11-03 修）：此前是 cph4/fleet/** 全收，把主控手写的设计
        # 文档、正典和别人刚写的回执一起卷进 "state(bm-c) snapshot before rebase"，
        # 提交史（CEO 唯一审计面）里于是出现"内容与提交信息完全不相干"的文件。
        if p.startswith(STATE_PREFIXES) or p in STATE_FILES:
            paths.append(p)
    if not paths:
        return 0
    run_msg(["git", "add", "--"] + paths, 120)
    rc_c, _ = run_msg(["git", "commit", "-q", "-m",
                       "state(bm-c): node state snapshot before rebase [via bm-c]",
                       "--"] + paths, 120)
    if rc_c == 0:
        note("committed %d state files before rebase" % len(paths))
    return rc_c


def git_full(argv, timeout=180):
    """Run git and keep the whole stderr: rebase refusals name every colliding path."""
    try:
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return r.returncode, ((r.stderr or "") + "\n" + (r.stdout or "")).strip()
    except Exception as e:
        return 1, str(e)


def resolve_rebase_conflicts():
    """Finish a conflicted rebase instead of aborting it.

    Why (2026-11-02): the master and this node both touch the shared queue/backlog and both
    produce receipts, so replaying a local artifact commit hits add/add conflicts
    (cph4/fleet/queue-receipts/mv-transition.json on bm-c). Aborting there means the node can
    never catch up: every cycle finds the same conflict. Rule: shared state belongs to the
    master (take origin), our own artifacts belong to us (take the commit being applied).
    """
    rc, out = git_full(["git", "diff", "--name-only", "--diff-filter=U"], 60)
    files = [p.strip() for p in out.splitlines() if p.strip()]
    if not files:
        return 1
    for p in files:
        # 2026-11-04: lanes/ belongs to the master's pen - on conflict take origin's side.
        # Nodes re-publishing their stale lane snapshot is the poison vector.
        side = "--ours" if p.startswith("cph4/fleet/PRODUCTION-QUEUE.jsonl") or \
            p.startswith("cph4/fleet/PRODUCTION-BACKLOG.jsonl") or \
            p.startswith("cph4/fleet/lanes/") or \
            p.startswith("cph4/fleet/plans/") else "--theirs"
        run_msg(["git", "checkout", side, "--", p], 60)
        # poison guard: never stage a file that still carries conflict markers
        try:
            with open(os.path.join(ROOT, p.replace("/", os.sep)), encoding="utf-8", errors="replace") as _fh:
                _t = _fh.read()
            if "^<<<<<<<" in _t and ">>>>>>>" in _t:
                note("POISON-GUARD: %s still has conflict markers, NOT staged" % p)
                continue
        except Exception:
            pass
        run_msg(["git", "add", "--", p], 60)
    note("resolved %d rebase conflicts" % len(files))
    r, _ = run_msg(["git", "-c", "core.editor=true", "rebase", "--continue"], 180)
    return r


def stash_untracked_collisions(msg):
    """Move aside untracked files the checkout refuses to overwrite.

    Why (2026-11-02): origin may start tracking a file this node already created locally
    (bm-c had an untracked cph4/fleet/voicebank/discover/jobs_v02.txt). git then aborts the whole
    rebase with "The following untracked working tree files would be overwritten", the node stays
    behind for good, and the local copy might be the only one. Move it under media/ (gitignored)
    rather than deleting it.
    """
    paths, grab = [], False
    for ln in msg.splitlines():
        if "would be overwritten by checkout" in ln:
            grab = True
            continue
        if grab:
            s = ln.strip()
            if (not s or s.startswith("Please move") or s.startswith("Aborting")
                    or s.startswith("error") or s.startswith("hint")):
                break
            paths.append(s)
    dest = os.path.join(ROOT, "media", "logs", "untracked-collisions",
                        time.strftime("%Y%m%d-%H%M%S"))
    moved = 0
    for p in paths[:20]:
        src = os.path.join(ROOT, p.replace("/", os.sep))
        if not os.path.exists(src):
            continue
        try:
            os.makedirs(dest, exist_ok=True)
            shutil.move(src, os.path.join(dest, os.path.basename(p)))
            moved += 1
        except Exception:
            pass
    return moved


def ensure_sparse_cone():
    """2026-11-10 CEO-PROXY 事件班 bm-b 实锚：sparse cone 只物化了 queue-receipts/lanes，
    数据面（cph4/fleet/asset-lib-v1/ASSET-PROMPTS-v1.json、LINE-REGISTRY.json 等）不在锥内
    -> 卡上的脚本读不到配置就 0.1s 秒退，rc=0/3 且不产交付物，表现为「有卡不干 + 假完成重开」。
    缺数据文件是假失败，不是机器不行。幂等：非 cone 模式不动；失败只记日志不阻断拉取。
    """
    try:
        _r, mode = run_msg(["git", "config", "core.sparseCheckout"], 30)
        if (mode or "").strip().lower() not in ("true", "yes", "1"):
            return
        # add 只增不删（set 会重置其它路径，禁用）。
        run_msg(["git", "sparse-checkout", "add", "cph4/fleet", "Tools/fleet"], 120)
        note("sparse-cone ensured: cph4/fleet + Tools/fleet")
    except Exception as e:
        note("sparse-cone guard skipped: %s" % str(e)[:120])


def pull():
    # Codes must arrive before the executor runs, otherwise the node keeps running the bug
    # we already fixed on the master. Never autostash (it swallowed hand edits once).
    ensure_sparse_cone()
    #
    # R2.57: plain `pull --rebase --no-autostash` can never succeed here. SUPERVISOR.md is
    # rewritten by the local steward every 5 min and committed by bm-m on every pulse, so the
    # tree is permanently dirty and pull dies with "cannot pull with rebase: You have unstaged
    # changes" -- silently, for weeks. The tree then drifts thousands of commits behind and any
    # local writer lands on a stale base (the stuck-rebase loop of R2.54/R2.55/R2.56).
    # Fix: fetch, fast-forward when possible, and only fall back to clearing GEN_STATE.
    run_msg(["git", "fetch", "--quiet", "origin", "main"], 120)
    rc, tail = run_msg(["git", "merge", "--ff-only", "origin/main"], 120)
    if rc == 0:
        note("ff-only ok: %s" % tail)
        heal_deleted()
        return rc
    cleared = []
    for p in GEN_STATE:
        r, _ = run_msg(["git", "checkout", "HEAD", "--", p], 60)
        if r == 0:
            cleared.append(p)
    rc2, tail2 = run_msg(["git", "merge", "--ff-only", "origin/main"], 120)
    if rc2 == 0:
        note("ff-only after clear ok: %s" % tail2)
        return rc2
    # R2.61 (2026-11-03, bm-b 实锚)：本机产出不先落提交，pull 就被自己的输出锁死。
    # 实测 FleetAgent 树 76 个脏件（回执/队列/docs 汇总）把 ff 与 rebase 挡了 20 小时：
    # 代码停在 11-02 03:35、回执一条都上不了链，主控读到的却是"这台机器不行"。
    # 规则：自己名下的产出（回执/lane/队列行）→ 本地 WIP 提交，随 push 正常上链；
    #       其余脏件（他机回执、docs 汇总等再生件）→ 还原到 HEAD，不让它们继续挡路。
    #       只处理已跟踪文件；未跟踪件不动。
    OUR_OUTPUT = ("cph4/fleet/queue-receipts/", "cph4/fleet/lanes/")
    OWN_FILES = ("cph4/fleet/PRODUCTION-QUEUE.jsonl",)
    rc_s, dirty = run_msg(["git", "status", "--porcelain"], 60)
    own, foreign = [], []
    for ln in (dirty or "").split("|"):
        ln = ln.rstrip()
        if len(ln) < 4:
            continue
        p = ln[3:].strip()
        if not p or ln[:2] == "??":
            continue
        if p.startswith(OUR_OUTPUT) or p in OWN_FILES:
            own.append(p)
        else:
            foreign.append(p)
    if foreign:
        run_msg(["git", "checkout", "HEAD", "--"] + foreign, 120)
        note("quarantine: reset %d foreign dirty paths" % len(foreign))
    if own:
        run_msg(["git", "add", "-A", "--"] + own, 120)
        _nm = os.environ.get("FLEET_NODE") or os.environ.get("COMPUTERNAME") or "node"
        run_msg(["git", "-c", "user.name=" + _nm,
                 "-c", "user.email=" + _nm + "@fleet.fluxgroup.local",
                 "commit", "-m", "wip(%s): local artifacts before pull" % _nm], 120)
        note("quarantine: committed %d own output paths" % len(own))
    rc2b, tail2b = run_msg(["git", "merge", "--ff-only", "origin/main"], 120)
    if rc2b == 0:
        note("ff-only after quarantine ok: %s" % tail2b)
        return rc2b
    # Diverged: local commits exist. Rebase onto the master, but only when the tree is clean --
    # git refuses on its own otherwise, so a shift mid-edit is never destroyed.
    commit_state()
    # Whatever is left dirty is not fleet state (hand edits, quant settings, scratch files).
    # git refuses to rebase over it, so park it in a stash, sync, and put it back. Without this
    # the node can sit permanently diverged (2026-11-02: ahead/behind 6/8 with the only blocker
    # being quant/.codely-cli/settings.json). A failed pop is logged, never fatal -- the work is
    # still in the stash for a human to recover.
    parked = False
    try:
        left = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                              capture_output=True, text=True, timeout=60,
                              encoding="utf-8", errors="replace").stdout or ""
        if any(ln.strip() and not ln.startswith("??") for ln in left.splitlines()):
            rc_s, _ = run_msg(["git", "stash", "push", "-m", "auto-sync-bm-c"], 120)
            parked = rc_s == 0
            if parked:
                note("parked local edits in stash before rebase")
    except Exception:
        pass
    # 禁 rebase 硬律（2026-11-04 事故）：多机同推时 rebase 会把共享工作树卡在中段，
    # 冲突标记留在队列里，读队列的脚本 try/except 跳过坏行 → 静默少看卡。
    # 这里改成 merge --ff-only：能快进就快进，不能就让主控去收，绝不重放提交。
    rc3, full3 = git_full(["git", "fetch", "origin"], 120)
    rc3, full3 = git_full(["git", "merge", "--ff-only", "origin/main"], 180)
    tail3 = full3.replace("\n", " | ")[:240]
    if rc3 != 0 and "would be overwritten by checkout" in full3:
        moved = stash_untracked_collisions(full3)
        note("moved %d untracked collisions aside, retrying merge" % moved)
        rc3, full3 = git_full(["git", "merge", "--ff-only", "origin/main"], 180)
        tail3 = full3.replace("\n", " | ")[:240]
    if rc3 == 0:
        # 2026-11-04 poison guard: never publish a tree that still carries conflict markers.
        rc_pg, out_pg = git_full(["git", "grep", "-l", "^<<<<<<<", "--", "cph4/fleet/"], 60)
        if rc_pg == 0:
            note("POISON-GUARD: conflict markers in tree, push suppressed: %s"
                 % out_pg.replace("\n", " | ")[:200])
        else:
            run_msg(["git", "push", "origin", "HEAD:main"], 120)
    if parked:
        rc_p, _ = run_msg(["git", "stash", "pop"], 120)
        if rc_p != 0:
            note("stash pop conflicted; local edits kept in stash")
    note("ff-only blocked (%s) -> cleared %d gen-state -> rebase rc=%s %s"
         % (tail, len(cleared), rc3, tail3))
    if rc3 != 0:
        # R2.60: git's refusal message is truncated to 240 chars and names only the first few
        # colliding paths, so a 22-file dirty tree looked like a 4-file problem and every shift
        # re-diagnosed it from scratch. Log the whole remaining set: whatever is here is either
        # work that exists nowhere else (resolve it) or machine state missing from GEN_STATE.
        rc_s, dirty = run_msg(["git", "status", "--porcelain"], 60)
        blocked = [ln[3:] for ln in dirty.split("|") if ln.strip()]
        note("blocking paths (%d): %s" % (len(blocked), ", ".join(blocked)[:900]))
    return rc3


def note(msg, fname="agent-pull.log"):
    """Evidence line; media/ is gitignored so this never dirties the tree."""
    try:
        d = os.path.join(ROOT, "media", "logs")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, fname), "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg))
    except Exception:
        pass


def push():
    """R2.59: the pull leg had no counterpart. Lane/night rounds commit work locally and it
    never left the box, so every `reset --mixed origin/main` closeout (R2.54/R2.56/R2.57)
    silently destroyed that work -- 4 night-round commits sat unpushed for 70 minutes on
    11-01 and were one closeout away from being lost.

    Safety: never force, and only push after a rebase has proven the branch is origin/main
    plus our commits (an append). A diverged tree that will not rebase is left alone and the
    skip is logged, so a broken worktree can never overwrite the master's history."""
    # 2026-11-05 根因修复（bm-b 实锚·v3 定稿）：ff-only 拉取成功时，工作树里的自有面改动
    # （回执 / lane 副本 / 状态件删除——含 need-work 撤标）原样躺着永不提交——
    # bm-b 的 60+ 份回执滞留本地一整天、远端 need-work 死旗不撤，主控对 bm-b 实况半盲。
    # v1 逐路径收集撞中文八进制转义；v2 前缀法撞稀疏锥外+ignore 规则；v3=前缀式
    # add -A --sparse -f（--sparse 让锥外自有件可入索引；-f 穿 state/ 的 ignore；
    # 拉取面只物化本机已提交件=零额外 blob 成本）。队列/申报清单不进这里
    # （行合并走既有专用路径，避免收据被队列冲突扣为人质）。
    try:
        prefixes = list(OUR_OUTPUT) + list(STATE_PREFIXES)
        run_msg(["git", "add", "-A", "-f", "--sparse", "--"] + prefixes, 120)
        rc_d, _ = run_msg(["git", "diff", "--cached", "--quiet"], 60)
        if rc_d != 0:
            run_msg(["git", "commit", "-q", "-m",
                     "state: own deltas (receipts/state/lane) [via agent]",
                     "--"] + prefixes, 120)
            note("committed own deltas before push", "agent-push.log")
    except Exception as e:
        note("own-delta commit skipped: %s" % str(e)[:120], "agent-push.log")
    rc, tail = run_msg(["git", "push", "origin", "HEAD:main"], 300)
    if rc == 0:
        note("ok: %s" % tail, "agent-push.log")
        return 0
    # origin moved under us (the master pulses every minute): re-anchor and retry once.
    run_msg(["git", "fetch", "--quiet", "origin", "main"], 120)
    # 禁 rebase 硬律（2026-11-04）：这里原本 push 失败后 rebase 重放，多机同推时会把
    # 共享工作树卡在中段。改成 ff-only：能快进就快进，不能就如实跳过留给主控收。
    rc1, t1 = run_msg(["git", "merge", "--ff-only", "origin/main"], 180)
    if rc1 != 0:
        note("skip (ff-only merge refused): %s" % t1, "agent-push.log")
        return rc1
    rc2, tail2 = run_msg(["git", "push", "origin", "HEAD:main"], 300)
    note("retry rc=%s %s" % (rc2, tail2), "agent-push.log")
    return rc2


def tick(node, do_push=False, with_pull=False):
    if with_pull:
        pull()
    rc_hb, t_hb = run([PY, "Tools/fleet/fleet_hb.py", "--node", node, "--root", ROOT], 120)
    # Lane intake must re-read origin every cycle. fleet_lane.lane_payload() only runs
    # `git fetch` when asked, and this call used to pass --no-fetch: after the single
    # startup pull the node kept re-reading a frozen origin/main ref, so a lanes/<node>.json
    # the master published minutes later never arrived and the lane reported IDLE forever
    # (2026-11-01 measured: lane file on disk 21:03, agent started 21:52, no intake since).
    rc_ln, t_ln = run([PY, "Tools/fleet/lane_agent.py", "--node", node, "--root", ROOT], 3600)
    t_ps = "-"
    if do_push:
        t_ps = "rc=%s" % push()
    print("agent %s hb=%s(%s) lane=%s(%s) push=%s" % (node, rc_hb, t_hb, rc_ln, t_ln, t_ps))
    return 0 if rc_hb == 0 else 1


def _pid_alive(pid):
    if os.name == "nt":
        try:
            r = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid],
                               capture_output=True, text=True, timeout=30,
                               encoding="utf-8", errors="replace")
            return str(pid) in (r.stdout or "")
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def claim_lock(node):
    """One agent per node. Two claimers on one lane take the same card twice and fight over
    the GPU lease; the master's design is exactly one resident executor per box."""
    path = os.path.join(ROOT, ".codely-cli", "tmp", "agent-%s.lock" % node)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    pid = int((f.read().split() or ["0"])[0])
            except Exception:
                pid = 0
            if pid and pid != os.getpid() and _pid_alive(pid):
                return None
        with open(path, "w", encoding="utf-8") as f:
            f.write("%d %d" % (os.getpid(), int(time.time())))
    except Exception:
        return None
    return path


def touch_lock(path):
    # fleet_hb.self_bootstrap() reads this file's mtime as "a live agent owns the node";
    # refreshing it each tick is what stops it from spawning a second agent.
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("%d %d" % (os.getpid(), int(time.time())))
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--loop", type=int, default=0, help="0 = one tick; N = every N seconds")
    ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--pull-every", type=int, default=5,
                    help="in --loop mode, pull once every N ticks (default 5 = 5 min)")
    ap.add_argument("--push", action="store_true",
                    help="push locally authored commits after each tick (append-only; see push())")
    a = ap.parse_args()
    lock = None
    if a.loop:
        lock = claim_lock(a.node)
        if lock is None:
            print("agent %s already running (lock held) - this instance exits" % a.node)
            return 0
    if not a.loop:
        return tick(a.node, a.push, with_pull=not a.no_pull)
    every = max(1, a.pull_every)
    i = 0
    while True:
        try:
            tick(a.node, a.push, with_pull=(not a.no_pull) and i % every == 0)
        except Exception as e:  # a crashed tick must not kill the resident agent
            print("agent %s tick error: %s" % (a.node, str(e)[:200]))
        touch_lock(lock)
        i += 1
        time.sleep(a.loop)


if __name__ == "__main__":
    sys.exit(main())