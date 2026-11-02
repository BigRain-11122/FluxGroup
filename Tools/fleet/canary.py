#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""canary.py - 端到端自检：证明"一条卡能被无人值守地跑完并留下产物"。

为什么要有它（2026-11-02 CEO 质问"为什么每次都能发现问题"）：
过去每一次改动都只用"零件级"证据验收——某个函数返回对不对、某条断言红不红。
于是供给、队列、领取、执行、回执、状态、产物这六环，每一环单独看都对，
连起来却层层漏：尸体积压 → 队列空 → 卡钉死 → rc=127 → 回执假绿。
问题不是"改动写错"，而是**从来没有一条测试把整条链跑通一次**。

所以这里只做一件事：投一张真卡，走 production 的同一条路（pick→claim→run→
receipt→queue state→deliverable），逐环断言；任一环断就 FAIL 并指出断在哪。
它不替代任何域闸，它就是"自动化到底成不成"的唯一判据。

用法：
  python3 canary.py               # 跑一次，PASS/FAIL，写 state/canary.json
  python3 canary.py --node bm-a   # 指定机器（默认本机）
  python3 canary.py --json
Exit: 0 = PASS, 2 = FAIL, 1 = canary 自己坏了。
"""
import argparse
import json
import os
import socket
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
CANARY_STATE = os.path.join(STATE, "canary.json")
RUN_DIR = os.path.join(STATE, "canary")

sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402


def _node_default():
    # 本机是 bm-m（主控笔记本）；其他机器由 --node 指定。
    return "bm-m"


def _job(jid, node, stamp):
    out = os.path.join("cph4", "fleet", "state", "canary", "RUN-%s.txt" % stamp)
    # 卡里不许出现机器名（I2：卡声明 needs，不写主机）；机器只放在 nodes 偏好字段里。
    payload = "canary %s — 端到端自检产物，不是业务活" % stamp
    cmd = 'python -c "open(r\'%s\',\'w\',encoding=\'utf-8\').write(\'%s\')"' % (out, payload)
    return {
        "id": jid, "title": "端到端自检：投卡→领取→执行→回执→产物",
        "cmd": cmd, "cwd": "",
        "requires": [], "deliverable": out,
        "needs": "cpu", "nodes": [node], "prio": "P3", "day_ok": True, "heavy": False,
        "line": "fleet-ops", "ok_rc": [0],
        "night_rules": ["no-cloud", "no-publish", "no-spend", "no-delete"],
        "created_by": "canary", "created_at": fl.now_iso(),
        "why": "acceptance: prove the whole chain works unattended, not just its parts",
        "state": "OPEN",
    }


def run(node, keep=False):
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    jid = "CANARY-%s" % stamp
    os.makedirs(RUN_DIR, exist_ok=True)
    qpath = os.path.join(ROOT, fl.QUEUE_REL.replace("/", os.sep))
    links = {}

    # 1) 投卡（走唯一写入口）
    job = _job(jid, node, stamp)
    try:
        fl.merge_jsonl(qpath, [job])
        links["1_supply"] = {"ok": True, "card": jid}
    except Exception as e:
        links["1_supply"] = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}

    # 2-4) 领取 + 执行（同一条 self_dispatch 路径，只认这一张卡）
    import lane_agent as LA
    res = None
    if links["1_supply"]["ok"]:
        try:
            res = LA.self_dispatch(ROOT, node, False, 120, fl.HUB_DEFAULT, fl.PORT_DEFAULT,
                                   False, only=jid)
        except Exception as e:
            res = {"id": jid, "rc": None, "note": "self_dispatch raised: %s" % e}
        picked = bool(res) and res.get("id") == jid
        links["2_pick"] = {"ok": picked,
                           "note": (res or {}).get("note") if res else "no pick (card not eligible?)"}
    if res and links.get("2_pick", {}).get("ok"):
        links["3_exec"] = {"ok": res.get("rc") == 0, "rc": res.get("rc"),
                           "seconds": res.get("seconds")}

    # 5) 回执
    rc_path = os.path.join(FLEET, "queue-receipts", "%s-%s.json" % (jid, node))
    rc = None
    if os.path.exists(rc_path):
        try:
            rc = json.load(open(rc_path, encoding="utf-8-sig"))
        except Exception:
            rc = None
    links["4_receipt"] = {"ok": bool(rc) and rc.get("rc") == 0,
                          "file": os.path.relpath(rc_path, ROOT) if rc else None,
                          "rc": (rc or {}).get("rc"),
                          "error_class": (rc or {}).get("error_class")}

    # 6) 产物
    dl = os.path.join(ROOT, job["deliverable"])
    links["5_artifact"] = {"ok": os.path.exists(dl) and os.path.getsize(dl) > 0,
                           "path": job["deliverable"]}

    # 7) 队列状态
    now = None
    for r in fl.read_jsonl(qpath):
        if r.get("id") == jid:
            now = r
    links["6_state"] = {"ok": bool(now) and now.get("state") == "DONE"
                        and now.get("rc") in (0, None),
                        "state": (now or {}).get("state"), "rc": (now or {}).get("rc")}

    verdict = "PASS" if all(v.get("ok") for v in links.values()) else "FAIL"

    # 收尾：归档这张卡（不留在队列里干扰派单），产物留作证据
    if now and not keep:
        now.update({"state": "ARCHIVED", "archived_at": fl.now_iso(),
                    "archived_by": "canary: keep the queue clean"})
        fl.merge_jsonl(qpath, [now])

    prev = {}
    try:
        prev = json.load(open(CANARY_STATE, encoding="utf-8-sig"))
    except Exception:
        pass
    streak = int(prev.get("consecutive_pass") or 0)
    streak = streak + 1 if verdict == "PASS" else 0
    hist = (prev.get("history") or [])[-19:] + [{"ts": fl.now_iso(), "verdict": verdict,
                                                 "node": node, "card": jid}]
    out = {"ts": fl.now_iso(), "node": node, "card": jid, "verdict": verdict,
           "links": links, "consecutive_pass": streak, "history": hist,
           "note": "唯一验收口径：这条链跑通才算自动化成立；零件级绿灯不算。"}
    os.makedirs(STATE, exist_ok=True)
    with open(CANARY_STATE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out


def _prune(qpath, days=2):
    """清掉自己的旧卡与旧回执，避免每轮自检把队列撑爆。"""
    cutoff = time.time() - days * 86400

    def keep(r):
        if not str(r.get("id") or "").startswith("CANARY-"):
            return True
        t = str(r.get("created_at") or "")
        try:
            from datetime import datetime as _dt
            return _dt.fromisoformat(t).timestamp() >= cutoff
        except Exception:
            return False

    try:
        fl.prune_jsonl(qpath, keep)
    except Exception:
        pass
    rd = os.path.join(FLEET, "queue-receipts")
    try:
        for n in os.listdir(rd):
            if n.startswith("CANARY-") and os.path.getmtime(os.path.join(rd, n)) < cutoff:
                os.remove(os.path.join(rd, n))
    except Exception:
        pass


def _recent_pass(min_interval):
    """刚通过过就不再跑（脉冲每 60s 一轮，自检跑 10 分钟一次足够）。"""
    if min_interval <= 0:
        return None
    try:
        st = json.load(open(CANARY_STATE, encoding="utf-8-sig"))
    except Exception:
        return None
    if st.get("verdict") != "PASS":
        return None
    try:
        from datetime import datetime as _dt
        age = (datetime.now() - _dt.fromisoformat(str(st.get("ts")))).total_seconds()
    except Exception:
        return None
    return st if age < min_interval else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default=_node_default())
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--keep", action="store_true", help="不归档自检卡（排查用）")
    ap.add_argument("--min-interval", type=int, default=600,
                    help="距上次 PASS 不足这么多秒就跳过（默认 600）")
    ap.add_argument("--force", action="store_true", help="忽略节流，强制跑")
    a = ap.parse_args(argv)
    prev = None if a.force else _recent_pass(a.min_interval)
    if prev:
        print("CANARY SKIP  上次 PASS %.0fs 前（--force 可强制），连续通过=%s"
              % (time.time() - os.path.getmtime(CANARY_STATE) if os.path.exists(CANARY_STATE) else 0,
                 prev.get("consecutive_pass")))
        return 0
    try:
        out = run(a.node, keep=a.keep)
        _prune(os.path.join(ROOT, fl.QUEUE_REL.replace("/", os.sep)))
    except Exception as e:
        print("canary itself broke: %s: %s" % (type(e).__name__, e))
        return 1
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("CANARY %s  node=%s  连续通过=%d" % (out["verdict"], out["node"],
                                                out["consecutive_pass"]))
        for k in sorted(out["links"]):
            v = out["links"][k]
            extra = v.get("note") or v.get("rc") or v.get("path") or v.get("state") or ""
            print("  %-12s %s  %s" % (k, "OK  " if v.get("ok") else "FAIL", str(extra)[:70]))
    return 0 if out["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))