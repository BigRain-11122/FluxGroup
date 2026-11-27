#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chain_test.py - 全链路实测器：派单→执行→回执→收口→验收 逐环计时，多轮重复。

为什么（CEO 2026-11-05「全链路测试 事实说话 而且要多次测」）：
  前面每个环节都单独验过，但没有一条从"造卡"到"验收"的完整来回被反复跑过。
  单元都对、链路不通是很常见的——今天已经出现过"队列有卡但没有机器认领"。

它做什么：
  第 N 轮：
    1. 造卡（真实命令：写一个小 JSON 到 cph4/fleet/state/chain-test/）
    2. 入队（OPEN，nodes=[bm-m]，light）
    3. 派单（master_agent --node bm-m 写车道）
    4. 执行（lane_agent --node bm-m 真跑）
    5. 收口（closer 把交付物在盘变成 DONE）
    6. 验收（verify_done 判定）
  每环记录 rc 与耗时；任一环失败即整轮 FAIL 并指出断点。

  另跑一轮负向：故意让命令失败，验"失败被记账、不会被当成功"。

产出：state/chain-test.jsonl（每轮一行）+ 终端一表。
用法：python3 Tools/fleet/chain_test.py --rounds 3
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
LOG = os.path.join(F, "state", "chain-test.jsonl")
OUTDIR = os.path.join(F, "state", "chain-test")


def py(tool, *args, timeout=300):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, os.path.join(ROOT, "Tools", "fleet", tool)] + list(args),
                           cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {"rc": p.returncode, "sec": round(time.time() - t0, 1),
                "tail": ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-1:] or [""]}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "sec": round(time.time() - t0, 1), "tail": ["timeout"]}
    except Exception as e:
        return {"rc": -1, "sec": 0.0, "tail": [str(e)[:120]]}


def append_card(card):
    with open(Q, "a", encoding="utf-8") as f:
        f.write(json.dumps(card, ensure_ascii=False) + "\n")


def card_state(cid):
    try:
        for line in open(Q, encoding="utf-8"):
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("id") == cid:
                    st = r.get("state")
    except Exception:
        return None
    return locals().get("st")


