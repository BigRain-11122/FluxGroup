#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fork_repair.py - 节点分叉自愈：把「拉不动 → 越拉越旧 → 零产出」这条死路自动收口。

为什么（2026-11-10 实锚）：
  bm-c 的 HEAD 停在 c9b16b7a8，领先 313 / 落后 4162，`merge --ff-only` 永远失败 →
  它看到的队列是 13 小时前的，任何新卡都不存在，于是「在线但零产出」。
  bm-a 同理（head b696cdb 在 origin 上根本不存在，35 个提交推不上去）。
  旧机制只在 pull 失败后写一行日志，没人修，雪球越滚越大。

判据（每台 enabled 且不是主控的节点）：
  sync_ok          ahead==0 且 head 在 origin 上        → 不动
  adoptable        head 是 origin/node/<id> 的祖先      → 收编祖先（-s ours），让它能快进
  orphan_head      head 在 origin 上完全不存在          → 只能在本机 reset，发 NODE-SYNC 卡
  frozen_stamp     /status 的 last_pull 时间戳不前进    → poke + 发对等修复卡（走健康机 WinRM）

动作全部幂等、带冷却，单轮失败不阻塞下一轮；主控脉每轮调一次即可。

用法：
  python3 Tools/fleet/fork_repair.py            # 只诊断（默认）
  python3 Tools/fleet/fork_repair.py --apply    # 真动作
  python3 Tools/fleet/fork_repair.py --json
退出码：0 全部同步/已处理；1 有节点仍需人工（无通道）
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state", "fork-repair.json")
NODES = os.path.join(ROOT, "Tools", "fleet-nodes.json")
sys.path.insert(0, HERE)

STALE_STAMP_S = 900        # /status 的 last-pull 戳超过这么久没动 = 搬不动 git
POKE_COOLDOWN_S = 600
CARD_COOLDOWN_S = 3600
PORT = 8790


def now():
    return time.time()


def ts_iso(t=None):
    return datetime.fromtimestamp(t or now()).isoformat(timespec="seconds")


