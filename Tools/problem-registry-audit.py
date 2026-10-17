#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PROBLEM-REGISTRY mechanical audit — C-20261017-01 problem-traceability loop.

Parses cph4/fleet/PROBLEM-REGISTRY.md: every '### PR-YYYYMMDD-NN' block must
carry the six required fields with ASCII-colon labels, a numeric recurrence
count, a valid status prefix, and an escalation record whenever count > 0.
ASCII-only output; exit 0 on PASS, 1 on FAIL. Wired into the CEO-PROXY 23:43
night-shift piece and the Sunday deep review (docs/governance.md sec.9).
"""
import os
import re
import sys

# ascii fail-labels: src / root / gate / evidence
FIELDS = ["- 来源:", "- 复发史", "- 出生地闸:", "- 验证证据:"]
LABELS = {"- 来源:": "src", "- 复发史": "root", "- 出生地闸:": "gate", "- 验证证据:": "evidence"}
COUNT_RE = re.compile(r"^- 复发计数: (\d+)\s*$", re.M)
STATUS_RE = re.compile(r"^- 状态: (open-CEO|open|armed|closed)(?:\s|$)", re.M)
BLOCK_RE = re.compile(r"^### (PR-\d{8}-\d+)\b.*$", re.M)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(here, os.pardir, "cph4", "fleet", "PROBLEM-REGISTRY.md"))
    if not os.path.isfile(path):
        print("registry not found: %s" % path)
        print("VERDICT: FAIL")
        return 1
    with open(path, encoding="utf-8") as f:
        text = f.read()
    ids = [(m.group(1), m.start()) for m in BLOCK_RE.finditer(text)]
    entries = []
    for i, (pid, pos) in enumerate(ids):
        end = ids[i + 1][1] if i + 1 < len(ids) else len(text)
        entries.append((pid, text[pos:end]))
    fails, seen = [], set()
    for pid, body in entries:
        if pid in seen:
            fails.append("%s duplicate id" % pid)
        seen.add(pid)
        for fld in FIELDS:
            if fld not in body:
                fails.append("%s missing field %s" % (pid, LABELS[fld]))
        m = COUNT_RE.search(body)
        if not m:
            fails.append("%s missing/bad recurrence count" % pid)
        else:
            if int(m.group(1)) > 0 and "- 升格记录:" not in body:
                fails.append("%s count>0 missing escalation record" % pid)
        if not STATUS_RE.search(body):
            fails.append("%s missing/bad status" % pid)
    print("entries: %d" % len(entries))
    for f in fails:
        print("FAIL %s" % f)
    ok = bool(entries) and not fails
    print("VERDICT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
