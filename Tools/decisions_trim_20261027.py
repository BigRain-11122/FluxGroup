"""Trim decisions hot file under the 250KB line: move executed rows dated < 2026-10-21
into the monthly volume (byte-faithful, append-only)."""
import re

from pathlib import Path

R = Path(r"C:\Users\sjs20\Desktop\FluxGroup")
MAIN = R / "docs" / "decisions.md"
VOL = R / "docs" / "decisions-archive-2026-10.md"
CUTOFF = "2026-10-21"
ROW = re.compile(rb"^\|\s*(2026-\d{2}-\d{2})")
INFLIGHT = (b"dispatched", b"executing", b"ceo-pending", b"escalated")

raw = MAIN.read_bytes()
lines = raw.split(b"\n")
kept, moved = [], []
for line in lines:
    m = ROW.match(line)
    if m and m.group(1).decode() < CUTOFF and not any(t in line for t in INFLIGHT):
        moved.append(line)
    else:
        kept.append(line)

if moved:
    new_main = b"\n".join(kept)
    MAIN.write_bytes(new_main)
    block = b"\n".join(moved) + b"\n"
    with open(VOL, "ab") as f:
        f.write(b"\n<!-- split 2026-10-27 (2) from decisions.md -->\n" + block)
    print(f"moved={len(moved)} main={len(new_main)}B vol={VOL.stat().st_size}B")
else:
    print("nothing moved", len(raw))