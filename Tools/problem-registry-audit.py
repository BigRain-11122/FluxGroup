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
import subprocess
import sys

# ascii fail-labels: src / root / gate / evidence
FIELDS = ["- 来源:", "- 复发史", "- 出生地闸:", "- 验证证据:"]
LABELS = {"- 来源:": "src", "- 复发史": "root", "- 出生地闸:": "gate", "- 验证证据:": "evidence"}
COUNT_RE = re.compile(r"^- 复发计数: (\d+)\s*$", re.M)
STATUS_RE = re.compile(r"^- 状态: (open-CEO|open|armed|closed)(?:\s|$)", re.M)
BLOCK_RE = re.compile(r"^### (PR-\d{8}-\d+)\b.*$", re.M)


def run_config_gates(here):
    """Execute the assertion gates that registry entries name as their self-check.

    PR-20261017-02 shipped a recipe with two broken values and nothing ever ran the
    check, so the breakage survived a week. A gate that is only written down is not a
    gate: the nightly audit runs it. Missing script = skip (not a failure).
    """
    fails = []
    guard = os.path.join(here, "fleet-silence-guard.ps1")
    if not os.path.isfile(guard):
        print("gate fleet-silence-guard: SKIP (script not present)")
        return fails
    try:
        cp = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", guard],
            capture_output=True, timeout=180,
        )
    except Exception as exc:  # noqa: BLE001 - report, never crash the audit
        fails.append("fleet-silence-guard could not run: %s" % exc)
        return fails
    tail = ""
    for line in cp.stdout.decode("utf-8", "replace").splitlines():
        s = line.strip()
        if s.startswith("----") or s.startswith("FAIL"):
            tail = s
            if s.startswith("FAIL"):
                fails.append("fleet-silence-guard: %s" % s[5:].strip())
    print("gate fleet-silence-guard: rc=%d %s" % (cp.returncode, tail))
    if cp.returncode != 0 and not fails:
        fails.append("fleet-silence-guard rc=%d" % cp.returncode)
    return fails


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
    fails.extend(run_config_gates(here))
    for f in fails:
        print("FAIL %s" % f)
    ok = bool(entries) and not fails
    print("VERDICT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
