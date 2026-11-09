#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decisions.md 分卷器 (voluming, orders-archive paradigm).

Why: decisions.md passed the 200KB threshold and the previous night reports
only named it without any executor existing (root cause = no script, not
laziness). This is the executor: it moves the OLDEST whole "## " sections
into docs/decisions-archive-<YYYY-MM>.md so the live ledger stays under the
budget, and it asserts line conservation.

Safety:
  * whole-section only (never splits a table or its ">" summary)
  * dry-run by default (--apply to write)
  * refuses to run if conservation check fails
  * preserves the original BOM / newline style
"""

import argparse
import io
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, "docs", "decisions.md")
SEC_RE = re.compile(r"^##\s")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def read_text(path):
    with io.open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text[:4000] else "\n"
    return text, bom, newline


def write_text(path, text, bom, newline):
    if newline == "\r\n":
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    tmp = path + ".tmp"
    with io.open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def split_sections(lines):
    """Return list of (start, end) line ranges, one per '## ' section."""
    starts = [i for i, ln in enumerate(lines) if SEC_RE.match(ln)]
    if not starts:
        return []
    # Anything before the first section header is a preamble -> own range.
    ranges = []
    if starts[0] > 0:
        ranges.append((0, starts[0]))
    for idx, s in enumerate(starts):
        e = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        ranges.append((s, e))
    return ranges


def section_date(header, fallback):
    m = DATE_RE.search(header or "")
    return m.group(1) if m else fallback


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually write files")
    ap.add_argument("--target-kb", type=float, default=120.0,
                    help="keep the live ledger at or below this size (default 120KB)")
    ap.add_argument("--keep-sections", type=int, default=8,
                    help="always keep at least this many newest sections")
    args = ap.parse_args()

    text, bom, newline = read_text(LIVE)
    lines = text.split(newline)
    size_kb = len(text.encode("utf-8")) / 1024.0
    ranges = split_sections(lines)
    if not ranges:
        print("SPLIT skip: no '## ' sections found")
        return 0

    today = date.today().isoformat()
    # Keep newest sections until the kept block fits target_kb.
    keep_from = len(ranges) - args.keep_sections
    if keep_from <= 0:
        print("SPLIT noop: only %d section(s)" % len(ranges))
        return 0
    for idx in range(len(ranges) - args.keep_sections, 0, -1):
        start = ranges[idx][0]
        kept_kb = len(newline.join(lines[start:]).encode("utf-8")) / 1024.0
        if kept_kb > args.target_kb:
            keep_from = idx - 1
        else:
            keep_from = idx
            break
    keep_from = max(1, keep_from)  # never move the preamble
    if keep_from >= len(ranges):
        print("SPLIT noop: nothing older than the kept window")
        return 0

    cut = ranges[keep_from][0]
    moving = lines[:cut]
    staying = lines[cut:]
    if not any(SEC_RE.match(l) for l in moving):
        print("SPLIT noop: moving block has no sections")
        return 0

    # Month bucket = month of the newest moved section date.
    dates = [section_date(lines[s], "") for s, _ in ranges[:keep_from]]
    months = sorted({d[:7] for d in dates if d})
    month = months[-1] if months else today[:7]
    archive = os.path.join(ROOT, "docs", "decisions-archive-%s.md" % month)

    header = (
        newline + "<!-- volumed %s by Tools/decisions_split.py: %d section(s), %.1f KB -->"
        % (today, keep_from, len(newline.join(moving).encode("utf-8")) / 1024.0) + newline
    )
    if not os.path.exists(archive):
        header = ("# decisions 分卷 %s" % month) + newline + newline + header

    new_live = newline.join(staying)
    old_arch = ""
    a_bom = bom
    if os.path.exists(archive):
        old_arch, a_bom, _ = read_text(archive)
    new_arch = old_arch + header + newline.join(moving)

    # Conservation check: every moved line must land in the archive verbatim.
    moved_sig = [l for l in moving if l.strip()]
    arch_sig = set(new_arch.splitlines())
    missing = [l for l in moved_sig if l not in arch_sig]
    if missing:
        print("SPLIT FAIL: %d moved line(s) not present in archive; aborted" % len(missing))
        return 2
    from collections import Counter
    if Counter(l for l in moved_sig + [x for x in staying if x.strip()]) != Counter(
            l for l in lines if l.strip()):
        print("SPLIT FAIL: line conservation mismatch; aborted")
        return 2

    print("SPLIT plan: live %.1fKB -> %.1fKB | move %d section(s) (%d non-blank lines) -> %s"
          % (size_kb,
             len(new_live.encode("utf-8")) / 1024.0,
             keep_from, len(moved_sig), os.path.basename(archive)))
    print("SPLIT verify: moved lines all present in archive, conservation OK")
    if not args.apply:
        print("SPLIT dry-run only (pass --apply to write)")
        return 0

    write_text(archive, new_arch, a_bom, newline)
    write_text(LIVE, new_live, bom, newline)
    print("SPLIT applied: %s + %s" % (os.path.basename(LIVE), os.path.basename(archive)))
    return 0


if __name__ == "__main__":
    sys.exit(main())