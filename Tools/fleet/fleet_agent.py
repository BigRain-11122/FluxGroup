#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_agent.py - per-node command receiver + ack (stdlib only, cross-platform).

Why: the trial proved distribution != execution. A poke wakes a node's default task
list, not the command's handler, and no node reports back. This agent is the missing
receiver + executor of the unified command plane (cph4/fleet/UNIFIED-COMMAND-PLANE-v1.md,
2026-10-28 CEO order): subscribes to fleet.cmd, dedupes by id, runs a WHITELIST of actions,
reports ack via NATS + a local acks/ dir. Nodes never write the group repo any more - that
is exactly what diverged the worktree and stopped order intake on 2026-10-28. Commands are
read straight from origin/main blobs, so a dirty worktree cannot block intake either.
It never executes arbitrary shell from a command.

Usage:
  python3 fleet_agent.py --node bm-a --serve
  python3 fleet_agent.py --node bm-a --once --wait 8
  python3 fleet_agent.py --node bm-a --once --no-push --no-scan
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def now():
    return datetime.now(timezone.utc)


def ts_str():
    return now().isoformat(timespec="milliseconds").replace("+00:00", "Z")


def run(cmd, timeout=10):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           creationflags=CREATE_NO_WINDOW)
        return (p.stdout or "").strip()
    except Exception:
        return ""


def stats():
    st = {"cpu_load_pct": None, "ram_free_gb": None, "disk_free_gb": None,
          "gpu_util_pct": None, "vram_used_mb": None, "vram_total_mb": None}
    try:
        st["disk_free_gb"] = round(shutil.disk_usage(ROOT_DEFAULT).free / 1e9, 1)
    except Exception:
        pass
    try:
        if os.name == "nt":
            v = run(["powershell", "-NoProfile", "-Command",
                     "(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average"])
            if v and v.replace(".", "").isdigit():
                st["cpu_load_pct"] = round(float(v), 1)
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            m = MEMORYSTATUSEX()
            m.dwLength = ctypes.sizeof(m)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            st["ram_free_gb"] = round(m.ullAvailPhys / 1e9, 1)
        else:
            st["cpu_load_pct"] = round(os.getloadavg()[0], 1)
            if platform.system() == "Darwin":
                vm = run(["vm_stat"])
                page, free = 4096, 0
                for line in vm.splitlines():
                    if "page size of" in line:
                        page = int(line.split("page size of")[1].split()[0])
                    if line.startswith(("Pages free", "Pages inactive")):
                        free += int(line.split(":")[1].strip().rstrip("."))
                st["ram_free_gb"] = round(free * page / 1e9, 1)
            elif os.path.exists("/proc/meminfo"):
                for line in open("/proc/meminfo"):
                    if line.startswith("MemAvailable:"):
                        st["ram_free_gb"] = round(int(line.split()[1]) / 1e6, 1)
                        break
    except Exception:
        pass
    g = run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"])
    if g:
        parts = [x.strip() for x in g.splitlines()[0].split(",")]
        try:
            st["gpu_util_pct"] = int(parts[0])
            st["vram_used_mb"] = int(parts[1])
            st["vram_total_mb"] = int(parts[2])
        except Exception:
            pass
    return st


class NatsSub:
    def __init__(self, host, port=4222, timeout=5.0):
        self.sock = socket.create_connection((host, port), timeout)
        self.sock.settimeout(timeout)
        self.buf = b""
        self._read_line()
        self._send(b'CONNECT {"verbose":false,"pedantic":false}\r\n')
        self._send(b"SUB fleet.cmd 1\r\n")

    def _send(self, data):
        self.sock.sendall(data)

    def _read_line(self):
        while b"\r\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("nats closed")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\r\n", 1)
        return line.decode("utf-8", "replace")

    def _read_exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("nats closed")
            self.buf += chunk
        data, self.buf = self.buf[:n], self.buf[n:]
        return data

    def next(self, timeout):
        self.sock.settimeout(timeout)
        try:
            while True:
                line = self._read_line()
                if line == "PING":
                    self._send(b"PONG\r\n")
                    continue
                if line.startswith("MSG "):
                    n = int(line.split()[-1])
                    data = self._read_exact(n)
                    self._read_exact(2)
                    return data
        except socket.timeout:
            return None
        except Exception:
            return None


