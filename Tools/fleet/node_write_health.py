#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""node_write_health.py - 区分「推不上来」和「没干活」。

为什么（2026-11-11 实锚）：bm-a 领先 32 个提交、reset 卡连失败、连兜底的 node/<机>
分支都推不上，但它确实在执行任务、产出文件——活全留在本地。主控只看到「ahead 在涨」，
分不清是"机器在干活但推不回来"还是"机器没动"。
回执文件写入是 git 推送成功的直接证据：有在跑的卡、却没有新回执 = 写链路断了。

用法：python3 Tools/fleet/node_write_health.py [--minutes 40] [--json]
Exit: 0 全健康 / 2 有节点写链路可疑
"""
import argparse
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
NODES = ("bm-a", "bm-b", "bm-c")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=40)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = []
    for ln in open(os.path.join(F, "PRODUCTION-QUEUE.jsonl"), encoding="utf-8"):
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass
    cutoff = time.time() - a.minutes * 60
    out = []
    for n in NODES:
        rec = [p for p in glob.glob(os.path.join(F, "queue-receipts", "*-%s.json" % n))
               if os.path.getmtime(p) >= cutoff]
        running = [r["id"] for r in rows if r.get("owner") == n and r.get("state") == "RUNNING"]
        suspect = (not rec) and bool(running)
        out.append({"node": n, "receipts_in_window": len(rec), "running": len(running),
                    "write_suspect": suspect})
    bad = [x["node"] for x in out if x["write_suspect"]]
    if a.json:
        print(json.dumps({"suspect": bad, "nodes": out}, ensure_ascii=False))
    else:
        print("[write-health] 窗口 %d 分钟 · 可疑=%s" % (a.minutes, bad or "无"))
        for x in out:
            print("  %-5s 回执 %2d · 在跑 %2d · %s" % (
                x["node"], x["receipts_in_window"], x["running"],
                "写链路可疑" if x["write_suspect"] else "正常"))
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
