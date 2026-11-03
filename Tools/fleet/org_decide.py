#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""org_decide.py - 线级"该加算力 / 该修 / 该砍"的机器判定。

为什么（2026-11-03 CEO「你科学决策优化 并落地执行」）：
  现有判定层各管一段：ops_metrics 管过闸率自动停线，squeeze 管压榨余量，inventory 管断粮。
  但没有人回答"这条 ACTIVE 线到底有没有产物、主控看不看得见"。实测 15 条线里 7 条 ACTIVE
  在本机一条证据路径都不存在 —— 状态是自称，不是事实。本工具只做**判定与排序**，不改状态
  （唯一状态写入口仍是 ops_metrics/人工），避免第二处各写一套判据。

判据（三条，全部来自盘上事实）：
  1. 可见性：证据路径在本机存在几条 → 0 条 = EVIDENCE-BLIND（"在役"不可核）
  2. 产物年龄：证据目录里**非文档产物**（视频/图/音频/CSV/包）的最新 mtime；
     只改 .md/.json 台账不算产物（否则写文档就能装成有产出）
  3. 停滞：产物年龄 > stale_after_h → STALE

输出（每线一条建议）：
  INVEST   有新鲜产物 + 车道有余量 → 可加卡
  KEEP     有产物、节奏正常
  FIX-EVIDENCE  标 ACTIVE 但证据不可见 → 先修路径/投影，不许再报在役
  PARK-RECOMMEND 无产物超期 → 建议停（需 ops_metrics 或人执行）
  PARKED   已停

Exit: 0 全部可核；2 有 ACTIVE 线证据不可见（假绿告警）。
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(ROOT, "cph4", "fleet", "LINE-REGISTRY.json")
STATE = os.path.join(ROOT, "cph4", "fleet", "state", "squeeze.json")
DOC_EXT = (".md", ".json", ".jsonl", ".txt", ".yaml", ".yml")


def newest(paths, skip_doc):
    t = 0.0
    for p in paths:
        full = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if not os.path.exists(full):
            continue
        if os.path.isdir(full):
            for dp, _, fs in os.walk(full):
                for f in fs:
                    if skip_doc and f.lower().endswith(DOC_EXT):
                        continue
                    try:
                        t = max(t, os.path.getmtime(os.path.join(dp, f)))
                    except OSError:
                        pass
        else:
            if skip_doc and full.lower().endswith(DOC_EXT):
                continue
            try:
                t = max(t, os.path.getmtime(full))
            except OSError:
                pass
    return t


