"""D-20261116-02 option (b): mark the visual lane's OPEN cards BLOCKED with the
reason that is true on this machine right now, instead of leaving a face that
looks like work is queued when no executor is running.

Guards: re-read mtime before writing (abort if the queue moved under us),
per-line JSON round-trip, atomic replace, and a printed before/after count.
"""
import json
import os
import sys
import time

Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue.jsonl")
LOCK = Q + ".lock"

BLOCKED_BY = "visual-executor-not-running"
REASON = (
    "D-20261116-02 option (b): station heartbeat stale since 2026-11-15T13:51:16 "
    "(round 594) while state.json is written by the 23:49 auditor, so the log is "
    "not card execution; D-12 freezes registering/restoring the self-starting "
    "station task, so this card is parked rather than re-lifted."
)


def main(apply):
    mtime = os.path.getmtime(Q)
    with open(Q, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    rows = []
    for ln in lines:
        rows.append(json.loads(ln) if ln.strip() else None)

    open_idx = [i for i, r in enumerate(rows) if r and r.get("state") == "OPEN"]
    print("queue=%s lines=%d open=%d" % (os.path.basename(Q), len(lines), len(open_idx)))
    for i in open_idx:
        r = rows[i]
        print("  OPEN %-38s prio=%-2s needs=%-3s nodes=%s" % (
            r.get("id"), r.get("prio"), r.get("needs"), ",".join(r.get("nodes") or [])))

    if not apply:
        print("dry-run: nothing written")
        return 0

    if os.path.getmtime(Q) != mtime:
        print("ABORT: queue.jsonl moved between read and write")
        return 2

    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    for i in open_idx:
        r = rows[i]
        r["state"] = "BLOCKED"
        r["blocked_by"] = BLOCKED_BY
        r["blocked_reason"] = REASON
        r["blocked_at"] = stamp
        r["blocked_note"] = "card face reconciled to the side conclusion (r1742 bm-c)"

    out = "\n".join(json.dumps(r, ensure_ascii=False) if r is not None else ""
                    for r in rows) + "\n"
    tmp = Q + ".bmc-tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    # verify every line still parses before it replaces the live face
    with open(tmp, "r", encoding="utf-8") as fh:
        chk = [json.loads(x) for x in fh.read().splitlines() if x.strip()]
    assert len(chk) == len([r for r in rows if r is not None]), "line count drift"
    os.replace(tmp, Q)

    with open(Q, "r", encoding="utf-8") as fh:
        after = [json.loads(x) for x in fh.read().splitlines() if x.strip()]
    still = [r.get("id") for r in after if r.get("state") == "OPEN"]
    print("written: blocked=%d open_after=%d %s" % (len(open_idx), len(still), still))
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
