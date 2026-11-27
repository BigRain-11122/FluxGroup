# -*- coding: utf-8 -*-
# verify_patched.py - lint-verify every patched production script's JOBS (no generation, pure text check)
import io, sys, importlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma")
from prompt_lexicon import lint

# each entry: module name, JOBS-like list of (name, prompt, seed) tuples OR dict of prompts
TARGETS = ["krea2_campus", "krea2_designs2", "krea2_designs3"]

fail = 0
for mod in TARGETS:
    m = importlib.import_module(mod)
    jobs = getattr(m, "JOBS", None)
    if jobs is None:
        print("[%s] NO JOBS EXPORT" % mod); fail += 1; continue
    bad = 0
    for item in jobs:
        name, prompt = item[0], item[1]
        hits = lint(prompt)
        wc = len(prompt.split())
        if hits or wc > 200 or wc < 15:
            bad += 1
            print("[FAIL] %s.%s words=%d hits=%s" % (mod, name, wc, hits))
    print("[%s] %d/%d jobs %s" % (mod, len(jobs) - bad, len(jobs), "LINT GREEN" if bad == 0 else "FAILED"))
    fail += bad
print("TOTAL:", "ALL GREEN" if fail == 0 else ("%d FAIL" % fail))
