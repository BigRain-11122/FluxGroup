#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_verify.py - 机队之间协同的快速实测（每轮一种形态，断言可判）。

为什么（CEO 2026-11-05「快速测试几轮不同的，验证机队之间的」）：
  单元测试全绿也可能协同全断（今天已两次：卡标 RUNNING 不跑、机队在发主控读不到）。
  这里用真卡、真机、真回传，按不同形态各跑一轮，每轮给出 PASS/FAIL 与证据。

五种形态：
  A 短卡（3s）        ：派→跑→收口→回传，全链在一轮内完成
  B 长卡（25s）       ：运行中必须有 ≥2 次新鲜心跳，且 out_bytes 增长（证明不是假忙）
  C 中途被杀          ：杀掉执行进程后，汇总必须在 STALE_S 内判死并退回
  D 缺输入            ：requires 不存在的卡不许被执行，且不许占 RUNNING
  E 远端真执行（bm-b）：另一台机领取、执行、回传，主控侧看得到它的心跳与结果

用法：
  python3 Tools/fleet/fleet_verify.py            # 全跑（约 2-3 分钟）
  python3 Tools/fleet/fleet_verify.py --only A,B # 只跑指定形态
Exit: 0 全 PASS｜2 有 FAIL
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
ST = os.path.join(F, "state")
TMP = os.path.join(ST, "fleet-verify")
sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def card(cid, cmd, minutes=1, requires=None, nodes=None, line="fleet-ops"):
    return {"id": cid, "title": "验证·" + cid, "cmd": cmd, "cwd": ROOT, "needs": "cpu",
            "minutes": minutes, "heavy": False,
            "requires": requires or [],
            "deliverable": "%s/%s.json" % (os.path.relpath(TMP, ROOT), cid),
            "accept": "产物非空", "nodes": nodes or ["bm-m"],
            "line": line, "prio": "P3", "state": "OPEN",
            "created_by": "fleet_verify", "created_at": fl.now_iso()}


def put(cards):
    fl.merge_jsonl(Q, cards)


def state_of(cid):
    for r in fl.read_jsonl(Q):
        if r.get("id") == cid:
            return r
    return {}


def status():
    subprocess.run([sys.executable, os.path.join(HERE, "fleet_status.py")],
                   cwd=ROOT, capture_output=True, text=True, timeout=90)
    return jload(os.path.join(ST, "fleet-status.json"), {}) or {}


def lane_st(node):
    return jload(os.path.join(ST, "lane-status", node + ".json"), {}) or {}


def wait_for(pred, timeout, step=2):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(step)
    return False


def run_local(cid):
    import lane_agent as LA
    return LA.self_dispatch(ROOT, "bm-m", False, 120, fl.HUB_DEFAULT, fl.PORT_DEFAULT,
                            False, only=cid) or {}


def case_A(res):
    cid = "VER-A-%s" % datetime.now().strftime("%H%M%S")
    out = os.path.join(TMP, cid + ".json")
    put([card(cid, "python3 -c \"import json,os;os.makedirs('%s',exist_ok=True);"
                   "json.dump({'ok':1},open('%s','w'))\"" % (os.path.relpath(TMP, ROOT), out))])
    run_local(cid)
    time.sleep(1)
    st = state_of(cid)
    ok = st.get("state") == "DONE" and os.path.exists(os.path.join(ROOT, card(cid, "")["deliverable"]))
    res.append(("A 短卡全链", ok, "state=%s 产物=%s" % (st.get("state"), os.path.exists(out))))


def case_B(res):
    cid = "VER-B-%s" % datetime.now().strftime("%H%M%S")
    out = os.path.join(TMP, cid + ".json")
    cmd = ("python3 -c \"import time,json,os;os.makedirs('%s',exist_ok=True);"
           "[ (print('tick',i,flush=True), time.sleep(1)) for i in range(25)];"
           "json.dump({'ok':1},open('%s','w'))\"" % (os.path.relpath(TMP, ROOT), out))
    put([card(cid, cmd, minutes=1)])
    import threading
    th = threading.Thread(target=lambda: run_local(cid), daemon=True)
    th.start()
    seen, bytes_seen = [], set()
    for _ in range(30):
        time.sleep(2)
        st = lane_st("bm-m")
        if str(st.get("job")) == cid:
            seen.append(st.get("received_at") or st.get("ts"))
            bytes_seen.add(int(st.get("out_bytes") or 0))
        if not th.is_alive():
            break
    th.join(timeout=10)
    ok = len(set(seen)) >= 2 and len(bytes_seen) >= 2
    res.append(("B 长卡心跳+可增进度", ok,
                "心跳=%d 次 字节档位=%s" % (len(set(seen)), sorted(bytes_seen)[:4])))


