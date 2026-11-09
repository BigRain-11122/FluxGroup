#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_sync.py - 状态同步面：独立于主控脉的 commit/pull/push。

为什么（2026-11-09 根治）：
  主控脉每拍都要先同步 git（commit 状态 -> pull -> merge），任何一次冲突/脏树
  都会让整拍卡住 2 分钟，自动化等于被 git 绑住。同步不是调度的一部分。
  所以把 git 从脉里拆出来：
    - 脉：只跑阶段（PULSE_NO_PULL=1），永不碰 git；
    - 本件：每 60s 由 launchd 跑一次，失败只记日志 + 熔断，不影响调度。
  跨机可见性靠本件 push/pull；本机最坏晚 60s 看到远端状态，换来电永不被 git 卡死。

用法：python3 Tools/fleet/state_sync.py
退出码：0 同步成功/无变化；1 有失败（已熔断）；2 被熔断跳过。
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
HEALTH = os.path.join(STATE, "state-sync.json")
LOG = os.path.join(STATE, "state-sync.log")
BACKOFF_S = 900
MAX_FAILS = 3


def log(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def sh(args, timeout=90):
    try:
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def health():
    try:
        return json.load(open(HEALTH, encoding="utf-8"))
    except Exception:
        return {"fails": []}


def save(h):
    try:
        os.makedirs(STATE, exist_ok=True)
        json.dump(h, open(HEALTH, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass


def main():
    h = health()
    now = time.time()
    if now < float(h.get("until") or 0):
        return 2
    fails = [x for x in (h.get("fails") or []) if now - x < 1800]

    # 1) 只提交生成态；Tools/ 等手写代码脏了不硬来
    rc, out = sh(["git", "status", "--porcelain"])
    if rc != 0:
        fails.append(now); h["fails"] = fails; h["err"] = out[-200:]; save(h)
        log("status-fail %s" % out[-120:])
        return 1
    dirty = [l[3:] for l in out.splitlines() if l.strip()]
    hand = [p for p in dirty if p.startswith(("Tools/", "docs/"))]
    if hand:
        # 手写代码/正典 dirty：交给人或会话处理，不自动提交
        log("skip: hand-edit %s" % hand[0])
        return 0

    if dirty:
        rc, out = sh(["git", "add", "-A", "cph4/fleet"])
        rc, out = sh(["git", "commit", "-m", "state: sync [via state_sync]"])
        if rc != 0 and "nothing to commit" not in out:
            log("commit-fail %s" % out[-160:])

    # 2) 拉远端（快进优先，分叉用本地优先合并）
    rc, out = sh(["git", "fetch", "--quiet", "origin", "main"])
    if rc != 0:
        fails.append(now); h["fails"] = fails; h["err"] = out[-200:]; save(h)
        log("fetch-fail %s" % out[-160:])
        return 1
    rc, out = sh(["git", "pull", "--ff-only", "--autostash", "origin", "main"])
    if rc != 0:
        rc2, out2 = sh(["git", "merge", "--no-edit", "-X", "ours", "origin/main"])
        if rc2 != 0:
            sh(["git", "merge", "--abort"])
            fails.append(now)
            h["fails"] = fails
            h["err"] = (out + out2)[-200:]
            if len(fails) >= MAX_FAILS:
                h["until"] = now + BACKOFF_S
                log("quarantine %ds after %d fails" % (BACKOFF_S, len(fails)))
            save(h)
            log("merge-fail %s" % (out2 or out)[-160:])
            return 1

    # 3) 推
    rc, out = sh(["git", "push", "origin", "main"])
    if rc != 0:
        log("push-fail %s" % out[-160:])
        fails.append(now); h["fails"] = fails; h["err"] = out[-200:]; save(h)
        return 1

    save({"fails": [], "ok_ts": now})
    return 0


if __name__ == "__main__":
    sys.exit(main())
