#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fluxctl.py - 一个入口看全盘子。实验室交付的第一件内部工具（2026-11-02）。

为什么：此前要看状态得跑五六个脚本（comms/invariants/checkups/metrics/showcase），
每条线还要自己找对应闸。这里合成三条命令：
  flux status            一屏：机器、队列、断言、体检、债
  flux check <线>        跑这条线的体检单
  flux gate <线> <文件>  跑这条线的闸（内容/游戏/策略）
  flux chief             看一眼总管今天的决定与早报

用法：python3 fluxctl.py status|check|gate|chief [...]
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def run(script, *args):
    p = os.path.join(HERE, script)
    return subprocess.run([sys.executable, p] + list(args), capture_output=True, text=True)


def status():
    inv = jload(os.path.join(STATE, "invariants.json"), {}) or {}
    com = jload(os.path.join(STATE, "comms.json"), {}) or {}
    ck = jload(os.path.join(STATE, "checkups.json"), {}) or {}
    met = jload(os.path.join(STATE, "metrics.json"), {}) or {}
    red = [(c["id"], c["count"]) for c in (inv.get("checks") or []) if c.get("count")]
    print("=== 盘子")
    q = com.get("queue") or {}
    print("队列：在飞 %s ｜ 待领 %s ｜ 已完成 %s" % (q.get("running"), q.get("open"), q.get("cards_done")))
    print("断言：%s ｜ 红 %d 项 %s" % (inv.get("verdict"), len(red),
                                     ",".join("%s x%s" % r for r in red[:5]) or "-"))
    bad_ck = [r for r in (ck.get("lines") or []) if r.get("status") == "FAIL"]
    print("体检：不合格 %d 条 %s" % (len(bad_ck), "、".join(r["line"] for r in bad_ck[:5]) or "-"))
    if met.get("debt") is not None:
        print("结构债：%s 条（降 %s%%）" % (met.get("debt"), met.get("debt_drop_pct")))
    print("=== 机器")
    for n in com.get("nodes") or []:
        print("  %-10s %-8s %-8s %s" % (n.get("name"), "在线" if n.get("online") else "离线",
                                        (n.get("job") or "-")[:24],
                                        "、".join(n.get("flags") or []) or "正常"))
    return 0


def check(line):
    r = run("checkups.py", "--line", line)
    print(r.stdout.strip() or r.stderr.strip())
    return r.returncode


def gate(line, path):
    kind = {"bigstream-mv": "drama", "bigstream-duanju": "drama", "bigstream-drama": "drama",
            "biggame": "game", "bigmoney": "strategy"}.get(line)
    if not kind:
        print("这条线没有对应闸：%s（内容→drama，游戏→game，策略→strategy）" % line)
        return 2
    r = run("line_gate.py", kind, path)
    print(r.stdout.strip() or r.stderr.strip())
    return r.returncode


def chief():
    p = os.path.join(FLEET, "chief")
    if os.path.isdir(p):
        briefs = sorted([n for n in os.listdir(p) if n.startswith("BRIEF-")])
        if briefs:
            print(open(os.path.join(p, briefs[-1]), encoding="utf-8").read())
            return 0
    print("还没有早报")
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    c = argv[0]
    if c == "status":
        return status()
    if c == "check" and len(argv) > 1:
        return check(argv[1])
    if c == "gate" and len(argv) > 2:
        return gate(argv[1], argv[2])
    if c == "chief":
        return chief()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))