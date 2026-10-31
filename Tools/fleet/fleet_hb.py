#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_hb.py - cross-platform fleet heartbeat + clock calibration (stdlib only).

Why: the Windows PowerShell heartbeat cannot run on macOS, and the Mac is becoming the
group master-control node. This client speaks the NATS wire protocol directly, measures
its clock offset against the hub's clock.ask responder, and publishes the same v2 schema
(ts_utc_ms / seq / clock_offset_ms) to FLEET_STATE and hb.<node>.

Usage:
  python3 fleet_hb.py --node bm-m [--hub 100.110.185.62] [--root PATH]
Exit 0 on success, 1 if the bus is unreachable.
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Nats:
    def __init__(self, host, port=4222, timeout=5.0):
        self.sock = socket.create_connection((host, port), timeout)
        self.sock.settimeout(timeout)
        self.buf = b""
        self._read_line()  # INFO {...}
        self._send(b'CONNECT {"verbose":false,"pedantic":false}\r\n')

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

    def _read_crlf(self):
        while len(self.buf) < 2:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("nats closed")
            self.buf += chunk
        self.buf = self.buf[2:]

    def publish(self, subject, payload, reply=None):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        if reply:
            head = "PUB %s %s %d\r\n" % (subject, reply, len(payload))
        else:
            head = "PUB %s %d\r\n" % (subject, len(payload))
        self._send(head.encode() + payload + b"\r\n")

    def subscribe(self, subject, sid="1"):
        self._send(("SUB %s %s\r\n" % (subject, sid)).encode())

    def request(self, subject, payload, timeout=2.0):
        inbox = "_INBOX." + os.urandom(8).hex()
        self.subscribe(inbox, "9")
        self.publish(subject, payload, reply=inbox)
        old = self.sock.gettimeout()
        self.sock.settimeout(timeout)
        try:
            while True:
                line = self._read_line()
                if line == "PING":
                    self._send(b"PONG\r\n")
                    continue
                if line.startswith("MSG "):
                    parts = line.split()
                    # MSG <subject> <sid> [reply] <bytes>
                    n = int(parts[-1])
                    data = self._read_exact(n)
                    self._read_crlf()
                    return data
                # ignore +OK / other info
        finally:
            self.sock.settimeout(old)


def probe_offset(hub, port, samples=5):
    vals = []
    # One connection per sample: a reused connection drifts out of sync on the
    # trailing PING of the previous reply (measured: request 2+ times out).
    for _ in range(samples):
        try:
            c = Nats(hub, port, timeout=3.0)
        except Exception:
            continue
        try:
            t1 = time.time_ns()
            data = c.request("clock.ask", "x", timeout=2.0)
            t4 = time.time_ns()
            txt = data.decode("ascii", "ignore").strip()
            if not txt.isdigit():
                continue
            hub_ticks = int(txt)
            # .NET ticks are 100ns since 0001-01-01; Python ns since 1970.
            hub_ns = (hub_ticks - 621355968000000000) * 100
            vals.append(((hub_ns - (t1 + t4) / 2.0) / 1e6, (t4 - t1) / 1e6))
        except Exception:
            pass
        finally:
            try:
                c.sock.close()
            except Exception:
                pass
    if not vals:
        return None
    vals.sort()
    off, rtt = vals[len(vals) // 2]
    return {"offset_ms": round(off, 1), "rtt_ms": round(rtt, 1),
            "precision_ms": round(rtt / 2.0, 1), "samples": len(vals)}


def host_stats():
    stats = {"load1": None, "ram_free_gb": None, "disk_free_gb": None,
             "gpu_util_pct": None, "vram_used_mb": None, "vram_total_mb": None}
    try:
        stats["load1"] = round(os.getloadavg()[0], 2)
    except Exception:
        pass
    try:
        stats["disk_free_gb"] = round(shutil.disk_usage("/").free / 1e9, 1)
    except Exception:
        pass
    try:
        if sys.platform == "darwin":
            total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip())
            vm = subprocess.check_output(["vm_stat"]).decode()
            page = 4096
            free_pages = 0
            # macOS "Pages free" alone is not usable memory; reclaimable pages sit in
            # inactive/speculative/purgeable. Counting only free+inactive understated the
            # box (2026-10-30: reported 4.3GB while 23GB was actually available).
            for line in vm.splitlines():
                if "page size of" in line:
                    page = int(line.split("page size of")[1].split()[0])
                if any(line.startswith(k) for k in (
                        "Pages free", "Pages inactive", "Pages speculative", "Pages purgeable")):
                    free_pages += int(line.split(":")[1].strip().rstrip("."))
            stats["ram_free_gb"] = round(free_pages * page / 1e9, 1)
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"], stderr=subprocess.DEVNULL).decode()
        parts = [x.strip() for x in out.splitlines()[0].split(",")]
        stats["gpu_util_pct"] = int(parts[0])
        stats["vram_used_mb"] = int(parts[1])
        stats["vram_total_mb"] = int(parts[2])
    except Exception:
        pass
    return stats


def self_bootstrap(node):
    """The heartbeat task is the only thing proven alive on every node, so it carries the
    bootstrap: if cph4/fleet/nodes/<node>/AGENT-REQUIRED exists and no agent process is
    running, start one detached. Because this file itself is refreshed by `git pull`, a node
    that pulls once becomes self-deploying without SSH or a human at the keyboard.
    """
    import subprocess as sp
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not os.path.exists(os.path.join(root, "cph4", "fleet", "nodes", node, "AGENT-REQUIRED")):
        return
    try:
        r = sp.run(["pgrep", "-f", "fleet/agent.py --node %s" % node], capture_output=True)
        alive = r.returncode == 0
    except Exception:
        alive = False
    if alive:
        return
    try:
        kw = {}
        if os.name == "posix":
            kw["start_new_session"] = True
        else:
            kw["creationflags"] = 0x00000008  # DETACHED_PROCESS
        sp.Popen([sys.executable, os.path.join(root, "Tools", "fleet", "agent.py"),
                  "--node", node, "--loop", "60"], cwd=root, **kw)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--hub", default="100.110.185.62")
    ap.add_argument("--port", type=int, default=4222)
    ap.add_argument("--root", default=ROOT_DEFAULT)
    a = ap.parse_args()

    data_dir = os.path.join(a.root, "Tools", "nats", "data")
    os.makedirs(data_dir, exist_ok=True)
    seq_f = os.path.join(data_dir, "seq.%s.txt" % a.node)
    try:
        with open(seq_f) as f:
            seq = int(f.read().strip() or "0")
    except Exception:
        seq = 0
    seq += 1
    with open(seq_f, "w") as f:
        f.write(str(seq))

    clk = probe_offset(a.hub, a.port) or {}
    now = datetime.now(timezone.utc)
    state = {
        "node": a.node,
        "host": socket.gethostname(),
        "ts": now.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "ts_utc_ms": int(now.timestamp() * 1000),
        "seq": seq,
        "clock_offset_ms": clk.get("offset_ms"),
        "clock_rtt_ms": clk.get("precision_ms"),
    }
    state.update(host_stats())
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))

    try:
        c = Nats(a.hub, a.port, timeout=5.0)
        c.publish("$KV.FLEET_STATE.state.%s" % a.node, payload)
        c.publish("hb.%s" % a.node, payload)
        time.sleep(0.2)
        c.sock.close()
    except Exception as e:
        print("HB-FAIL %s" % e)
        return 1
    print("HB %s seq=%d offset=%sms" % (a.node, seq, state["clock_offset_ms"]))
    try:
        self_bootstrap(args.node)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())