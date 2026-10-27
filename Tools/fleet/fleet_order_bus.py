#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_order_bus.py - cross-platform one-command fan-out (stdlib only).

Same contract as Tools/fleet-order-bus.ps1, but runs on macOS/Linux because the Mac is
becoming the group master-control node. A CEO sentence is split by lane, written as a
unique command file (conflict-free transport) plus the human ledger row, pushed, and each
node is poked via FleetLink with its own wake_tasks; the fetched sha is verified.

Usage:
  python3 fleet_order_bus.py --send-file cmd.txt
  python3 fleet_order_bus.py --send "text" --dry-run
  python3 fleet_order_bus.py --status
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
DUTY = {
    "bm-a": "拆解/装配/核验/回执；HQ 车道可执行件立即开工",
    "bm-b": "配音/混音/词锚/声音车道可执行件立即开工",
    "bm-c": "KF/i2v/渲染/画质链可执行件立即开工",
    "bm-m": "主控：分发/看板/时钟/出包；不接生产 GPU 件",
}


def route(text, override=""):
    if override:
        return [x.strip() for x in override.split(",") if x.strip()]
    t = text.lower()
    explicit = len(re.findall(r"bm-[abc]", t))
    if explicit >= 2 or re.search(r"所有|全部|全域|全集团|各司|子公司|机队|全员|自检|回执|三机|全线|各机", t):
        return ["bm-a", "bm-b", "bm-c"]
    lanes = set()
    if re.search(r"视频|渲染|出片|mv|镜头|kf|i2v|图|画|美术|lora|模型|gpu|comfy|升档", t):
        lanes.add("bm-c")
    if re.search(r"配音|音|tts|bgm|混音|歌|语音|旁白|whisper|字幕", t):
        lanes.add("bm-b")
    if re.search(r"装配|剪辑|合流|核验|签|提交|仓库|订单|调度|日报|台账|发布|自动化|命令", t):
        lanes.add("bm-a")
    return sorted(lanes) if lanes else ["bm-a", "bm-b", "bm-c"]


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", default="")
    ap.add_argument("--send-file", default="")
    ap.add_argument("--lanes", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    bus_dir = os.path.join(root, "cph4", "fleet", "order-bus", "receipts")
    os.makedirs(bus_dir, exist_ok=True)

    if a.status:
        files = sorted(
            [os.path.join(bus_dir, f) for f in os.listdir(bus_dir) if f.endswith(".json")],
            key=os.path.getmtime, reverse=True)[:10]
        if not files:
            print("NO-ORDERS")
            return 0
        for f in files:
            try:
                j = json.load(open(f, encoding="utf-8"))
                print("%s lanes=%s nodes=%s sha=%s %s" % (
                    j.get("id"), ",".join(j.get("lanes", [])), ",".join(j.get("nodes", [])),
                    j.get("sha", "")[:8], j.get("dispatch", "")))
            except Exception:
                pass
        return 0

    text = a.send
    if a.send_file:
        with open(a.send_file, encoding="utf-8") as f:
            text = f.read().strip()
    if not text:
        print('usage: --send-file <utf8.txt> | --send "text" | --status')
        return 2

    lanes = route(text, a.lanes)
    now = datetime.now()
    oid = "OB-" + now.strftime("%Y%m%d-%H%M%S") + "-" + str(random.randint(100, 999))
    stamp = now.strftime("%Y-%m-%d %H:%M")

    if a.dry_run:
        print("DRY id=%s lanes=%s" % (oid, ",".join(lanes)))
        for l in lanes:
            print("  %s :: %s" % (l, DUTY.get(l, "按令自领")))
        return 0

    # unique command file = conflict-free transport
    cmd_dir = os.path.join(root, "cph4", "fleet", "cmd")
    os.makedirs(cmd_dir, exist_ok=True)
    cmd_path = os.path.join(cmd_dir, oid + ".json")
    with open(cmd_path, "w", encoding="utf-8") as f:
        json.dump({"id": oid, "ts": stamp, "text": text, "lanes": lanes,
                   "src": os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME", ""),
                   "status": "dispatched"}, f, ensure_ascii=False, indent=1)

    orders = os.path.join(root, "docs", "orders.md")
    duty = "；".join("%s=%s" % (l, DUTY.get(l, "按令自领")) for l in lanes)
    row = ("| %s（自动分发 %s） | CEO 令（原话）：「%s」 | **机队自动分发令（id=%s）**：车道=%s；%s；"
           "各车道轮首自领、禁等人工分配；回执落 cph4/fleet/order-bus/receipts/ | dispatched %s | "
           "[via fleet-order-bus.py] |\n") % (
        stamp, oid, text.replace("|", "/"), oid, "/".join(lanes), duty, oid)
    with open(orders, "a", encoding="utf-8") as f:
        f.write(row)

    rel_cmd = os.path.join("cph4", "fleet", "cmd", oid + ".json")
    git(root, "add", "--", "docs/orders.md", rel_cmd)
    git(root, "commit", "-m", "orders: auto fanout " + oid,
        "-m", "CEO one-line command split to lanes: " + ",".join(lanes),
        "--", "docs/orders.md", rel_cmd)
    git(root, "fetch", "origin", "main:refs/remotes/origin/main")
    behind = 0
    try:
        behind = int(git(root, "rev-list", "--count", "HEAD..origin/main").stdout.strip() or "0")
    except Exception:
        pass
    if behind > 0:
        subprocess.run(["git", "-C", root, "-c", "rebase.autostash=true", "rebase", "origin/main"],
                       capture_output=True, text=True)
    sha = ""
    if not a.no_push:
        p = git(root, "push", "origin", "HEAD:main")
        if p.returncode != 0:
            print("PUSH-FAIL " + (p.stderr or p.stdout).strip())
            return 1
    sha = git(root, "rev-parse", "HEAD").stdout.strip()

    cfg = {}
    try:
        with open(os.path.join(root, "Tools", "fleet-nodes.json"), encoding="utf-8-sig") as f:
            cfg = json.load(f)
    except Exception:
        pass
    nodes, tasks = [], []
    for n in cfg.get("nodes", []):
        if not n.get("enabled"):
            continue
        lane = n.get("lane", "")
        want = {"hq-central-night-gpu": "bm-a", "cpu-sound": "bm-b",
                "gpu-production": "bm-c", "master-control": "bm-m"}.get(lane, n.get("id"))
        if want not in lanes:
            continue
        nodes.append(n.get("id"))
        tasks.extend(n.get("wake_tasks", []))
    tasks = sorted(set(tasks))
    results = []
    for n in cfg.get("nodes", []):
        if not n.get("enabled") or n.get("id") not in nodes:
            continue
        ip = n.get("tailnet_ip", "")
        if not ip or ip.startswith("PENDING"):
            continue
        body = json.dumps({"reason": "order:" + oid, "tasks": tasks, "repos": []}).encode()
        try:
            req = urllib.request.Request("http://%s:8790/poke" % ip, data=body,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=25) as r:
                ok = json.loads(r.read().decode()).get("ok")
        except Exception as e:
            results.append("%s ERR %s" % (n.get("id"), e))
            continue
        synced = "accepted"
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                with urllib.request.urlopen("http://%s:8790/status" % ip, timeout=10) as r:
                    st = json.loads(r.read().decode())
                heads = st.get("repo_heads", {}) or {}
                lp = st.get("last_pull", {}) or {}
                if heads.get(".") == sha or lp.get("origin_main") == sha:
                    synced = "SYNCED"
                    break
            except Exception:
                pass
            time.sleep(2)
        results.append("%s ok=%s %s" % (n.get("id"), ok, synced))

    receipt = {"id": oid, "ts": stamp, "text": text, "lanes": lanes, "nodes": nodes,
               "sha": sha, "dispatch": " | ".join(results), "dry": False}
    with open(os.path.join(bus_dir, oid + ".json"), "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
    print("ORDER %s lanes=%s nodes=%s sha=%s" % (oid, ",".join(lanes), ",".join(nodes), sha[:8]))
    print("DISPATCH " + " | ".join(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())