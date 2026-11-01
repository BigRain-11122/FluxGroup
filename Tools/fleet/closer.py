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
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
EV = os.path.join(F, "dispatcher", "events.jsonl")


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


def main():
    rows = [json.loads(l) for l in open(Q, encoding="utf-8") if l.strip()]
    beats = lane_beat()
    closed, waiting, requeued = [], [], []
    for r in rows:
        if r.get("state") not in ("RUNNING", "DONE"):
            continue
        dl = r.get("deliverable") or ""
        local = os.path.join(ROOT, dl) if dl and not os.path.isabs(dl) else dl
        ok = bool(dl) and os.path.exists(local)
        if ok and r.get("state") == "RUNNING":
            r["state"] = "DONE"
            r["closed_by"] = "closer.py"
            r["closed_at"] = datetime.now().isoformat(timespec="seconds")
            r["audit"] = {"deliverable": dl, "exists": True,
                          "size": os.path.getsize(local) if os.path.isfile(local) else None}
            closed.append(r["id"])
        elif not ok and r.get("state") == "RUNNING":
            owner = r.get("owner")
            age = beats.get(owner, 1e9)
            if age > HEARTBEAT_TIMEOUT_S:      # worker silent -> release, do not hang forever
                r["state"] = "OPEN"
                r["owner"] = None
                r["retries"] = int(r.get("retries") or 0) + 1
                r["note"] = "lease-heartbeat-timeout(%.0fs)" % age
                requeued.append(r["id"])
            else:
                waiting.append(r["id"])
    if closed or requeued:
        tmp = Q + ".closer.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, Q)
        with open(EV, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "kind": "close", "cards": closed}, ensure_ascii=False) + "\n")
    print("[closer] closed=%d requeued=%d waiting=%d %s"
          % (len(closed), len(requeued), len(waiting), ",".join(requeued[:3] or waiting[:3])))
    return 0


if __name__ == "__main__":
    sys.exit(main())