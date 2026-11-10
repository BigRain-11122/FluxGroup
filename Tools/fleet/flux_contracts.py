#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flux_contracts.py - the six contracts every module speaks, and nothing else.

Why this file exists (2026-11-02): the queue had 55 optional fields across 97 rows,
`when_all` meant both "dependency id" and "input file path", `deliverable` lived in
three different path spaces, and `rc=9009` (command not found) was recorded as DONE.
Rules lived in prose; the machine could not tell a good card from a typo. This module
is the single definition: one field list per contract, one validator, one rc semantics.

Contracts map to open standards so that we do not invent a protocol:
  CARD / RECEIPT  -> A2A task lifecycle (submitted/working/completed/failed + artifacts)
  ARTIFACT        -> content-addressed asset record (C2PA-friendly)
  ORDER           -> CEO input face (no external standard)
  VERDICT         -> gate judgement (tool_version + input hash)
  RECIPE          -> product definition (capability chain + kill criteria)

CLI:
  python3 flux_contracts.py --emit cph4/contracts     # write readable JSON specs
  python3 flux_contracts.py --check card FILE.json    # validate one object
"""
import json
import os
import re
import sys

VERSION = "1.0-20261102"

# rc -> error class. "rc!=0 but the artifact exists" is no longer success.
ERROR_CLASS = {
    2: "E-CONTRACT",
    3: "E-BLOCKED-INPUT",   # 缺上游输入（等投料不是失败，2026-11-03 定：与 E-CONTRACT 分开）
    124: "E-TIMEOUT",
    125: "E-UNKNOWN",
    126: "E-MODEL",
    127: "E-PATH",      # POSIX: command not found
    9009: "E-PATH",     # Windows: command not found
}
DEFAULT_OK_RC = [0]

ERROR_CLASSES = ["E-OK", "E-CONTRACT", "E-PATH", "E-MEM", "E-MODEL", "E-QUOTA",
                 "E-TIMEOUT", "E-COMPLIANCE", "E-ARTIFACT", "E-BLOCKED-INPUT", "E-INPUT",
                 "E-UNKNOWN"]
# E-INPUT=本机缺输入（不是失败，是换机信号）；E-OK=成功回执也带类别。
# 2026-11-04 实锚：receipt_attrib 自己抄了一份旧表，把 12 份 E-INPUT 判成"不在分类学内"。

MACHINE_RE = re.compile(r"\b(bm-[a-z]|DASHENG)\b")
DRIVE_RE = re.compile(r"(^|[\s\"'])([A-Za-z]:[\\/])")
HOME_RE = re.compile(r"(^|[\s\"'])(/Users/|/home/)")

CONTRACTS = {
    "order": {
        "required": ["id", "ceo_verbatim", "scope"],
        "optional": ["affects", "receipt_window_s", "veto_window_s", "ts", "by"],
        "types": {"affects": list},
    },
    "card": {
        "required": ["id", "line", "stage", "deliverable", "accept"],
        "optional": ["mode", "needs", "ok_rc", "ttl_s", "idempotency_key", "cmd",
                     "prompt", "prio", "created_by", "created_at", "state",
                     "line_ref", "notes"],
        "types": {"needs": dict, "accept": list, "ok_rc": list, "deliverable": dict},
        "enums": {"mode": ["cmd", "prompt", "gate", "publish"]},
        "forbid_in": ["cmd", "prompt", "deliverable", "notes"],
    },
    "receipt": {
        "required": ["id", "node", "rc", "seconds", "ts"],
        "optional": ["error_class", "outcome", "ok_rc", "artifacts", "deliverable",
                     "deliverable_exists", "cmd", "stdout_tail", "stderr_tail", "job"],
        "types": {"artifacts": list},
        "enums": {"outcome": ["OK", "FAIL"]},
    },
    "artifact": {
        "required": ["sha256", "kind", "path", "bytes"],
        "optional": ["license", "provenance", "gate_status", "created_at", "source_url"],
        "types": {"provenance": dict},
        "enums": {"gate_status": ["none", "pending", "pass", "fail", "waived"]},
    },
    "verdict": {
        "required": ["gate", "input_sha", "checks", "pass", "tool_version"],
        "optional": ["approved_by", "ts", "scope", "waived", "notes"],
        "types": {"checks": list},
    },
    "recipe": {
        "required": ["product", "chain", "acceptance", "channel", "unit_economics",
                     "kill_criteria"],
        "optional": ["owner", "status", "notes", "started_at"],
        "types": {"chain": list, "acceptance": list, "unit_economics": dict},
        "enums": {"status": ["active", "paused", "killed", "shipped"]},
    },
}


def spec(kind):
    c = CONTRACTS[kind]
    return {"contract": kind, "version": VERSION, **c}


def error_class(rc):
    try:
        rc = int(rc)
    except (TypeError, ValueError):
        return "E-UNKNOWN"
    if rc == 0:
        return None
    return ERROR_CLASS.get(rc, "E-UNKNOWN")


def ok_rc(card):
    v = (card or {}).get("ok_rc")
    return [int(x) for x in v] if isinstance(v, list) and v else list(DEFAULT_OK_RC)


def deliverable_of(card):
    """Legacy cards carry a string; new cards carry {path,min_bytes}."""
    d = (card or {}).get("deliverable")
    if isinstance(d, dict):
        return d.get("path") or ""
    return d or ""


def deliverable_blocked(path):
    """True when a deliverable file is really an interception receipt.

    A guard that refuses to run on the wrong box still leaves a trace, and that trace
    lands on the path the card promised. Then "the deliverable exists" is true while
    nothing was delivered (2026-11-03: three Windows audit cards were closed DONE on
    macOS this way, twice - the guard was fixed to use a -blocked-* path, but a card
    whose cmd passes --out explicitly walked straight around it). So the check belongs
    here, at the contract layer, not inside one tool.
    """
    if not path:
        return False
    if not os.path.isfile(path) or os.path.getsize(path) > 262144:
        return False
    # CSV/text deliverables (the sellable holdings signal) carry the same marker in row 1.
    if os.path.splitext(path)[1].lower() in (".csv", ".tsv", ".md", ".txt"):
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                head = f.read(400).upper()
            if "RECEIPT_IS_NOT_DELIVERABLE" in head:
                return True
            # "BLOCKED" must open the file (a guard's refusal line), not appear anywhere
            # in the head. 2026-11-10: two genuine deliverables (a queue-state report and
            # a fleet test artifact) were booked FAILED/E-ARTIFACT because their content
            # listed "BLOCKED: 6" among queue states - "a file that mentions blocked work"
            # is not "a refusal receipt", and the contract layer must not conflate them.
            first = next((ln.strip() for ln in head.splitlines() if ln.strip()), "")
            return first.startswith("BLOCKED")
        except Exception:
            return False
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            obj = json.load(f)
    except Exception:
        return False
    if not isinstance(obj, dict):
        return False
    if obj.get("receipt_is_not_deliverable") is True:
        return True
    for k in ("verdict", "status", "state", "outcome"):
        if str(obj.get(k) or "").strip().upper() == "BLOCKED":
            return True
    # Some tools record the refusal as a reason string under "blocked".
    blk = obj.get("blocked")
    if blk is True:
        return True
    if isinstance(blk, str) and blk.strip().lower() not in ("", "false", "none", "0"):
        return True
    return str(obj.get("error_class") or "").upper().startswith("E-BLOCKED")


def artifact_ok(path):
    """A declared deliverable counts only if it is on disk AND is not a refusal receipt."""
    return bool(path) and os.path.isfile(path) and not deliverable_blocked(path)


def is_ok(card, rc, deliverable_exists):
    """A step succeeded only if the process exit code is allowed AND its declared
    deliverable is on disk. 'It produced a file' alone no longer means success."""
    try:
        rc = int(rc)
    except (TypeError, ValueError):
        return False
    if rc not in ok_rc(card):
        return False
    return deliverable_exists if deliverable_of(card) else True


def validate(kind, obj):
    """Return a list of 'CODE: message'. Empty list = conforms."""
    if kind not in CONTRACTS:
        return ["UNKNOWN: no contract named %r" % kind]
    if not isinstance(obj, dict):
        return ["TYPE: %s must be an object" % kind]
    c = CONTRACTS[kind]
    out = []
    for f in c["required"]:
        if obj.get(f) in (None, "", [], {}):
            out.append("REQUIRED: missing %s" % f)
    for f, t in (c.get("types") or {}).items():
        if f in obj and obj[f] is not None and not isinstance(obj[f], t):
            out.append("TYPE: %s must be %s, got %s" % (f, t.__name__, type(obj[f]).__name__))
    for f, allowed in (c.get("enums") or {}).items():
        if obj.get(f) not in (None, "") and obj[f] not in allowed:
            out.append("ENUM: %s=%r not in %s" % (f, obj[f], allowed))
    if kind == "card":
        for f in c.get("forbid_in") or []:
            v = obj.get(f)
            blob = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v or "")
            if MACHINE_RE.search(blob):
                out.append("FORBID: %s names a machine (cards declare needs, not hosts)" % f)
            if DRIVE_RE.search(blob) or HOME_RE.search(blob):
                out.append("FORBID: %s carries an absolute host path (use repo-relative)" % f)
        if not (obj.get("cmd") or obj.get("prompt")):
            out.append("REQUIRED: card needs cmd or prompt")
    if kind == "receipt":
        rc = obj.get("rc")
        if rc not in (None,) and error_class(rc) and not obj.get("error_class"):
            out.append("REQUIRED: rc=%r needs error_class" % rc)
        if obj.get("error_class") not in (None, "") and obj["error_class"] not in ERROR_CLASSES:
            out.append("ENUM: error_class %r not in %s" % (obj["error_class"], ERROR_CLASSES))
    if kind == "artifact":
        s = str(obj.get("sha256") or "")
        if s and not re.fullmatch(r"[0-9a-f]{64}", s):
            out.append("FORMAT: sha256 must be 64 lowercase hex chars")
        try:
            if int(obj.get("bytes") or 0) <= 0:
                out.append("RANGE: bytes must be > 0")
        except (TypeError, ValueError):
            out.append("TYPE: bytes must be an integer")
    return out


def main(argv):
    if len(argv) >= 3 and argv[1] == "--emit":
        out = argv[2]
        os.makedirs(out, exist_ok=True)
        for kind in CONTRACTS:
            p = os.path.join(out, "%s.json" % kind)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(spec(kind), f, ensure_ascii=False, indent=2)
                f.write("\n")
        print("emitted %d contract specs -> %s (v%s)" % (len(CONTRACTS), out, VERSION))
        return 0
    if len(argv) >= 4 and argv[1] == "--check":
        with open(argv[3], encoding="utf-8-sig") as f:
            obj = json.load(f)
        errs = validate(argv[2], obj)
        for e in errs:
            print(e)
        print("%s: %s" % (argv[2], "OK" if not errs else "%d problem(s)" % len(errs)))
        return 0 if not errs else 2
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))