#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane_install.py — 按 LOCAL-LANES-v1.json 安装/卸载「一线一进程」的 launchd 作业。

只做三件事：
  install    生成并加载 2 个底座服务 + 5 条线（已存在则先 bootout 再装，不重复）
  uninstall  卸载本节点的全部作业并移走 plist（不删日志与状态，便于复盘）
  status     列出本表作业的加载状态与最近退出码

不碰 disabled/ 里的历史归档，也不碰其他 com.* 作业。

用法：
  python3 Tools/fleet/lane_install.py --install
  python3 Tools/fleet/lane_install.py --status
  python3 Tools/fleet/lane_install.py --kick bili
  python3 Tools/fleet/lane_install.py --uninstall
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CFG_PATH = os.path.join(ROOT, "cph4", "fleet", "LOCAL-LANES-v1.json")
LA = os.path.expanduser("~/Library/LaunchAgents")
LOGDIR = os.path.join(ROOT, ".codely-cli", "state", "lanes")
U = str(os.getuid())
PY = sys.executable


def cfg():
    with open(CFG_PATH, encoding="utf-8") as f:
        return json.load(f)


def launchctl(*args):
    return subprocess.run(["launchctl"] + list(args), capture_output=True, text=True)


def write_plist(label, program, keep_alive=None, interval=None, env=None, nice=True):
    os.makedirs(LA, exist_ok=True)
    os.makedirs(LOGDIR, exist_ok=True)
    log = os.path.join(LOGDIR, label.replace("com.fluxgroup.", "") + ".log")
    d = {
        "Label": label,
        "ProgramArguments": program,
        "WorkingDirectory": ROOT,
        "StandardOutPath": log,
        "StandardErrorPath": log,
        "RunAtLoad": bool(keep_alive),
        "ThrottleInterval": 30,
        "ProcessType": "Background",
        "EnvironmentVariables": env or {},
    }
    if keep_alive:
        d["KeepAlive"] = True
    if interval:
        d["StartInterval"] = int(interval)
    if nice:
        d["LowPriorityIO"] = True
    path = os.path.join(LA, label + ".plist")
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        plistlib.dump(d, f)
    os.replace(tmp, path)
    return path


def install():
    c = cfg()
    py = PY
    made = []
    for b in c.get("base_services") or []:
        prog = [x.format(root=ROOT, venv=os.path.join(ROOT, ".venv-housing")) for x in b["program"]]
        p = write_plist(b["label"], prog, keep_alive=True, env=b.get("env") or {})
        made.append((b["label"], p, "base:" + b["id"]))
    for x in c.get("lanes") or []:
        prog = [py, os.path.join(HERE, "line_runner.py"), "--lane", x["id"]]
        p = write_plist(x["label"], prog, keep_alive=False, interval=x.get("every_s") or 600,
                        env=x.get("env") or {})
        made.append((x["label"], p, "lane:" + x["id"]))
    for label, p, kind in made:
        launchctl("bootout", "gui/%s/%s" % (U, label))
        launchctl("enable", "gui/%s/%s" % (U, label))
        r = launchctl("bootstrap", "gui/%s" % U, p)
        print("%-8s %-34s %s" % ("OK" if r.returncode == 0 else "FAIL", label,
                                 (r.stderr or "").strip()[:80]))
    print("installed %d jobs" % len(made))
    return 0


def uninstall():
    c = cfg()
    labels = [b["label"] for b in c.get("base_services") or []]
    labels += [x["label"] for x in c.get("lanes") or []]
    for label in labels:
        launchctl("bootout", "gui/%s/%s" % (U, label))
        launchctl("disable", "gui/%s/%s" % (U, label))
        p = os.path.join(LA, label + ".plist")
        if os.path.exists(p):
            os.remove(p)
        print("removed", label)
    return 0


def status():
    c = cfg()
    labels = [b["label"] for b in c.get("base_services") or []]
    labels += [x["label"] for x in c.get("lanes") or []]
    out = launchctl("list").stdout
    loaded = {}
    for line in out.splitlines()[1:]:
        p = line.split("\t")
        if len(p) >= 3:
            loaded[p[2]] = {"pid": p[0], "last_exit": p[1]}
    for label in labels:
        v = loaded.get(label)
        print("%-36s %s" % (label, ("pid=%s last_exit=%s" % (v["pid"], v["last_exit"]))
                            if v else "NOT LOADED"))
    return 0


def kick(lane):
    c = cfg()
    label = None
    for x in c.get("lanes") or []:
        if x["id"] == lane:
            label = x["label"]
    if not label:
        print("未知车道 %s" % lane)
        return 2
    r = launchctl("kickstart", "-k", "gui/%s/%s" % (U, label))
    print("kickstart %s rc=%d %s" % (label, r.returncode, (r.stderr or "").strip()[:120]))
    return 0 if r.returncode == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--kick", default="")
    a = ap.parse_args(argv)
    if a.install:
        return install()
    if a.uninstall:
        return uninstall()
    if a.kick:
        return kick(a.kick)
    return status()


if __name__ == "__main__":
    sys.exit(main())
