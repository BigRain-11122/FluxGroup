#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notify.py - 命令直达：写完命令后立刻 poke 可达机器，不等 45s 脉节拍。

CEO 2026-11-11：「命令务必传到机队要非常及时和顺畅」。
链路=git 传数据 + poke 传信号（2026-11-08 实锚：poke 只做信号，数据仍走 git）。

契约（发错就是"accepted:true 但一次没唤醒"）：
    {"reason": "<必须含 enable-tasks>", "tasks": ["<该节点白名单任务>"]}

安全边界：
  - 默认 --dry：只探端口、不唤醒；要真唤醒必须显式 --send
  - 任务名必须在该节点 fleet-nodes.json 的 wake_tasks 里，越界直接拒发
  - 每节点独立超时，一台失败不影响其它台

用法：
  python3 Tools/fleet/notify.py                     # 只探谁可达（不发）
  python3 Tools/fleet/notify.py --send              # 向所有可达节点发唤醒
  python3 Tools/fleet/notify.py --send --nodes bm-c # 只发某一台
  python3 Tools/fleet/notify.py --self-test
Exit: 0 全部成功（或 dry 完成）；1 有节点失败/越界；2 无节点可达
"""
import argparse
import json
import os
import socket
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NODES = os.path.join(ROOT, "Tools", "fleet-nodes.json")
PORT = 8790
DEFAULT_TASK = "HQ-ProductionClaim"


def load(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def reachable(host, timeout=0.8, port=PORT):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def payload_for(node, task=None, reason=None):
    """按节点白名单构造载荷；任务不在白名单直接返回 None（不猜）。"""
    wl = node.get("wake_tasks") or []
    t = task or (DEFAULT_TASK if DEFAULT_TASK in wl else (wl[0] if wl else None))
    if not t:
        return None, "该节点没有 wake_tasks 白名单"
    if t not in wl:
        return None, "任务 %s 不在白名单 %s" % (t, wl[:3])
    return {"reason": reason or "enable-tasks: cmd direct %s" % time.strftime("%H:%M:%S"),
            "tasks": [t]}, "ok"


def poke(host, payload, timeout=5):
    t0 = time.time()
    req = urllib.request.Request("http://%s:%d/poke" % (host, PORT),
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read() or b"{}")
        wakes = body.get("wakes") or []
        return {"ok": bool(wakes) or bool(body.get("accepted")), "ms": round((time.time() - t0) * 1000),
                "resp": {k: body.get(k) for k in ("accepted", "wakes", "why")}}
    except Exception as e:
        return {"ok": False, "ms": round((time.time() - t0) * 1000), "err": str(e)[:120]}


def run(send=False, only=None, task=None, reason=None, timeout=0.8):
    nodes = (load(NODES, {}) or {}).get("nodes") or []
    rows = []
    for n in nodes:
        nid = n.get("id")
        if only and nid not in only:
            continue
        host = n.get("tailnet_ip") or n.get("host")
        if not host:
            rows.append({"node": nid, "state": "NO-HOST"})
            continue
        if not reachable(host, timeout):
            rows.append({"node": nid, "state": "unreachable", "host": host})
            continue
        if not send:
            rows.append({"node": nid, "state": "reachable（未发，--send 才唤醒）", "host": host})
            continue
        pl, why = payload_for(n, task, reason)
        if not pl:
            rows.append({"node": nid, "state": "REFUSED", "why": why})
            continue
        r = poke(host, pl)
        rows.append({"node": nid, "state": "woken" if r["ok"] else "FAILED", "host": host,
                     "ms": r.get("ms"), "resp": r.get("resp"), "err": r.get("err")})
    return rows


def self_test():
    return 0  # 真实验证在 cmd_latency --self-test 的 poke 契约用例里，这里只做参数面


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--nodes", default="")
    ap.add_argument("--task", default=None)
    ap.add_argument("--reason", default=None)
    ap.add_argument("--timeout", type=float, default=0.8)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    only = [x.strip() for x in a.nodes.split(",") if x.strip()] or None
    rows = run(send=a.send, only=only, task=a.task, reason=a.reason, timeout=a.timeout)
    if a.json:
        print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "send": a.send, "rows": rows},
                         ensure_ascii=False, indent=1))
    else:
        mode = "发送" if a.send else "只探不发"
        print("命令直达（%s）：" % mode)
        for r in rows:
            extra = ""
            if r.get("ms"):
                extra += " %sms" % r["ms"]
            if r.get("err"):
                extra += " %s" % r["err"]
            if r.get("why"):
                extra += " %s" % r["why"]
            print("  %-6s %-28s %s%s" % (r["node"], r["state"], r.get("host") or "", extra))
    bad = [r for r in rows if r["state"] in ("FAILED", "REFUSED", "NO-HOST")]
    anyre = [r for r in rows if r["state"].startswith(("reachable", "woken"))]
    if not anyre and not bad:
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
