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
    # 顺序很重要：先把工作树对齐到最新 origin，再复制状态面，再提交推送。
    # 反过来（先复制再 rebase）在有并发推送时必然冲突——队列是 append log，同一行必撞。
    copied = 0
    for attempt in range(1, 5):
        sh(["git", "fetch", "--quiet", "origin", "main"], cwd=WT)
        sh(["git", "reset", "-q", "--hard", "origin/main"], cwd=WT)
        copied = sync_into_worktree()
        rc, dirty, _ = sh(["git", "status", "--porcelain"], cwd=WT)
        if not dirty.strip():
            # 2026-11-08 假绿修复：状态面没变化 ≠ 已同步。以前到这里直接 return 0，
            # 而主工作树可能有未推的提交（实测：报"1429 个文件已同步"，实际本地领先
            # origin 2 个提交、机队拿不到新代码/新卡）——ops_metrics 的"同步成功 0%"就是这个。
            rc, ahead, _ = sh(["git", "rev-list", "--count", "origin/main..HEAD"], cwd=ROOT)
            rc2, behind, _ = sh(["git", "rev-list", "--count", "HEAD..origin/main"], cwd=ROOT)
            try:
                n_ahead, n_behind = int((ahead or "0").strip()), int((behind or "0").strip())
            except Exception:
                n_ahead = n_behind = 0
            if n_ahead and not n_behind:
                if a.dry:
                    print("[state-push] would push %d pending commit(s)" % n_ahead)
                    return 0
                rc3, out3, err3 = sh(["git", "push", "-q", "origin", "HEAD:main"], cwd=ROOT)
                if rc3 == 0:
                    print("[state-push] 补推 %d 个未推提交（状态面本已同步，%d 个文件）"
                          % (n_ahead, copied))
                    return 0
                print("[state-push] 补推失败(%d 提交):%s" % (n_ahead, (err3 or out3)[:160]))
                return 2
            if n_ahead and n_behind:
                # 既领先又落后：不在共享工作树里 rebase（会与脉/并发车道抢树），显式报出。
                print("[state-push] DIVERGED 本地领先 %d / 落后 %d，未自动处理"
                      % (n_ahead, n_behind))
                return 2
            print("[state-push] 无状态变化（%d 个文件已同步）" % copied)
            return 0
        if a.dry:
            print("[state-push] would push:\n" + dirty[:1200])
            return 0
        sh(["git", "add", "-A"], cwd=WT)
        name = sh(["git", "config", "user.name"])[1] or "fleet"
        mail = sh(["git", "config", "user.email"])[1] or "fleet@local"
        msg = "state: 队列/回执同步 %s [via bm-m]" % time.strftime("%Y-%m-%dT%H:%M")
        rc, out, err = sh(["git", "-c", "user.name=" + name, "-c", "user.email=" + mail,
                           "commit", "-q", "-m", msg], cwd=WT)
        if rc != 0:
            print("[state-push] commit 失败:", (err or out)[:160])
            return 2
        rc, out, err = sh(["git", "push", "-q", "origin", "HEAD:main"], cwd=WT)
        if rc == 0:
            head = sh(["git", "rev-parse", "--short", "HEAD"], cwd=WT)[1]
            print("[state-push] pushed", head, "files=%d attempt=%d" % (copied, attempt))
            return 0
        time.sleep(2)
    print("[state-push] push 失败（4 次，并发推送太密）")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))