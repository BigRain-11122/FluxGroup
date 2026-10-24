# -*- coding: utf-8 -*-
"""mv_reburn_when_idle.py - queue the static-take reburn behind whatever is on the GPU.

Why: the stability gate (D-20261024-05) fails 5 source takes because the i2v motion
came out near-static. Re-burning them needs the GPU, which is currently running a
production batch that must not be preempted. This waiter polls ComfyUI, waits for the
queue to be empty for three consecutive checks, then launches the 480P verification
slice from run-bmc-static-reburn480.json.

Guards:
  - machine-state pause flag (CEO using the machine) stops the waiter cold.
  - a live owner batch that keeps the queue busy for longer than MAX_WAIT_H just
    exits and logs, rather than surprising anyone hours later.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "local-i2v")
MANIFEST = "cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-static-reburn480.json"
LOG = os.path.join(REPO, "media", "mv-album-001-jay", "reburn-waiter.log")
PAUSE_FLAG = os.path.join(os.path.expanduser("~"), ".codely-cli", "machine-state.flag")
SERVER = "http://127.0.0.1:8188"
POLL_S = 60
IDLE_NEEDED = 3
MAX_WAIT_H = 6.0


def log(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    try:
        print(line, flush=True)
    except Exception:
        pass


def paused():
    try:
        return os.path.isfile(PAUSE_FLAG) and "paused" in open(PAUSE_FLAG, encoding="utf-8").read().lower()
    except Exception:
        return False


def queue_state():
    with urllib.request.urlopen(SERVER + "/queue", timeout=15) as r:
        q = json.loads(r.read().decode("utf-8", "replace"))
    return len(q.get("queue_running", [])), len(q.get("queue_pending", []))


def main():
    log("WAITER-START manifest=%s idle_checks=%d max_wait=%.1fh" % (MANIFEST, IDLE_NEEDED, MAX_WAIT_H))
    deadline = time.time() + MAX_WAIT_H * 3600
    idle = 0
    while time.time() < deadline:
        if paused():
            log("WAITER-STOP machine paused (CEO using the box); nothing launched")
            return 0
        try:
            run, pend = queue_state()
        except Exception as e:
            log("queue probe failed: %s" % e)
            idle = 0
            time.sleep(POLL_S)
            continue
        if run == 0 and pend == 0:
            idle += 1
            log("idle %d/%d" % (idle, IDLE_NEEDED))
            if idle >= IDLE_NEEDED:
                break
        else:
            if idle:
                log("queue busy again running=%d pending=%d" % (run, pend))
            idle = 0
        time.sleep(POLL_S)
    else:
        log("WAITER-GAVE-UP queue never stayed empty inside the wait window")
        return 0

    args = ["D:\\ComfyUI\\python_embeded\\python.exe",
            os.path.join(PKG, "h3_i2v_album.py"),
            "--repo", REPO, "--lane", "bmcverify", "--manifest", MANIFEST]
    log("LAUNCH " + " ".join(args))
    out = open(os.path.join(REPO, "media", "mv-album-001-jay", "log-reburn480.out.txt"), "ab")
    err = open(os.path.join(REPO, "media", "mv-album-001-jay", "log-reburn480.err.txt"), "ab")
    p = subprocess.Popen(args, cwd=PKG, stdout=out, stderr=err,
                         creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    log("LAUNCHED pid=%d" % p.pid)
    return 0


if __name__ == "__main__":
    sys.exit(main())