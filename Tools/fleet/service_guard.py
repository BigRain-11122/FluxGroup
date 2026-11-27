#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""service_guard.py - 保证"该跑的都跑着"：缺了就拉起，超时就重启。

2026-11-10 CEO：之前安排给本地智能体的任务，要开始走本地模型、不间断自动化。
本件只做一件事：把 launchd 里的自动化看住，别让某一条悄悄停掉。
  - 期望集 = ~/Library/LaunchAgents/com.fluxgroup.*.plist
  - 未加载 -> launchctl bootstrap（立刻拉起来）
  - 有产物且超期 -> launchctl kickstart -k（重启一次）
  - 结果写 state/services.json
用法：python3 Tools/fleet/service_guard.py [--apply]
"""
import argparse
import glob
import json
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
OUT = os.path.join(STATE, "services.json")
LA = os.path.expanduser("~/Library/LaunchAgents")
UID = os.getuid()

# 有明确产物的任务：超期就重启（秒）
ARTIFACTS = {
    "com.fluxgroup.pulse": ("cph4/fleet/dispatcher/PULSE.json", 900),
    "com.fluxgroup.statesync": ("cph4/fleet/state/state-sync.json", 900),
    "com.fluxgroup.localworker": ("cph4/fleet/state/local-digest.jsonl", 900),
    "com.fluxgroup.patrolseats": ("cph4/fleet/state/patrol-local.json", 1800),
    "com.fluxgroup.auditor": ("cph4/fleet/state/local-audit.jsonl", 1800),
    "com.fluxgroup.selfdrive": ("cph4/fleet/PRODUCTION-BACKLOG.jsonl", 3600),
    "com.fluxgroup.capabilities": ("cph4/fleet/state/capabilities.json", 1800),
}


def loaded():
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=10).stdout
        return {l.split("\t")[2] for l in out.splitlines() if "com.fluxgroup." in l}
    except Exception:
        return set()


def age(p):
    try:
        return time.time() - os.path.getmtime(os.path.join(ROOT, p))
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    have = loaded()
    expected = sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(LA, "com.fluxgroup.*.plist")))
    rows, healed = [], []
    for lab in expected:
        plist = os.path.join(LA, lab + ".plist")
        row = {"label": lab, "loaded": lab in have}
        if lab not in have and a.apply:
            r = subprocess.run(["launchctl", "bootstrap", "gui/%d" % UID, plist], capture_output=True)
            row["action"] = "bootstrap rc=%s" % r.returncode
            healed.append(lab)
        if lab in ARTIFACTS:
            p, limit = ARTIFACTS[lab]
            ag = age(p)
            row["artifact_age_s"] = None if ag is None else round(ag)
            if ag is not None and ag > limit and a.apply:
                r = subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/%s" % (UID, lab)], capture_output=True)
                row["action"] = (row.get("action") or "") + " kickstart rc=%s" % r.returncode
                healed.append(lab)
        rows.append(row)
    os.makedirs(STATE, exist_ok=True)
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "expected": len(expected),
               "loaded": sum(1 for r in rows if r["loaded"]), "healed": healed, "services": rows},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("services %d/%d loaded; healed=%s" % (sum(1 for r in rows if r["loaded"]), len(expected), healed))
    return 0


if __name__ == "__main__":
    main()
