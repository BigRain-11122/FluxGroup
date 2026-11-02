#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gpu_lease.py - one owner per GPU at a time (cross-platform, stdlib only).

Why: bm-a sat at 9% GPU with 11.2/12.3GB used. The resident Ollama model (7.3GB) and
the keep-warm task were holding the card, so a production KF batch could not load.
Nothing arbitrated "production vs sentinel". This is that arbiter: acquire -> evict
lower-priority residents (Ollama + keep-warm tasks) -> wait for VRAM -> optionally start
ComfyUI in lowvram; release -> stop what we started -> restore the residents.

Usage:
  python3 gpu_lease.py --node bm-a --status
  python3 gpu_lease.py --node bm-a --acquire --need-mb 12000 --start-comfy
  python3 gpu_lease.py --node bm-a --release
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "Tools", "nats", "data")
COMFY_ROOT = r"D:\AI\comfyui-krea\ComfyUI_windows_portable"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
KEEPWARM = ["MiniGameOllamaKeepWarm", "MiniGameOllamaServe"]


def lease_path(node):
    return os.path.join(DATA, "gpu.%s.lease.json" % node)


def sh(args, timeout=30):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                           creationflags=CREATE_NO_WINDOW)
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except Exception as e:
        return 1, "", str(e)


def ps(cmd, timeout=30):
    return sh(["powershell", "-NoProfile", "-Command", cmd], timeout)


def vram():
    rc, out, _ = sh(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"])
    if rc != 0 or not out.strip():
        return None, None
    parts = [x.strip() for x in out.splitlines()[0].split(",")]
    return int(parts[0]), int(parts[1])


def driven_comfy_up(port=8188):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/system_stats" % port, timeout=3):
            return True
    except Exception:
        return False


def stop_ollama():
    rc, out, _ = sh(["ollama", "ps"])
    names = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if parts:
            names.append(parts[0])
    for n in set(names):
        sh(["ollama", "stop", n], timeout=20)
    return names


def set_tasks(enable):
    verb = "Enable-ScheduledTask" if enable else "Disable-ScheduledTask"
    for t in KEEPWARM:
        ps("%s -TaskName '%s' -ErrorAction SilentlyContinue | Out-Null" % (verb, t))


def start_comfy(port=8188, need_mb=12000):
    if driven_comfy_up(port):
        return None, True
    py = os.path.join(COMFY_ROOT, "python_embeded", "python.exe")
    if not os.path.exists(py):
        py = "python"
    args = [py, "main.py", "--listen", "0.0.0.0", "--port", str(port),
            "--lowvram", "--disable-auto-launch"]
    p = subprocess.Popen(args, cwd=os.path.join(COMFY_ROOT, "ComfyUI"),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=CREATE_NO_WINDOW)
    deadline = time.time() + 240
    while time.time() < deadline:
        if driven_comfy_up(port):
            return p.pid, True
        if p.poll() is not None:
            return p.pid, False
        time.sleep(3)
    return p.pid, False


def acquire(node, need_mb, with_comfy, owner="", job_id="", relaxed=False):
    """Exclusive GPU lease. Identity matters: on 2026-11-02 the lease carried the literal
    owner "gpu_lease" and `--if-held-ok` defaulted to true, so a second job was told
    "lease ok" while another job was already using the card. Same job re-acquires and
    renews; a different job is busy."""
    lp = lease_path(node)
    if os.path.exists(lp):
        try:
            old = json.load(open(lp, encoding="utf-8"))
            age = time.time() - old.get("epoch", 0)
            if age < old.get("ttl_s", 7200):
                if job_id and old.get("job_id") == job_id:
                    old["epoch"] = time.time()
                    old["ts"] = datetime.now().isoformat(timespec="seconds")
                    _atomic_write(lp, old)
                    print("LEASE-RENEW job=%s" % job_id)
                    return 0
                print("LEASE-BUSY owner=%s job=%s age=%ds"
                      % (old.get("owner"), old.get("job_id"), int(age)))
                return 0 if relaxed else 2
        except Exception:
            pass
    stopped = stop_ollama()
    set_tasks(False)
    deadline = time.time() + 90
    used = total = None
    while time.time() < deadline:
        used, total = vram()
        if used is not None and (total - used) >= need_mb:
            break
        time.sleep(3)
    used, total = vram()
    ok = used is not None and (total - used) >= need_mb
    comfy_pid = None
    if ok and with_comfy:
        comfy_pid, up = start_comfy(need_mb=need_mb)
        ok = ok and up
    lease = {"node": node, "owner": owner or "unattributed", "job_id": job_id,
             "need_mb": need_mb,
             "vram_used_mb": used, "vram_total_mb": total,
             "comfy_pid": comfy_pid, "stopped_ollama": stopped,
             "epoch": time.time(), "ttl_s": 7200,
             "ts": datetime.now().isoformat(timespec="seconds")}
    os.makedirs(DATA, exist_ok=True)
    _atomic_write(lp, lease)
    if not ok:
        print("LEASE-FAIL free=%sMB need=%sMB" % ((total - used) if used else "?", need_mb))
        return 1
    print("LEASE-OK free=%sMB need=%sMB comfy_pid=%s" % (total - used, need_mb, comfy_pid))
    return 0


def _atomic_write(path, obj):
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def release(node, owner="", force=False):
    """Only the holder may release. Before 2026-11-02 any lane could delete any lease,
    which silently handed a busy card to the next job."""
    lp = lease_path(node)
    lease = {}
    if os.path.exists(lp):
        try:
            lease = json.load(open(lp, encoding="utf-8"))
        except Exception:
            pass
        if owner and not force and lease.get("owner") not in (None, "", owner):
            print("LEASE-RELEASE-DENIED holder=%s caller=%s" % (lease.get("owner"), owner))
            return 2
        os.remove(lp)
    pid = lease.get("comfy_pid")
    if pid:
        sh(["taskkill", "/PID", str(pid), "/T", "/F"], timeout=20)
    set_tasks(True)
    print("LEASE-RELEASED comfy_stopped=%s keepwarm_restored=True" % bool(pid))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--acquire", action="store_true")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--need-mb", type=int, default=12000)
    ap.add_argument("--start-comfy", action="store_true")
    ap.add_argument("--owner", default="", help="who holds it (node or agent id)")
    ap.add_argument("--job", default="", help="card id; the same id re-acquires its own lease")
    ap.add_argument("--relaxed", action="store_true",
                    help="DEPRECATED: treat a held lease as success (breaks exclusivity)")
    ap.add_argument("--force", action="store_true", help="release regardless of holder")
    a = ap.parse_args()
    if a.status:
        used, total = vram()
        print("VRAM used=%s total=%s free=%s" % (used, total, (total - used) if used else "?"))
        lp = lease_path(a.node)
        print("LEASE " + (open(lp, encoding="utf-8").read().strip() if os.path.exists(lp) else "none"))
        return 0
    if a.acquire:
        return acquire(a.node, a.need_mb, a.start_comfy, a.owner, a.job, a.relaxed)
    if a.release:
        return release(a.node, a.owner, a.force)
    print("usage: --status | --acquire [--need-mb N] [--start-comfy] | --release")
    return 2


if __name__ == "__main__":
    sys.exit(main())