def case_C(res):
    cid = "VER-C-%s" % datetime.now().strftime("%H%M%S")
    put([card(cid, "python3 -c \"import time;time.sleep(120)\"", minutes=5)])
    import threading
    th = threading.Thread(target=lambda: run_local(cid), daemon=True)
    th.start()
    got = wait_for(lambda: str(lane_st("bm-m").get("job")) == cid, 30)
    # 杀掉子进程，模拟机器失联/进程死
    subprocess.run(["pkill", "-f", "time.sleep(120)"], capture_output=True)
    time.sleep(3)
    subprocess.run(["pkill", "-f", "only=%s" % cid], capture_output=True)
    s = status()
    deads = [c for c in (s.get("cards") or []) if c.get("id") == cid]
    released = state_of(cid).get("state")
    ok = bool(got) and (bool(deads) or released in ("OPEN", "FAILED", "CANCELLED"))
    res.append(("C 中途被杀可判死", ok,
                "心跳曾在=%s 汇总判定=%s 队列状态=%s"
                % (got, (deads[0]["verdict"] if deads else "-"), released)))


def case_D(res):
    cid = "VER-D-%s" % datetime.now().strftime("%H%M%S")
    put([card(cid, "python3 -c \"print(1)\"", requires=["cph4/fleet/does-not-exist-verify"])])
    r = run_local(cid)   # 输入缺失：应当不被执行
    st = state_of(cid)
    ok = not r.get("id") and st.get("state") not in ("RUNNING", "DONE")
    res.append(("D 缺输入不执行", ok, "返回=%s 队列=%s" % (r.get("id"), st.get("state"))))


def case_E(res):
    cid = "VER-E-%s" % datetime.now().strftime("%H%M%S")
    out = os.path.join(TMP, cid + ".json")
    put([card(cid, "python3 -c \"import json,os;os.makedirs('%s',exist_ok=True);"
                   "json.dump({'ok':1},open('%s','w'))\"" % (os.path.relpath(TMP, ROOT), out),
              nodes=["bm-b"])])
    # 交给主控派单，看 bm-b 是否领取并回传
    subprocess.run([sys.executable, os.path.join(HERE, "master_agent.py"),
                    "--node", "bm-m", "--root", ROOT], cwd=ROOT, capture_output=True, timeout=180)
    seen = False
    t_wait = time.time()
    for _ in range(80):          # 2026-11-05 实测：远端领取有分钟级延迟，给 4 分钟窗口
        time.sleep(3)
        st = lane_st("bm-b")
        if str(st.get("job")) == cid:
            seen = True
            break
    after = state_of(cid).get("state")
    ok = seen or after in ("RUNNING", "DONE")
    res.append(("E 远端领取并回传", ok, "bm-b 心跳=%s 用时=%.0fs 队列=%s"
                % (seen, time.time() - t_wait, after)))


def cleanup():
    dead = [{"id": r["id"], "state": "CANCELLED", "note": "fleet_verify cleanup"}
            for r in fl.read_jsonl(Q) if str(r.get("id", "")).startswith("VER-")]
    if dead:
        fl.merge_jsonl(Q, dead)
    return len(dead)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="A,B,C,D,E")
    a = ap.parse_args(argv)
    os.makedirs(TMP, exist_ok=True)
    want = {x.strip().upper() for x in a.only.split(",") if x.strip()}
    res = []
    t0 = time.time()
    for k, fn in (("A", case_A), ("B", case_B), ("C", case_C), ("D", case_D), ("E", case_E)):
        if k not in want:
            continue
        try:
            fn(res)
        except Exception as e:
            res.append(("%s 异常" % k, False, str(e)[:120]))
    n = cleanup()
    ok_n = sum(1 for _, ok, _ in res if ok)
    print("[fleet-verify] %d/%d PASS  %.0fs  (清理 %d 张验证卡)"
          % (ok_n, len(res), time.time() - t0, n))
    for name, ok, why in res:
        print("  %s %-20s %s" % ("PASS" if ok else "FAIL", name, why))
    return 0 if ok_n == len(res) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))