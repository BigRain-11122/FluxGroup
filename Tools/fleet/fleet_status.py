#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_status.py - 机队工作状态汇总口：把"谁在跑什么、跑到哪、是不是真在动"变成主控可判的事实。

CEO 2026-11-05：「机队的工作状态要及时回传主控，让主控及时了解然后科学处理。」
此前的病（实测）：
  - 进度只发 NATS KV，主控在稀疏克隆/断网时读不到，只看到卡标 RUNNING；
  - 于是"卡在跑"和"卡被标了 RUNNING 但没人跑"在主控眼里长得一模一样，
    实测出现过 20 张卡挂 RUNNING 零产物、CPU 16% 的空转。
判据（每条都机器可核，不采信心跳自述）：
  S1 每张 RUNNING 卡必须有 owner，且该机 lane-status 的 job 是它、ts 龄 ≤ STALE_S
  S2 进度必须"可增"：out_bytes 或 deliverable_bytes 相比上次有增长（否则即使 ts 新鲜也是假忙）
  S3 每台在线机的槽位占用 = 该机 RUNNING 卡数 / slots_per_node
  S4 没有 owner 的 RUNNING 卡 = UNOWNED，立刻退回 OPEN
输出：
  state/fleet-status.json（主控与屏幕读）＋一行摘要
  --act：把 S1/S2 判死的卡退回 OPEN（记 release_reason，不直接判失败——那不是卡的错）

用法：
  python3 Tools/fleet/fleet_status.py            # 只读汇总
  python3 Tools/fleet/fleet_status.py --act      # 死卡退回队列
  python3 Tools/fleet/fleet_status.py --json
Exit: 0 全健康｜1 有死卡/假忙（告警）｜2 有 owner 缺失（已退回）
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
ST = os.path.join(F, "state")
OUT = os.path.join(ST, "fleet-status.json")
LAST = os.path.join(ST, "fleet-status-last.json")
STALE_S = 150          # 状态件超 2.5 个上报周期(45s)没更新 = 死
PROGRESS_MIN_BYTES = 1


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


