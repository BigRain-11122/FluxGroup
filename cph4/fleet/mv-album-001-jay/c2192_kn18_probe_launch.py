"""C2192: KN18 480P probe from the re-burned clean keyframe.

Same one-process shape as C2186/C2189 (server bring-up + run, zero console), so
the card never idles waiting for a human to notice.  The motion prompt is
unchanged from C2189 r4 - the keyframe is the only variable under test, because
the r4 harvest traced the amber nebula to the KF itself.

Usage (detached, zero console):
    pythonw c2192_kn18_probe_launch.py
Log: media/mv-album-001-jay/logs/kn-galaxy480-c2192.log
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
MANIFEST = os.path.join(HERE, "local-i2v", "run-bmc-kn-galaxy480-c2192.json")
LOGDIR = os.path.join(REPO, "media", "mv-album-001-jay", "logs")
LOG = os.path.join(LOGDIR, "kn-galaxy480-c2192.log")


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
        out = open(os.path.join(LOGDIR, "comfy-c2192.out.log"), "ab")
        err = open(os.path.join(LOGDIR, "comfy-c2192.err.log"), "ab")
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