def load_seen(path):
    try:
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(path, seen):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sorted(seen)[-1000:], f)
    except Exception:
        pass


def git_push(path, root, message):
    rel = os.path.relpath(path, root).replace("\\", "/")
    run(["git", "-C", root, "add", "--", rel], timeout=20)
    run(["git", "-C", root, "commit", "-m", message, "--", rel], timeout=20)
    p = subprocess.run(["git", "-C", root, "push", "origin", "HEAD:main"],
                       capture_output=True, text=True, timeout=45,
                       creationflags=CREATE_NO_WINDOW)
    return p.returncode == 0


def nats_pub(hub, port, subject, payload, timeout=3.0):
    """Fire-and-forget publish (no dependency on the SUB client)."""
    try:
        s = socket.create_connection((hub, port), timeout=timeout)
        data = payload.encode("utf-8")
        s.sendall(b"PUB " + subject.encode() + b" " + str(len(data)).encode() + b"\r\n" + data + b"\r\nPING\r\n")
        s.close()
        return True
    except Exception:
        return False


def run_actions(cmd, root):
    """Only whitelisted kinds execute. Anything else is queued for the owner."""
    out = []
    for a in (cmd.get("actions") or []):
        kind = str(a.get("kind") or "")
        if kind == "selfcheck":
            out.append({"kind": kind, "ok": True, "stats": stats()})
        elif kind == "noop":
            out.append({"kind": kind, "ok": True})
        elif kind == "sync":
            run(["git", "-C", root, "fetch", "--quiet", "origin", "main"], timeout=120)
            out.append({"kind": kind, "ok": True,
                        "origin_main": run(["git", "-C", root, "rev-parse", "--short", "origin/main"])})
        else:
            out.append({"kind": kind, "ok": False, "note": "not-whitelisted"})
    return out


def handle(cmd, node, root, hub="100.110.185.62", port=4222, push_ack=False):
    cid = str(cmd.get("id") or "")
    text = str(cmd.get("text") or "")
    lanes = cmd.get("lanes") or []
    if not cid:
        return None
    if lanes and node not in lanes and "all" not in lanes:
        return None
    low = text.lower()
    actions = cmd.get("actions") or []
    if not actions:
        if "自检" in text or "selfcheck" in low or "状态回执" in text or "noop" in low:
            actions = [{"kind": "selfcheck"}]
    results = run_actions({"actions": actions}, root) if actions else []
    ok = bool(results) and all(r.get("ok") for r in results)
    status = "done" if ok else ("received" if not results else "failed")
    ack = {
        "cmd_id": cid, "node": node, "host": socket.gethostname(),
        "status": status, "ts": ts_str(), "ts_utc_ms": int(now().timestamp() * 1000),
        "lanes": lanes, "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
        "actions": results,
        "head": run(["git", "-C", root, "rev-parse", "--short", "HEAD"]),
        "note": "" if results else "no-executor-for-this-command",
    }
    # Unified command plane: nodes never write the group repo (that is what diverged the
    # worktree and stopped order intake). Ack goes to NATS + a local, gitignored acks/ dir.
    ack_dir = os.path.join(root, "cph4", "fleet", "acks")
    os.makedirs(ack_dir, exist_ok=True)
    with open(os.path.join(ack_dir, "%s.%s.ack.json" % (cid, node)), "w", encoding="utf-8") as f:
        json.dump(ack, f, ensure_ascii=False, indent=1)
    nats_pub(hub, port, "fleet.ack", json.dumps(ack, ensure_ascii=False))
    if push_ack:
        cmd_dir = os.path.join(root, "cph4", "fleet", "cmd")
        os.makedirs(cmd_dir, exist_ok=True)
        p2 = os.path.join(cmd_dir, "%s.%s.ack.json" % (cid, node))
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(ack, f, ensure_ascii=False, indent=1)
        git_push(p2, root, "ack: %s %s" % (node, cid))
    print("ACK %s %s %s actions=%s" % (cid, node, status, len(results)))
    return ack


