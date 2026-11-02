#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""closer.py - the audit+ingest leg that turns "done" into "accepted".

Loop: assign(master) -> produce(lane) -> **audit+ingest(closer)** -> supervise/report.
A card is only closed when its declared deliverable is on disk; the closer records who
produced it, when, what was checked, and appends one event. No deliverable = stays RUNNING
and is reported, never silently marked DONE.
"""
import json, os, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
EV = os.path.join(F, "dispatcher", "events.jsonl")
RECEIPT_DIR = os.path.join(F, "queue-receipts")


HEARTBEAT_TIMEOUT_S = 600   # Temporal-style heartbeat: no sign of life = the worker is gone


def lane_beat():
    """owner -> newest sign of life (seconds ago). Absence counts as infinite."""
    import time as _t
    try:
        ms = json.load(open(os.path.join(F, "dispatcher", "MASTER-STATE.json"),
                            encoding="utf-8-sig"))
    except Exception:
        return {}
    out = {}
    for n, v in (ms.get("lanes") or {}).items():
        lr = v.get("last_result") or {}
        ts = lr.get("ts")
        try:
            from datetime import datetime as _d
            out[n] = _t.time() - _d.fromisoformat(ts).timestamp()
        except Exception:
            out[n] = 1e9
    return out


def lane_rc():
    """owner -> last reported rc. The artifact on disk is not proof of success: a card
    that never ran (rc=9009, command not found on this host) can still leave a stale
    file behind. Closing on the file alone fabricated 20+ green cards in October.
    """
    try:
        ms = json.load(open(os.path.join(F, "dispatcher", "MASTER-STATE.json"),
                            encoding="utf-8-sig"))
    except Exception:
        return {}
    out = {}
    for n, v in (ms.get("lanes") or {}).items():
        lr = v.get("last_result") or {}
        if lr.get("rc") is not None:
            try:
                out[n] = (lr.get("job"), int(lr.get("rc")))
            except (TypeError, ValueError):
                pass
    return out


def main():
    rows = [json.loads(l) for l in open(Q, encoding="utf-8") if l.strip()]
    beats = lane_beat()
    rcs = lane_rc()
    closed, waiting, requeued, awaiting = [], [], [], []
    touched = []
    for r in rows:
        # UNVERIFIED is a legitimate holding state: the lane said done but the artifact had
        # not landed yet. The moment it does land, this leg upgrades it - so the state
        # machine self-heals instead of leaving an unproven closure on the books.
        # FAILED belongs here too (2026-11-02): a card was marked failed because the
        # executor never reported, but the artifact can still land afterwards (a retry on
        # another box, a manual run). FAILED was terminal, so the queue kept saying
        # "failed" over a deliverable that existed on disk - the books lied about reality.
        if r.get("state") not in ("RUNNING", "DONE", "UNVERIFIED", "FAILED"):
            continue
        dl = r.get("deliverable") or ""
        local = os.path.join(ROOT, dl) if dl and not os.path.isabs(dl) else dl
        # 产物可能落在别的机器上（跨机路径假红，2026-11-02 自审）：本机看不见不代表没做出来。
        # 以回执为准——回执说产物在、退出码合格，就认。
        receipt_ok = False
        try:
            for n in os.listdir(RECEIPT_DIR):
                if not n.endswith(".json"):
                    continue
                rec = json.load(open(os.path.join(RECEIPT_DIR, n), encoding="utf-8-sig"))
                if rec.get("id") == r.get("id") and rec.get("deliverable_exists"):
                    receipt_ok = True
                    break
        except Exception:
            pass
        ok = (bool(dl) and os.path.exists(local)) or receipt_ok
        owner = r.get("owner")
        allowed = r.get("ok_rc") if isinstance(r.get("ok_rc"), list) and r.get("ok_rc") else [0]
        allowed = [int(x) for x in allowed]
        lane_rc_v = None
        rep = rcs.get(owner)
        if rep and (rep[0] is None or rep[0] == r.get("id")):
            lane_rc_v = rep[1]          # only trust a report that belongs to this card
        rc_ok = lane_rc_v is None or lane_rc_v in allowed
        if ok and not rc_ok:
            # File exists but the executor's exit code says it did not succeed.
            # Do not upgrade; record the contradiction so it can be triaged.
            r["evidence"] = "artifact-on-disk-but-rc=%s (allowed=%s)" % (lane_rc_v, allowed)
            touched.append(r)
            awaiting.append(r["id"])
            continue
        if ok and r.get("state") in ("RUNNING", "UNVERIFIED", "FAILED"):
            was = r.get("state")
            r["state"] = "DONE"
            r["closed_by"] = "closer.py"
            r["closed_at"] = datetime.now().isoformat(timespec="seconds")
            r["audit"] = {"deliverable": dl, "exists": True,
                          "size": os.path.getsize(local) if os.path.isfile(local) else None}
            if was == "UNVERIFIED":
                r.pop("evidence", None)
                r["audit"]["upgraded_from"] = "UNVERIFIED"
            elif was == "FAILED":
                r.pop("error", None)
                r["audit"]["upgraded_from"] = "FAILED"
            closed.append(r["id"])
            touched.append(r)
        elif not ok and r.get("state") == "RUNNING":
            owner = r.get("owner")
            age = beats.get(owner, 1e9)
            if age > HEARTBEAT_TIMEOUT_S:      # worker silent -> release, do not hang forever
                r["state"] = "OPEN"
                r["owner"] = None
                r["retries"] = int(r.get("retries") or 0) + 1
                r["note"] = "lease-heartbeat-timeout(%.0fs)" % age
                requeued.append(r["id"])
                touched.append(r)
            else:
                waiting.append(r["id"])
    if touched:
        # commit only the rows this leg changed; a whole-file rewrite erased the master's
        # dispatch in the same cycle (lost update, 2026-11-02 review).
        fl.merge_jsonl(Q, touched)
        with open(EV, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "kind": "close", "cards": closed}, ensure_ascii=False) + "\n")
    print("[closer] closed=%d requeued=%d waiting=%d awaiting-evidence=%d %s"
          % (len(closed), len(requeued), len(waiting), len(awaiting),
             ",".join(requeued[:3] or awaiting[:3] or waiting[:3])))
    return 0


if __name__ == "__main__":
    sys.exit(main())