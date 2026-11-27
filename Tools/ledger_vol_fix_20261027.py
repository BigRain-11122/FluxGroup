"""Repair orders volume: restore HEAD bytes, then append moved rows byte-faithfully."""
import re
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\sjs20\Desktop\FluxGroup")
VOL = ROOT / "docs" / "orders-archive-2026-10.md"
CUTOFF = "2026-10-20"
ROW = re.compile(r"^\|\s*(2026-\d{2}-\d{2})")

subprocess.run(["git", "checkout", "--", "docs/orders-archive-2026-10.md"], cwd=ROOT, check=True)
base = VOL.read_bytes()
orig = subprocess.run(
    ["git", "show", "HEAD:docs/orders.md"], cwd=ROOT, check=True, capture_output=True
).stdout

moved = []
for line in orig.splitlines(keepends=True):
    m = ROW.match(line.decode("utf-8", "replace"))
    in_flight = any(tok.encode() in line for tok in ("dispatched", "executing", "ceo-pending", "escalated"))
    if m and m.group(1) < CUTOFF and not in_flight:
        moved.append(line)

block = b"".join(moved)
prefix = b"\n<!-- split 2026-10-27 from orders.md (D-20261027-12) -->\n"
VOL.write_bytes(base + prefix + block)
print(f"restored={len(base)}B moved={len(moved)} rows block={len(block)}B total={VOL.stat().st_size}B")