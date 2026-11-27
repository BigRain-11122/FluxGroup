"""C2179: fire the KN re-burn 480P slice the moment the 768P wave exits.

Why this file exists
--------------------
A second i2v runner cannot be started while the 30-unit wave is burning: the
runner unloads models at startup (`/free`), which evicts the resident int8 model
under the in-flight unit and would also split the 16GB card across two H3
pipelines.  So the re-burn was blocked on the wave finishing - exactly the kind
of dependency that used to turn into an hour of idle card waiting for the next
tick to notice.  This script holds the dependency instead of a human: it watches
the wave's PID, and the moment it exits it launches the verification slice.

It is deliberately dumb: one PID, one manifest, one lane (bmcverify, 672x384
int4, clips-verify-480), one log file.  No retries, no state machine - if the
wave dies, the re-burn still fires, because the point of the slice is to answer
"does the fixed camera clause move?" and that question is cheapest answered in
one shot.

Usage
-----
    pythonw kn_waveend_chain_c2179.py --watch-pid 29056 \
        --manifest cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-kn-reburn480-c2179.json

Runs detached; log = media/mv-album-001-jay/logs/kn-reburn480-c2179.log,
runner progress = clips-verify-480/progress-bmcverify.jsonl.
"""
import argparse
import ctypes
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def alive(pid):
    """True while the PID exists (zero-cost, no psutil, no WMI)."""
    PROCESS_QUERY_LIMITED = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return False
        return code.value == 259  # STILL_ACTIVE
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch-pid", type=int, required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--repo", default=r"K:\Fluxgroup\FluxGroup")
    ap.add_argument("--lane", default="bmcverify")
    ap.add_argument("--poll", type=int, default=30)
    ap.add_argument("--settle", type=int, default=25,
                    help="seconds to let the card drain ComfyUI before the new runner")
    a = ap.parse_args()

    logdir = os.path.join(a.repo, "media", "mv-album-001-jay", "logs")
    os.makedirs(logdir, exist_ok=True)
    log = os.path.join(logdir, "kn-reburn480-c2179.log")

    def say(msg):
        line = "%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(line)

    say("CHAIN-ARM watch_pid=%d manifest=%s lane=%s" % (a.watch_pid, a.manifest, a.lane))
    while alive(a.watch_pid):
        time.sleep(a.poll)
    say("CHAIN-WAVE-EXIT pid=%d settling %ds" % (a.watch_pid, a.settle))
    time.sleep(a.settle)

    cmd = [sys.executable, os.path.join(HERE, "local-i2v", "h3_i2v_album.py"),
           "--repo", a.repo, "--lane", a.lane, "--manifest", a.manifest]
    say("CHAIN-FIRE %s" % " ".join(cmd))
    with open(log, "a", encoding="utf-8") as fh:
        rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
    say("CHAIN-END rc=%d" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())