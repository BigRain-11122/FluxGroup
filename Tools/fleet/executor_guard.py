#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""executor_guard.py - 主控侧执行器守护：被禁就受控启用，别等人去 poke。

Why（2026-11-06 夜实测）：bm-c 的 HQ-ProductionClaim 被受控启用成 Running 之后，二十多分钟
又被某个本机机制禁回 Disabled，机队随即停产——而主控这一侧没有任何角色负责"发现被禁并
重新启用"，只能靠人记得再 poke 一次。停产一整夜的成本远高于多跑一次幂等检查。

边界（三条，缺一条就是越权）：
  1. 只处理 roster 里 `enable_tasks` 明示的任务——绝不扩大到别的任务；
  2. CEO 让路态（AUTONOMY-CONFIG nodes.<id>.paused_by_ceo）期间整台机跳过；
  3. 只调既有的大众入口 /poke（reason 必含 enable-tasks 才会启用），不碰 OS、不杀进程。

用法：
  python3 Tools/fleet/executor_guard.py            # 一轮
  python3 Tools/fleet/executor_guard.py --dry      # 只报不动
Exit: 0 正常（含无事可做）｜2 全部节点不可达
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "state", "executor-guard.jsonl")
sys.path.insert(0, HERE)


def http(url, data=None, timeout=25):
    try:
        req = urllib.request.Request(url, data=(json.dumps(data).encode() if data else None),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"err": str(e)[:80]}


def roster():
    try:
        d = json.load(open(os.path.join(ROOT, "Tools", "fleet-nodes.json"), encoding="utf-8-sig"))
        return {n.get("id"): n for n in (d.get("nodes") or []) if n.get("id")}
    except Exception:
        return {}


def paused():
    try:
        d = json.load(open(os.path.join(ROOT, "cph4", "fleet", "AUTONOMY-CONFIG.json"),
                           encoding="utf-8"))
        return {k for k, v in (d.get("nodes") or {}).items()
                if isinstance(v, dict) and v.get("paused_by_ceo")}
    except Exception:
        return set()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    nodes = roster()
    skip = paused()
    rows, reachable = [], 0
    for nid, n in nodes.items():
        if not n.get("enabled"):
            continue
        want = [str(x) for x in (n.get("enable_tasks") or [])]
        if not want:
            continue
        if nid in skip:
            rows.append({"node": nid, "action": "skip-ceo-pause", "tasks": want})
            continue
        code, st = http("http://%s:8790/status" % nid, timeout=30)
        if code != 200:
            rows.append({"node": nid, "action": "unreachable", "code": code})
            continue
        reachable += 1
        states = (st.get("last_pull") or {}).get("task_states") or {}
        off = [t for t in want if str(states.get(t, "")) == "Disabled"]
        running = [t for t in want if str(states.get(t, "")) in ("Ready", "Running")]
        if not off:
            # 空串 = 该任务不在本机 status stamp 的 task_states 里（stamp 只覆盖 roster 的
            # wake_tasks）。不能把"看不到"记成 OK——那正是 10-31 那次盲区的形状。
            unknown = [t for t in want if not str(states.get(t, ""))]
            rows.append({"node": nid,
                         "action": "unknown-state" if unknown else "ok",
                         "tasks": running or unknown or want})
            continue
        if a.dry:
            rows.append({"node": nid, "action": "would-enable", "tasks": off})
            continue
        # 同样的 ASCII reason：监听器 1.9.7 之前对多字节 body 直接 400。
        code2, j2 = http("http://%s:8790/poke" % nid,
                         {"reason": "master: enable-tasks", "tasks": off}, timeout=60)
        rows.append({"node": nid, "action": "enable-requested" if code2 == 200 else "enable-failed",
                     "tasks": off, "code": code2})
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "rows": rows}
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    acted = [r for r in rows if r["action"] in ("enable-requested", "enable-failed")]
    print("[executor-guard] nodes=%d reachable=%d acted=%d" %
          (len(rows), reachable, len(acted)))
    for r in rows:
        print("  %-6s %-16s %s" % (r["node"], r["action"], ",".join(r.get("tasks") or [])))
    return 0 if reachable or not rows else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))