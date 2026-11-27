#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ack_write.py - 写命令回执（每令每机一个文件，法条：cph4/fleet/cmd/<id>.<node>.ack.json）。

为什么单独成件（2026-11-03）：回执写入原本要内联在 .cmd 的一行 python -c 里，批处理的
百分号转义一改就炸，且换台机器没法验证。回执是命令闭环的唯一凭据，必须能被单独跑、
单独验。

用法：
  python3 ack_write.py --id OB-20261103-1230-REMOTE-EXEC-REPAIR --node bm-b --rc 0
Exit: 0 回执已写；1 参数缺失或目录不可写。
"""
import argparse
import json
import os
import platform
import socket
import sys
import time


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--node", required=True)
    ap.add_argument("--rc", type=int, default=-1)
    ap.add_argument("--note", default="")
    ap.add_argument("--log", default="")
    ap.add_argument("--root", default="")
    a = ap.parse_args(argv)

    root = a.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    outdir = os.path.join(root, "cph4", "fleet", "cmd")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "%s.%s.ack.json" % (a.id, a.node))
    rec = {
        "id": a.id,
        "lane": a.node,
        "ack_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "rc": a.rc,
        "verdict": "OK" if a.rc == 0 else "FAILED",
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "repo": root,
        "log": a.log,
        "note": a.note,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
    except OSError as e:
        print("ack 写不了：%s" % e)
        return 1
    print("ack -> %s (rc=%d %s)" % (path, a.rc, rec["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))