# -*- coding: utf-8 -*-
"""brain_brief.py - the control plane's own one-page brief, computed from facts.

Why (CEO 2026-11-01: 大脑要「及时、准确、创新、严格」):
  * 及时 - it runs on the pulse, so the page is never older than the slow batch;
  * 准确 - every line in it is keyed to a path on disk or a queue row; no impressions;
  * 创新 - it does not list status, it names the ONE decision that moves the fleet now;
  * 严格 - a line with no artifact is printed as NO-EVIDENCE, never as "在推进".

Output: cph4/fleet/dispatcher/BRAIN.md (one page, regenerated; history stays in events.jsonl)

Usage: python3 Tools/fleet/brain_brief.py [--root PATH]
"""
import argparse
import glob
import json
import os
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "dispatcher", "BRAIN.md")
OFFLINE_AFTER = 1800          # a lane file older than this is a dead box, not a busy one


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def jl(p):
    out = []
    try:
        with open(p, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        pass
    except Exception:
        pass
    return out


def evidence_state(paths):
    """(newest_ts, newest_path, state) where state is EVIDENCE / EMPTY / OFFBOX.

    OFFBOX matters for honesty: gaming/MiniGame and quant/bigmoney are separate repos and
    the media trees only exist on the production boxes. A line whose evidence root is not
    on this clone has NOT been proven idle - it is unobserved. Reporting that as "无产出"
    would be the exact "没回执就倒推没干活" mistake (2026-11-01 判例).
    """
    best, bestp, seen_root, existing = 0.0, "", False, False
    for pat in paths or []:
        full = os.path.join(ROOT, pat)
        if os.path.isdir(full):
            seen_root = True
            for dp, _dn, fns in os.walk(full):
                for fn in fns:
                    existing = True
                    try:
                        m = os.path.getmtime(os.path.join(dp, fn))
                    except Exception:
                        continue
                    if m > best:
                        best, bestp = m, os.path.join(dp, fn)
        else:
            hits = [p for p in glob.glob(full, recursive=True) if os.path.isfile(p)]
            if hits:
                seen_root = True
                existing = True
                for p in hits:
                    m = os.path.getmtime(p)
                    if m > best:
                        best, bestp = m, p
    if not seen_root:
        return 0.0, "", "OFFBOX"
    if not existing:
        return 0.0, "", "EMPTY"
    return best, bestp, "EVIDENCE"


def machine_names():
    """code -> 人话机名. CEO 2026-11-02: 不要用 bm-x 代号，他看不懂是哪台。"""
    try:
        import sys as _s
        _s.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
        import fleet_lane as _fl
        return {k: (v.get("name_cn") or k) for k, v in _fl.LANES.items()}
    except Exception:
        return {}


def rel(p):
    try:
        return os.path.relpath(p, ROOT)
    except Exception:
        return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    import builtins
    rows_q = jl(os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl"))
    rows_b = jl(os.path.join(root, "cph4", "fleet", "PRODUCTION-BACKLOG.jsonl"))
    reg = jload(os.path.join(root, "cph4", "fleet", "LINE-REGISTRY.json"), {})
    steps = jload(os.path.join(root, "cph4", "fleet", "LINE-NEXT-STEPS.json"), {})
    pulse = jload(os.path.join(root, "cph4", "fleet", "dispatcher", "PULSE.json"), {})
    now = time.time()
    NAME = machine_names()   # 人话机名，全篇统一使用（CEO 令：不要代号）

    inflight = {}
    for r in rows_q + rows_b:
        if r.get("state") in ("OPEN", "RUNNING"):
            inflight.setdefault(r.get("line") or "", []).append(r.get("id"))

    lanes = {}
    for fn in glob.glob(os.path.join(root, "cph4", "fleet", "lanes", "*.json")):
        d = jload(fn, {})
        node = d.get("node") or os.path.basename(fn)[:-5]
        age = now - os.path.getmtime(fn)
        lanes[node] = {"age_s": round(age, 0), "online": age <= OFFLINE_AFTER,
                       "jobs": [j.get("id") for j in d.get("jobs") or []],
                       "note": d.get("capacity_note") or "", "idle": d.get("idle_reason") or ""}
    # The pulse node is alive by definition while its own PULSE.json is fresh: lane_agent
    # on the control plane does not rewrite lanes/<node>.json, so reading only that file
    # reported the master as "掉线" while it was busy producing this very page.
    pl = pulse.get("node") or ""
    if pl and pl in lanes and str(pulse.get("ts") or "")[:10] == datetime.now().strftime("%Y-%m-%d"):
        lanes[pl]["online"] = True
        lanes[pl].setdefault("jobs", [])

    lines = []
    for ln in (reg.get("lines") or []):
        lid = ln.get("id")
        if not lid:
            continue
        last_ts, last_p, ev_state = evidence_state(
            [p for st in (ln.get("stages") or []) for p in (st.get("evidence") or [])])
        age_h = round((now - last_ts) / 3600.0, 1) if last_ts else None
        limit = float(ln.get("stale_after_h") or 48)
        job = (inflight.get(lid) or [None])[0]
        has_next = bool(((steps.get("lines") or {}).get(lid) or {}).get("cards"))
        status = ln.get("status") or "ACTIVE"
        if status == "PARKED":
            verdict = "PARKED"
        elif job:
            verdict = "WORKING"
        elif ev_state == "OFFBOX":
            verdict = "OFFBOX"          # 证据在别的机器上，本机看不见，不代表没干活
        elif ev_state == "EMPTY":
            verdict = "NO-EVIDENCE"     # 目录在、里面是空的
        elif age_h is not None and age_h > limit:
            verdict = "LATE"
        else:
            verdict = "OK"
        lines.append({"id": lid, "name": ln.get("name"), "verdict": verdict, "age_h": age_h,
                      "limit": limit, "job": job, "has_next": has_next,
                      "evidence": rel(last_p) if last_p else ""})

    failed = [r for r in rows_q if r.get("state") == "FAILED"]
    # Rows the local 4B refused to decide. They are my work, not the fleet's: the cloud
    # seat only exists inside an agent session, so a script must never pretend to close
    # them (CEO 2026-11-01: 不超能力，该上云就上云).
    escalated = [r for r in jl(os.path.join(root, "cph4", "fleet", "dispatcher",
                                            "JUDGMENT-QUEUE.jsonl"))
                 if r.get("state") == "ESCALATED"]
    open_n = len([r for r in rows_q if r.get("state") == "OPEN"])
    run_n = len([r for r in rows_q if r.get("state") == "RUNNING"])
    idle_boxes = [n for n, v in lanes.items() if v["online"] and not v["jobs"]]

    # THE decision: the most valuable line that is LATE / NO-EVIDENCE but has a declared
    # next product and no card running. Ties break on cadence (tighter deadline first).
    cands = [l for l in lines if l["verdict"] in ("LATE", "NO-EVIDENCE") and not l["job"]]
    cands.sort(key=lambda l: (0 if l["has_next"] else 1, l["limit"], l["age_h"] or 0))
    decision = None
    if escalated:
        # Escalated judgments outrank dispatch: they are decisions already blocking lines,
        # and only an agent session (cloud seat) can answer them.
        decision = ("先清 %d 件 ESCALATED 判断（本地 4B 判不了→上云席位，我自己来）"
                    % len(escalated))
    elif cands:
        c = cands[0]
        decision = ("派 %s 的下一步产物（现 %s，阈值 %.0fh，声明=%s）"
                    % (c["id"], ("无产出证据" if c["age_h"] is None else "%.1fh 前" % c["age_h"]),
                       c["limit"], "有" if c["has_next"] else "无"))
    elif idle_boxes:
        decision = "%s 空闲且无线到期：按 CPU-CAPACITY 补料或停一台省电" % "、".join(NAME.get(x, x) for x in idle_boxes)
    else:
        decision = "全线在跑，无待决"

    L = []
    L.append("# 大脑简报 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    L.append("")
    L.append("## 本轮唯一决策")
    L.append("- **%s**" % decision)
    L.append("")
    L.append("## 机队事实（来源：lanes/*.json + PULSE.json）")
    live = "、".join("%s%s" % (NAME.get(n, n), "" if v["jobs"] else "（空闲）")
                    for n, v in sorted(lanes.items()) if v["online"]) or "无"
    dead = [NAME.get(n, n) for n, v in lanes.items() if not v["online"]]
    L.append("- 在线：%s%s" % (live, ("；掉线：" + "、".join(dead)) if dead else ""))
    L.append("- 队列：跑 %d · 待派 %d · 失败 %d｜主控脉 %s（%s）"
             % (run_n, open_n, len(failed), "ok" if pulse.get("ok") else "DEGRADED",
                (pulse.get("ts") or "-")[:16]))
    L.append("")
    L.append("## 逐线（每条都指向盘上证据，无证据就是无证据）")
    L.append("")
    L.append("| 线 | 判定 | 最近产出 | 在跑卡 | 下一步已声明 |")
    L.append("|---|---|---|---|---|")
    order = {"LATE": 0, "NO-EVIDENCE": 1, "OFFBOX": 2, "WORKING": 3, "OK": 4, "PARKED": 5}
    for l in sorted(lines, key=lambda x: (order.get(x["verdict"], 9), x["id"])):
        age = ("证据在别机" if l["verdict"] == "OFFBOX" else "无证据") if l["age_h"] is None else "%.1fh" % l["age_h"]
        L.append("| %s | %s | %s | %s | %s |" % (l["id"], l["verdict"], age,
                                                 l["job"] or "-", "是" if l["has_next"] else "否"))
    if failed:
        L.append("")
        L.append("## 失败件（不许挂着）")
        for r in failed:
            res = r.get("result") or {}
            L.append("- `%s` rc=%s %s" % (r.get("id"), res.get("rc"),
                                          str(res.get("note") or res.get("stderr") or "")[:90]))
    L.append("")
    L.append("## 本机角色自检（轻度赋能：主控是不是在抢生产的活）")
    try:
        la = os.getloadavg()
        nproc = os.cpu_count() or 1
        seat = jload(os.path.join(root, "cph4", "fleet", "BRAIN-SEAT.json"), {})
        tiers = seat.get("tiers") or []
        act = [t.get("id") for t in tiers if str(t.get("state") or "").upper() == "ACTIVE"]
        pend = [t.get("id") for t in tiers if str(t.get("state") or "").upper() != "ACTIVE"]
        L.append("- 负载 %.2f/%.2f/%.2f（%d 核，占比 %.0f%%）"
                 % (la[0], la[1], la[2], nproc, 100.0 * la[0] / nproc))
        L.append("- 判断席：在用 %s%s" % (",".join(act) or "未声明",
                                          ("；待接管 " + ",".join(pend)) if pend else ""))
        L.append("- 判据：主控只做判断/派单/监督；本机负载长期接近核数＝角色越界，应把活路由出去")
    except Exception:
        L.append("- 负载不可读")
    L.append("")
    L.append("## 严格性自检")
    L.append("- 本页所有判定均来自 lanes/*.json、PRODUCTION-QUEUE/BACKLOG 与 LINE-REGISTRY 的证据目录；")
    L.append("- 「NO-EVIDENCE」= 证据目录里没有任何文件，不得读成「在推进」；")
    L.append("- 主控脉非 ok 时，本页其余内容一律视为过期。")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(L) + "\n")
    print("[brain] lines=%d late=%d no-evidence=%d decision=%s"
          % (len(lines), len([l for l in lines if l["verdict"] == "LATE"]),
             len([l for l in lines if l["verdict"] == "NO-EVIDENCE"]), decision[:60]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())