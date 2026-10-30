#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_deadline.py - output timeliness + direction alignment, measured on git receipts.

Why a separate leg: the master already knew each line's *evidence dir* freshness, but on the
control plane most business evidence lives on another machine, so every stage read NO-DATA
and the fleet looked calm while lines were silently starved. Operations land receipts in git
(`cph4/fleet/queue-receipts/`), and that is the one surface the Mac can always see - even
when a lane is asleep. So freshness is measured there.

Two verdicts, no model, no invention:

  output  : last receipt for a line vs its `stale_after_h`  -> OK / LATE / NO-DATA
  direction: does at least one open card or receipt in the last 24h touch a current CEO
             priority (cph4/fleet/NORTH-STAR.json)? -> ALIGNED / DRIFT

LATE lines get one JUDGMENT entry per line per day (dedupe by key), never a fake work card.

Usage: python3 Tools/fleet/fleet_deadline.py [--dry]
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
JUDGMENT = os.path.join(FLEET, "dispatcher", "JUDGMENT-QUEUE.jsonl")
OUT_MD = os.path.join(FLEET, "dispatcher", "DEADLINES.md")
STAR = os.path.join(FLEET, "NORTH-STAR.json")


def load(p, default):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def jl(p):
    out = []
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def append_jl(p, row):
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def output_globs():
    return load(os.path.join(FLEET, "OUTPUT-SOURCES.json"), {}).get("lines") or {}


def newest_by_glob(patterns):
    import glob as _g
    best = None
    for pat in patterns:
        for p in _g.glob(os.path.join(ROOT, pat), recursive=True):
            if os.path.isfile(p):
                mt = os.path.getmtime(p)
                if best is None or mt > best[0]:
                    best = (mt, os.path.relpath(p, ROOT))
    return best


def receipt_index():
    """line id -> (mtime, filename). Filename convention carries the line id."""
    idx = {}
    if not os.path.isdir(RECEIPTS):
        return idx
    for f in os.listdir(RECEIPTS):
        p = os.path.join(RECEIPTS, f)
        if not os.path.isfile(p):
            continue
        # brain-*.md is the control plane's own daily essay, not line output. Counting it
        # made every line look fresh (2026-10-31 false-green); only real receipts count.
        if f.startswith("brain-"):
            continue
        try:
            mt = os.path.getmtime(p)
        except OSError:
            continue
        for m in re.finditer(r"(bigstream-[a-z]+|bigmoney|biggame|bighouse|biglife|bigdomain|bigcompute|fluxverse|car-gaming|recon)", f):
            k = m.group(1)
            if k not in idx or idx[k][0] < mt:
                idx[k] = (mt, f)
    return idx


