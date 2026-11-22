#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bmc_orchestrator.py - bm-c 本机总控排号器（CEO 令 2026-11-22）

「本机的各种任务要做好排序，不要互相打架抢资源，要有本机的总控智能体去负责排号，
  科学利用本地算力。」

为什么要有（2026-11-22 实测）：
  · 本机同时跑两个 ComfyUI（8188 主渲染 / 8189 PuLID 工厂），共享一张 16GB 卡；
  · GPU 15565/16384MB、util 100%、RAM free 2.7GB；
  · BmcIdleGuard 空闲 10 分钟就直接 Popen 银行里的活，不看资源、不看别人在跑什么；
  · 共享的 gpu_lease.py 用 fcntl（Unix 专有），在 Windows 上 import 即失败
    → 本机实际上一直没有租约，全靠"谁先起谁占"。

本文件补的就是这一层：唯一裁决者。
  · 资源账本：GPU util/显存、RAM、CPU、两个 ComfyUI 的队列状态
  · 租约：lane + 名额 + VRAM 需求 + TTL + pid 存活校验（Windows 原生，无 fcntl）
  · 排号：优先级队列（P0 CEO/主控 → P1 续跑 → P2 备货 → P3 维护）
  · 回收：空闲的 ComfyUI 实例 /free 归还显存；RAM 见底时列出可回收进程
  · 尊重让路：machine-state.flag=paused 时零动作

用法
  python Tools/fleet/bmc_orchestrator.py --tick        # 每分钟（计划任务调用）
  python Tools/fleet/bmc_orchestrator.py --status      # 人读一屏
  python Tools/fleet/bmc_orchestrator.py --plan        # 当前排号结果
  python Tools/fleet/bmc_orchestrator.py --acquire <name> --lane gpu-exclusive \
         [--need-mb 12000] [--ttl 3600] [--prio 2] [--port 8188] [--note ...]
  python Tools/fleet/bmc_orchestrator.py --release <name>
  python Tools/fleet/bmc_orchestrator.py --try <name> --lane ...   # 只有拿到 rc=0

  acquire 拿不到时 rc=3（调用方让路，不排队硬闯）。
