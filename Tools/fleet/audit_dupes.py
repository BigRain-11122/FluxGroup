#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_dupes.py - find the four things the CEO keeps paying for twice:

  1. 重复活   same title / same cmd / same deliverable dispatched more than once
  2. 无产出   cards that ran, produced nothing, and were retried or closed anyway
  3. 闲置     lanes with capacity but no job while open work exists
  4. 同步坏   pulse cycles that skipped git or failed to push

Read-only. Writes cph4/fleet/state/dupes.json and prints a ledger.
Why: the 2026-11-02 review found 7 scripts rewriting one queue, 207 receipts with no
common schema, and 90/97 cards with no `line`. Duplication was invisible, so it could
not be removed -- only argued about.

Usage: python3 audit_dupes.py [--json] [--since HOURS]
"""
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
RECEIPTS = os.path.join(F, "queue-receipts")
MASTER = os.path.join(F, "dispatcher", "MASTER-STATE.json")
PULSE_LOG = "/tmp/fluxgroup-pulse.log"

TITLE_NOISE = re.compile(r"[\s\-_/#:：（）()\[\]【】0-9]+")


def jlines(p):
    out = []
    try:
        with open(p, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return out


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def norm_title(t):
    return TITLE_NOISE.sub("", str(t or "").lower())


def cmd_hash(c):
    c = str(c or "").strip()
    return hashlib.sha1(c.encode("utf-8")).hexdigest()[:10] if c else ""


def dup_groups(rows):
    """Three independent signals: same normalized title, same cmd, same deliverable."""
    out = {}
    for label, keyfn in (
        ("title", lambda r: norm_title(r.get("title"))),
        ("cmd", lambda r: cmd_hash(r.get("cmd"))),
        ("deliverable", lambda r: str(r.get("deliverable") or "").strip()),
    ):
        g = defaultdict(list)
        for r in rows:
            k = keyfn(r)
            if k:
                g[k].append(r)
        out[label] = [
            {"key": k[:90], "n": len(v),
             "ids": [x.get("id") for x in v][:8],
             "states": [x.get("state") for x in v][:8]}
            for k, v in g.items() if len(v) > 1
        ]
    return out


def no_output(rows, receipts):
    """A card that finished but whose deliverable never existed."""
    by_id = {}
    for r in receipts:
        if isinstance(r, dict) and r.get("id"):
            by_id.setdefault(r["id"], []).append(r)
    no_file, no_rc, failed = [], [], []
    for cid, recs in by_id.items():
        last = recs[-1]
        rc = last.get("rc")
        if rc is None:
            no_rc.append(cid)
        elif int(rc) != 0:
            failed.append((cid, rc, last.get("error_class") or ""))
        if last.get("deliverable") and last.get("deliverable_exists") is False:
            no_file.append((cid, rc))
    retried = [(r.get("id"), int(r.get("retries") or 0)) for r in rows
               if int(r.get("retries") or 0) >= 2]
    return {"ran_without_deliverable": len(no_file), "samples_no_file": no_file[:8],
            "receipt_without_rc": len(no_rc), "samples_no_rc": no_rc[:5],
            "nonzero_rc": len(failed), "samples_nonzero": failed[:8],
            "cards_retried_2plus": len(retried), "samples_retried": retried[:8]}


def idle_vs_work(rows):
    ms = jload(MASTER, {}) or {}
    lanes = ms.get("lanes") or {}
    open_cards = [r for r in rows if r.get("state") in ("OPEN", "RUNNING")]
    out = {"open_or_running": len(open_cards), "lanes": {}}
    for n, v in lanes.items():
        out["lanes"][n] = {
            "job": v.get("job"),
            "hb_age_s": round(v.get("hb_age_s") or 0, 1),
            "ram_free_gb": v.get("ram_free_gb"),
            "cpu_pct": v.get("cpu_load_pct"),
            "gpu_pct": v.get("gpu_util_pct"),
            "idle_rounds": (ms.get("idle_rounds") or {}).get(n),
            "idle_with_work": bool(not v.get("job") and open_cards),
        }
    return out


def sync_health():
    """How often the loop could not push, and why."""
    reasons = Counter()
    cycles = ok = 0
    try:
        with open(PULSE_LOG, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-400:]
    except FileNotFoundError:
        return {"cycles": 0, "skipped": 0, "reasons": {}}
    for ln in lines:
        if "pulse " not in ln:
            continue
        cycles += 1
        m = re.search(r"git=skipped:([^\s]+)|git=([a-z\-]+)", ln)
        if "skipped" in ln:
            tag = (m.group(1) if (m and m.group(1)) else "unknown")[:40]
            reasons[tag] += 1
        if "pulse OK" in ln:
            ok += 1
    return {"cycles": cycles, "ok": ok, "skipped": sum(reasons.values()),
            "reasons": dict(reasons.most_common(6))}


def dup_scripts():
    """Scripts whose names share a verb+noun stem, i.e. likely two implementations."""
    d = HERE
    names = sorted(n[:-3] for n in os.listdir(d) if n.endswith(".py"))
    stems = defaultdict(list)
    for n in names:
        parts = re.split(r"[_\-]", n)
        stems[parts[-1]].append(n)
        if len(parts) > 1:
            stems["~".join(parts[-2:])].append(n)
    groups = {k: sorted(set(v)) for k, v in stems.items() if len(set(v)) > 1 and k != ""}
    # only report groups where the shared token is meaningful
    interesting = {k: v for k, v in groups.items()
                   if any(len(x) > 3 for x in [k]) and not k.startswith("~")}
    return dict(sorted(interesting.items(), key=lambda kv: -len(kv[1]))[:12])


def main(argv):
    os.makedirs(STATE, exist_ok=True)
    rows = jlines(QUEUE)
    backlog = jlines(BACKLOG)
    receipts = []
    if os.path.isdir(RECEIPTS):
        for n in sorted(os.listdir(RECEIPTS)):
            if n.endswith(".json"):
                x = jload(os.path.join(RECEIPTS, n))
                if isinstance(x, dict):
                    receipts.append(x)

    live = [r for r in rows if r.get("state") not in ("CANCELLED",)]
    out = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "source": "audit_dupes.py - read only",
        "queue": {"total": len(rows), "live": len(live)},
        "duplicates": dup_groups(live),
        "no_output": no_output(live, receipts),
        "idle_vs_work": idle_vs_work(live),
        "sync": sync_health(),
        "script_stems": dup_scripts(),
        "backlog_dupes": len(dup_groups(backlog).get("title") or []),
    }
    with open(os.path.join(STATE, "dupes.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    d = out["duplicates"]
    print("== 重复活（活跃卡）")
    for kind in ("title", "cmd", "deliverable"):
        gs = [g for g in d[kind] if g["n"] > 1]
        print("  %-12s %d 组, 涉及 %d 张卡" % (kind, len(gs), sum(g["n"] for g in gs)))
        for g in sorted(gs, key=lambda x: -x["n"])[:3]:
            print("     x%-2d %s  %s" % (g["n"], g["key"][:46], g["ids"][:3]))

    n = out["no_output"]
    print("== 无产出")
    print("  跑完但交付物不存在 %d | 回执无 rc %d | rc!=0 %d | 重试>=2 次 %d"
          % (n["ran_without_deliverable"], n["receipt_without_rc"],
             n["nonzero_rc"], n["cards_retried_2plus"]))
    for x in n["samples_no_file"][:3]:
        print("     %s rc=%s" % x)
    for x in n["samples_retried"][:3]:
        print("     重试 %s x%s" % x)

    iv = out["idle_vs_work"]
    print("== 闲置对账（在飞 %d 张卡）" % iv["open_or_running"])
    for k, v in iv["lanes"].items():
        print("  %-6s job=%-28s hb=%5ss ram=%-6s idle_rounds=%-4s %s"
              % (k, str(v["job"])[:28], v["hb_age_s"], v["ram_free_gb"],
                 v["idle_rounds"], "IDLE-WITH-WORK" if v["idle_with_work"] else ""))

    s = out["sync"]
    print("== 同步 %d 轮, skipped %d" % (s["cycles"], s["skipped"]))
    for k, v in (s.get("reasons") or {}).items():
        print("   x%-3d %s" % (v, k))

    print("== 疑似双份实现")
    for k, v in out["script_stems"].items():
        if len(v) > 1:
            print("   %-14s %s" % (k, ", ".join(v)))
    print("-> cph4/fleet/state/dupes.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))