def git_show(root, path):
    try:
        p = subprocess.run(["git", "-C", root, "show", "origin/main:" + path],
                           capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=20)
        if p.returncode == 0:
            return p.stdout.decode("utf-8-sig", "replace")
    except Exception:
        pass
    return None


def list_cmd_names(root):
    names = []
    try:
        p = subprocess.run(["git", "-C", root, "ls-tree", "--name-only", "origin/main", "--", "cph4/fleet/cmd"],
                           capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=30)
        if p.returncode == 0:
            for line in p.stdout.decode("utf-8", "replace").splitlines():
                n = line.strip().split("/")[-1]
                if n.endswith(".json") and not n.endswith(".ack.json"):
                    names.append(n)
    except Exception:
        pass
    if not names:
        cmd_dir = os.path.join(root, "cph4", "fleet", "cmd")
        if os.path.isdir(cmd_dir):
            names = [n for n in sorted(os.listdir(cmd_dir))
                     if n.endswith(".json") and not n.endswith(".ack.json")]
    return names


def scan(root, node, seen, hub, port, push_ack=False):
    """Read the command plane straight from origin/main blobs.

    A dirty or diverged worktree can no longer block order intake - that failure mode
    stopped bm-b/bm-c for 11h on 2026-10-28.
    """
    run(["git", "-C", root, "fetch", "--quiet", "origin", "main"], timeout=120)
    n = 0
    for name in list_cmd_names(root):
        raw = git_show(root, "cph4/fleet/cmd/" + name)
        if raw is None:
            p = os.path.join(root, "cph4", "fleet", "cmd", name)
            if not os.path.exists(p):
                continue
            try:
                with open(p, encoding="utf-8-sig") as f:
                    raw = f.read()
            except Exception:
                continue
        try:
            cmd = json.loads(raw)
        except Exception:
            continue
        cid = str(cmd.get("id") or "")
        if not cid or cid in seen:
            continue
        if handle(cmd, node, root, hub, port, push_ack):
            seen.add(cid)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--hub", default="100.110.185.62")
    ap.add_argument("--port", type=int, default=4222)
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--wait", type=float, default=0)
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--push-ack", action="store_true",
                    help="legacy: also commit the ack into the repo (breaks the read-only node rule)")
    ap.add_argument("--no-scan", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    seen_path = os.path.join(root, "Tools", "nats", "data", "seen.%s.json" % a.node)
    seen = load_seen(seen_path)

    if not a.no_scan:
        scan(root, a.node, seen, a.hub, a.port, a.push_ack)
        save_seen(seen_path, seen)

    if a.once and a.wait <= 0:
        return 0

    if a.serve or a.wait > 0:
        deadline = time.time() + (a.wait if a.wait > 0 else 10 ** 9)
        while time.time() < deadline:
            try:
                sub = NatsSub(a.hub, a.port, timeout=5.0)
            except Exception:
                if a.serve:
                    time.sleep(3)
                    continue
                return 1
            while time.time() < deadline:
                data = sub.next(min(5.0, max(0.5, deadline - time.time())))
                if data is None:
                    if a.serve:
                        scan(root, a.node, seen, a.hub, a.port, a.push_ack)
                        save_seen(seen_path, seen)
                    continue
                try:
                    cmd = json.loads(data.decode("utf-8"))
                except Exception:
                    continue
                cid = str(cmd.get("id") or "")
                if cid and cid not in seen:
                    if handle(cmd, a.node, root, a.hub, a.port, a.push_ack):
                        seen.add(cid)
                        save_seen(seen_path, seen)
                if a.wait > 0:
                    return 0
            if not a.serve:
                return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())