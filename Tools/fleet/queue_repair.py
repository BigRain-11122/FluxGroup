#!/usr/bin/env python3
"""PRODUCTION-QUEUE.jsonl repair: strip merge-conflict markers, dedupe duplicated ids.

Why this exists: a mid-rebase/merged queue file leaves `<<<<<<<` rows behind and
re-appends cards under the same id. Every queue reader parses line-by-line and
silently skips bad lines, so the master ends up acting on a partial queue with
no error anywhere. Fixing it by hand has been repeated; this tool makes the
repair reproducible and auditable.

Usage:
  python Tools/fleet/queue_repair.py                 # dry run (reports only)
  python Tools/fleet/queue_repair.py --apply         # write, with .bak-<ts> backup
  python Tools/fleet/queue_repair.py --apply --file <path>
"""
import argparse
import json
import os
import shutil
import sys
import time

MARKERS = ("<<<<<<<", "=======", ">>>>>>>", "|||||||")
DEFAULT = os.path.join("cph4", "fleet", "PRODUCTION-QUEUE.jsonl")


def _finish_ts(row):
    return (row.get("finished_at") or row.get("updated_at")
            or row.get("closed_at") or row.get("claimed_at") or "")


def load(path):
    good, bad = [], []
    with open(path, encoding="utf-8-sig") as fh:
        for i, line in enumerate(fh, 1):
            raw = line.strip()
            if not raw:
                continue
            if raw.startswith(MARKERS):
                bad.append((i, "CONFLICT", raw[:60]))
                continue
            try:
                good.append((i, json.loads(raw)))
            except Exception as exc:  # noqa: BLE001 - reported, not hidden
                bad.append((i, "BADJSON", "%s | %s" % (raw[:60], exc)))
    return good, bad


def dedupe(rows):
    """Keep one row per id: newest terminal evidence wins; else later line."""
    best = {}
    dropped = []
    for idx, (lineno, row) in enumerate(rows):
        cid = row.get("id")
        if cid is None:
            continue
        prev = best.get(cid)
        if prev is None:
            best[cid] = (lineno, row, idx)
            continue
        prev_ts = _finish_ts(prev[1])
        cur_ts = _finish_ts(row)
        if cur_ts > prev_ts or (cur_ts == prev_ts and lineno > prev[0]):
            dropped.append((prev[0], prev[1].get("state")))
            best[cid] = (lineno, row, idx)
        else:
            dropped.append((lineno, row.get("state")))
    keep_idx = {v[2] for v in best.values()}
    kept = [r for i, r in enumerate(rows) if i in keep_idx]
    # rows without id are preserved untouched
    for i, (lineno, row) in enumerate(rows):
        if row.get("id") is None and i not in keep_idx:
            kept.append((lineno, row))
    kept.sort(key=lambda t: t[0])
    return kept, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        print("[queue-repair] MISSING %s" % args.file)
        return 2

    rows, bad = load(args.file)
    kept, dropped = dedupe(rows)
    print("[queue-repair] parsed=%d bad_lines=%d dup_dropped=%d kept=%d"
          % (len(rows), len(bad), len(dropped), len(kept)))
    for lineno, kind, detail in bad:
        print("  bad L%d %s %s" % (lineno, kind, detail))
    for lineno, state in dropped:
        print("  drop L%d state=%s" % (lineno, state))

    if not args.apply:
        print("[queue-repair] dry-run; pass --apply to write")
        return 0 if (bad or dropped) else 0

    backup = "%s.bak-%s" % (args.file, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(args.file, backup)
    tmp = args.file + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        for _lineno, row in kept:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, args.file)
    print("[queue-repair] wrote %d rows; backup=%s" % (len(kept), backup))
    return 0


if __name__ == "__main__":
    sys.exit(main())