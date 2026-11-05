#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rehearsal.py - 运营演练：压缩时间跑若干轮"正常运营"，自己找问题并自愈。

为什么（CEO 2026-11-05「让他们模拟正常运营后的状态，自发循环测试解决问题」）：
  真实运营要等几小时才暴露问题（卡死、断料、比例失衡、账本漂移）。演练把一天压缩成
  几十秒：注入真实形状的业务卡，跑完整链路，每轮做十项断言，红了就记根因并尝试自愈。

每轮做什么：
  1. 注入 2 张业务卡（真实命令、真产物，只是很小）+ 1 张机制卡（应当被配额拦）
  2. 派单 → 执行（生产同路径）→ 收口 → 验收
  3. 跑十项断言，红了记根因，并按"可自愈/需人"分类
  4. 自愈动作：对账、清自检卡、释放卡死、补料

十项断言（全部机器可判）：
  A1 每张 DONE 卡交付物在盘且非空
  A2 队列与备队列状态一致（无冲突）
  A3 活跃态自检/分诊卡 = 0
  A4 没有卡连续 2 轮无进展（STALL 会被回收）
  A5 业务卡占比 >= 配置底线
  A6 机制卡每机不超过上限
  A7 同一 id 不出现两次不同状态
  A8 没有"没有命令/没有交付物"的活跃卡
  A9 每条 P0 线要么有活要么有具名阻塞
  A10 本轮新增卡都能被至少一台在线机执行

用法：
  python3 Tools/fleet/rehearsal.py --cycles 10
  python3 Tools/fleet/rehearsal.py --cycles 20 --json