def receipts_by_line():
    """产物回执按线前缀归集（回执是"干过活"的唯一机读证据）。"""
    d = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
    out = {}
    if not os.path.isdir(d):
        return out
    for f in os.listdir(d):
        p = os.path.join(d, f)
        try:
            t = os.path.getmtime(p)
        except OSError:
            continue
        low = f.lower()
        for key in ("quant", "drama", "mv", "asset", "game", "city", "voice", "car"):
            if key in low:
                out.setdefault(key, []).append(t)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--apply", action="store_true",
                    help="把 visibility/last_artifact_h 写回 LINE-REGISTRY（只加字段，不改 status）")
    ap.add_argument("--out", default=os.path.join("cph4", "fleet", "state", "org-decide.json"))
    a = ap.parse_args(argv)
    reg = json.load(open(REG, encoding="utf-8"))
    cap = {}
    if os.path.exists(STATE):
        try:
            s = json.load(open(STATE, encoding="utf-8"))
            for n in s.get("nodes") or []:
                cap[n.get("node")] = n.get("can_take_more") or n.get("can_take") or 0
        except Exception:
            pass
    rl = receipts_by_line()
    now = time.time()
    rows, blind = [], []
    for ln in reg.get("lines") or []:
        ev = []
        for st in ln.get("stages") or []:
            ev += list(st.get("evidence") or [])
        ev = [e for e in ev if not e.startswith(("D:", "K:", "C:"))]
        exist = [e for e in ev if os.path.exists(os.path.join(ROOT, e)
                                                if not os.path.isabs(e) else e)]
        # 使能线（基建/竞品拆解）的产物本来就是文档与闸，不能按"文档不算产物"判死；
        # 业务线才要求非文档产物（否则写一篇 md 就能装成有产出）。
        doc_is_product = (ln.get("org") in ("enabling", "platform"))
        art_t = newest(exist, skip_doc=not doc_is_product)
        doc_t = newest(exist, skip_doc=False)
        # 回执也当产物证据（按线关键词匹配，找不到就不算）
        keymap = {"bigstream-mv": "mv", "bigstream-drama": "drama", "bigmoney": "quant",
                  "asset-lib": "asset", "biggame": "game", "car-gaming": "game",
                  "fluxverse": "city", "biglife": "city", "bighouse": "city",
                  "bigdomain": "city", "bigcompute": "city"}
        k = keymap.get(ln.get("id"))
        if k and rl.get(k):
            art_t = max(art_t, max(rl[k]))
        age_art = (now - art_t) / 3600 if art_t else None
        age_doc = (now - doc_t) / 3600 if doc_t else None
        status = ln.get("status") or "?"
        stale_after = ln.get("stale_after_h") or reg.get("default_stale_after_h") or 48
        if not exist and status == "ACTIVE":
            verdict = "FIX-EVIDENCE"
            blind.append(ln.get("id"))
        elif status in ("PARKED", "PAUSED", "DORMANT"):
            verdict = "PARKED"
        elif age_art is None or age_art > stale_after:
            verdict = "PARK-RECOMMEND"
        elif cap and sum(cap.values()) > 0:
            verdict = "INVEST"
        else:
            verdict = "KEEP"
        rows.append({"id": ln.get("id"), "name": ln.get("name"), "status": status,
                     "evidence_paths": len(ev), "evidence_visible": len(exist),
                     "last_artifact_h": round(age_art, 1) if age_art is not None else None,
                     "last_doc_h": round(age_doc, 1) if age_doc is not None else None,
                     "stale_after_h": stale_after, "verdict": verdict,
                     "priority": ln.get("priority")})
        if a.apply:
            ln["visibility"] = "OK" if exist else "BLIND"
            ln["last_artifact_h"] = (round(age_art, 1) if age_art is not None else None)
    order = {"FIX-EVIDENCE": 0, "PARK-RECOMMEND": 1, "INVEST": 2, "KEEP": 3, "PARKED": 4}
    rows.sort(key=lambda r: (order.get(r["verdict"], 9),
                             r["last_artifact_h"] if r["last_artifact_h"] is not None else 9999))
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "lines": len(rows),
           "by_verdict": {v: sum(1 for r in rows if r["verdict"] == v) for v in order},
           "capacity_free_slots": sum(cap.values()) if cap else None,
           "blind_active": blind, "rows": rows}
    if a.apply:
        json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        out["applied"] = "visibility/last_artifact_h 已写回 LINE-REGISTRY"
    p = os.path.join(ROOT, a.out) if not os.path.isabs(a.out) else a.out
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        bv = out["by_verdict"]
        print("[decide] %d 条线：可加算力 %d / 正常 %d / 建议停 %d / 证据看不见 %d / 已停 %d"
              % (len(rows), bv["INVEST"], bv["KEEP"], bv["PARK-RECOMMEND"],
                 bv["FIX-EVIDENCE"], bv["PARKED"]))
        for r in rows:
            if r["verdict"] == "FIX-EVIDENCE":
                print("  ! %-20s 标 %s 但证据路径 0 条可见（%d 条声明）"
                      % (r["id"], r["status"], r["evidence_paths"]))
            elif r["verdict"] == "PARK-RECOMMEND":
                print("  ! %-20s 产物年龄 %s h > 阈值 %s h → 建议停"
                      % (r["id"], r["last_artifact_h"], r["stale_after_h"]))
    return 0 if not blind else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))