#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回执原语（W3）：写/验闸回执，绑定契约哈希与版本。

写:
  python Tools/agents/receipt.py --project cph4/fleet/game-v2/contracts/gimmeall.yaml \
      --gate G3 --status NOT_RUN --note "无真机首启证据"
验:
  python Tools/agents/receipt.py --verify
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "cph4" / "fleet" / "game-v2"
RECEIPTS = BASE / "receipts"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_lint import check_project, contract_hash, load_yaml  # noqa: E402

GATES = {f"G{i}" for i in range(1, 9)}
STATUS = {"PASS", "FAIL", "NOT_RUN"}


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def write_receipt(args) -> int:
    const = load_yaml(BASE / "constitution.yaml")
    classes = load_yaml(BASE / "classes.yaml")
    cpath = (ROOT / args.project) if not Path(args.project).is_absolute() else Path(args.project)
    if not cpath.exists():
        print(f"contract not found: {cpath}", file=sys.stderr)
        return 2

    p = load_yaml(cpath)
    fails = check_project(p, const, classes)
    if fails:
        print(json.dumps({"error": "contract_invalid", "failures": fails}, ensure_ascii=False))
        return 3

    if args.gate not in GATES:
        print(f"gate must be one of {sorted(GATES)}", file=sys.stderr)
        return 2
    if args.status not in STATUS:
        print(f"status must be one of {sorted(STATUS)}", file=sys.stderr)
        return 2
    if args.status == "PASS" and not args.evidence:
        print("PASS requires at least one evidence path", file=sys.stderr)
        return 2

    evidence = []
    for e in args.evidence or []:
        ep = (ROOT / e) if not Path(e).is_absolute() else Path(e)
        evidence.append({"path": rel(ep), "exists": ep.exists()})

    rec = {
        "receipt": f"gate/{args.gate}",
        "project_id": p.get("project_id"),
        "contract_file": rel(cpath),
        "contract_hash": contract_hash(p),
        "constitution_version": p.get("constitution_version"),
        "class_version": p.get("class_version"),
        "status": args.status,
        "evidence": evidence,
        "note": args.note or "",
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    outdir = RECEIPTS / str(p.get("project_id"))
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{args.gate}.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"written": rel(out), "status": rec["status"], "hash": rec["contract_hash"]},
                     ensure_ascii=False))
    return 0


def verify() -> int:
    problems = []
    n = 0
    if not RECEIPTS.exists():
        print(json.dumps({"receipts": 0, "problems": 0}, ensure_ascii=False))
        return 0
    for f in sorted(RECEIPTS.glob("*/*.json")):
        if f.parent.name.startswith("_"):
            continue
        n += 1
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            problems.append({"file": rel(f), "why": f"json error: {exc}"})
            continue
        cpath = ROOT / r.get("contract_file", "")
        if not cpath.exists():
            problems.append({"file": rel(f), "why": "contract missing"})
            continue
        p = load_yaml(cpath)
        if contract_hash(p) != r.get("contract_hash"):
            problems.append({"file": rel(f), "why": "contract hash changed (stale)"})
        if p.get("constitution_version") != r.get("constitution_version"):
            problems.append({"file": rel(f), "why": "constitution version mismatch"})
        if r.get("status") not in STATUS:
            problems.append({"file": rel(f), "why": f"bad status {r.get('status')}"})
        if r.get("status") == "PASS" and not r.get("evidence"):
            problems.append({"file": rel(f), "why": "PASS without evidence"})
    print(json.dumps({"receipts": n, "problems": len(problems), "detail": problems[:20]},
                     ensure_ascii=False))
    return 0 if not problems else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--gate")
    ap.add_argument("--status")
    ap.add_argument("--evidence", nargs="*")
    ap.add_argument("--note", default="")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.verify:
        return verify()
    if not (args.project and args.gate and args.status):
        ap.error("--project, --gate, --status are required (or use --verify)")
    return write_receipt(args)


if __name__ == "__main__":
    raise SystemExit(main())
