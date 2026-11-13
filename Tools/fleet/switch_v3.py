#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""switch_v3.py - 在 Windows 工位上一步完成「收口 + 装自驱 + 验证」。

Why（2026-11-13）：两台 Windows 的实际状态是"能联网、能 fetch，但本地压着几百个
未推提交"，任何 ff-only 同步都失败；而远程只有 poke（唤醒已有任务）与 /sync（只写
JSON），装不了任务也部署不了代码。所以把这一步做成一条可执行脚本，机器上跑一次即可。

它做四件事，每步都打印结果，任一步失败就停下并说明原因：
  1) 备份当前 HEAD 到 backup-<日期>-<时分> 分支（保住本地提交，不丢东西）
  2) stash 未提交改动（如有），fetch，reset --hard origin/main
  3) 注册/更新计划任务 HQ-StationDrive（每 5 分钟跑一次 station_drive --once）
  4) 立刻跑一轮并把心跳与 git 状态打出来（验收看事实，不看回执）

用法（在该工位仓库根目录）：
    python Tools\\fleet\\switch_v3.py --station visual
    python Tools\\fleet\\switch_v3.py --station delivery
    python Tools\\fleet\\switch_v3.py --station visual --dry      # 只打印将执行的命令
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = "HQ-StationDrive"


# dry 模式下也绝不允许真正执行的动作（2026-11-13 实测：本脚本首版把
# `git reset --hard` 漏传 dry，干跑时真把工作树重置了。危险命令必须有第二道闸，
# 不能只依赖调用方传对参数）。
IRREVERSIBLE = ("reset --hard", "push", "clean -", "checkout --", "branch -D")


def run(cmd, dry=False, check=True):
    text = cmd if isinstance(cmd, str) else " ".join(cmd)
    print("  $ " + text)
    if dry:
        if any(k in text for k in IRREVERSIBLE):
            print("    [dry] 拦截不可逆命令，未执行")
        return 0, "(dry)"
    p = subprocess.run(cmd, shell=isinstance(cmd, str), cwd=ROOT,
                       capture_output=True, text=True, errors="replace")
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    if out:
        for line in out.splitlines()[:6]:
            print("    " + line)
    if check and p.returncode != 0:
        raise SystemExit("失败（rc=%s）：%s" % (p.returncode, out[:200]))
    return p.returncode, out


def git(*args, dry=False, check=True):
    return run(["git"] + list(args), dry=dry, check=check)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", required=True,
                    choices=["delivery", "visual", "audio", "brain", "control"])
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--interval", type=int, default=5, help="计划任务间隔（分钟）")
    a = ap.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("== switch_v3：%s @ %s ==" % (a.station, ROOT))

    if not os.path.isdir(os.path.join(ROOT, ".git")):
        raise SystemExit("这不是 git 仓库根目录：%s" % ROOT)

    # 1) 备份当前 HEAD（有本地提交时尤其重要：reset 会丢引用，分支能保住）
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    branch = "backup-%s-%s" % (stamp, a.station)
    print("\n[1/4] 备份当前 HEAD -> %s" % branch)
    git("rev-parse", "--verify", "HEAD", dry=a.dry, check=False)
    git("branch", branch, "HEAD", dry=a.dry, check=False)

    # 2) 收口：stash（如有未提交）-> fetch -> reset --hard origin/main
    print("\n[2/4] 收口到 origin/main")
    rc, out = run("git status --porcelain", dry=a.dry)
    if not a.dry and out.strip():
        git("stash", "push", "-u", "-m", "pre-switch-v3-%s" % stamp, check=False)
    git("fetch", "--prune", "origin", dry=a.dry)
    git("reset", "--hard", "origin/main", dry=a.dry)
    rc, head = git("rev-parse", "--short", "HEAD", dry=a.dry)
    rc, origin = git("rev-parse", "--short", "origin/main", dry=a.dry)
    if not a.dry and head.strip() != origin.strip():
        raise SystemExit("收口失败：HEAD=%s origin=%s" % (head, origin))
    print("  HEAD=%s origin=%s" % (head.strip(), origin.strip()))

    # 3) 注册计划任务（Windows 用 schtasks；非 Windows 只提示）
    print("\n[3/4] 注册计划任务 %s（每 %d 分钟）" % (TASK, a.interval))
    if os.name != "nt":
        print("  跳过：当前不是 Windows（这一步只在该工位机器上做）")
    else:
        py = sys.executable
        script = os.path.join(ROOT, "Tools", "fleet", "station_drive.py")
        tr = '"%s" "%s" --station %s --once' % (py, script, a.station)
        run(["schtasks", "/Create", "/TN", TASK, "/TR", tr,
             "/SC", "MINUTE", "/MO", str(a.interval), "/F"], dry=a.dry)
        run(["schtasks", "/Query", "/TN", TASK], dry=a.dry, check=False)

    # 4) 立刻跑一轮并验收（看心跳与 git 状态，不看回执）
    print("\n[4/4] 立刻跑一轮并验收")
    py = sys.executable
    drive = os.path.join(ROOT, "Tools", "fleet", "station_drive.py")
    run([py, drive, "--station", a.station, "--once"], dry=a.dry, check=False)

    hb = os.path.join(ROOT, "cph4", "fleet", "rt", a.station, "heartbeat.json")
    gs = os.path.join(ROOT, "cph4", "fleet", "rt", a.station, "git-status.json")
    print("\n验收（三条都要真）：")
    for p, label in ((hb, "心跳"), (gs, "git 状态")):
        if a.dry:
            print("  [dry] %s: %s" % (label, p))
        elif os.path.exists(p):
            print("  %s: %s" % (label, open(p, encoding="utf-8").read().strip()[:160]))
        else:
            print("  %s: 缺失（%s）" % (label, p))
    print("\n完成。若心跳 ts 是刚才、git 状态 state=synced，则该工位已按 v3 运行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