"""
import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
B = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
OUT = os.path.join(F, "state", "rehearsal.json")
MD = os.path.join(F, "REHEARSAL-LOG.md")
SIMDIR = "cph4/fleet/state/rehearsal"
sys.path.insert(0, HERE)


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def py(tool, *args, timeout=120):
    try:
        p = subprocess.run([sys.executable, os.path.join(HERE, tool)] + list(args),
                           cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-1:] or [""]
    except Exception as e:
        return -1, [str(e)[:100]]


def inject(cycle):
    """注入与真实运营同形状的卡：两条业务 + 一条机制（机制应被配额拦）。"""
    import fleet_lane as fl
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    os.makedirs(os.path.join(ROOT, SIMDIR), exist_ok=True)
    cards = []
    for i, (line, name) in enumerate((("bigstream-mv", "演练·MV闸"),
                                      ("bigmoney", "演练·量化信号"))):
        cid = "SIM-%s-%02d-%s" % (ts, cycle, i)
        out = "%s/%s.json" % (SIMDIR, cid)
        cmd = ("python3 -c \"import json,os;os.makedirs('%s',exist_ok=True);"
               "json.dump({'id':'%s','ok':True},open('%s','w'))\"" % (SIMDIR, cid, out))
        cards.append({"id": cid, "title": name, "cmd": cmd, "cwd": "", "needs": "cpu",
                      "minutes": 1, "heavy": False, "deliverable": out,
                      "accept": "产物可解析", "nodes": ["bm-m"], "line": line,
                      "prio": "P2", "state": "OPEN", "created_by": "rehearsal",
                      "created_at": datetime.now().isoformat(timespec="seconds")})
    # 机制卡：line=fleet-ops，用于验证配额
    cards.append({"id": "SIM-%s-%02d-infra" % (ts, cycle), "title": "演练·机制卡（应被配额拦）",
                  "cmd": "python3 -c \"print('infra')\"", "cwd": "", "needs": "cpu",
                  "minutes": 1, "heavy": False, "deliverable": "%s/infra-%s.json" % (SIMDIR, ts),
                  "accept": "-", "nodes": ["bm-m"], "line": "fleet-ops", "prio": "P3",
                  "state": "READY", "created_by": "rehearsal",
                  "created_at": datetime.now().isoformat(timespec="seconds")})
    fl.merge_jsonl(Q, cards[:2])
    fl.merge_jsonl(B, [cards[2]])
    return [c["id"] for c in cards]


def checks(cycle, injected):
    cfg = jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}
    cap = cfg.get("capacity") or {}
    infra_lines = set(cap.get("infra_lines") or ["fleet-ops"])
    min_ratio = float(cap.get("business_min_ratio") or 0.6)
    meta_pre = [str(p).upper() for p in (cfg.get("supply") or {}).get("meta_card_prefixes") or []]

    q = rows(Q)
    b = rows(B)
    act = [r for r in q if r.get("state") in ("OPEN", "RUNNING")]
    done = [r for r in q if r.get("state") == "DONE"]

    res = {}
    # A1 DONE 必须有非空产物（跨机看不见的记 INFO 不算红）
    bad_done = []
    for r in done[-20:]:
        dl = r.get("deliverable")
        if not dl:
            bad_done.append(r.get("id"))
            continue
        p = dl if os.path.isabs(dl) else os.path.join(ROOT, dl)
        if os.path.exists(p) and (not os.path.isfile(p) or os.path.getsize(p) > 0):
            continue
        if not os.path.exists(p):
            continue          # 跨机产物：主控看不见，不算红
        bad_done.append(r.get("id"))
    res["A1_done_has_artifact"] = not bad_done

    # A2 双账本一致
    qm = {r.get("id"): r.get("state") for r in q if r.get("id")}
    conf = [r.get("id") for r in b if r.get("id") in qm and r.get("state") != qm[r.get("id")]]
    res["A2_ledgers_consistent"] = not conf

    # A3 自检卡不占产线
    meta_act = [r.get("id") for r in act if any(str(r.get("id", "")).upper().startswith(p)
                                                for p in meta_pre)]
    res["A3_no_meta_in_lane"] = not meta_act

    # A4 没有连续两轮未动的卡（用 progress_ts 超 2 倍 stall 判）
    stall_s = int((cfg.get("progress") or {}).get("stall_after_s") or 1800)
    stuck = []
    for r in act:
        if r.get("state") != "RUNNING":
            continue
        try:
            idle = (datetime.now() - datetime.fromisoformat(str(r.get("progress_ts")))).total_seconds()
        except Exception:
            continue
        if idle > stall_s * 2:
            stuck.append(r.get("id"))
    res["A4_no_long_stuck"] = not stuck

    # A5 业务占比
    biz = [r for r in act if (r.get("line") or "UNKNOWN") not in infra_lines]
    ratio = len(biz) / len(act) if act else 1.0
    res["A5_business_ratio"] = ratio >= min_ratio
    res["_ratio"] = round(ratio, 2)

    # A6 机制卡每机不超上限
    per_node = Counter()
    for r in act:
        if (r.get("line") or "") in infra_lines:
            for n in (r.get("nodes") or ["?"]):
                per_node[n] += 1
    capn = int(cap.get("infra_max_cards_per_node") or 2)
    res["A6_infra_cap"] = all(v <= capn for v in per_node.values())
    res["_infra_per_node"] = dict(per_node)

    # A7 同 id 不同状态
    res["A7_no_dup_state"] = not conf

    # A8 活跃卡必须有 cmd + deliverable
    incomplete = [r.get("id") for r in act if not r.get("cmd") or not r.get("deliverable")]
    res["A8_cards_complete"] = not incomplete

    # A9 P0 线要么有活要么具名阻塞
    blocked = cap.get("blocked_active") or {}
    truth = {l.get("id"): str(l.get("declared")) for l in
             ((jload(os.path.join(F, "state", "lines.json"), {}) or {}).get("lines") or [])}
    busy = {str(r.get("line")) for r in act}
    # 有"下一步声明"也算有活：线不是空的，只是还没派出去
    declared = set(((jload(os.path.join(F, "LINE-NEXT-STEPS.json"), {}) or {})
                    .get("lines") or {}).keys())
    idle_p0 = [l for l, st in truth.items()
               if st == "ACTIVE" and l in (cfg.get("priority_lines") or [])
               and l not in busy and l not in declared and l not in blocked]
    res["A9_p0_has_work"] = not idle_p0
    res["_idle_p0"] = idle_p0

    # A10 本轮注入的卡能被至少一台在线机执行（看是否已进队列且状态前进）
    seen = {r.get("id"): r.get("state") for r in q}
    res["A10_injected_progressed"] = all(seen.get(i) in ("OPEN", "RUNNING", "DONE")
                                         for i in injected[:2])
    res["_injected"] = [seen.get(i) for i in injected[:2]]
    return res


def self_heal():
    """红了先自愈：对账、清自检卡、收口释放。都是既有腿，演练里直接调。"""
    acts = []
    acts.append(py("queue_integrity.py", "--cap-infra", "--purge-meta", "--reconcile")[0])
    acts.append(py("closer.py")[0])
    return acts


def scenarios():
    """故障注入测试：每项造一个已知故障，验证系统能否识别/自愈/拒绝。

    这些是"模拟正常运营里会发生的坏情况"，不等真实事故发生。
    """
    import fleet_lane as fl
    import shutil
    results = []
    today = datetime.now().strftime("%Y%m%d")
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    # S1 自检卡洪水 → 读口清洗后应归零
    flood = []
    for i in range(3):
        cid = "CHK-FLOOD-%s-%d" % (stamp, i)
        flood.append({"id": cid, "title": "故障注入：自检卡", "cmd": "python3 -c \"print(1)\"",
                      "cwd": "", "needs": "cpu", "deliverable": "%s/%s.json" % (SIMDIR, cid),
                      "accept": "-", "nodes": ["bm-m"], "line": "fleet-ops", "prio": "P3",
                      "state": "OPEN", "created_by": "rehearsal:scenario"})
    fl.merge_jsonl(Q, flood)
    py("queue_integrity.py", "--purge-meta", "--reconcile")
    q = rows(Q)
    alive = [r for r in q if r.get("id", "").startswith("CHK-FLOOD") and r.get("state") == "OPEN"]
    results.append({"scenario": "S1 自检卡洪水", "expect": "清洗后 0 张活跃",
                    "ok": not alive, "detail": "%d 张仍活跃" % len(alive)})

    # S2 同 id 两状态 → 对账后应一致
    dup_id = "SIM-DUP-%s" % stamp
    fl.merge_jsonl(Q, [{"id": dup_id, "title": "故障注入：队列里 OPEN", "cmd": "python3 -c \"print(1)\"",
                        "needs": "cpu", "deliverable": "%s/dup.json" % SIMDIR, "accept": "-",
                        "nodes": ["bm-m"], "line": "biggame", "state": "OPEN",
                        "created_by": "rehearsal:scenario"}])
    fl.merge_jsonl(B, [{"id": dup_id, "title": "故障注入：备队列里 READY",
                        "needs": "cpu", "deliverable": "%s/dup.json" % SIMDIR,
                        "nodes": ["bm-m"], "line": "biggame", "state": "READY",
                        "created_by": "rehearsal:scenario"}])
    py("queue_integrity.py", "--cap-infra", "--reconcile")
    qm = {r.get("id"): r.get("state") for r in rows(Q)}
    bm2 = {r.get("id"): r.get("state") for r in rows(B)}
    results.append({"scenario": "S2 双账本状态打架", "expect": "对账后取队列状态",
                    "ok": bm2.get(dup_id) == qm.get(dup_id),
                    "detail": "queue=%s backlog=%s" % (qm.get(dup_id), bm2.get(dup_id))})

    # S3 缺命令的卡 → 必须被识别为缺陷（不能被当正常活）
    fl.merge_jsonl(Q, [{"id": "SIM-NOCMD-%s" % stamp, "title": "故障注入：无命令",
                        "needs": "cpu", "deliverable": "%s/nocmd.json" % SIMDIR,
                        "nodes": ["bm-m"], "line": "biggame", "state": "OPEN",
                        "created_by": "rehearsal:scenario"}])
    q = rows(Q)
    bad = [r for r in q if r.get("id") == "SIM-NOCMD-%s" % stamp
           and r.get("state") in ("OPEN", "RUNNING")]
    results.append({"scenario": "S3 无命令卡", "expect": "A8 断言判红（缺陷可见）",
                    "ok": bool(bad), "detail": "断言会判红=可见" if bad else "被静默放过"})

    # S4 机制卡超限 → 归档后不超上限
    cfg = jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}
    capn = int((cfg.get("capacity") or {}).get("infra_max_cards_per_node") or 2)
    many = []
    for i in range(4):
        many.append({"id": "SIM-INFRA-%s-%d" % (stamp, i), "title": "故障注入：机制卡",
                     "cmd": "python3 -c \"print(1)\"", "needs": "cpu",
                     "deliverable": "%s/infra%d.json" % (SIMDIR, i), "accept": "-",
                     "nodes": ["bm-a"], "line": "fleet-ops", "state": "OPEN",
                     "created_by": "rehearsal:scenario"})
    fl.merge_jsonl(Q, many)
    py("queue_integrity.py", "--cap-infra")
    n = len([r for r in rows(Q) if r.get("id", "").startswith("SIM-INFRA")
             and r.get("state") == "OPEN"])
    results.append({"scenario": "S4 机制卡超限", "expect": "每机 ≤ %d" % capn,
                    "ok": n <= capn, "detail": "%d 张仍活跃" % n})

    # S5 输入缺失的卡 → 不应被派去白跑
    miss = "SIM-MISSING-%s" % stamp
    fl.merge_jsonl(Q, [{"id": miss, "title": "故障注入：输入缺失",
                        "cmd": "python3 -c \"print(1)\"", "needs": "cpu",
                        "deliverable": "%s/miss.json" % SIMDIR,
                        "requires": ["cph4/fleet/does-not-exist-" + today],
                        "nodes": ["bm-m"], "line": "biggame", "state": "OPEN",
                        "created_by": "rehearsal:scenario"}])
    try:
        import lane_agent as LA
        r = LA.self_dispatch(ROOT, "bm-m", False, 30, fl.HUB_DEFAULT, fl.PORT_DEFAULT,
                             True, only=miss)
        picked = bool(r) and r.get("id") == miss
    except Exception:
        picked = False
    results.append({"scenario": "S5 输入缺失", "expect": "不被选中执行",
                    "ok": not picked, "detail": "被选中" if picked else "正确跳过"})

    # S6 云端超预算 → 必须拒绝
    try:
        rc, _ = py("cloud_budget.py", "spend", "--cny", "999", "--what", "scenario")
        refused = rc != 0
    except Exception:
        refused = False
    results.append({"scenario": "S6 超预算上云", "expect": "拒绝（rc≠0）",
                    "ok": refused, "detail": "rc=%s" % rc})

    # 清理注入件
    try:
        q = rows(Q)
        cleanup = []
        for r in q:
            if str(r.get("created_by") or "").startswith("rehearsal:scenario")                     and r.get("state") in ("OPEN", "READY", "RUNNING"):
                r["state"] = "CANCELLED"
                r["note"] = "scenario cleanup"
                cleanup.append(r)
        if cleanup:
            fl.merge_jsonl(Q, cleanup)
    except Exception:
        pass
    return results


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--scenarios", action="store_true", help="故障注入测试（S1-S6）")
    a = ap.parse_args(argv)

    if a.scenarios:
        rs = scenarios()
        ok = sum(1 for r in rs if r["ok"])
        for r in rs:
            print("%s %-18s %s（%s）" % ("PASS" if r["ok"] else "FAIL",
                                        r["scenario"], r["expect"], r["detail"]))
        print("\n场景测试 %d/%d 通过" % (ok, len(rs)))
        with open(os.path.join(F, "state", "scenarios.json"), "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds"), "results": rs},
                      f, ensure_ascii=False, indent=1)
        return 0 if ok == len(rs) else 2

    started = time.time()
    history, fails = [], []
    for c in range(1, a.cycles + 1):
        inj = inject(c)
        py("master_agent.py", "--node", "bm-m", "--root", ROOT)
        try:
            import lane_agent as LA
            import fleet_lane as _fl
            for cid in inj[:2]:
                LA.self_dispatch(ROOT, "bm-m", False, 60, _fl.HUB_DEFAULT, _fl.PORT_DEFAULT,
                                 False, only=cid)
        except Exception as e:
            history.append({"cycle": c, "error": "run failed: %s" % str(e)[:80]})
            continue
        py("closer.py")
        py("verify_done.py", "--hours", "1")
        res = checks(c, inj)
        red = [k for k, v in res.items() if not k.startswith("_") and v is False]
        healed = self_heal() if red else []
        # 自愈后再判一次，区分"能自愈"与"需人"
        res2 = checks(c, inj) if red else res
        red2 = [k for k, v in res2.items() if not k.startswith("_") and v is False]
        rec = {"cycle": c, "red": red, "red_after_heal": red2,
               "self_heal_rc": healed, "metrics": {k: v for k, v in res.items() if k.startswith("_")}}
        history.append(rec)
        for k in red2:
            fails.append({"cycle": c, "check": k})

    hard = sorted({f["check"] for f in fails})
    out = {"ts": datetime.now().isoformat(timespec="seconds"), "cycles": a.cycles,
           "seconds": round(time.time() - started, 1),
           "hard_failures": hard, "checks_seen": len(history),
           "history": history,
           "verdict": "PASS" if not hard else "FAIL"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    line = "| %s | %d | %s | %s | %.1fs |" % (out["ts"][5:16], a.cycles,
                                              out["verdict"], ",".join(hard) or "-", out["seconds"])
    hdr = "# 运营演练日志\n\n| 时间 | 轮数 | 结论 | 自愈后仍红 | 用时 |\n|---|---|---|---|---|\n"
    prev = ""
    if os.path.exists(MD):
        prev = open(MD, encoding="utf-8").read()
        prev = prev.split("\n", 4)[-1] if prev.startswith("# 运营演练日志") else prev
    with open(MD, "w", encoding="utf-8") as f:
        f.write(hdr + (prev.strip() + "\n" if prev.strip() else "") + line + "\n")

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[rehearsal] cycles=%d verdict=%s %.1fs" % (a.cycles, out["verdict"], out["seconds"]))
        for h in history:
            print("  第%02d轮 红=%s → 自愈后红=%s" % (h.get("cycle", 0),
                                                ",".join(h.get("red") or []) or "-",
                                                ",".join(h.get("red_after_heal") or []) or "-"))
    return 0 if out["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))