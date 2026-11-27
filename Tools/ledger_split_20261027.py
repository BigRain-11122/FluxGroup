"""Ledger split: move dated table rows older than cutoff into a monthly volume.

Implements D-20261027-12 (orders/decisions both exceed 250KB hot-file line).
Deterministic, zero-LLM. Use --apply to write; default is a dry run report.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\sjs20\Desktop\FluxGroup")
CUTOFF = "2026-10-20"  # hot window = 7 days ending 2026-10-27
ROW = re.compile(r"^\|\s*(2026-\d{2}-\d{2})")

SPECS = [
    (ROOT / "docs" / "orders.md", ROOT / "docs" / "orders-archive-2026-10.md", "orders"),
    (ROOT / "docs" / "decisions.md", ROOT / "docs" / "decisions-archive-2026-10.md", "decisions"),
]


def run(apply: bool) -> int:
    for main_path, vol_path, label in SPECS:
        text = main_path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        moved, kept = [], []
        for line in lines:
            m = ROW.match(line)
            in_flight = any(tok in line for tok in ("dispatched", "executing", "ceo-pending", "escalated"))
            if m and m.group(1) < CUTOFF and not in_flight:
                moved.append(line if line.endswith("\n") else line + "\n")
            else:
                kept.append(line)
        print(f"[{label}] total={len(lines)} moved_rows={len(moved)} kept={len(kept)}")
        if not moved:
            continue
        print(f"[{label}] before={len(text.encode('utf-8'))}B after={len(''.join(kept).encode('utf-8'))}B")
        if not apply:
            continue
        if vol_path.exists():
            body = vol_path.read_text(encoding="utf-8")
            if not body.endswith("\n"):
                body += "\n"
        else:
            body = (
                f"# {label.capitalize()} Archive Volume 2026-10\n\n"
                "> 集团分卷件（D-20261027-12·分卷日 2026-10-27）：承接主档 2026-10-20 之前的历史行。\n"
                "> 纪律=行级追加不改写；主档只保留 7 天热窗。\n\n"
                "## 台账\n\n| 时间 | 内容 |\n|---|---|\n\n"
            )
        body += f"\n<!-- split 2026-10-27 from {main_path.name} -->\n" + "".join(moved)
        vol_path.write_text(body, encoding="utf-8")
        index = (
            f"\n> **分卷索引**：2026-10-20 之前的历史行已迁入 `docs/{vol_path.name}`"
            "（分卷日 2026-10-27·D-20261027-12·行级追加不改写）。\n"
        )
        new_text = "".join(kept)
        if f"`docs/{vol_path.name}`" not in new_text:
            anchor = "## 台账"
            if anchor in new_text:
                new_text = new_text.replace(anchor, anchor + index, 1)
            else:
                new_text = new_text.rstrip("\n") + "\n" + index
        main_path.write_text(new_text, encoding="utf-8")
        print(f"[{label}] written; main={len(new_text.encode('utf-8'))}B volume={len(body.encode('utf-8'))}B")
    return 0


if __name__ == "__main__":
    sys.exit(run("--apply" in sys.argv))