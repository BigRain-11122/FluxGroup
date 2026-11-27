# -*- coding: utf-8 -*-
# c2139_twin_triage.py -- before rebasing FluxGroup main, the remote already carries the c2133/c2135
# batch files; local copies are untracked twins that block checkout. Byte-compare each against
# origin/main and delete only the exact twins; anything different is moved to quarantine.
import os
import shutil
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
QDIR = r"K:\Fluxgroup\FluxGroup\.codely-cli\tmp\c2139_twin_quarantine"

PATHS = """cph4/fleet/mv-album-001-jay/c2133_bank_reviewpack.py
cph4/fleet/mv-album-001-jay/c2133_bank_surgery.py
cph4/fleet/mv-album-001-jay/c2133_bank_surgery2.py
cph4/fleet/mv-album-001-jay/c2133_closeout_writes.py
cph4/fleet/mv-album-001-jay/c2133_fg_push2.py
cph4/fleet/mv-album-001-jay/c2133_fg_replay_push.py
cph4/fleet/mv-album-001-jay/c2133_notes_and_kanban.py
cph4/fleet/mv-album-001-jay/c2133_state_surgery.py
cph4/fleet/mv-album-001-jay/c2135_bank_cmd_fix.py
cph4/fleet/mv-album-001-jay/c2135_bank_harvest_prestow.py
cph4/fleet/mv-album-001-jay/c2135_fg_replay_push.py
cph4/fleet/mv-album-001-jay/c2135_loudnorm_bakeoff.py
cph4/fleet/mv-album-001-jay/c2135_loudnorm_bakeoff2.py
cph4/fleet/mv-album-001-jay/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json
cph4/fleet/mv-album-001-jay/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.md
cph4/fleet/mv-album-001-jay/xq-PACKA-CONFORM-c2133.json
cph4/fleet/mv-album-001-jay/xq-PACKA-CONFORM-v2-loudnorm-c2135.json
cph4/fleet/mv-album-001-jay/xq-PACKA-CUTPOINTS-c2133.json
cph4/fleet/mv-album-001-jay/xq_packa_conform_c2133.py
cph4/fleet/mv-album-001-jay/xq_packa_cutpoints_c2133.py
cph4/fleet/mv-album-001-jay/xq_packa_index_verify_c2133.py
cph4/fleet/mv-album-001-jay/xq_packa_loudnorm_c2135.py
cph4/fleet/mv-album-001-jay/xq_packa_origin_verify_c2133.py
cph4/fleet/mv-album-001-jay/xq_packa_review_pack_c2133.py
cph4/fleet/mv-album-001-jay/xq_packa_v2_origin_verify_c2135.py""".split()


def run(args, **kw):
    return subprocess.run(args, cwd=REPO, capture_output=True, **kw)


os.makedirs(QDIR, exist_ok=True)
same = diff = missing = 0
for p in PATHS:
    full = os.path.join(REPO, p.replace("/", os.sep))
    if not os.path.isfile(full):
        missing += 1
        print("MISSING", p)
        continue
    local = run(["git", "hash-object", "--no-filters", p]).stdout.strip().decode()
    remote = run(["git", "rev-parse", "origin/main:" + p]).stdout.strip().decode()
    if local and local == remote:
        os.remove(full)
        same += 1
    else:
        dst = os.path.join(QDIR, os.path.basename(p))
        shutil.move(full, dst)
        diff += 1
        print("DIFF-MOVED", p, "local=%s remote=%s" % (local[:12], remote[:12] or "ABSENT"))

print("TWIN-TRIAGE-END same=%d diff=%d missing=%d" % (same, diff, missing))