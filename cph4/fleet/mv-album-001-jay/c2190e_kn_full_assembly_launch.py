"""C2190e: fire the film v2 re-assembly (KN) detached after KN17 joins the pack.

The KN17 768P production clip cleared its gate (p99 32/31/32, no shard striations
at 1:1) and was promoted to clips-local-768/KN_A-KN17.mp4, so the full-film
assembly that had been blocked on that unit can run. The encode is fired detached
(pythonw + redirected logs) so the tick round can close without holding the shell,
and a wave-harvest flag is written for the next round to adopt the resulting film.
"""

import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r"K:\Fluxgroup\FluxGroup"
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
LOGDIR = os.path.join(MEDIA, "logs")
FLAG = os.path.join(REPO, ".codely-cli", "engine-tick", "wave-harvest-pending.json")
BATCH = "C2190e"
OUT_LOG = os.path.join(LOGDIR, "kn-full-assembly-c2190e.log")
OUT_ERR = os.path.join(LOGDIR, "kn-full-assembly-c2190e.err.log")


def main():
    os.makedirs(LOGDIR, exist_ok=True)
    script = os.path.join(HERE, "kn_full_assembly_c2183.py")
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.isfile(pyw):
        pyw = sys.executable

    with io.open(OUT_LOG, "w", encoding="utf-8") as out, \
            io.open(OUT_ERR, "w", encoding="utf-8") as err:
        proc = subprocess.Popen(
            [pyw, "-u", script, "--encode"],
            cwd=HERE, stdout=out, stderr=err,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
        )

    payload = {
        "batch": BATCH,
        "project": "mv-album-001-jay / KN PACK-A whole film v2 (C2183 assembly, re-encoded)",
        "fired_at": time.strftime("%Y-%m-%d %H:%M"),
        "what": "full-film v2 re-assembly with KN_A-KN17.mp4 (C2190 768P green, p99 32/31/32) in place",
        "verdict_paths": [
            OUT_LOG,
            OUT_ERR,
            "media/mv-album-001-jay/assembly-packA-KN/",
        ],
        "harvest_round_task": (
            "0) read log tail until the assembly reports its output path, or err log shows a failure; "
            "1) ffprobe the new film (duration ~239.0s, 30 units + 11 replay windows, audio -14 LUFS); "
            "2) spot-check 3 native frames around the galaxy band (KN17 window 109.00-117.46s) for the band read; "
            "3) KN18 still needs its keyframe re-burn (light block galaxy_dust_cu is already committed) "
            "before a fresh 480P probe - it is NOT in this cut; 4) director re-pass; delete this file once harvested."
        ),
        "prior": (
            "C2190 harvested at 17:02: KN17 768P GREEN - p99 32/31/32 (threshold 47), "
            "no vertical shard striations or hard torn edge at 1:1, clip tracks its keyframe "
            "(37/18) one point cooler rather than adding glow. KN18 prompt-side fix committed "
            "(2e773bcf): its amber nebula is inherited from the galaxy_gold establishing-band "
            "light block, now replaced by a close-up-only galaxy_dust_cu block."
        ),
        "pid": proc.pid,
    }
    os.makedirs(os.path.dirname(FLAG), exist_ok=True)
    with io.open(FLAG, "w", encoding="ascii") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=True)

    print("launched pid=%d log=%s" % (proc.pid, OUT_LOG))
    print("flag:", FLAG)
    return 0


if __name__ == "__main__":
    sys.exit(main())