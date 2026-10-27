# -*- coding: utf-8 -*-
"""cloud_lane_lint.py - T0 cloud-off mechanical gate for dispatch cards.

Purpose (CLOUD-OFF-LANDING-20261020.md §四-1): a dispatch card that names a
cloud path must be refused before it ships. DISPATCHER-CHARTER §五.6 states the
rule in prose; this is the machine assertion.

Scope discipline: historical ledgers, logs, receipts and research are NEVER
rewritten or judged here. Only cards that are still live (open / in-flight) are
scanned, and orders.md is scanned only when --orders-since is given, so old rows
with cloud model names do not produce noise.

Exit codes: 0 = clean (warnings allowed), 1 = at least one BLOCK hit.

Usage:
    python Tools/cloud_lane_lint.py                     # scan live POOL cards
    python Tools/cloud_lane_lint.py --all-statuses      # include closed cards (audit)
    python Tools/cloud_lane_lint.py --path <file.md>    # scan any ad-hoc card
    python Tools/cloud_lane_lint.py --orders-since 2026-10-20
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "POOL.json")
ORDERS = os.path.join(ROOT, "docs", "orders.md")

LIVE_STATUSES = {"open", "in-flight", "queued", "claimed"}

# Hard blocks: unambiguous cloud provider / cloud-path markers.
# Model names that also exist as LOCAL weights (krea, qwen-image, hunyuan,
# cogvideox, wan2, flux) are deliberately NOT here - they go to WARN.
BLOCK = [
    r"云端", r"\bcloud\b", r"\bapi\b", r"api\.",
    r"seedance", r"即梦", r"jimeng",
    r"\bkling\b", r"可灵",
    r"\brunway\b", r"\bluma\b", r"\bveo\b", r"\bsora\b",
    r"pixverse", r"\bvidu\b", r"\bpika\b", r"higgsfield",
    r"hailuo", r"海螺", r"\bminimax\b",
    r"\bmidjourney\b", r"\bseedream\b", r"\bideogram\b", r"\brecraft\b",
    r"\btripo\b", r"\bmeshy\b", r"\brodin\b", r"\bviggle\b",
    r"elevenlabs", r"\bopenai\b", r"\bgpt-", r"\bgemini\b", r"\bclaude\b",
    r"豆包", r"doubao",
]

# Advisory: names that may be a local weights deployment (legal) or a cloud
# call (illegal). Human must say which; this never blocks on its own.
WARN = [
    r"\bkrea\b", r"qwen-image", r"\bhunyuan\b", r"混元", r"cogvideox",
    r"wan2", r"万相", r"\bflux\b", r"\bsvd\b", r"stable video",
]

# Lines that explicitly record the T0 prohibition are self-documenting, not a
# violation ("禁云端", "云端已停用", "cloud-off", ...).
EXEMPT = re.compile(
    r"停用|废止|冻结|禁(用|止)?云|云端已停|cloud[- ]off|T0|不(走|用|再)云|零云", re.I)


def compile_all(pats):
    return [(p, re.compile(p, re.I)) for p in pats]


BLOCK_RX = compile_all(BLOCK)
WARN_RX = compile_all(WARN)


def scan_text(text, where):
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if EXEMPT.search(line):
            continue
        for pat, rx in BLOCK_RX:
            if rx.search(line):
                hits.append(("BLOCK", where, lineno, pat, line.strip()[:160]))
        for pat, rx in WARN_RX:
            if rx.search(line):
                hits.append(("WARN", where, lineno, pat, line.strip()[:160]))
    return hits


def card_text(card):
    # Only the fields that describe the work, not historical result notes.
    keep = ("id", "priority", "status", "lane", "title", "spec", "acceptance", "notes")
    return "\n".join("%s: %s" % (k, card.get(k, "")) for k in keep if card.get(k))


def scan_pool(all_statuses):
    with open(POOL, encoding="utf-8") as f:
        cards = json.load(f)
    hits, scanned = [], 0
    for card in cards:
        if not all_statuses and card.get("status") not in LIVE_STATUSES:
            continue
        scanned += 1
        hits += scan_text(card_text(card), "POOL.json/" + card.get("id", "?"))
    return hits, scanned


def scan_orders_since(since):
    with open(ORDERS, encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    hits = []
    for line in text.splitlines():
        m = re.match(r"\|\s*(\d{4}-\d{2}-\d{2})", line)
        if not m or m.group(1) < since:
            continue
        if EXEMPT.search(line):
            continue
        for pat, rx in BLOCK_RX:
            if rx.search(line):
                hits.append(("BLOCK", "orders.md@" + m.group(1), 0, pat, line.strip()[:160]))
        for pat, rx in WARN_RX:
            if rx.search(line):
                hits.append(("WARN", "orders.md@" + m.group(1), 0, pat, line.strip()[:160]))
    return hits


def main():
    # console may be GBK; never die on a BOM or an emoji inside a card
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-statuses", action="store_true")
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument("--orders-since", default="")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    hits, scanned = scan_pool(args.all_statuses)
    for p in args.path:
        try:
            with open(p, encoding="utf-8-sig", errors="replace") as f:
                hits += scan_text(f.read(), p)
            scanned += 1
        except OSError as e:
            print("READ-FAIL %s: %s" % (p, e))
    if args.orders_since:
        hits += scan_orders_since(args.orders_since)

    blocks = [h for h in hits if h[0] == "BLOCK"]
    warns = [h for h in hits if h[0] == "WARN"]

    if not args.quiet:
        for kind, where, lineno, pat, line in hits:
            loc = "%s:%s" % (where, lineno) if lineno else where
            print("%-5s %-28s pat=%-18s %s" % (kind, loc, pat, line))

    print()
    print("cloud-lane-lint: scanned=%d block=%d warn=%d -> %s" % (
        scanned, len(blocks), len(warns), "REFUSE" if blocks else "PASS"))
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
