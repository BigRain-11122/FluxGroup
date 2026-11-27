# -*- coding: utf-8 -*-
"""Regenerate the G4 segment table from mv_rebuild_v722.py --dry.

Writes canon/v722-segments.json (id / t0 / t1 / era). Run after any change to the
era split so the contract gate and the rebuild script always agree.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
out = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "canon", "v722-segments.json")

r = subprocess.run([sys.executable, os.path.join(HERE, "mv_rebuild_v722.py"), "X", "--dry"],
                   capture_output=True, text=True, errors="replace", cwd=ROOT)
rows = []
for ln in r.stdout.splitlines():
    m = re.match(r"\s*([0-9.]+)\s+([0-9.]+)\s+(\S+)\s+v=([0-9.]+)\s+(modern_night|transition|modern|ancient)", ln)
    if m:
        rows.append({"id": m.group(3), "t0": float(m.group(1)),
                     "t1": float(m.group(2)), "era": m.group(5)})
io.open(out, "w", encoding="utf-8").write(json.dumps(rows, ensure_ascii=False, indent=1))
kinds = {}
for x in rows:
    kinds[x["era"]] = kinds.get(x["era"], 0) + 1
print("wrote %s  rows=%d  %s" % (out, len(rows), kinds))