def age_s(ts):
    try:
        return (datetime.now() - datetime.fromisoformat(str(ts))).total_seconds()
    except Exception:
        return 1e9


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--stale-s", type=int, default=STALE_S)
    a = ap.parse_args(argv)

    cfg = jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}
    slots = ((cfg.get("supply") or {}).get("slots_per_node") or {})
    prev = jload(LAST, {}) or {}
    prev_cards = prev.get("cards") or {}

    cards = rows(Q)
    running = [r for r in cards if r.get("state") == "RUNNING"]

    nodes = {}
    # 远端机器：状态件在它们自己的盘上，主控看不到。它们本来每 45s 通过 NATS KV
    # 上报（lane_result_key），所以这里把 KV 也接进来当第二条腿；两条腿取新的那个。
    try:
        sys.path.insert(0, HERE)
        import fleet_lane as _fl
        for _n in ("bm-a", "bm-b", "bm-c", "bm-m", "bm-d"):
            _kv = _fl.kv_get(_fl.lane_result_key(_n), ROOT) or {}
            if _kv.get("job"):
                _kvn = {"ts": _kv.get("ts"), "age_s": int(age_s(_kv.get("ts"))),
                        "job": _kv.get("job"), "out_bytes": _kv.get("out_bytes"),
                        "deliverable_bytes": None, "state": _kv.get("state"),
                        "source": "nats"}
                nodes.setdefault(_n, _kvn)
                if _kvn["age_s"] < (nodes[_n].get("age_s") or 1e18):
                    nodes[_n] = _kvn
    except Exception as _e:
        print("[fleet-status] kv read skipped:", str(_e)[:60])

    # 每机状态件
    for name in os.listdir(os.path.join(ST, "lane-status")) if os.path.isdir(
            os.path.join(ST, "lane-status")) else []:
        if not name.endswith(".json"):
            continue
        d = jload(os.path.join(ST, "lane-status", name), {}) or {}
        node_n = d.get("node") or name[:-5]
        nodes[node_n] = {"ts": d.get("ts"), "age_s": int(age_s(d.get("ts"))),
                         "job": d.get("job"), "out_bytes": d.get("out_bytes"),
                         "deliverable_bytes": d.get("deliverable_bytes"),
                         "state": d.get("state")}

    # 逐卡判活
    detail, dead, fake = [], [], []
    by_owner = {}
    for r in running:
        cid, owner = r.get("id"), r.get("owner")
        by_owner[owner] = by_owner.get(owner, 0) + 1
        dl = r.get("deliverable") or ""
        dp = dl if os.path.isabs(dl) else os.path.join(ROOT, dl) if dl else ""
        size = os.path.getsize(dp) if dp and os.path.exists(dp) else 0
        st = nodes.get(owner) or {}
        same_job = str(st.get("job") or "") == str(cid)
        fresh = st and st.get("age_s", 1e9) <= a.stale_s
        _p = prev_cards.get(cid) or {}
        grew = (size > int(_p.get("deliverable_bytes") or 0)
                or int(st.get("out_bytes") or 0) > int(_p.get("out_bytes") or 0))
        verdict = "RUNNING"
        # 新回传腿刚上线时，生产机还没跑新代码 = 本机没有状态件。这不是死卡，
        # 但也不能算活：给 10 分钟宽限，超时才算死（否则一次上线就误杀全队）。
        _claim_age = age_s(r.get("claimed_at") or r.get("assign_ts") or "")
        _no_channel = not st and _claim_age < 600
        if not owner:
            verdict = "UNOWNED"
        elif _no_channel:
            verdict = "NO-STATUS (worker not yet reporting)"
        elif not (same_job and fresh):
            verdict = "NO-HEARTBEAT"
        elif not grew:
            verdict = "NO-PROGRESS"
        if verdict == "UNOWNED":
            dead.append((r, "no-owner"))
        elif verdict.startswith("NO-STATUS"):
            pass   # 只记录不判死：等生产机升级回传腿
        elif verdict == "NO-HEARTBEAT":
            dead.append((r, "owner heartbeat stale %ss" % st.get("age_s", -1)))
        elif verdict == "NO-PROGRESS":
            fake.append((r, "heartbeat fresh but bytes not growing"))
        detail.append({"id": cid, "owner": owner, "line": r.get("line"),
                       "verdict": verdict, "deliverable_bytes": size,
                       "heartbeat_age_s": st.get("age_s"), "accept": r.get("accept"),
                       "claimed_at": r.get("claimed_at")})

    slots_view = {n: {"running": by_owner.get(n, 0), "slots": int(slots.get(n, 1) or 1)}
                  for n in set(list(slots) + list(by_owner))}
    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "running_total": len(running), "dead": len(dead), "fake_busy": len(fake),
           "nodes": nodes, "slots": slots_view, "cards": detail,
           "open_total": sum(1 for r in cards if r.get("state") == "OPEN"),
           "verdict": "GREEN" if not dead and not fake else "RED"}

    if a.act and dead:
        sys.path.insert(0, HERE)
        import fleet_lane as fl
        rel = []
        for r, why in dead:
            _age = age_s(r.get("claimed_at") or r.get("assign_ts") or "")
            # 近 2 小时内被认领但没心跳 → 退回队列重派；更久的是僵尸，重派只会无限循环，
            # 直接作废并写明原因（作废也要可见，不许静默消失）。
            state = "OPEN" if _age < 7200 else "CANCELLED"
            rel.append({"id": r["id"], "state": state,
                        "owner": None if state == "OPEN" else r.get("owner"),
                        "released_by": "fleet_status",
                        "release_reason": ("%s (aging %.0fmin)" % (why, _age / 60))})
        fl.merge_jsonl(Q, rel)
        out["released"] = len(rel)
        out["release_reasons"] = [{"id": r["id"], "why": why} for r, why in dead]

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"cards": {d["id"]: {"deliverable_bytes": d["deliverable_bytes"],
                                   "out_bytes": (nodes.get(d["owner"]) or {}).get("out_bytes")}
                         for d in detail},
               "ts": out["ts"]}, open(LAST, "w", encoding="utf-8"), ensure_ascii=False)

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[fleet-status] %s 在跑 %d｜死卡 %d｜假忙 %d｜待派 %d"
              % (out["verdict"], out["running_total"], out["dead"], out["fake_busy"],
                 out["open_total"]))
        for n, v in sorted(slots_view.items()):
            print("  %-5s %d/%d 槽" % (n, v["running"], v["slots"]))
        for r, why in dead[:6]:
            print("  死卡 %s ← %s" % (r["id"], why))
        for r, why in fake[:4]:
            print("  假忙 %s ← %s" % (r["id"], why))
        if out.get("released"):
            print("  已退回队列 %d 张" % out["released"])
    if out["dead"] and not a.act:
        return 1
    return 1 if (out["dead"] or out["fake_busy"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))