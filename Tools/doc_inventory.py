# -*- coding: utf-8 -*-
"""doc_inventory.py - find version clusters, exact duplicates and orphan docs.

Read-only. Prints three sections:
  1. CLUSTERS   same topic, several version-suffixed files (candidate supersession)
  2. DUPLICATES byte-identical pairs (one is redundant)
  3. UNREFERENCED docs nobody links to from any .md
"""
import hashlib
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# HQ governance surface only. Sub-repos (gaming/quant/media/life/domain/compute/
# house) are separate git repos with their own cleanup; counting them here just
# inflates the numbers and risks deleting into someone else's tree.
SCAN = ["cph4", "docs", "Tools"]
SUBREPO = ("gaming", "quant", "media", "life", "domain", "compute", "house")

VER_RX = re.compile(r"[-_]v(\d+(?:\.\d+)?)(?=[-_.]|$)", re.I)
DATE_RX = re.compile(r"\d{8}|[-_]r\d{3,4}")


def norm(name):
    """Strip extension and version tokens to get a topic key."""
    base = os.path.splitext(name)[0]
    key = VER_RX.sub("", base)
    key = re.sub(r"[-_]{2,}", "-", key).strip("-_").lower()
    return key


def collect():
    files, seen = [], set()
    # root-level docs
    for fn in os.listdir(ROOT):
        if fn.lower().endswith((".md", ".txt")) and os.path.isfile(os.path.join(ROOT, fn)):
            p = os.path.join(ROOT, fn)
            files.append((fn, p, fn))
            seen.add(fn)
    for d in SCAN:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in
                           (".git", "node_modules", "__pycache__", ".venv", "media",
                            "_archive") and x not in SUBREPO]
            for fn in filenames:
                if not fn.lower().endswith((".md", ".txt")):
                    continue
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                if rel in seen:
                    continue
                seen.add(rel)
                files.append((rel, p, fn))
    return files


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    files = collect()
    print("scanned docs: %d" % len(files))

    # 1. version clusters - only vN tokens count as versions; dated docs are
    # separate records (council bills, daily scans), not newer drafts of one file.
    clusters = defaultdict(list)
    for rel, p, fn in files:
        stem = os.path.splitext(fn)[0]
        if DATE_RX.search(stem):
            continue
        m = VER_RX.search(stem)
        if not m:
            continue
        key = norm(fn)
        ver = float(m.group(1))
        clusters[(key, os.path.dirname(rel))].append((rel, p, ver))

    print("\n=== VERSION CLUSTERS (same topic dir, vN siblings) ===")
    n_clusters = 0
    superseded = []
    for (k, d), members in sorted(clusters.items()):
        if len(members) < 2:
            continue
        n_clusters += 1
        top = max(m[2] for m in members)
        print("\n[%s]  (%s)  newest=v%s" % (k, d, top))
        for rel, p, ver in sorted(members, key=lambda x: -x[2]):
            tag = "  NEWEST" if ver == top else "  superseded"
            print("   %8d  v%-5s %s%s" % (os.path.getsize(p), ver, rel, tag))
            if ver < top:
                superseded.append(rel)
    print("\nclusters: %d ; superseded candidates: %d" % (n_clusters, len(superseded)))

    # 2. duplicates
    hashes = defaultdict(list)
    for rel, p, fn in files:
        if os.path.getsize(p) > 2_000_000:
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        hashes[h].append(rel)
    dups = {h: v for h, v in hashes.items() if len(v) > 1}
    print("\n=== DUPLICATES (byte-identical) ===")
    for h, v in dups.items():
        print("  " + "  ==  ".join(v))
    print("\nduplicate groups: %d" % len(dups))

    # 3. unreferenced
    blob = []
    for rel, p, fn in files:
        try:
            blob.append(open(p, encoding="utf-8", errors="ignore").read())
        except OSError:
            pass
    corpus = "\n".join(blob)
    orphans = []
    for rel, p, fn in files:
        base = os.path.basename(rel)
        if corpus.count(base) <= 1:      # only its own heading mentions it
            orphans.append(rel)
    print("\n=== UNREFERENCED (name appears once in the whole corpus) ===")
    for o in sorted(orphans)[:40]:
        print("  " + o)
    print("\norphans: %d" % len(orphans))


if __name__ == "__main__":
    main()