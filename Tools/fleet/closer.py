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


def main():
    rows = [json.loads(l) for l in open(Q, encoding="utf-8") if l.strip()]
    closed, waiting = [], []
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
            waiting.append(r["id"])
    if closed:
        tmp = Q + ".closer.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, Q)
        with open(EV, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "kind": "close", "cards": closed}, ensure_ascii=False) + "\n")
    print("[closer] closed=%d waiting=%d %s" % (len(closed), len(waiting),
                                                ",".join(waiting[:4])))
    return 0


if __name__ == "__main__":
    sys.exit(main())