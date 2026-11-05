#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""useful_load.py - 算力占用归因：占着 CPU/GPU 的进程到底有没有产出。

为什么（CEO：「要确认占用的算力都在干有用的」）：
  「进程活着」不等于「在干活」——之前实测过卡死进程照样报进度、心跳照样跳。
  这里换判据：占用资源的同时必须伴随**可增的产出**（写文件变大/变多，或子进程字节增长）。

判据：
  1) 采样窗口 T 秒，记录每个高占用进程的 CPU 时间增量；
  2) 同时用 lsof 找它写的文件，记录文件 size 增量；
  3) CPU 增量 > 2s 且 写字节增量 = 0 → 判 SPIN（占算力不出活）；
  4) 有写字节增量 → USEFUL，并给出「每 CPU 秒产出多少字节」。

用法：
  python3 Tools/fleet/useful_load.py [--seconds 20] [--cpu-min 5]
Exit: 0 无 SPIN；1 发现 SPIN；2 采样失败
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "useful-load.json")
# 系统/界面类进程不计（不是我们的作业）
IGNORE = ("WindowServer", "WebKit", "SkyLight", "Qianwen", "Stats", "Tuanjie",
          "DriverKit", "BCMWLAN", "IO80211", "bluetoothd", "sharingd", "rapportd",
          "Finder", "Dock", "loginwindow", "kernel_task", "coreaudiod", "syspolicyd",
          "opendirectoryd", "mds", "mdworker", "bird", "cloudd")


def snapshot(cpu_min):
    ps = subprocess.run(["ps", "-A", "-o", "pid=,pcpu=,time=,comm="],
                        capture_output=True, text=True).stdout
    rows = []
    for line in ps.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        pid, pcpu, ctime, comm = parts
        try:
            pcpu = float(pcpu)
        except ValueError:
            continue
        if pcpu < cpu_min:
            continue
        if any(k in comm for k in IGNORE):
            continue
        rows.append({"pid": int(pid), "pcpu": pcpu, "time": ctime, "comm": comm.strip()})
    return rows


def cpu_seconds(ctime):
    """ps 的 TIME 形如 1:23.45 或 12:34 → 秒"""
    try:
        if "." in ctime:
            m, s = ctime.split(":")
            return int(m) * 60 + float(s)
        parts = [int(x) for x in ctime.split(":")]
        sec = 0
        for p in parts:
            sec = sec * 60 + p
        return float(sec)
    except Exception:
        return 0.0


def has_net(pid):
    """有 ESTABLISHED 连接=正在收发网络数据（下载/推理请求），也算在干活。"""
    try:
        out = subprocess.run(["lsof", "-p", str(pid), "-i", "-n", "-P"],
                             capture_output=True, text=True, timeout=10).stdout
        return "ESTABLISHED" in out
    except Exception:
        return False


def written_bytes(pid):
    """该进程当前打开用于写的文件总大小；取不到返回 0。"""
    try:
        out = subprocess.run(["lsof", "-p", str(pid), "-F", "n"],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return 0, []
    total, files = 0, []
    for line in out.splitlines():
        if not line.startswith("n"):
            continue
        p = line[1:].strip()
        if not p.startswith("/"):
            continue
        try:
            if os.path.isfile(p):
                total += os.path.getsize(p)
                files.append(p)
        except OSError:
            pass
    return total, files[:5]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=20)
    ap.add_argument("--cpu-min", type=float, default=5.0)
    a = ap.parse_args(argv)

    first = snapshot(a.cpu_min)
    if not first:
        print("[useful] 当前没有 CPU>%.0f%% 的作业进程（空载）" % a.cpu_min)
    base = {}
    for r in first:
        b, fs = written_bytes(r["pid"])
        base[r["pid"]] = {"cpu0": cpu_seconds(r["time"]), "bytes0": b, "files": fs,
                          "pcpu": r["pcpu"], "comm": r["comm"]}
    t0 = time.time()
    time.sleep(a.seconds)
    second = {r["pid"]: r for r in snapshot(a.cpu_min)}

    rows = []
    for pid, b in base.items():
        r = second.get(pid)
        if not r:
            continue  # 采样期内退出的进程不参与判定
        cpu1 = cpu_seconds(r["time"])
        bytes1, _ = written_bytes(pid)
        dcpu = max(0.0, cpu1 - b["cpu0"])
        dbytes = max(0, bytes1 - b["bytes0"])
        # 进程可能在窗口内新建了文件：用文件数变化兜底
        if dcpu < 2:
            verdict = "IDLE"
        elif dbytes > 0:
            verdict = "USEFUL-FILE"
        elif has_net(pid):
            verdict = "USEFUL-NET"
        else:
            verdict = "SPIN"
        rows.append({
            "pid": pid, "comm": b["comm"], "pcpu": r["pcpu"],
            "cpu_s_delta": round(dcpu, 2),
            "bytes_delta": dbytes,
            "bytes_per_cpu_s": round(dbytes / dcpu, 1) if dcpu > 0 else None,
            "files": b["files"][:3],
            "verdict": verdict,
        })
    # 常驻模型空占检查：模型驻留内存但对应作业没在跑 = 占着内存不出活
    resident = []
    try:
        import urllib.request
        d = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5).read())
        jobs = subprocess.run(["pgrep", "-fl", "asset_caption|local_task|local_gen"],
                              capture_output=True, text=True).stdout.strip()
        for m in d.get("models", []):
            name = m.get("name", "")
            gb = round(m.get("size", 0) / 1e9, 2)
            idle = (("qwen3.5" in name or "mlx" in name) and "asset_caption" not in jobs)
            resident.append({"model": name, "gb": gb,
                             "verdict": "IDLE-RESIDENT" if idle else "IN-USE"})
    except Exception as e:
        resident.append({"error": str(e)[:80]})

    spin = [x for x in rows if x["verdict"] == "SPIN"]
    useful = [x for x in rows if x["verdict"].startswith("USEFUL")]
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "window_s": a.seconds,
           "cpu_min_pct": a.cpu_min, "rows": rows,
           "useful": len(useful), "spin": len(spin),
           "resident_models": resident,
           "idle_resident_gb": round(sum(r.get("gb", 0) for r in resident
                                         if r.get("verdict") == "IDLE-RESIDENT"), 2),
           "verdict": "SPIN" if spin else "CLEAN",
           "note": "SPIN=占着 CPU 但窗口内没有写出任何字节；系统/界面进程已排除"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    print("[useful] 窗口 %ds，高占用进程 %d 个：有用 %d / 空转 %d"
          % (a.seconds, len(rows), len(useful), len(spin)))
    for x in rows:
        print("  %-6s %-28s cpu+%.1fs 写出 %d B（%.0f B/CPU秒）"
              % (x["verdict"], x["comm"][-28:], x["cpu_s_delta"], x["bytes_delta"],
                 x["bytes_per_cpu_s"] or 0))
    for r in resident:
        if r.get("verdict") == "IDLE-RESIDENT":
            print("  IDLE-RESIDENT %s %.2fGB（没在跑对应作业，白占内存）"
                  % (r["model"], r["gb"]))
    return 1 if spin else 0


if __name__ == "__main__":
    sys.exit(main())