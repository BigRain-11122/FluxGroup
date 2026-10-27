# -*- coding: utf-8 -*-
"""c2099 sidecar guard (bm-c POOL-0021 leg-2): keep the v0.42 ComfyUI sidecar
(port 8199, Qwen-Image-2.1 nodes) alive and idle-cheap.

Contract:
  * alive  : if /system_stats does not answer, relaunch the bootstrap detached
             (InvisibleRunner-style hidden start; no console window -- U060).
  * idle   : the sidecar keeps ~12GB of weights resident after a run. On this
             machine (generative-visual dedicated lane, GPU floor 12GB for KF/i2v
             burns) a silent resident sidecar starves production, so whenever
             nothing is queued the guard posts /free to drop VRAM to baseline.
  * respect: does nothing while the machine is in a CEO pause window
             (machine-state.flag) or while the governor flag says gen with a
             live production burn -- only the alive+idle legs run, no relaunch
             storm.
Runs from the HQ-SidecarGuard scheduled task (every 10 min) and is safe to run
by hand. ASCII prints only.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

PORT = 8199
BASE = "http://127.0.0.1:%d" % PORT
PY = r"D:\ComfyUI\python_embeded\python.exe"
BOOT = r"K:\ComfyUICore\c2099_sidecar_boot.py"
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\comfy-sidecar"
FLAG = r"K:\Fluxgroup\.codely-cli\machine-state.flag"
GOV = r"K:\Fluxgroup\.codely-cli\gpu-mode.flag"
STATE = os.path.join(LOGDIR, "sidecar-guard-state.json")


def log(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    with open(os.path.join(LOGDIR, "sidecar-guard.log"), "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")


def get(path, timeout=15):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post(path, body, timeout=60):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def alive():
    try:
        s = get("/system_stats", timeout=10)
        return True, s
    except Exception:
        return False, None


def relaunch():
    os.makedirs(LOGDIR, exist_ok=True)
    args = [PY, BOOT, "--port", str(PORT), "--listen", "127.0.0.1",
            "--base-directory", r"K:\ComfyUICore",
            "--extra-model-paths-config", r"K:\ComfyUICore\extra_model_paths.yaml",
            "--disable-auto-launch"]
    flags = 0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS
    out = open(os.path.join(LOGDIR, "sidecar.out.txt"), "ab")
    err = open(os.path.join(LOGDIR, "sidecar.err.txt"), "ab")
    p = subprocess.Popen(args, cwd=LOGDIR, stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                         creationflags=flags, close_fds=True)
    log("relaunch pid=%d" % p.pid)
    return p.pid


def paused():
    # machine-state.ps1 writes BOTH "pause ..." and "resumed ..." into this flag;
    # only a pause line means the CEO has the machine (a bare presence test would
    # freeze the guard forever after the first resume).
    try:
        with open(FLAG, "r", encoding="ascii", errors="replace") as f:
            return f.read().strip().lower().startswith("pause")
    except Exception:
        return False


def main():
    st = {"runs": 0}
    if os.path.isfile(STATE):
        try:
            st.update(json.load(open(STATE, encoding="utf-8")))
        except Exception:
            pass
    st["runs"] += 1
    st["last_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if paused():
        st["last_action"] = "skip-paused"
        log("machine pause flag present -- no-op")
    else:
        ok, s = alive()
        if not ok:
            relaunch()
            time.sleep(45)
            ok, s = alive()
            st["last_action"] = "relaunched" if ok else "relaunch-failed"
            log("alive=%s after relaunch" % ok)
        if ok:
            try:
                q = get("/queue")
                busy = len(q.get("queue_running", [])) + len(q.get("queue_pending", []))
            except Exception:
                busy = -1
            st["queue"] = busy
            if busy == 0:
                try:
                    post("/free", {"unload_models": True, "free_memory": True}, timeout=90)
                    st["last_action"] = "idle-free"
                except Exception as e:
                    st["last_action"] = "free-failed:%s" % str(e)[:60]
            elif busy > 0:
                st["last_action"] = "busy-hold"
            vram_free = None
            try:
                vram_free = round(s["devices"][0]["vram_free"] / 1048576)
            except Exception:
                pass
            st["vram_free_mb"] = vram_free
            st["comfy_version"] = (s.get("system", {}) or {}).get("comfyui_version")
            log("alive v=%s busy=%s vram_free=%sMB action=%s" %
                (st.get("comfy_version"), busy, vram_free, st.get("last_action")))
    json.dump(st, open(STATE, "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())