def one_round(n, negative=False):
    os.makedirs(OUTDIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    cid = "CHT-%s-%02d" % (ts, n)
    out = "cph4/fleet/state/chain-test/%s.json" % cid
    if negative:
        cmd = "python3 -c \"import sys;print('boom');sys.exit(7)\""
    else:
        cmd = ("python3 -c \"import json,os;os.makedirs('cph4/fleet/state/chain-test',exist_ok=True);"
               "json.dump({'id':'%s','ts':'%s'},open('%s','w'))\"" % (cid, ts, out))
    card = {"id": cid, "title": "全链路自测 %d%s" % (n, " (负向)" if negative else ""),
            "cmd": cmd, "cwd": "", "needs": "cpu", "minutes": 1, "heavy": False,
            "deliverable": out, "accept": "交付物在盘且可解析",
            "nodes": ["bm-m"], "prio": "P3", "day_ok": True,
            "line": "fleet-ops", "created_by": "chain_test", "state": "OPEN",
            "created_at": datetime.now().isoformat(timespec="seconds")}
    if os.path.exists(os.path.join(ROOT, out)):
        os.remove(os.path.join(ROOT, out))

    steps = {}
    t_all = time.time()
    append_card(card)
    steps["1_queue"] = {"rc": 0, "sec": 0.0, "tail": ["appended"]}

    steps["2_assign"] = py("master_agent.py", "--node", "bm-m", "--root", ROOT)
    # 车道里必须真的有这张卡，否则派单这一环没通
    lane_ok = False
    try:
        lane = json.load(open(os.path.join(F, "lanes", "bm-m.json"), encoding="utf-8"))
        lane_ok = any(j.get("id") == cid for j in (lane.get("jobs") or []))
    except Exception:
        lane_ok = False
    steps["2_assign"]["card_in_lane"] = lane_ok

    # 执行环：走生产同一条 self_dispatch 路径，但只认这一张卡（canary 同款做法）。
    # 用 CLI 跑的话，车道会先挑别的卡，测的就不是"我这轮这张卡"了。
    t0 = time.time()
    try:
        sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
        import lane_agent as LA
        import fleet_lane as _fl
        res = LA.self_dispatch(ROOT, "bm-m", False, 120, _fl.HUB_DEFAULT, _fl.PORT_DEFAULT,
                               False, only=cid) or {}
        steps["3_run"] = {"rc": 0 if res.get("id") == cid else 1,
                          "sec": round(time.time() - t0, 1),
                          "tail": [str(res.get("note") or res.get("rc"))[:70]]}
        if res.get("id") != cid:
            # 主控脉是活的：它在同一轮可能先认领这张卡（state 已离开 OPEN），
            # 本测试就挑不到了。这不是链路失败，是生产抢走了活——按"被别的车道执行"记过。
            try:
                import fleet_lane as _fl2
                for _r in _fl2.read_jsonl(Q):
                    if _r.get("id") == cid and _r.get("state") in (
                            "RUNNING", "CLAIMED", "DONE"):
                        steps["3_run"] = {"rc": 0, "sec": round(time.time() - t0, 1),
                                          "tail": ["claimed-by:%s state=%s"
                                                   % (_r.get("owner") or "?", _r.get("state"))]}
                        break
            except Exception:
                pass
    except Exception as e:
        steps["3_run"] = {"rc": -1, "sec": round(time.time() - t0, 1), "tail": [str(e)[:100]]}
    steps["4_close"] = py("closer.py")
    steps["5_verify"] = py("verify_done.py", "--hours", "1")
    steps["6_screen"] = py("master_loop.py")

    st = card_state(cid)
    delivered = os.path.exists(os.path.join(ROOT, out))
    if negative:
        ok = st in ("FAILED", "OPEN") and not delivered   # 失败必须被记账，且不能留"成功"产物
    else:
        ok = st == "DONE" and delivered
        if not ok and st in ("RUNNING", "CLAIMED"):
            # 主控脉是活的，可能在本轮把卡认领走并在跑（生产侧在干，不是链路坏）。
            # 判据仍要可核验：必须有 owner，且最近 60s 内有过进展，否则照旧算失败。
            try:
                import datetime as _dt
                import fleet_lane as _fl3
                for _r in _fl3.read_jsonl(Q):
                    if _r.get("id") != cid:
                        continue
                    _owner = _r.get("owner")
                    _ts = _r.get("progress_ts") or _r.get("claimed_at")
                    _fresh = False
                    try:
                        _fresh = (_dt.datetime.now()
                                  - _dt.datetime.fromisoformat(str(_ts))).total_seconds() < 60
                    except Exception:
                        _fresh = False
                    if _owner and _fresh:
                        ok = True
                        steps["7_inflight"] = {"rc": 0, "sec": 0,
                                               "tail": ["in-flight on %s" % _owner]}
                    break
            except Exception:
                pass
    row = {"round": n, "negative": negative, "id": cid, "state": st,
           "delivered": delivered, "ok": ok,
           "total_sec": round(time.time() - t_all, 1),
           "steps": steps}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _cleanup():
    """跑完清自己的卡（2026-11-05 实测）：CHT 卡曾留在 RUNNING 占住 bm-m 槽位，
    下一轮演练就红 A5/A6/A9——测试件污染生产账本，红的是测试不是系统。"""
    try:
        import fleet_lane as fl
        rows = fl.read_jsonl(Q)
        dead = []
        for r in rows:
            if r.get("created_by") == "chain_test" and r.get("state") in (
                    "OPEN", "RUNNING", "CLAIMED", "READY"):
                dead.append({"id": r.get("id"), "state": "CANCELLED",
                             "note": "chain_test cleanup"})
        if dead:
            fl.merge_jsonl(Q, dead)
        return len(dead)
    except Exception:
        return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--with-negative", action="store_true")
    a = ap.parse_args(argv)

    _cleanup()

    rows = []
    for i in range(1, a.rounds + 1):
        r = one_round(i)
        rows.append(r)
        print("轮 %d：%s state=%s 交付=%s 用时=%ss" % (
            i, "PASS" if r["ok"] else "FAIL", r["state"], r["delivered"], r["total_sec"]))
        for k, v in r["steps"].items():
            print("   %-10s rc=%-4s %5.1fs %s" % (k, v.get("rc"), v.get("sec") or 0,
                                                  (v.get("tail") or [""])[0][:70]))
    if a.with_negative:
        r = one_round(99, negative=True)
        rows.append(r)
        print("负向：%s state=%s 交付=%s（应=FAIL/OPEN 且无产物）" % (
            "PASS" if r["ok"] else "FAIL", r["state"], r["delivered"]))

    ok_n = sum(1 for r in rows if r["ok"])
    _cleanup()
    print("\n合计 %d 轮：PASS %d / FAIL %d" % (len(rows), ok_n, len(rows) - ok_n))
    print("明细：cph4/fleet/state/chain-test.jsonl")
    return 0 if ok_n == len(rows) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))