"""C2185: start ComfyUI (hidden) then run the KN galaxy 480P probe slice.

The C2183 cut failed its one content item, so the probe has to answer one
question on the card: does the rewritten motion body (discrete round points
instead of arc/band/currents) still drift into twining golden filaments?  A
verification slice is worth nothing if it waits for a human to notice the card
is idle, so the server bring-up and the run live in one detached process.

Usage (detached, zero console):
    pythonw c2185_kn_galaxy_probe_launch.py
Log: media/mv-album-001-jay/logs/kn-galaxy480-c2185.log
"""
import os
import subprocess
import sys
import time
import urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
HERE = os.path.dirname(os.path.abspath(__file__))
COMFY = r"D:\ComfyUI"
PY = os.path.join(COMFY, "python_embeded", "python.exe")
MAIN = os.path.join(COMFY, "ComfyUI", "main.py")
MANIFEST = os.path.join(HERE, "local-i2v", "run-bmc-kn-galaxy480-c2185.json")
LOGDIR = os.path.join(REPO, "media", "mv-album-001-jay", "logs")
LOG = os.path.join(LOGDIR, "kn-galaxy480-c2185.log")


def say(msg):
    line = "%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line)


def server_up():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    os.makedirs(LOGDIR, exist_ok=True)
    say("LAUNCH-PROBE manifest=%s" % MANIFEST)

    if server_up():
        say("SERVER already up")
    else:
        out = open(os.path.join(LOGDIR, "comfy-c2185.out.log"), "ab")
        err = open(os.path.join(LOGDIR, "comfy-c2185.err.log"), "ab")
        flags = 0x08000000  # CREATE_NO_WINDOW
        proc = subprocess.Popen([PY, MAIN, "--port", "8188"], cwd=COMFY,
                                stdout=out, stderr=err, creationflags=flags)
        say("SERVER spawn pid=%d" % proc.pid)
        t0 = time.time()
        while time.time() - t0 < 240:
            if server_up():
                say("SERVER ready after %.0fs" % (time.time() - t0))
                break
            time.sleep(5)
        else:
            say("FATAL server did not come up in 240s")
            return 1

    cmd = [sys.executable, os.path.join(HERE, "local-i2v", "h3_i2v_album.py"),
           "--repo", REPO, "--lane", "bmcverify", "--manifest", MANIFEST]
    say("RUN " + " ".join(cmd))
    with open(LOG, "a", encoding="utf-8") as fh:
        rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
    say("PROBE-END rc=%d" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())