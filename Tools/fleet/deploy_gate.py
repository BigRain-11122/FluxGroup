#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deploy_gate.py - 改完主控代码，先过闸再重启；闸不过就不许上线。

Why (2026-11-02): 我自己两次把主控改成崩溃状态（`cold` 未定义 → 循环崩 2.5h；
`_visible` 用错作用域 → 派单阶段 NameError）。这两次都能被一条 30 秒的闸拦住：
编译不过、模块导入失败、关键工具跑不起来、JSON 坏了 —— 一个都不许进生产。

用法:
  python3 Tools/fleet/deploy_gate.py            # 只检查
  python3 Tools/fleet/deploy_gate.py --restart  # 通过后重启主控脉
"""
import argparse
import glob
import json
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PY = sys.executable
FAIL = []


def step(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, "%s: %s" % (type(e).__name__, str(e)[:120])
    print("%-22s %s %s" % (name, "PASS" if ok else "FAIL", detail or ""))
    if not ok:
        FAIL.append(name)
    return ok


def compile_all():
    bad = []
    for p in glob.glob(os.path.join(ROOT, "Tools", "**", "*.py"), recursive=True):
        try:
            py_compile.compile(p, doraise=True)
        except Exception as e:
            bad.append("%s(%s)" % (os.path.relpath(p, ROOT), str(e).split("\n")[0][:60]))
    return (not bad), ("; ".join(bad[:3]) if bad else "%d files" % len(glob.glob(os.path.join(ROOT, "Tools", "**", "*.py"), recursive=True)))


def import_core():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    mods = ["master_pulse", "master_agent", "lane_agent", "closer", "workgen",
            "night_plan", "brain_brief", "local_judge", "mem_gate", "fleet_lane"]
    bad = []
    for m in mods:
        try:
            __import__(m)
        except Exception as e:
            bad.append("%s(%s)" % (m, str(e)[:60]))
    return (not bad), ("; ".join(bad) if bad else "%d modules" % len(mods))


def json_ok():
    bad = []
    for p in glob.glob(os.path.join(ROOT, "cph4", "fleet", "*.json")) + \
             glob.glob(os.path.join(ROOT, "cph4", "fleet", "dispatcher", "*.json")) + \
             glob.glob(os.path.join(ROOT, "cph4", "fleet", "lines", "*.json")):
        try:
            with open(p, encoding="utf-8-sig") as f:
                json.load(f)
        except Exception as e:
            bad.append("%s(%s)" % (os.path.basename(p), str(e)[:40]))
    return (not bad), ("; ".join(bad[:3]) if bad else "ok")


def agent_dry():
    r = subprocess.run([PY, os.path.join(HERE, "master_agent.py"), "--node", "bm-m",
                        "--root", ROOT, "--dry"], capture_output=True, text=True, timeout=300)
    tail = (r.stdout or r.stderr or "").strip().splitlines()[-1:] or [""]
    return (r.returncode == 0), tail[0][:110]


def brief_runs():
    r = subprocess.run([PY, os.path.join(HERE, "brain_brief.py"), "--root", ROOT],
                       capture_output=True, text=True, timeout=180)
    return (r.returncode == 0), (r.stdout or r.stderr or "").strip()[:110]


def canary_runs():
    """端到端：投一张真卡走完整条链。零件都绿但这条红 = 不许重启。

    2026-11-02 CEO 质问"为什么每次都能发现问题"之后立的唯一验收口径：
    自动化成不成，只看这条链能不能无人值守跑通一次，不看某个函数对不对。
    """
    r = subprocess.run([PY, os.path.join(HERE, "canary.py"), "--force"],
                       capture_output=True, text=True, timeout=180)
    tail = [l for l in (r.stdout or r.stderr or "").strip().splitlines() if l]
    first = tail[0][:110] if tail else ""
    return (r.returncode == 0), first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--restart", action="store_true")
    a = ap.parse_args()
    step("compile", compile_all)
    step("import", import_core)
    step("json", json_ok)
    step("master --dry", agent_dry)
    step("brain_brief", brief_runs)
    step("canary end-to-end", canary_runs)
    if FAIL:
        print("\nGATE BLOCKED: %s —— 不许重启，先修代码" % ",".join(FAIL))
        return 1
    print("\nGATE PASS")
    if a.restart:
        subprocess.run(["launchctl", "kickstart", "-k",
                        "gui/%d/com.fluxgroup.pulse" % os.getuid()], capture_output=True)
        print("pulse restarted")
    return 0


if __name__ == "__main__":
    sys.exit(main())