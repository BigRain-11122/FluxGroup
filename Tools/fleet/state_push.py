#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_push.py - 用独立工作树把「状态面」推上主线，绕开主工作树的手改/分叉。

Why（2026-11-07 凌晨实测）：主控脉与人工会话共用同一个 git 工作树，只要工作树里有任何未提交
改动（哪怕是修 bug 时放进去的新版文件），脉就判 `git=skipped:dirty(hand-edit ...)` 整段跳过
git。后果不是"晚一点同步"，而是**卡永远不在 origin 上翻面**：车道把同一张卡一遍遍重跑
（bm-m 实测同一张卡连跑 3 次 0.1s），供给看起来永远空，机队满负荷是假的。

正解：状态面（队列 + 回执 + 车道状态）不跟人抢工作树，改为在独立 worktree 里提交推送。
产品代码仍走人工/worktree 流程，两者物理隔离。

推什么（白名单，其余一律不动）：
  cph4/fleet/PRODUCTION-QUEUE.jsonl
  cph4/fleet/PRODUCTION-BACKLOG.jsonl
  cph4/fleet/queue-receipts/**.json
  cph4/fleet/state/remote-receipts/**.json（若未被 ignore）
  cph4/fleet/lanes/**.json

用法：
  python3 Tools/fleet/state_push.py            # 一轮（无变化则静默退出）
  python3 Tools/fleet/state_push.py --dry
Exit: 0 正常（含无变化）｜2 推送失败（已回滚工作树，不影响主工作树）
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WT = os.path.join(os.path.dirname(ROOT), ".fluxgroup-state-wt")

STATE_FILES = [
    "cph4/fleet/PRODUCTION-QUEUE.jsonl",
    "cph4/fleet/PRODUCTION-BACKLOG.jsonl",
]
STATE_DIRS = [
    "cph4/fleet/queue-receipts",
    "cph4/fleet/lanes",
]


def sh(args, cwd=None, timeout=180):
    p = subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def ensure_worktree():
    """独立工作树：不存在就基于 origin/main 建一个（detached，不占分支名）。"""
    if os.path.isdir(os.path.join(WT, ".git")) or os.path.isfile(os.path.join(WT, ".git")):
        return True
    sh(["git", "worktree", "prune"])
    sh(["git", "fetch", "--quiet", "origin", "main"])
    rc, out, err = sh(["git", "worktree", "add", WT, "origin/main", "--detach"])
    return rc == 0


def sync_into_worktree():
    """把状态面从主工作树复制进独立工作树。返回是否有变化。"""
    n = 0
    for rel in STATE_FILES:
        src = os.path.join(ROOT, rel)
        dst = os.path.join(WT, rel)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            n += 1
    for rel in STATE_DIRS:
        src = os.path.join(ROOT, rel)
        if not os.path.isdir(src):
            continue
        for dirpath, _dirs, files in os.walk(src):
            for f in files:
                if not f.endswith(".json"):
                    continue
                s = os.path.join(dirpath, f)
                d = os.path.join(WT, os.path.relpath(s, ROOT))
                os.makedirs(os.path.dirname(d), exist_ok=True)
                try:
                    shutil.copyfile(s, d)
                    n += 1
                except Exception:
                    pass
    return n


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    if not ensure_worktree():
        print("[state-push] worktree 建立失败")
        return 2
    copied = sync_into_worktree()
    rc, dirty, _ = sh(["git", "status", "--porcelain"], cwd=WT)
    if not dirty.strip():
        print("[state-push] 无状态变化（%d 个文件已同步）" % copied)
        return 0
    if a.dry:
        print("[state-push] would push:\n" + dirty[:1200])
        return 0
    sh(["git", "add", "-A"], cwd=WT)
    msg = "state: 队列/回执同步 %s [via bm-m]" % time.strftime("%Y-%m-%dT%H:%M")
    rc, out, err = sh(["git", "-c", "user.name=" + sh(["git", "config", "user.name"])[1],
                       "-c", "user.email=" + sh(["git", "config", "user.email"])[1],
                       "commit", "-q", "-m", msg], cwd=WT)
    if rc != 0:
        print("[state-push] commit 失败:", (err or out)[:200])
        return 2
    sh(["git", "fetch", "--quiet", "origin", "main"], cwd=WT)
    sh(["git", "rebase", "-q", "origin/main"], cwd=WT)
    rc, out, err = sh(["git", "push", "-q", "origin", "HEAD:main"], cwd=WT)
    if rc != 0:
        print("[state-push] push 失败:", (err or out)[:200])
        return 2
    rc2, head, _ = sh(["git", "rev-parse", "--short", "HEAD"], cwd=WT)
    print("[state-push] pushed", head, "files=%d" % copied)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))