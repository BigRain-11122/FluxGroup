# -*- coding: utf-8 -*-
"""fleet-sync: 把「控制面」文件从主仓对象直接物化到 FleetRuntime（bm-b 车道运行副本）。

为什么不用稀疏检出：本机 partial clone 逐 blob 经 SSH 代理拉取极慢（单文件一次往返），
主仓已缓存这些对象，直接从主仓 git show 出来是秒级。运行副本不做提交，只跑车道。

用法：python fleet-sync.py [--src C:\\Fluxgroup\\FluxGroup] [--dst C:\\Fluxgroup\\FleetRuntime]
"""
import argparse
import os
import subprocess
import sys

MANIFEST = [
    "Tools/fleet/lane_agent.py",
    "Tools/fleet/fleet_lane.py",
    "Tools/fleet/fleet_hb.py",
    "Tools/fleet/master_agent.py",
    "Tools/fleet/env_selfheal.py",
    "Tools/fleet/gpu_lease.py",
    "Tools/fleet/inventory_guard.py",
    "Tools/backlog_fill.py",
    "Tools/queue_claim.py",
    "cph4/fleet/MODEL-POLICY.json",
    "cph4/fleet/LINE-REGISTRY.json",
    "cph4/fleet/WORK-RULES.jsonl",
    "cph4/fleet/PRODUCTION-BACKLOG.jsonl",
    "cph4/fleet/PRODUCTION-QUEUE.jsonl",
    "cph4/fleet/MASTER-NODE.json",
    "cph4/fleet/dispatcher/MASTER-STATE.json",
    "cph4/fleet/dispatcher/NEED-JUDGMENT.md",
]


def run(args):
    p = subprocess.run(args, capture_output=True)
    return p.returncode, p.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=r"C:\Fluxgroup\FluxGroup")
    ap.add_argument("--dst", default=r"C:\Fluxgroup\FleetRuntime")
    a = ap.parse_args()
    rc, _ = run(["git", "-C", a.src, "fetch", "origin", "main", "--quiet"])
    ok = miss = 0
    for rel in MANIFEST:
        rc, blob = run(["git", "-C", a.src, "show", "origin/main:" + rel])
        if rc != 0:
            print("MISS", rel)
            miss += 1
            continue
        out = os.path.join(a.dst, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(blob)
        ok += 1
    for sub in ("cph4/fleet/lanes", "cph4/fleet/queue-receipts", "cph4/fleet/subco"):
        os.makedirs(os.path.join(a.dst, sub.replace("/", os.sep)), exist_ok=True)
    print("SYNCED %d / missing %d" % (ok, miss))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())