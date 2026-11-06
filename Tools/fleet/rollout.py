#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rollout.py - 一条命令把"改完必然生效"跑通，并指出断在哪一环。

为什么（CEO 2026-11-06「你已经把这个来来回回修了多少次了还是有问题」）：
  48 小时内 lane_agent 改了 17 次、fleet 相关 62 个提交，问题仍在——因为每次只验了我
  这一侧，远端链路的四环（推码→拉码→重载→回执）没有任何一环被强制验证。这里把四环
  串成一条可失败、可定位的链：哪台机断在哪一环，一眼可见，不用再猜。

四环（每台机）：
  L1 可达    FleetLink :8790 /health 200
  L2 会拉    /poke 接受，且 /status.last_pull.ts 晚于本次开始、pulls 含 updated
  L3 是新码  该机 HEAD == 我方推送 sha（拉到了才算新码）
  L4 会跑    投一张探针卡，180 秒内 hub 收到该机回执（rc 任意，能回来就行）

用法：
  python3 Tools/fleet/rollout.py            # 全机队
  python3 Tools/fleet/rollout.py --only bm-c
  python3 Tools/fleet/rollout.py --no-canary   # 只验 L1-L3
Exit: 0 全绿｜2 有机断链
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
ST = os.path.join(F, "state")
HUB = os.environ.get("FLEET_HUB") or "http://100.75.133.10:8791"
NODES = ("bm-a", "bm-b", "bm-c")
sys.path.insert(0, HERE)


def http(url, data=None, timeout=8):
    try:
        req = urllib.request.Request(url, data=(json.dumps(data).encode() if data else None),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"err": str(e)[:80]}


def sh(args, timeout=60):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def local_sha():
    rc, out, _ = sh(["git", "rev-parse", "--short", "HEAD"])
    return out


def push_local():
    """把本地改动推到主线；返回 (sha, 说明)。分叉时先合远端，工具取我方。"""
    rc, branch, _ = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch != "main":
        return None, "本地不在 main（%s），先归位" % branch
    st = subprocess.run(["git", "status", "--porcelain", "Tools/"], cwd=ROOT,
                        capture_output=True, text=True).stdout.strip()
    if st:
        sh(["git", "add", "Tools"])
        sh(["git", "commit", "-q", "-m", "rollout: 同步工具改动"])
    rc, out, err = sh(["git", "push", "origin", "HEAD:main"], timeout=180)
    if rc != 0:
        return None, "push 失败: %s" % (err or out)[:80]
    return local_sha(), "pushed"


def poke(node, tasks, t0_iso):
    # ASCII only: the listener's Read-Request rejects bodies with multibyte chars
    # (live 2026-11-06: Chinese reason -> 400 bad-request in 31s, ASCII -> 200 in 1s).
    body = {"reason": "rollout: pull and reload", "tasks": tasks}
    for _ in range(3):
        code, _j = http("http://%s:8790/poke" % node, body, timeout=12)
        if code == 200:
            return True, ""
        time.sleep(2)
    return False, "poke 无响应"


def status(node):
    code, j = http("http://%s:8790/status" % node, timeout=10)
    return j if code == 200 else {}


def probe_card(node):
    cid = "ROLL-%s-%s" % (node.replace("-", ""), datetime.now().strftime("%H%M%S"))
    card = {"id": cid, "title": "rollout 探针（%s）" % node, "cmd": "python -c \"print('ok')\"",
            "cwd": ".", "needs": "cpu", "minutes": 1, "heavy": False,
            "deliverable": "cph4/fleet/queue-receipts/%s.json" % cid,
            "accept": "能跑完并回执", "nodes": [node], "verify_on_node": True,
            "line": "fleet-ops", "prio": "P3", "state": "OPEN",
            "created_by": "rollout", "created_at": datetime.now().isoformat(timespec="seconds")}
    import fleet_lane as fl
    fl.merge_jsonl(Q, [card])
    return cid


def wait_receipt(node, cid, seconds=180):
    end = time.time() + seconds
    while time.time() < end:
        for p in glob.glob(os.path.join(ST, "remote-receipts", "%s-%s.json" % (cid, node))):
            return True, json.load(open(p, encoding="utf-8"))
        time.sleep(5)
    return False, {}


def live_tasks(node):
    try:
        d = json.load(open(os.path.join(ROOT, "Tools", "fleet-nodes.json"), encoding="utf-8-sig"))
        for n in d.get("nodes") or []:
            if n.get("id") == node:
                return n.get("wake_tasks") or []
    except Exception:
        pass
    return []


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--no-canary", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args(argv)
    nodes = [x.strip() for x in a.only.split(",") if x.strip()] or list(NODES)
    t0 = datetime.now()
    t0_iso = t0.isoformat(timespec="seconds")
    print("[rollout] 开始 %s" % t0_iso)

    if a.no_push:
        _, sha, _ = sh(["git", "rev-parse", "--short", "origin/main"])
        why = "no-push: 以 origin/main 尖端为基准"
    else:
        sha, why = push_local()
    print("[rollout] L0 基准码: %s（%s）" % (sha or "失败", why))
    if not sha:
        return 2

    rows = []
    for node in nodes:
        rec = {"node": node}
        code, _ = http("http://%s:8790/health" % node, timeout=8)
        rec["L1"] = "PASS" if code == 200 else "FAIL(health=%s)" % code
        if code != 200:
            rows.append(rec)
            continue
        ok, err = poke(node, live_tasks(node), t0_iso)
        rec["L2a"] = "PASS" if ok else "FAIL(%s)" % err
        pulled = False
        j = {}
        end = time.time() + 120
        while time.time() < end:
            j = status(node)
            lp = j.get("last_pull") or {}
            if str(lp.get("ts") or "") >= t0_iso and "updated" in str(lp.get("pulls")):
                pulled = True
                break
            time.sleep(5)
        rec["L2b"] = "PASS" if pulled else "FAIL(未拉到新码, last=%s)" % (
            (j.get("last_pull") or {}).get("ts"))
        heads = j.get("repo_heads") or {}
        head = heads.get(".") or heads.get("repo") or ""
        rec["L3"] = "PASS" if str(head).startswith(sha[:7]) or sha[:7] in str(head) \
            else "FAIL(node HEAD=%s 我方=%s)" % (str(head)[:7], sha[:7])
        if a.no_canary:
            rows.append(rec)
            continue
        cid = probe_card(node)
        got, rcpt = wait_receipt(node, cid)
        rec["L4"] = "PASS(rc=%s)" % rcpt.get("rc") if got else "FAIL(180s 无回执 %s)" % cid
        rows.append(rec)

    print("\n%-6s %-22s %-14s %-26s %s" % ("机器", "L1 可达", "L2 会拉", "L3 是新码", "L4 会跑"))
    for r in rows:
        print("%-6s %-22s %-14s %-26s %s" % (r["node"], r["L1"], r.get("L2b", "-"),
                                             r.get("L3", "-"), r.get("L4", "-")))
    bad = [r for r in rows if any(str(v).startswith("FAIL") for k, v in r.items() if k != "node")]
    print("\n断链机器：%s" % (", ".join(r["node"] for r in bad) or "无"))
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))