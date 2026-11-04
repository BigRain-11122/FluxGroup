#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clock_resync.py - node-side w32time status + best-effort resync, always writes a receipt.

Why this exists
---------------
cph4/fleet/dispatcher/CLOCK-SKEW.json reports bm-b/bm-c as SKEW-HIGH (offset beyond
2*precision+20). The offset is self-reported by each node (clock_offset_ms), so the fix
can only run ON that node. Before this script the fleet had no locatable owner for the
fix: every shift could only say "clock drifted" and re-log it (R4-4 family).

Nothing here is fatal by design: a resync denied for lack of elevation is still
evidence (verdict=DENIED-NEED-ELEVATION), and the caller keeps a JSON artifact.

Usage (from a queue card or by hand on the node):
    python Tools/fleet/clock_resync.py --out D:/FleetWorker/clock_resync-bm-b.json
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def run(args, timeout=40):
    t0 = time.time()
    try:
        p = subprocess.run(args, capture_output=True, text=True, errors="replace",
                           timeout=timeout, creationflags=CREATE_NO_WINDOW)
        return {"argv": list(args), "rc": p.returncode,
                "out": (p.stdout or "").strip(), "err": (p.stderr or "").strip(),
                "seconds": round(time.time() - t0, 2)}
    except FileNotFoundError:
        return {"argv": list(args), "rc": 127, "out": "", "err": "binary-missing",
                "seconds": 0.0}
    except subprocess.TimeoutExpired:
        return {"argv": list(args), "rc": 124, "out": "", "err": "timeout",
                "seconds": float(timeout)}
    except Exception as e:  # noqa: BLE001 - receipt must survive anything
        return {"argv": list(args), "rc": 125, "out": "", "err": "exception: %s" % e,
                "seconds": 0.0}


def service_state():
    r = run(["sc", "query", "w32time"])
    text = (r["out"] + " " + r["err"]).upper()
    if "RUNNING" in text.replace("STOP_PENDING", ""):
        state = "RUNNING"
    elif "STOPPED" in text:
        state = "STOPPED"
    else:
        state = "UNKNOWN"
    return state, r


# w32tm exits with raw HRESULTs, which carry the real meaning; the text is localized
# (a zh-CN box prints 服务尚未启动, so text matching alone mislabels it as UNKNOWN).
HRESULT = {
    2147943462: "SERVICE-STOPPED",        # 0x80070426 ERROR_SERVICE_NOT_ACTIVE
    2147943458: "SERVICE-DISABLED",       # 0x80070422 ERROR_SERVICE_DISABLED
    2147942405: "DENIED-NEED-ELEVATION",  # 0x80070005 ERROR_ACCESS_DENIED
    2147943712: "SERVICE-STOPPED",        # 0x80070520 ERROR_SERVICE_NOT_STARTED
}


def classify(resync):
    """Turn a resync attempt into a verdict a scheduler can act on."""
    blob = ((resync.get("out") or "") + " " + (resync.get("err") or "")).lower()
    if resync.get("rc") == 0:
        return "RESYNCED"
    if resync.get("rc") in HRESULT:
        return HRESULT[resync.get("rc")]
    if "access is denied" in blob or "拒绝访问" in blob or "\u62d2\u7edd" in blob:
        return "DENIED-NEED-ELEVATION"
    if "service has not been started" in blob or "not started" in blob:
        return "SERVICE-STOPPED"
    if "no time data" in blob or "no data available" in blob:
        return "NO-TIME-SOURCE"
    if resync.get("rc") in (124, 127, 125):
        return "TOOL-FAILED"
    return "UNKNOWN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="receipt JSON path (absolute or repo-relative)")
    ap.add_argument("--timeout", type=int, default=40)
    a = ap.parse_args()

    node = os.environ.get("COMPUTERNAME") or "unknown"
    steps = []
    svc_before, svc_r = service_state()
    steps.append({"step": "sc-query-before", "result": svc_r})

    q1 = run(["w32tm", "/query", "/status"], a.timeout)
    steps.append({"step": "query-status-before", "result": q1})
    cfg = run(["w32tm", "/query", "/configuration"], a.timeout)
    steps.append({"step": "query-configuration", "result": cfg})

    resync = run(["w32tm", "/resync", "/force"], a.timeout)
    steps.append({"step": "resync-force", "result": resync})
    verdict = classify(resync)

    if verdict == "RESYNCED":
        time.sleep(2)
    q2 = run(["w32tm", "/query", "/status"], a.timeout)
    steps.append({"step": "query-status-after", "result": q2})
    svc_after, svc_r2 = service_state()
    steps.append({"step": "sc-query-after", "result": svc_r2})

    rec = {
        "node": node,
        "ts_local": datetime.now().isoformat(timespec="milliseconds"),
        "ts_utc_ms": int(time.time() * 1000),
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "w32time_state_before": svc_before,
        "w32time_state_after": svc_after,
        "verdict": verdict,
        "resync_rc": resync.get("rc"),
        "next_action": {
            "RESYNCED": "none - re-read CLOCK-SKEW.json next report cycle",
            "DENIED-NEED-ELEVATION": "run once in an elevated session on this node "
                                     "(w32tm /resync /force), or re-register the loop task "
                                     "with highest privileges",
            "SERVICE-STOPPED": "start service once elevated: sc config w32time start= auto "
                               "&& net start w32time, then resync",
            "SERVICE-DISABLED": "re-enable once elevated: sc config w32time start= auto "
                                "&& net start w32time, then resync",
            "NO-TIME-SOURCE": "set a reachable peer: w32tm /config "
                              "/manualpeerlist:time.windows.com /syncfromflags:manual /update",
            "TOOL-FAILED": "w32tm missing on this host - report, do not retry blindly",
            "UNKNOWN": "read steps[].result.err in this file",
        }.get(verdict, "read steps"),
        "steps": steps,
    }

    out = a.out
    if not os.path.isabs(out):
        out = os.path.join(os.getcwd(), out)
    try:
        d = os.path.dirname(out)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
        rec["receipt"] = out
    except Exception as e:  # noqa: BLE001
        print("RECEIPT-WRITE-FAILED %s: %s" % (out, e))
        print(json.dumps(rec, ensure_ascii=False, indent=1))
        return 2

    print("node=%s svc=%s->%s verdict=%s rc=%s" % (node, svc_before, svc_after,
                                                   verdict, resync.get("rc")))
    print("receipt=%s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())