"""
from __future__ import annotations

import argparse
import ctypes
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
STATE_DIR = os.path.join(REPO, "cph4", "fleet", "state")
STATE = os.path.join(STATE_DIR, "bmc-orchestrator.json")
LOCK = os.path.join(STATE_DIR, "bmc-orchestrator.lock")
LOG = os.path.join(STATE_DIR, "bmc-orchestrator.log")
PAUSE_FLAG = r"K:\Fluxgroup\.codely-cli\machine-state.flag"
BANKS = [
    ("gpu", os.path.join(REPO, "cph4", "fleet", "work-bank", "bm-c-gpu-bank.json")),
    ("cpu", os.path.join(REPO, "cph4", "fleet", "work-bank", "bm-c-cpu-bank.json")),
]
LANE = os.path.join(REPO, "cph4", "fleet", "lanes", "bm-c.json")
NO_WINDOW = 0x08000000

# lane 容量与语义
LANES = {
    "gpu-exclusive": {"slots": 1, "gpu": True, "exclusive": True},
    "gpu-shared": {"slots": 2, "gpu": True, "exclusive": False},
    "cpu-heavy": {"slots": 2, "gpu": False, "exclusive": False},
    "cpu-light": {"slots": 4, "gpu": False, "exclusive": False},
}
RAM_FLOOR_GB = 3.0          # 起新 GPU 活的最低可用内存
DEFAULT_GPU_NEED_MB = 10000  # 银行 gpu 活没写 need_mb 时的保守估值
GPU_UTIL_BUSY = 15          # >= 视为在干活
COMFY_IDLE_FREE_S = 300     # 实例连续空闲 5 分钟才归还显存


# ---------------------------------------------------------------- 基础工具
def log(msg):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise
    except Exception:
        return default


def read_json_soft(path, default):
    try:
        return read_json(path, default)
    except Exception:
        return default


def prio_num(v, fallback=2):
    """'P0'/'P1'/0 都归一成 int。"""
    if isinstance(v, int):
        return v
    s = str(v or "").strip().upper()
    if s.startswith("P") and s[1:].isdigit():
        return int(s[1:])
    if s.isdigit():
        return int(s)
    return fallback


def write_json(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def run(cmd, timeout=20):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                           timeout=timeout, creationflags=NO_WINDOW)
        return p.stdout.strip()
    except Exception:
        return ""


def pid_alive(pid):
    """Windows 原生存活判定：OpenProcess + GetExitCodeProcess(STILL_ACTIVE)。"""
    try:
        pid = int(pid)
    except Exception:
        return False
    if pid <= 0:
        return False
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return False
    code = ctypes.c_ulong()
    ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(h)
    return bool(ok) and code.value == STILL_ACTIVE


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def ram():
    s = MEMORYSTATUSEX()
    s.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return round(s.ullAvailPhys / 1024 ** 3, 2), int(s.dwMemoryLoad)


def gpu():
    out = run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
               "--format=csv,noheader,nounits"], timeout=20)
    try:
        u, used, total = [int(x.strip()) for x in out.splitlines()[0].split(",")]
        return u, used, total
    except Exception:
        return -1, -1, -1


def comfy(port, timeout=8):
    """探活 + 队列。失败不抛。"""
    try:
        q = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/queue" % port, timeout=timeout).read())
        running = len(q.get("queue_running") or [])
        pending = len(q.get("queue_pending") or [])
    except Exception:
        return {"up": False, "running": 0, "pending": 0}
    return {"up": True, "running": running, "pending": pending, "busy": running + pending > 0}


def comfy_free(port, timeout=60):
    """卸载模型归还显存（不杀进程，服务保留）。"""
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:%d/free" % port,
            data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=timeout).read()
        return True
    except Exception:
        return False


def paused():
    try:
        with open(PAUSE_FLAG, encoding="utf-8", errors="replace") as f:
            return "paused" in f.read()
    except Exception:
        return False


def empty_state():
    return {"ts": None, "node": "bm-c", "kind": "bmc-orchestrator",
            "paused": False, "resources": {}, "comfy": {},
            "holders": [], "queue": [], "anomalies": [], "actions": [],
            "idle_since": {}}


# ---------------------------------------------------------------- 文件锁
class Guard:
    """跨平台互斥：O_CREAT|O_EXCL 原子建锁 + pid 校验 + TTL 过期回收。"""

    def __init__(self, path, ttl=90):
        self.path, self.ttl, self.fh = path, ttl, None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        deadline = time.time() + 10
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(fd, ("%d|%f" % (os.getpid(), time.time())).encode())
                self.fh = fd
                return self
            except FileExistsError:
                stale = True
                try:
                    with open(self.path) as f:
                        pid, ts = (f.read().split("|") + ["0", "0"])[:2]
                    stale = (not pid_alive(pid)) or (time.time() - float(ts) > self.ttl)
                except Exception:
                    stale = True
                if stale:
                    try:
                        os.remove(self.path)
                    except Exception:
                        pass
                    continue
                if time.time() >= deadline:
                    raise TimeoutError("lock busy: %s" % self.path)
                time.sleep(0.2)

    def __exit__(self, *a):
        try:
            if self.fh is not None:
                os.close(self.fh)
        except Exception:
            pass
        try:
            os.remove(self.path)
        except Exception:
            pass
        return False


# ---------------------------------------------------------------- 账本
def load():
    return read_json_soft(STATE, empty_state())


def save(doc):
    doc["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    write_json(STATE, doc)


def reap(doc, now):
    """回收死掉/超期的持证者。"""
    keep, dropped = [], []
    for h in doc.get("holders", []):
        alive = pid_alive(h.get("pid"))
        expired = now > float(h.get("expires") or 0)
        if alive and not expired:
            keep.append(h)
        else:
            dropped.append("%s(%s)" % (h.get("name"),
                                       "dead-pid" if not alive else "ttl"))
    doc["holders"] = keep
    return dropped


def lane_used(doc, lane):
    return [h for h in doc.get("holders", []) if h.get("lane") == lane]


def vram_reserved(doc):
    return sum(int(h.get("need_mb") or 0) for h in doc.get("holders", [])
               if h.get("lane", "").startswith("gpu"))


def can_acquire(doc, name, lane, need_mb, res):
    """返回 (ok, why)。"""
    if lane not in LANES:
        return False, "unknown-lane:%s" % lane
    for h in doc.get("holders", []):
        if h.get("name") == name:
            return True, "reentrant"
    if doc.get("paused"):
        return False, "paused(CEO让路窗)"
    cfg = LANES[lane]
    holders = doc.get("holders", [])
    if cfg["gpu"] and not need_mb:
        need_mb = DEFAULT_GPU_NEED_MB
    if cfg["gpu"]:
        excl = [h for h in holders if h.get("lane") == "gpu-exclusive"]
        if excl:
            return False, "gpu 被 %s 独占" % excl[0].get("name")
        if cfg["exclusive"] and [h for h in holders if h.get("lane", "").startswith("gpu")]:
            return False, "gpu 已有 %s 在用" % next(
                h.get("name") for h in holders if h.get("lane", "").startswith("gpu"))
        if len(lane_used(doc, lane)) >= cfg["slots"]:
            return False, "lane %s 满(%d)" % (lane, cfg["slots"])
        free_mb = res.get("vram_total_mb", 0) - res.get("vram_used_mb", 0)
        if need_mb and free_mb >= 0 and (free_mb - vram_reserved(doc)) < int(need_mb):
            return False, "显存不足 need=%dMB free=%dMB" % (need_mb, free_mb - vram_reserved(doc))
        if res.get("ram_free_gb", 99) < RAM_FLOOR_GB:
            return False, "内存见底 free=%.1fGB < %.1fGB" % (res.get("ram_free_gb", 0), RAM_FLOOR_GB)
    else:
        if len(lane_used(doc, lane)) >= cfg["slots"]:
            return False, "lane %s 满(%d)" % (lane, cfg["slots"])
    return True, "ok"


def snapshot(doc):
    u, used, total = gpu()
    free_gb, load = ram()
    doc["resources"] = {"gpu_util": u, "vram_used_mb": used, "vram_total_mb": total,
                        "vram_free_mb": (total - used) if total > 0 else -1,
                        "ram_free_gb": free_gb, "ram_load_pct": load}
    doc["comfy"] = {"8188": comfy(8188), "8189": comfy(8189)}
    return doc


# ---------------------------------------------------------------- 排号
def candidates(doc, anomalies=None):
    """候选活：GPU/CPU 两个银行 pending + 主控 lane 卡。只读，不点火。"""
    out = []
    for kind, path in BANKS:
        try:
            bank = read_json(path, {"jobs": []})
        except FileNotFoundError:
            if anomalies is not None:
                anomalies.append("bank-missing:%s" % os.path.basename(path))
            continue
        for j in bank.get("jobs", []):
            if j.get("status") != "pending" or not j.get("cmd"):
                continue
            needs = str(j.get("needs") or kind).lower()
            lane = "gpu-exclusive" if needs.startswith("gpu") else "cpu-heavy"
            out.append({"src": kind + "-bank", "name": j.get("id"),
                        "prio": prio_num(j.get("prio")), "lane": lane,
                        "need_mb": int(j.get("need_mb") or 0)})
    lane_doc = read_json_soft(LANE, {"jobs": []})
    for j in lane_doc.get("jobs", []):
        if j.get("state") not in (None, "READY", "OPEN", "pending"):
            continue
        out.append({"src": "lane", "name": j.get("id"), "prio": prio_num(j.get("prio"), 0),
                    "lane": j.get("lane") or "cpu-light",
                    "need_mb": int(j.get("need_mb") or 0)})
    out.sort(key=lambda x: (x["prio"], x["src"] != "lane"))
    return out


def plan(doc):
    """按当前资源给出可跑的下一个活（不改变账本）。"""
    res = doc.get("resources", {})
    picked = []
    for c in candidates(doc, doc.get("anomalies")):
        ok, why = can_acquire(doc, c["name"], c["lane"], c["need_mb"], res)
        if ok:
            picked.append(dict(c, decided="RUN"))
            break
    return picked


# ---------------------------------------------------------------- 子命令
def cmd_tick(args):
    with Guard(LOCK):
        doc = load()
        now = time.time()
        doc["paused"] = paused()
        snapshot(doc)
        doc["actions"] = []
        doc["anomalies"] = []

        if doc["paused"]:
            doc["idle_since"] = {}
            save(doc)
            log("paused window -> zero action")
            return 0

        dropped = reap(doc, now)
        if dropped:
            doc["actions"].append("released dead/expired: " + ",".join(dropped))

        res = doc["resources"]

        # 野占用：GPU 忙但没有本机持证者
        gpu_holders = [h for h in doc["holders"] if h.get("lane", "").startswith("gpu")]
        comfy_busy = any(v.get("busy") for v in doc["comfy"].values())
        if res["gpu_util"] >= GPU_UTIL_BUSY and not gpu_holders and not comfy_busy:
            doc["anomalies"].append("unknown-gpu-holder: util=%d%% 但无持证者" % res["gpu_util"])

        # 空闲 ComfyUI 实例归还显存（不杀进程）
        held_ports = {int(h["port"]) for h in doc["holders"] if h.get("port")}
        idle = doc.setdefault("idle_since", {})
        for port_s, info in doc["comfy"].items():
            port = int(port_s)
            if not info.get("up"):
                idle.pop(port_s, None)
                continue
            if info.get("busy") or port in held_ports:
                idle.pop(port_s, None)
                continue
            idle.setdefault(port_s, now)
            if now - float(idle[port_s]) >= COMFY_IDLE_FREE_S:
                if comfy_free(port):
                    doc["actions"].append("free-vram: %d 空闲 %.0fs 已卸载模型"
                                          % (port, now - float(idle[port_s])))
                    idle[port_s] = now
                else:
                    doc["anomalies"].append("free-vram-failed:%d" % port)

        # RAM 见底：登记可回收对象（不擅自杀，交由 --reclaim 或人工）
        if res["ram_free_gb"] < RAM_FLOOR_GB:
            doc["anomalies"].append("ram-low: free=%.1fGB" % res["ram_free_gb"])

        doc["plan"] = plan(doc)
        save(doc)
        line = ("tick gpu=%d%% vram=%d/%dMB ram=%.1fGB holders=%d plan=%s actions=%s"
                % (res["gpu_util"], res["vram_used_mb"], res["vram_total_mb"],
                   res["ram_free_gb"], len(doc["holders"]),
                   (doc["plan"][0]["name"] if doc["plan"] else "-"),
                   ";".join(doc["actions"]) or "-"))
        log(line)
        if not args.quiet:
            print(line)
            for a in doc["anomalies"]:
                print("  !", a)
        return 0


def cmd_status(args):
    doc = snapshot(load())
    res = doc.get("resources", {})
    print("bm-c orchestrator @ %s  paused=%s" % (doc.get("ts"), doc.get("paused")))
    print("  GPU   : util=%d%%  vram=%d/%dMB  free=%dMB"
          % (res.get("gpu_util", -1), res.get("vram_used_mb", -1),
             res.get("vram_total_mb", -1), res.get("vram_free_mb", -1)))
    print("  RAM   : free=%.1fGB  load=%d%%" % (res.get("ram_free_gb", -1), res.get("ram_load_pct", -1)))
    for port, i in (doc.get("comfy") or {}).items():
        print("  Comfy : %s up=%s busy=%s running=%s pending=%s"
              % (port, i.get("up"), i.get("busy"), i.get("running"), i.get("pending")))
    print("  Holders:")
    for h in doc.get("holders", []):
        age = int(time.time() - float(h.get("since") or time.time()))
        print("    %-22s %-14s pid=%s age=%ds ttl_left=%ds port=%s"
              % (h.get("name"), h.get("lane"), h.get("pid"), age,
                 int(float(h.get("expires") or 0) - time.time()), h.get("port") or "-"))
    if not doc.get("holders"):
        print("    (none)")
    q = doc.get("queue") or []
    print("  Queue : %d" % len(q))
    for x in q[:8]:
        print("    P%s %-30s %s" % (x.get("prio"), x.get("name"), x.get("lane")))
    for a in doc.get("anomalies", []):
        print("  ! " + a)
    return 0


def cmd_plan(args):
    doc = snapshot(load())
    doc.setdefault("anomalies", [])
    cands = candidates(doc, doc["anomalies"])
    res = doc.get("resources", {})
    print("candidates=%d  gpu=%d%% vram_free=%dMB ram=%.1fGB holders=%d"
          % (len(cands), res.get("gpu_util", -1), res.get("vram_free_mb", -1),
             res.get("ram_free_gb", -1), len(doc.get("holders", []))))
    # 串行模拟：GPU 池只放一个；CPU 池按各自名额放——不互相挡
    sim = {"paused": doc.get("paused", False),
           "holders": [dict(h) for h in doc.get("holders", [])]}
    first = True
    for c in cands[:14]:
        ok, why = can_acquire(sim, c["name"], c["lane"], c["need_mb"], res)
        tag = "RUN"
        if ok:
            if first:
                tag, first = "NEXT", False
            need = c["need_mb"] or (DEFAULT_GPU_NEED_MB if LANES[c["lane"]]["gpu"] else 0)
            sim["holders"].append({"name": c["name"], "lane": c["lane"], "need_mb": need})
        else:
            tag = "WAIT"
        print("  %-4s P%s %-30s %-14s need=%sMB  %s"
              % (tag, c["prio"], c["name"], c["lane"], c["need_mb"], why))
    for a in doc["anomalies"]:
        print("  ! " + a)
    return 0


def cmd_acquire(args, quiet_ok=False):
    name = args.acquire
    with Guard(LOCK):
        doc = load()
        doc["paused"] = paused()
        snapshot(doc)
        now = time.time()
        reap(doc, now)
        ok, why = can_acquire(doc, name, args.lane, args.need_mb, doc["resources"])
        if ok:
            holder = next((h for h in doc.get("holders", []) if h.get("name") == name), None)
            if holder is not None:
                # 重入=续租/换绑 pid（点火器先占位，Popen 拿到真 pid 后回填）
                if args.pid:
                    holder["pid"] = args.pid
                holder["expires"] = now + args.ttl
                if args.port:
                    holder["port"] = args.port
                doc["actions"] = ["renew:%s" % name]
            else:
                doc["holders"].append({
                    "name": name, "lane": args.lane,
                    "pid": args.pid or os.getpid(),
                    "since": now, "expires": now + args.ttl,
                    "need_mb": args.need_mb, "prio": prio_num(args.prio),
                    "port": args.port, "note": args.note,
                })
                doc["actions"] = ["acquire:%s(%s)" % (name, args.lane)]
        save(doc)
    print(("GRANT " if ok else "YIELD ") + name + " :: " + why)
    log(("acquire-ok " if ok else "acquire-denied ") + name + " :: " + why)
    return 0 if ok else 3


def cmd_release(args):
    name = args.release
    with Guard(LOCK):
        doc = load()
        before = len(doc.get("holders", []))
        doc["holders"] = [h for h in doc.get("holders", []) if h.get("name") != name]
        doc["actions"] = ["release:%s" % name]
        save(doc)
    print("RELEASED %s (holders %d -> %d)" % (name, before, len(doc.get("holders", []))))
    return 0


def cmd_reclaim(args):
    """按需回收：停 ollama serve（本机 LLM 已退役）等非生产占用。"""
    acted = []
    if args.ollama:
        if pid_alive_ollama():
            run(["taskkill", "/F", "/IM", "ollama.exe"], timeout=20)
            run(["taskkill", "/F", "/IM", "llama-server.exe"], timeout=20)
            acted.append("killed ollama family")
    print("RECLAIM " + (",".join(acted) if acted else "nothing"))
    return 0


def pid_alive_ollama():
    return "ollama.exe" in run(["tasklist", "/FI", "IMAGENAME eq ollama.exe"], timeout=15)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--tick", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--plan", action="store_true")
    g.add_argument("--acquire", metavar="NAME")
    g.add_argument("--release", metavar="NAME")
    g.add_argument("--reclaim", action="store_true")
    ap.add_argument("--lane", default="gpu-exclusive", choices=sorted(LANES))
    ap.add_argument("--need-mb", type=int, default=0)
    ap.add_argument("--ttl", type=int, default=3600)
    ap.add_argument("--prio", default="P2", help="P0..P4 或数字")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--pid", type=int, default=0,
                    help="持证进程 pid（默认=本进程；点火器可回填子进程 pid）")
    ap.add_argument("--note", default="")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--ollama", action="store_true")
    a = ap.parse_args()

    if a.tick:
        return cmd_tick(a)
    if a.status:
        return cmd_status(a)
    if a.plan:
        return cmd_plan(a)
    if a.acquire:
        return cmd_acquire(a)
    if a.release:
        return cmd_release(a)
    if a.reclaim:
        return cmd_reclaim(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
