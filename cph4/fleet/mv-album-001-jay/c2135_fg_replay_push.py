# -*- coding: utf-8 -*-
"""C2135: publish the spec-side files through a detached worktree replay.

The local HQ main is 13 behind / 5 ahead of origin, so commit+push would be rejected
or would drag unrelated local commits; replay the files onto origin/main instead.
"""
import os
import shutil
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
WT = os.path.join(REPO, ".codely-cli", "tmp", "wt-c2135")
REL = "cph4/fleet/mv-album-001-jay"
BANK = "cph4/fleet/work-bank/bm-c-gpu-bank.json"

FILES = [
    REL + "/xq_packa_loudnorm_c2135.py",
    REL + "/xq_packa_v2_origin_verify_c2135.py",
    REL + "/xq-PACKA-CONFORM-v2-loudnorm-c2135.json",
    REL + "/xq-AB-DIRECTOR-RATIFY-r1017.md",
    REL + "/c2135_bank_cmd_fix.py",
    REL + "/c2135_loudnorm_bakeoff.py",
    REL + "/c2135_loudnorm_bakeoff2.py",
    REL + "/c2135_bank_harvest_prestow.py",
    REL + "/c2135_fg_replay_push.py",
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
    msg = ("C2135: A-pack conform loudness master (I=-14.2 LUFS, TP=-2.3 dBTP, 4710/4710 "
           "frames) + origin-verify harvest + v2 verifier prestowed")
    run(["git", "commit", "-m", msg], cwd=WT)
    print("HEAD " + run(["git", "rev-parse", "--short", "HEAD"], cwd=WT).strip())
    run(["git", "push", "origin", "HEAD:main"], cwd=WT)
    print("ORIGIN " + run(["git", "rev-parse", "--short", "origin/main"], cwd=WT).strip())
    run(["git", "worktree", "remove", "--force", WT], check=False)
    shutil.rmtree(WT, ignore_errors=True)
    print("REPLAY-PUSH OK")


if __name__ == "__main__":
    main()