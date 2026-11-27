#!/usr/bin/env python3
"""prechange.py - 动手前同步闸（CEO 2026-11-18 令「每次动手改之前都要更新 git，然后再去做」）。

只做一件事：告诉你现在能不能直接改文件，不能的话给出一条可执行的路。
默认只读（只 fetch + 统计），不改工作树、不改分支。

用法：
    python Tools/fleet/prechange.py                 # 体检并给结论
    python Tools/fleet/prechange.py --worktree ts   # 需要改文件时，建一个对齐的工作树 _wt-ts
    python Tools/fleet/prechange.py --json          # 机读输出

退出码：
    0  READY      已对齐，可以直接改
   10  SYNC       落后但本地无自己的提交 -> 可以先快进/收口
   20  WORKTREE   分叉或有未提交改动 -> 必须用隔离工作树改（人/代理都一样）
   30  FAIL       git 不可用或 fetch 失败（不许在不确定状态下动手）
"""
import argparse
import json
import os
import subprocess
import sys
import time


def git(root, *args, timeout=300):
    try:
        p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return 1, "", str(exc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--worktree", default=None, help="需要改文件时，按这个名字建对齐工作树")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    rc, branch, _ = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if rc != 0:
        print("FAIL: not a git repo: %s" % root)
        return 30

    rc, _, err = git(root, "fetch", "origin", "--prune") if args.worktree else git(root, "fetch", "origin")
    fetch_rc = rc
    rc2, counts, _ = git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main")
    ahead = behind = None
    if rc2 == 0 and counts:
        parts = counts.split()
        if len(parts) == 2:
            ahead, behind = int(parts[0]), int(parts[1])
    _, porc, _ = git(root, "status", "--porcelain")
    lines = [x for x in (porc or "").splitlines() if x.strip()]
    dirty = sum(1 for x in lines if not x.startswith("??"))
    untracked = len(lines) - dirty

    rep = {"root": root, "branch": branch, "ahead": ahead, "behind": behind,
           "dirty_tracked": dirty, "untracked": untracked,
           "fetch_rc": fetch_rc, "fetch_err": (err or "")[-300:] if fetch_rc else ""}

    if fetch_rc != 0:
        rep["verdict"] = "FAIL"
        rep["advice"] = "fetch 失败：网络或凭据问题。不许在状态不明时改文件。"
        code = 30
    elif ahead == 0 and behind == 0 and dirty == 0:
        rep["verdict"] = "READY"
        rep["advice"] = "已与 origin/main 对齐、工作树干净，可以直接改。"
        code = 0
    elif dirty == 0 and ahead == 0 and behind > 0:
        rep["verdict"] = "SYNC"
        rep["advice"] = "落后 %d 个提交且无本地提交：先 git merge --ff-only origin/main 再动手。" % behind
        code = 10
    else:
        rep["verdict"] = "WORKTREE"
        rep["advice"] = ("分叉(ahead=%s behind=%s)或工作树有 %d 个已改文件："
                         "禁止在本工作树改，用隔离工作树。" % (ahead, behind, dirty))
        code = 20

    wt_path = None
    if args.worktree:
        name = args.worktree if args.worktree.startswith("_wt-") else "_wt-" + args.worktree
        wt_path = os.path.join(root, name)
        if os.path.exists(wt_path):
            rep["worktree_exists"] = True
        else:
            rc, out, werr = git(root, "worktree", "add", name, "--detach", "origin/main")
            rep["worktree_exists"] = rc == 0
            if rc != 0:
                rep["worktree_err"] = werr[-300:]
        rep["worktree_path"] = wt_path

    rep["next_actions"] = {
        "READY": ["直接改文件", "改完 git add <点名文件> && commit && push origin HEAD:main"],
        "SYNC": ["git merge --ff-only origin/main", "再跑本命令确认 READY"],
        "WORKTREE": [
            "python Tools/fleet/prechange.py --worktree <名字>",
            "在该工作树里改文件（不要动主工作树）",
            "git -C _wt-<名字> add <点名文件> && commit",
            "git -C _wt-<名字> push origin HEAD:main",
            "git worktree remove _wt-<名字> --force",
        ],
        "FAIL": ["先修网络/凭据", "再跑本命令"],
    }[rep["verdict"]]

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print("verdict : %s" % rep["verdict"])
        print("state   : branch=%s ahead=%s behind=%s dirty=%d untracked=%d"
              % (branch, ahead, behind, dirty, untracked))
        print("advice  : %s" % rep["advice"])
        if wt_path:
            print("worktree: %s (%s)" % (wt_path, "ready" if rep.get("worktree_exists") else "FAILED"))
        print("next    :")
        for a in rep["next_actions"]:
            print("  - %s" % a)
        print("checked : %s  (node=%s)" % (time.strftime("%Y-%m-%d %H:%M:%S"),
                                           os.environ.get("COMPUTERNAME", "?")))
    return code


if __name__ == "__main__":
    sys.exit(main())