def main() -> int:
    dry = "--dry" in sys.argv
    reg = load(os.path.join(FLEET, "LINE-REGISTRY.json"), {})
    star = load(STAR, {})
    ms_lanes = (load(os.path.join(FLEET, "dispatcher", "MASTER-STATE.json"), {})
                .get("lanes") or {})
    lanes_online = {n for n, v in ms_lanes.items() if v.get("online")}
    idx = receipt_index()
    now = time.time()
    rows, late = [], []
    for ln in reg.get("lines") or []:
        lid = ln.get("id")
        if (ln.get("status") or "") == "PARKED":
            continue      # CEO 明令停产：不是欠产出
        limit_h = float(ln.get("stale_after_h") or 48)
        # Which machines are supposed to produce this line? If none is online, silence is
        # expected (NO-LANE); if one is online, silence is a real miss (NO-OUTPUT).
        want = {st.get("lane") for st in (ln.get("stages") or []) if st.get("lane")}
        if want and not (want & lanes_online):
            rows.append((lid, "NO-LANE", None, limit_h, "承办机不在线：%s" % ",".join(sorted(want)),
                         ln.get("owner")))
            continue
        # Prefer the line's declared output globs when present: MV ships into canon/outbound,
        # and judging it by queue-receipts alone reported "no output" while the film moved.
        gl = output_globs().get(lid)
        hit = newest_by_glob(gl) if gl else idx.get(lid)
        if not hit:
            rows.append((lid, "NO-OUTPUT", None, limit_h,
                         "承办机在线（%s）但 24h 无落库回执" % ",".join(sorted(want or {"?"})),
                         ln.get("owner")))
            late.append((lid, 24.0, limit_h, "no receipt", ln.get("owner")))
            continue
        age_h = (now - hit[0]) / 3600
        v = "OK" if age_h <= limit_h else "LATE"
        rows.append((lid, v, age_h, limit_h, hit[1], ln.get("owner")))
        if v == "LATE":
            late.append((lid, age_h, limit_h, hit[1], ln.get("owner")))

    # direction: current CEO priorities must actually be moving
    today = datetime.now().strftime("%Y%m%d")
    qrows = [r for r in jl(QUEUE) if r.get("state") in ("OPEN", "RUNNING")]
    recent = [f for f in os.listdir(RECEIPTS) if os.path.getmtime(os.path.join(RECEIPTS, f)) > now - 86400] \
        if os.path.isdir(RECEIPTS) else []
    blob = " ".join([json.dumps(r, ensure_ascii=False) for r in qrows] + recent).lower()
    prios = star.get("priorities") or []
    aligned, missing = [], []
    running = [r for r in qrows if r.get("state") == "RUNNING"]
    for p in prios:
        if p.get("id") == "fleet-dispatch":
            # dispatch quality is proven by work actually running, not by the word "队列"
            (aligned if running else missing).append(p.get("id") if running else p)
            continue
        kws = [k.lower() for k in (p.get("keywords") or [])]
        (aligned if any(k in blob for k in kws) else missing).append(
            p.get("id") if any(k in blob for k in kws) else p)

    if late and not dry:
        have = {r.get("key") for r in jl(JUDGMENT)}
        made = 0
        for lid, age_h, limit_h, src, owner in late:
            if made >= 3:
                break      # 一天最多 3 条时效问询，避免把判断队列灌成噪音
            key = "LINE-LATE:%s:%s" % (lid, today)
            if key in have:
                continue
            append_jl(JUDGMENT, {
                "key": key, "kind": "LINE-LATE", "subject": lid,
                "question": "这条线已 %.0f 小时没有落库产出（阈值 %.0f），下一步该做什么？" % (age_h, limit_h),
                "evidence": {"last_receipt": src, "age_h": round(age_h, 1), "limit_h": limit_h,
                             "owner": owner},
                "tier": "local", "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                "state": "OPEN"})
            made += 1

    lines = ["# 产出与方向 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), "",
             "- 24h 新增回执 %d 份 · 队列在跑 %d 件 · 方向 %s"
             % (len(recent), len(qrows), "对齐" if not missing else "有缺口"),
             "", "## 产出时效"]
    for lid, v, age_h, limit_h, src, _owner in rows:
        if v in ("NO-DATA", "NO-LANE", "NO-OUTPUT"):
            lines.append("- %-18s %-9s %s" % (lid, v, src))
        else:
            lines.append("- %-18s %-4s 最近 %.1fh 前 / 阈值 %.0fh（%s）" % (lid, v, age_h, limit_h, src))
    lines += ["", "## 方向对齐（当前优先事项）"]
    if not prios:
        lines.append("- 未声明 NORTH-STAR（不判方向）")
    else:
        for p in prios:
            mark = "有活在跑" if p.get("id") in aligned else "**无活**"
            lines.append("- %-10s %s · %s" % (p.get("id"), p.get("why", ""), mark))
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("[deadline] late=%d no_data=%d align_missing=%d%s"
          % (len(late), sum(1 for r in rows if r[1] != "OK"), len(missing),
             " (dry)" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())