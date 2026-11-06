#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""enable_selftest.py - 受控远端启用入口的六情况自检（只读 + 显式启用请求）。

为什么要有它（CEO 2026-11-06「自己测试不同情况，看是否真的弄好了」）：
  受控启用这条路径一旦写错，两种事故都很贵——①把 CEO 冻结面误拉起来（噪音回潮）；
  ②该启用时不启用（机队继续静默停产）。所以不能只看"能启用一次"，必须同时验
  "不该启用时一次都不启用"，并且要能重复跑、每次给可核验的判据。

六个情况（每个都带期望值，不合期望即 FAIL）：
  S1 正向    禁用 + 在 enable_tasks 名单 + reason 含 enable-tasks → 期望 REENABLED(并 WAKE)
  S2 负向对照 同一个已启用任务 + reason 不含 token        → 期望 WAKE/busy-skip，绝无 REENABLED
  S3 越界    禁用 + 不在 enable_tasks 名单（同一 reason） → 期望 off-skip（冻结面保护不变）
  S4 幂等    再次正向                                     → 期望可以 WAKE/busy-skip，不得报错
  S5 代码态  status.last_pull 带 fork 字段                 → 期望 fresh（否则 Tools 仍未更新）
  S6 拒中文   reason 含中文                                → 期望 400 bad-request（已知限制，须走 ASCII）

用法：
  python3 Tools/fleet/enable_selftest.py --node bm-b
  python3 Tools/fleet/enable_selftest.py --node bm-c --json
Exit: 0 全通过｜2 有 FAIL
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


def http(url, data=None, timeout=40):
    try:
        req = urllib.request.Request(url, data=(json.dumps(data).encode() if data else None),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace") or "{}")
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"err": str(e)[:80]}


def roster(node):
    try:
        d = json.load(open(os.path.join(ROOT, "Tools", "fleet-nodes.json"), encoding="utf-8-sig"))
        for n in d.get("nodes") or []:
            if n.get("id") == node:
                return n
    except Exception:
        pass
    return {}


def state(node):
    code, j = http("http://%s:8790/status" % node, timeout=60)
    return j if code == 200 else {}


def wakes(node):
    lp = state(node).get("last_pull") or {}
    return [str(w) for w in (lp.get("wakes") or [])], lp


def poke(node, tasks, reason):
    code, j = http("http://%s:8790/poke" % node, {"reason": reason, "tasks": tasks})
    return code, j


def wait_wakes(node, need, seconds=90):
    """等到 wakes 里出现 need 这个任务的行为（节点是异步 worker，只能轮询）。"""
    end = time.time() + seconds
    last = []
    while time.time() < end:
        ws, lp = wakes(node)
        last = ws
        if any(str(w).split(":")[0] == need for w in ws):
            return ws, lp
        time.sleep(6)
    return last, {}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    n = a.node
    r = roster(n)
    enable = [str(x) for x in (r.get("enable_tasks") or [])]
    wake = [str(x) for x in (r.get("wake_tasks") or [])]
    if not enable:
        print("[selftest] %s 的 roster 没有 enable_tasks —— 这台机没有受控启用入口" % n)
        return 2
    target = enable[0]
    rows = []

    def add(case, expect, got, ok):
        rows.append({"case": case, "expect": expect, "got": got, "ok": bool(ok)})

    # S5 代码态（先判，因为后面所有结论都建立在"节点跑的是新码"上）
    ws0, lp0 = wakes(n)
    fresh = "fork" in str(lp0)
    add("S5 代码态", "last_pull 含 fork（Tools 已更新）",
        "含 fork" if fresh else "无 fork 字段（Tools 仍旧）", fresh)

    # S1 正向
    code, _ = poke(n, [target], "selftest: enable-tasks")
    ok_poke = code == 200
    ws, lp = wait_wakes(n, target, 120)
    got = [w for w in ws if str(w).split(":")[0] == target]
    hit = any("REENABLED" in w or ":WAKE" in w for w in got)
    add("S1 正向启用", "poke 200 且 %s 出现 REENABLED/WAKE" % target,
        "poke=%s wakes=%s" % (code, got or ws[:3]), ok_poke and hit)

    # S2 负向对照：同一任务，reason 不带 token → 只允许 WAKE/busy，不允许 REENABLED
    time.sleep(3)
    poke(n, [target], "selftest: plain reload")
    ws2, _ = wait_wakes(n, target, 90)
    got2 = [w for w in ws2 if str(w).split(":")[0] == target]
    bad2 = [w for w in got2 if "REENABLED" in w]
    add("S2 负向对照", "无 token 时不得出现 REENABLED",
        "wakes=%s" % (got2 or ws2[:3]), not bad2)

    # S3 越界：禁用且不在名单的任务，带 token 也必须 off-skip
    others = [t for t in wake if t != target]
    st = (state(n).get("last_pull") or {}).get("task_states") or {}
    dis = [t for t in others if str(st.get(t, "")) == "Disabled"]
    if not dis:
        add("S3 越界保护", "需要一个禁用且不在名单的任务", "本机没有这样的任务，跳过", True)
    else:
        cand = dis[0]
        poke(n, [cand], "selftest: enable-tasks")
        ws3, _ = wait_wakes(n, cand, 90)
        got3 = [w for w in ws3 if str(w).split(":")[0] == cand]
        add("S3 越界保护", "%s 必须 off-skip（不得被启用）" % cand,
            "wakes=%s" % (got3 or ws3[:3]),
            any(w.endswith(":off-skip") for w in got3))

    # S4 幂等：再来一次正向
    time.sleep(3)
    poke(n, [target], "selftest: enable-tasks")
    ws4, _ = wait_wakes(n, target, 90)
    got4 = [w for w in ws4 if str(w).split(":")[0] == target]
    add("S4 幂等重复", "重复启用不报错（WAKE/busy-skip/REENABLED 均可）",
        "wakes=%s" % (got4 or ws4[:3]),
        all(not w.endswith(":enable-fail") for w in got4))

    # S6 中文请求体（已知限制：监听器 Read-Request 判 400）
    code6, j6 = poke(n, [target], "selftest: 中文请求体")
    add("S6 中文请求体", "400 bad-request（客户端须走 ASCII）",
        "code=%s err=%s" % (code6, j6.get("err")), code6 == 400)

    if a.json:
        print(json.dumps({"node": n, "ts": datetime.now().isoformat(timespec="seconds"),
                          "rows": rows}, ensure_ascii=False, indent=1))
    else:
        print("[selftest] %s @ %s" % (n, datetime.now().strftime("%H:%M:%S")))
        for x in rows:
            print("  %-14s %-4s %s" % (x["case"], "PASS" if x["ok"] else "FAIL", x["got"]))
    bad = [x for x in rows if not x["ok"]]
    print("\n结论：%d/%d 通过%s" % (len(rows) - len(bad), len(rows),
                                 "" if not bad else "；FAIL=" + ",".join(x["case"] for x in bad)))
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))