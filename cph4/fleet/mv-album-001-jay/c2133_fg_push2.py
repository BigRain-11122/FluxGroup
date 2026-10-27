# -*- coding: ascii -*-
# c2133_fg_push2.py - publish the origin verifier used by the prestowed bank job.

import os
import shutil
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
WT = os.path.join(REPO, ".codely-cli", "tmp", "wt-c2133b")
REL = "cph4/fleet/mv-album-001-jay"
FILES = [
    REL + "/xq_packa_origin_verify_c2133.py",
    REL + "/c2133_fg_replay_push.py",
    REL + "/c2133_fg_push2.py",
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
    run(["git", "commit", "-m",
         "C2133-conform: origin verifier for the prestowed bank job + replay push helpers"],
        cwd=WT)
    print(run(["git", "rev-parse", "--short", "HEAD"], cwd=WT).strip())
    run(["git", "push", "origin", "HEAD:main"], cwd=WT)
    run(["git", "worktree", "remove", "--force", WT], check=False)
    shutil.rmtree(WT, ignore_errors=True)
    print("PUSH2 OK")


if __name__ == "__main__":
    main()