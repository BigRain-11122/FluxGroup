# -*- coding: ascii -*-
# c2133_fg_replay_push.py - publish the C2133 spec-side files via a detached
# worktree replay (the local main is 11 behind / 5 ahead of origin, so a plain
# commit+push would either be rejected or drag unrelated local commits).

import os
import shutil
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
WT = os.path.join(REPO, ".codely-cli", "tmp", "wt-c2133")
REL = "cph4/fleet/mv-album-001-jay"
BANK = "cph4/fleet/work-bank/bm-c-gpu-bank.json"

FILES = [
    REL + "/xq_packa_conform_c2133.py",
    REL + "/xq_packa_index_verify_c2133.py",
    REL + "/xq_packa_cutpoints_c2133.py",
    REL + "/xq_packa_review_pack_c2133.py",
    REL + "/c2133_bank_surgery.py",
    REL + "/c2133_bank_surgery2.py",
    REL + "/c2133_bank_reviewpack.py",
    REL + "/c2133_state_surgery.py",
    REL + "/c2133_closeout_writes.py",
    REL + "/c2133_notes_and_kanban.py",
    REL + "/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json",
    REL + "/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.md",
    REL + "/xq-PACKA-CONFORM-c2133.json",
    REL + "/xq-PACKA-CUTPOINTS-c2133.json",
    BANK,
]


def run(args, cwd=REPO, check=True):
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace")
    if check and p.returncode != 0:
        print("FAIL %s\n%s" % (" ".join(args), out))
        sys.exit(1)
    return out


def main():
    if os.path.isdir(WT):
        run(["git", "worktree", "remove", "--force", WT], check=False)
        shutil.rmtree(WT, ignore_errors=True)
    run(["git", "fetch", "origin", "--quiet"])
    run(["git", "worktree", "add", "--detach", WT, "origin/main"])
    for rel in FILES:
        src = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.exists(src):
            print("MISSING %s" % rel)
            sys.exit(2)
        dst = os.path.join(WT, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    run(["git", "add", "-f"] + FILES, cwd=WT)
    msg = ("C2133-conform: A-pack conform preview + index v2 authored order + cut-point "
           "proof + review pack; bank verify closed")
    run(["git", "commit", "-m", msg], cwd=WT)
    print(run(["git", "rev-parse", "--short", "HEAD"], cwd=WT).strip())
    run(["git", "push", "origin", "HEAD:main"], cwd=WT)
    print(run(["git", "rev-parse", "--short", "origin/main"], cwd=WT).strip())
    run(["git", "worktree", "remove", "--force", WT], check=False)
    shutil.rmtree(WT, ignore_errors=True)
    print("REPLAY-PUSH OK")


if __name__ == "__main__":
    main()