#!/usr/bin/env python3
"""Agent Library audit: skills <-> registry consistency check.

Usage: python Tools/agent-library-audit.py
Read-only, ASCII output. Used by agent-librarian skill and the weekly
CEO-PROXY deep review (cph4/agents/GOVERNANCE.md section 2).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON_DIR = os.path.join(ROOT, "cph4", "skills")
LOCAL_DIR = os.path.join(ROOT, ".codely-cli", "skills")
REGISTRY = os.path.join(ROOT, "cph4", "agents", "AGENT-LIBRARY.md")


def skill_name(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i > 30:
                    break
                m = re.match(r"^name:\s*(\S+)", line)
                if m:
                    return m.group(1).strip()
    except OSError:
        pass
    return None


def collect(root, skip_ccgs_children=False):
    out = {}
    if not os.path.isdir(root):
        return out
    for entry in sorted(os.listdir(root)):
        p = os.path.join(root, entry)
        if os.path.isfile(os.path.join(p, "SKILL.md")):
            n = skill_name(os.path.join(p, "SKILL.md")) or entry
            out[entry] = n
        elif entry == "ccgs" and os.path.isdir(p):
            for sub in sorted(os.listdir(p)):
                sp = os.path.join(p, sub, "SKILL.md")
                if os.path.isfile(sp):
                    n = skill_name(sp) or sub
                    out[sub] = n
    return out


def main():
    canon = collect(CANON_DIR)
    local = collect(LOCAL_DIR)
    registry = ""
    if os.path.isfile(REGISTRY):
        with open(REGISTRY, "r", encoding="utf-8", errors="replace") as f:
            registry = f.read()

    orphan_canon = [d for d, n in canon.items() if n and n not in registry]
    orphan_local = [d for d, n in local.items() if n and n not in registry]
    local_only = [d for d in local if d not in canon]
    canon_not_installed = [d for d in canon if d not in local]

    print("=== AGENT-LIBRARY AUDIT ===")
    print("canon skills (cph4/skills): %d" % len(canon))
    print("local installs (.codely-cli/skills): %d" % len(local))
    print("registry file present: %s" % ("yes" if registry else "MISSING"))
    print("-- canon skills missing from registry (ORPHAN-CANON, register them):")
    for d in orphan_canon:
        print("   %s (name=%s)" % (d, canon[d]))
    print("-- local installs missing from registry (ORPHAN-LOCAL, register them):")
    for d in orphan_local:
        print("   %s (name=%s)" % (d, local[d]))
    print("-- local installs with NO canon source (need canonization to cph4/skills/):")
    for d in local_only:
        print("   %s" % d)
    print("-- canon skills not installed locally (run Tools/agent-library-sync.ps1):")
    for d in canon_not_installed:
        print("   %s" % d)
    total_issues = len(orphan_canon) + len(orphan_local) + len(local_only)
    print("SUMMARY: registry-orphan issues=%d, canonization-needed=%d, uninstalled=%d"
          % (total_issues, len(local_only), len(canon_not_installed)))
    print("VERDICT: %s" % ("PASS" if total_issues == 0 else "GAPS FOUND - fix per GOVERNANCE.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