def http_json(url, data=None, timeout=25):
    try:
        req = urllib.request.Request(
            url, data=(json.dumps(data).encode() if data is not None else None),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace") or "{}")
    except Exception:
        return None


def git(args, timeout=120):
    try:
        p = subprocess.run(["git", "-C", ROOT] + args, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return 1, "", str(exc)


def load_nodes():
    try:
        d = json.load(open(NODES, encoding="utf-8-sig"))
    except Exception:
        return []
    out = []
    for n in d.get("nodes") or []:
        if n.get("id") == "bm-m" or not n.get("enabled"):
            continue
        out.append(n)
    return out


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        return {}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def probe(node):
    """拉 /status，返回归一化事实；探不到返回 {'reachable': False}。""" 
    ip = node.get("tailnet_ip")
    d = None
    for _ in range(3):
        d = http_json("http://%s:%d/status" % (ip, PORT), timeout=30)
        if d:
            break
        time.sleep(2)
    if not d:
        return {"reachable": False}
    lp = d.get("last_pull") or {}
    heads = d.get("repo_heads") or {}
    fork = lp.get("fork") or {}
    head = heads.get(".") or ""
    ahead = behind = None
    f = str(fork.get(".") or "")
    if "/" in f:
        try:
            # 实锚格式是 "313\t4162/main"（tab 分隔），早期是 "a/b"
            left = f.split("/")[0]
            ahead = int(left.split()[0])
        except Exception:
            ahead = None
    stamp = str(lp.get("ts") or d.get("ts") or "")
    age = None
    try:
        age = now() - datetime.fromisoformat(stamp).timestamp()
    except Exception:
        age = None
    return {"reachable": True, "head": head, "ahead": ahead, "behind": behind,
            "origin_main": lp.get("origin_main") or "", "stamp": stamp,
            "stamp_age": age, "pulls": lp.get("pulls") or [],
            "wakes": lp.get("wakes") or [], "ram": d.get("ram_free_gb"),
            "cpu": d.get("cpu_load_pct")}


def head_in_origin(head):
    if not head:
        return False
    git(["fetch", "-q", "origin", "--prune"])
    rc, _, _ = git(["cat-file", "-e", head + "^{commit}"], timeout=30)
    return rc == 0


def adopt(node, head, st):
    """把节点的 HEAD 收编成 main 的祖先：内容不动，只买回快进的可能。"""
    nid = node["id"]
    ref = "origin/node/%s" % nid
    git(["fetch", "-q", "origin", "--prune"])
    rc, _, err = git(["cat-file", "-e", ref + "^{commit}"], timeout=30)
    if rc != 0:
        return "no-node-branch", err[-120:]
    rc, _, _ = git(["merge-base", "--is-ancestor", head, ref], timeout=30)
    if rc != 0:
        return "head-not-on-node-branch", "head %s 不在 %s 上" % (head[:9], ref)
    rc, out, err = git(["merge", "-s", "ours", ref, "--no-edit",
                        "-m", "adopt %s ancestry so its clone can ff-merge again "
                              "(content stays main) [via bm-m]" % nid], timeout=120)
    if rc != 0:
        return "merge-failed", (err or out)[-160:]
    for _ in range(3):
        rc, _, err = git(["push", "-q", "origin", "main"], timeout=180)
        if rc == 0:
            st.setdefault(nid, {})["adopted"] = ts_iso()
            return "adopted", "origin/main now contains %s" % head[:9]
        git(["fetch", "-q", "origin"])
        git(["merge", "-q", "--no-edit", "origin/main"], timeout=120)
    return "push-failed", err[-160:]


def sync_card(node, st, reason):
    """发一张自包含的 NODE-SYNC 卡：不依赖节点上任何脚本，纯 git 收口。"""
    nid = node["id"]
    rid = "NODE-SYNC-%s-%s" % (nid, datetime.now().strftime("%Y%m%d"))
    qpath = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    try:
        import fleet_lane as fl
        for ln in open(qpath, encoding="utf-8"):
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("id") == rid and str(r.get("state")).upper() in ("OPEN", "RUNNING"):
                return "already-open", rid
    except Exception:
        fl = None
    out = "cph4/fleet/reports/%s.md" % rid.lower()
    # 2026-11-10 实锚：全量 `git fetch --prune` 在分叉节点上要拉几千个提交，DERP 上跑了
    # 十几分钟还没完，且拿着 index/ref 锁 —— 后面的 reset 卡全部排队，节点看起来"卡死"。
    # 收分叉其实不需要新数据：本地已有的 origin/main 就够把 HEAD 拉回来，所以这里用轻量式
    # （不 fetch），快进留给下一轮 poke 的 ff-only。要刷新代码的节点另派 NODE-UPDATE 卡。
    cmd = ("git -C . branch -f backup/%s-%s HEAD && "
           "git -C . reset --hard origin/main && "
           "git -C . log -1 --oneline > %s" % (nid, datetime.now().strftime("%Y%m%d"), out))
    card = {
        "id": rid, "title": "[self-heal] %s 分叉收口（reset 到 origin/main，先留备份分支）" % nid,
        "cmd": cmd, "cwd": "", "requires": [], "deliverable": out,
        "needs": "cpu", "nodes": [nid], "hard_nodes": [nid], "prio": "P0",
        "day_ok": True, "heavy": False, "rescue": True, "est_gb": 0.2,
        "line": "fleet-ops", "ok_rc": [0],
        "night_rules": ["no-cloud", "no-publish", "no-spend", "no-delete"],
        "created_by": "fork_repair", "created_at": ts_iso(),
        "why": reason, "state": "OPEN",
    }
    if fl is None:
        return "no-writer", ""
    fl.merge_jsonl(qpath, [card])
    st.setdefault(nid, {})["card"] = rid
    st[nid]["card_ts"] = now()
    return "enqueued", rid


def peer_card(node, peers, st, why):
    """本机搬不动 git 时，让健康机用 WinRM 去收口。"""
    nid = node["id"]
    ip = node.get("tailnet_ip")
    root = (node.get("root") or "").replace("/", "\\")
    rid = "PEER-SYNC-%s-%s" % (nid, datetime.now().strftime("%Y%m%d"))
    qpath = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    for ln in open(qpath, encoding="utf-8"):
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("id") == rid and str(r.get("state")).upper() in ("OPEN", "RUNNING"):
            return "already-open", rid
    out = "cph4/fleet/reports/%s.md" % rid.lower()
    ps = ("$e=$null; try { Invoke-Command -ComputerName %s -ScriptBlock { "
          "Set-Location '%s'; git fetch origin --prune; git branch -f backup/%s-%s HEAD 2>$null; "
          "git reset --hard origin/main; git log -1 --oneline } -ErrorAction Stop } "
          "catch { $e=$_.Exception.Message }; "
          "'winrm_err='+$e | Out-File -Encoding utf8 %s" % (
              ip, root, nid, datetime.now().strftime("%Y%m%d"), out))
    card = {
        "id": rid, "title": "[peer-heal] %s 用 WinRM 替 %s 收口" % (peers[0], nid),
        "cmd": 'powershell -NoProfile -Command "%s"' % ps.replace('"', '`"'),
        "cwd": "", "requires": [], "deliverable": out,
        "needs": "cpu", "nodes": peers, "hard_nodes": peers, "prio": "P0",
        "day_ok": True, "heavy": False, "rescue": True, "est_gb": 0.2,
        "line": "fleet-ops", "ok_rc": [0],
        "night_rules": ["no-cloud", "no-publish", "no-spend", "no-delete"],
        "created_by": "fork_repair", "created_at": ts_iso(),
        "why": why, "state": "OPEN",
    }
    import fleet_lane as fl
    fl.merge_jsonl(qpath, [card])
    st.setdefault(nid, {})["peer_card"] = rid
    st[nid]["peer_ts"] = now()
    return "enqueued", rid


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--force", action="store_true", help="忽略冷却：上一张卡没修好时重派")
    a = ap.parse_args(argv)
    st = load_state()
    rows = []
    stuck = []
    for node in load_nodes():
        nid = node["id"]
        p = probe(node)
        rec = {"node": nid, "reachable": p.get("reachable")}
        if not p.get("reachable"):
            rec.update(verdict="unreachable", action="none")
            stuck.append(nid)
            rows.append(rec)
            continue
        head, ahead = p["head"], p["ahead"]
        rec.update(head=(head or "")[:9], ahead=ahead, stamp_age=p["stamp_age"],
                   ram=p.get("ram"))
        node_st = st.setdefault(nid, {})
        if ahead == 0 and p["origin_main"] and p["stamp_age"] is not None \
                and p["stamp_age"] < STALE_STAMP_S:
            rec.update(verdict="sync_ok", action="none")
            rows.append(rec)
            continue
        # 1) 能收编祖先就先收编：这是唯一不需要碰节点就能解死结的动作
        # "head 对象在本地存在" ≠ "能收编"：收编要求 head 是 origin/node/<id> 的祖先。
        # 2026-11-10 实锚：只看对象存在，连续三轮把 bm-a 判成 adoptable，adopt 每次都
        # 失败在 "head-not-on-node-branch"，于是既没修成也没派 reset 卡 —— 空转三轮。
        _adoptable = False
        if head and ahead and ahead > 0:
            ref = "origin/node/%s" % nid
            if git(["cat-file", "-e", ref + "^{commit}"], timeout=30)[0] == 0 and \
                    git(["merge-base", "--is-ancestor", head, ref], timeout=30)[0] == 0:
                _adoptable = True
        if _adoptable:
            if not a.apply:
                rec.update(verdict="adoptable", action="would-adopt")
            else:
                act, note = adopt(node, head, st)
                rec.update(verdict="adoptable", action=act, note=note)
            rows.append(rec)
            continue
        # 2) 戳不前进 = 节点的 git 通道断了，只能靠对等机或本机 reset
        frozen = p["stamp_age"] is not None and p["stamp_age"] > STALE_STAMP_S
        rec["verdict"] = "frozen_stamp" if frozen else "behind"
        if not a.apply:
            rec["action"] = "would-poke+card"
            rows.append(rec)
            continue
        acted = []
        if now() - float(node_st.get("poke_ts") or 0) > POKE_COOLDOWN_S:
            r = http_json("http://%s:%d/poke" % (node["tailnet_ip"], PORT),
                          {"reason": "fork-repair:enable-tasks", "tasks": ["HQ-ProductionClaim"],
                           "repos": ["."]}, timeout=45)
            node_st["poke_ts"] = now()
            acted.append("poke=%s" % bool(r and r.get("accepted")))
        if frozen:
            # 对等机只要「探得到」就算健康：stamp 新旧不可靠（bm-b 干活正常但戳是 17h 前）
            peers = []
            for n in load_nodes():
                if n["id"] == nid:
                    continue
                pp = probe(n)
                if pp.get("reachable"):
                    peers.append(n["id"])
            if peers and now() - float(node_st.get("peer_ts") or 0) > CARD_COOLDOWN_S:
                act, rid = peer_card(node, peers[:1], st,
                                     "%s 的 last_pull 戳停在 %s（git 通道断），本机无法收口"
                                     % (nid, p["stamp"]))
                acted.append("%s:%s" % (act, rid))
            else:
                acted.append("no-healthy-peer")
            stuck.append(nid)
        else:
            if a.force or now() - float(node_st.get("card_ts") or 0) > CARD_COOLDOWN_S:
                act, rid = sync_card(node, st, "%s 落后 %s 个提交且无法快进" % (nid, ahead))
                acted.append("%s:%s" % (act, rid))
        rec["action"] = ",".join(acted) or "none"
        rows.append(rec)
    if a.apply:
        st["ts"] = ts_iso()
        save_state(st)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False))
    else:
        for r in rows:
            print("[fork] %-4s %-14s ahead=%-5s age=%-6s %s %s" % (
                r["node"], r.get("verdict"), r.get("ahead"), 
                ("%.0fs" % r["stamp_age"]) if r.get("stamp_age") is not None else "-",
                r.get("action"), r.get("note") or ""))
        print("[fork] %d 台 · 仍卡 %d 台%s" % (len(rows), len(stuck),
                                              (" (%s)" % ",".join(stuck)) if stuck else ""))
    return 0 if not stuck else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
