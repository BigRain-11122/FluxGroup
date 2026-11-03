#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""git-rebase-guard.py — 卡死 rebase / 游离 HEAD 自愈闸（T1 工艺面·2026-11-01 R2.56 事件班立）

为什么需要：master_agent.py:push_lane_files() 在 push 失败后 `git rebase --autostash
origin/main`，冲突时只 break、**不 rebase --abort**（受保护件·本闸为外部兜底不改其码）。
后果链：.git/rebase-merge 残留 → HEAD 游离在 origin/main → 每 20min 一轮 master-agent
用 `git commit -- <pathspec>`（rebase 中带 pathspec 的提交被 git 放行）继续往游离 HEAD
叠提交 → 本地永不 pull → 越落越远（2026-10-31 三次实证：93/8、109/8 落后）。

本闸只做一件事：发现「rebase 在途 ≥N 分钟」或「游离 HEAD ≥N 分钟」且无 git 活进程、
无 index.lock 时，先双备份（分支 + patch），再 quit/reset --mixed/checkout -B main 归位。

安全边界：
  * 默认 dry-run，只有 --apply 才动盘。
  * 备份永不省略：backup/bm-a-rebaseguard-<ts> 分支 + .codely-cli/tmp/rebaseguard-<ts>.patch。
  * 不动未跟踪文件；不删 stash；不改受保护脚本（master_agent/steward/L0）。
  * 只认本仓 root 的 .git；不碰其它 worktree。

回滚：git checkout backup/bm-a-rebaseguard-<ts>；或 git apply 对应 patch。
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT_DEFAULT = r"C:\Users\sjs20\Desktop\FluxGroup"
LOG_REL = os.path.join(".codely-cli", "tmp", "git-rebase-guard.log")


def git(root, *a, timeout=120):
    return subprocess.run(["git", "-C", root] + list(a), capture_output=True,
                          timeout=timeout, creationflags=0x08000000)  # CREATE_NO_WINDOW


def out(r):
    return (r.stdout or b"").decode("utf-8", "replace").strip()


def dir_age_min(path):
    """Age of the newest file INSIDE a rebase dir.

    The directory's own mtime is ignored on purpose: git re-creates the dir on every
    attempt, so a fresh dir mtime would mask a rebase that has been stuck for hours.
    Any real progress (conflict resolution, --continue) touches a file inside.
    """
    newest = None
    for dirpath, _dirs, files in os.walk(path):
        for n in files:
            try:
                m = os.path.getmtime(os.path.join(dirpath, n))
                newest = m if newest is None else max(newest, m)
            except OSError:
                pass
    if newest is None:
        newest = os.path.getmtime(path)
    return (time.time() - newest) / 60.0


def rebase_dirs(root):
    g = os.path.join(root, ".git")
    return [os.path.join(g, d) for d in ("rebase-merge", "rebase-apply")
            if os.path.isdir(os.path.join(g, d))]


def live_git_conflict(root):
    """True when another git process holds an index lock (a real operation is in flight)."""
    return os.path.exists(os.path.join(root, ".git", "index.lock"))


def head_state(root):
    br = out(git(root, "rev-parse", "--abbrev-ref", "HEAD"))
    sha = out(git(root, "rev-parse", "HEAD"))
    return br, sha


def log(root, rec):
    path = os.path.join(root, LOG_REL)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def recover(root, reason, dry):
    br, sha = head_state(root)
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup_ref = "backup/bm-a-rebaseguard-" + ts
    rec = {"reason": reason, "head_before": sha, "branch_before": br, "apply": not dry}
    if dry:
        rec["action"] = "DRY-RUN (would backup+quit+reset+reattach)"
        log(root, rec)
        print("DRY " + json.dumps(rec, ensure_ascii=False))
        return 0

    # 1) double backup: branch + patch
    git(root, "branch", backup_ref, sha)
    rec["backup_branch"] = backup_ref
    patch = os.path.join(root, ".codely-cli", "tmp", "rebaseguard-%s.patch" % ts)
    os.makedirs(os.path.dirname(patch), exist_ok=True)
    d = git(root, "diff", "--binary", "origin/main.." + sha)
    with open(patch, "wb") as fh:
        fh.write(d.stdout or b"")
    rec["backup_patch"] = patch
    rec["patch_bytes"] = len(d.stdout or b"")

    # 2) drop the stuck rebase, keep everything reachable via the backup branch
    if rebase_dirs(root):
        git(root, "rebase", "--quit")

    # 3) converge on the authoritative tip, then reattach the branch
    git(root, "fetch", "--quiet", "origin")
    r = git(root, "reset", "--mixed", "origin/main")
    rec["reset_rc"] = r.returncode
    r = git(root, "checkout", "-B", "main")
    rec["reattach_rc"] = r.returncode

    br2, sha2 = head_state(root)
    rec["head_after"] = sha2
    rec["branch_after"] = br2
    lm = out(git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main"))
    rec["vs_origin"] = lm
    try:
        rec["dirty_tracked"] = len([x for x in out(git(root, "status", "--porcelain")).splitlines()
                                    if x[:2].strip() in ("M", "D", "A")])
    except Exception:
        pass
    log(root, rec)
    print(json.dumps(rec, ensure_ascii=False))
    return 0 if rec.get("reattach_rc") == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--min-age-min", type=float, default=15.0)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    if not os.path.isdir(os.path.join(root, ".git")):
        print("SKIP: no .git at " + root)
        return 0
    if live_git_conflict(root):
        print("SKIP: index.lock present (git op in flight)")
        return 0
    # Never recover against a base we cannot resolve: reset would have no target and
    # checkout -B would silently repoint the branch at the stray commit.
    if git(root, "rev-parse", "--verify", "origin/main").returncode != 0:
        print("SKIP: origin/main not resolvable (no remote base to converge on)")
        return 0

    rds = rebase_dirs(root)
    if rds:
        age = min(dir_age_min(p) for p in rds)
        if age >= a.min_age_min:
            return recover(root, "stuck-rebase %.0fmin (%s)" % (age, os.path.basename(rds[0])), not a.apply)
        print("OK: rebase in progress %.0fmin (<%.0fmin threshold)" % (age, a.min_age_min))
        return 0

    # No rebase dir: also catch a long-lived detached HEAD that keeps drifting.
    br, _sha = head_state(root)
    if br == "HEAD":
        out_lr = out(git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main"))
        # How long has HEAD been detached? Reflog "checkout: moving from X to <sha>" is the anchor.
        rl = out(git(root, "reflog", "-1", "--date=unix", "--format=%ct"))
        try:
            age = (time.time() - float(rl)) / 60.0
        except ValueError:
            age = 0.0
        if age >= a.min_age_min:
            return recover(root, "detached-head %.0fmin (%s)" % (age, out_lr), not a.apply)
        print("OK: detached HEAD %.0fmin (<%.0fmin threshold) %s" % (age, a.min_age_min, out_lr))
        return 0

    print("OK: branch=%s, no stuck rebase" % br)
    return 0


if __name__ == "__main__":
    sys.exit(main())