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
    # 先做一次短超时可达性探针（2026-11-07 实测）：hub 不通时 5 个样本 × 3s 连接超时
    # 会让本阶段每轮白等 ~20s 再 HB-FAIL——心跳是最高频阶段，不该为一条死链付这个钱。
    # 不通就直接返回空，由调用方记 DEGRADED，一次 1.5s 结束。
    try:
        _probe = socket.create_connection((hub, port), timeout=1.5)
        _probe.close()
    except Exception:
        return vals
    # 先做一次短超时可达性探针（2026-11-07 实测）：hub 不通时 5 个样本 × 3s 连接超时
    # 会让本阶段每轮白等 ~20s 再 HB-FAIL——心跳是最高频阶段，不该为一条死链付这个钱。
    # 不通就直接返回空，由调用方记 DEGRADED，一次 1.5s 结束。
    try:
        _probe = socket.create_connection((hub, port), timeout=1.5)
        _probe.close()
    except Exception:
        return vals
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


def _win_stats(stats, node, root):
    """RAM and CPU for Windows nodes, without psutil and without spawning a shell.

    2026-11-01 measured: state.bm-c reached the bus with ram_free_gb=null and no cpu field,
    because the RAM branch below is macOS-only and Windows has no os.getloadavg(). The
    master then scored this lane as "ram-unknown" (master_agent.lane_capacity), i.e. it
    could never gate or aim RAM-heavy work at the box it actually has to fit.
    CPU comes from GetSystemTimes deltas (Windows has no instantaneous counter); the
    previous sample is kept next to the heartbeat sequence file.
    """
    import ctypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    try:
        m = MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            stats["ram_free_gb"] = round(m.ullAvailPhys / 1e9, 1)
    except Exception:
        pass

    class FILETIME(ctypes.Structure):
        _fields_ = [("lo", ctypes.c_uint), ("hi", ctypes.c_uint)]

    def _ticks(ft):
        return (ft.hi << 32) + ft.lo

    try:
        idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
        get = ctypes.windll.kernel32.GetSystemTimes
        if not get(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return
        cur = {"idle": _ticks(idle), "total": _ticks(kernel) + _ticks(user),
               "ts": time.time()}
        path = os.path.join(root, "Tools", "nats", "data", "cpusample.%s.json" % node)
        prev = None
        try:
            with open(path, encoding="utf-8") as f:
                prev = json.load(f)
        except Exception:
            pass
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cur, f)
        except Exception:
            pass
        if prev and cur["total"] > prev.get("total", 0):
            d_total = cur["total"] - prev["total"]
            d_idle = cur["idle"] - prev.get("idle", 0)
            stats["cpu_load_pct"] = int(round(100.0 * (d_total - d_idle) / d_total))
    except Exception:
        pass


def host_stats(node=None, root=None):
    stats = {"load1": None, "ram_free_gb": None, "disk_free_gb": None,
             "cpu_load_pct": None,
             "gpu_util_pct": None, "vram_used_mb": None, "vram_total_mb": None}
    try:
        stats["load1"] = round(os.getloadavg()[0], 2)
        # 2026-11-02: macOS 之前只有 load1、没有占用率，主控因此对 CPU 完全盲。
        # 2026-11-06 修正：load1 含「不可中断 I/O 等待」，一个狂扫磁盘的系统进程就能把它顶到
        # ≥核数 → 占用率恒 100% → 主控 CPU-SATURATED 闸停掉本机全部 CPU 活（实测 load 6.98/10
        # 核=70% 而 ps 口径仅 13%，bm-m 车道整天 LANE-IDLE）。改用具名指标 cpu_busy_pct
        # （实测忙占比），load1 原样保留供诊断；cpu_load_pct 仍写忙占比以免下游口径分裂。
        cores = os.cpu_count() or 1
        stats["cpu_cores"] = cores
        busy = None
        if os.name != "nt":
            try:
                out = subprocess.run(["ps", "-Ao", "pcpu="], capture_output=True,
                                     text=True, timeout=10).stdout
                tot = 0.0
                for x in out.split():
                    try:
                        tot += float(x)
                    except Exception:
                        pass
                busy = int(round(min(100.0, tot / cores)))
            except Exception:
                busy = None
        stats["cpu_busy_pct"] = busy
        stats["cpu_load_pct"] = (busy if busy is not None
                                 else int(round(100.0 * min(stats["load1"], cores) / cores)))
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
    if os.name == "nt" and node and root:
        _win_stats(stats, node, root)
    return stats


def self_bootstrap(node):
    """Bootstrap carrier = the heartbeat task (the only thing proven alive on every node).

    Safety (2026-10-31): the first version used `pgrep`, which does not exist on Windows, so
    "not running" was always true and every heartbeat respawned an agent. Replaced by a
    cross-platform lock file: create-exclusive, stale after 10 minutes, and a marker gate.
    Absent the marker nothing ever spawns.
    """
    import subprocess as sp
    import time as _t
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not os.path.exists(os.path.join(root, "cph4", "fleet", "nodes", node, "AGENT-REQUIRED")):
        return
    lock = os.path.join(root, ".codely-cli", "tmp", "agent-%s.lock" % node)
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    try:
        if os.path.exists(lock) and _t.time() - os.path.getmtime(lock) < 600:
            return                      # a live agent owns this node
        with open(lock, "w") as f:
            f.write("%d %d" % (os.getpid(), int(_t.time())))
    except Exception:
        return
    try:
        kw = {"start_new_session": True} if os.name == "posix" else {"creationflags": 0x00000008}
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
    state.update(host_stats(a.node, a.root))
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
        self_bootstrap(a.node)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())