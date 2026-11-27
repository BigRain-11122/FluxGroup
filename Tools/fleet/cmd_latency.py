#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cmd_latency.py - 命令下发延迟的实测与预算（CEO 2026-11-11「命令务必非常及时顺畅」）。

命令面只有两条真实通道，必须分清楚哪条是数据、哪条是信号：
  A git 通道（数据）：主控 commit+push → 各机 pull。全程可靠，但延迟由「脉节奏」决定。
  B poke 通道（信号）：POST /poke 唤醒目标机的启用任务，让它立刻拉。只传信号不传数据。
    契约（2026-11-08 实锚）：{"reason":"<含 enable-tasks>","tasks":["<白名单任务>"]}
    发错字段会返回 accepted:true 但 wakes 为空——看着叫过了，实际一次没唤醒。

本工具做三件事：
  1) 量 git 往返（push/fetch 各跑一次 dry-run，不产生提交）
  2) 用本地 stub 验 poke 载荷是否合规 + 量 RTT（不碰真机）
  3) 按实测值算两条通道的端到端延迟，与预算对比，并把"当前谁能收"列出来

预算（写死在 BUDGET，改口径要改这里）：
  P0 紧急（暂停/取消）≤ 15s ；常规卡 ≤ 60s ；poke 单跳 ≤ 3s

用法：
  python3 Tools/fleet/cmd_latency.py             # 全量测
  python3 Tools/fleet/cmd_latency.py --json
  python3 Tools/fleet/cmd_latency.py --self-test
Exit: 0 预算内且有节点可收；1 超预算或无人可收
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
NODES = os.path.join(ROOT, "Tools", "fleet-nodes.json")
OUT = os.path.join(FLEET, "state", "cmd-latency.json")

BUDGET = {"poke_s": 3.0, "p0_total_s": 15.0, "tick_total_s": 60.0}


def load(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def tick_s():
    """脉节奏（决定常规卡最快多久被拉一次）。"""
    c = load(os.path.join(FLEET, "COMMAND-CADENCE-v3.json"), {}) or {}
    return float(c.get("base_tick_s") or 45)


def time_cmd(argv, timeout=30):
    t0 = time.time()
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {"sec": round(time.time() - t0, 2), "rc": p.returncode,
                "err": (p.stderr or "")[:120]}
    except Exception as e:
        return {"sec": round(time.time() - t0, 2), "rc": 124, "err": str(e)[:120]}


def measure_git():
    """不产生提交：push 用 --dry-run，fetch 用 --dry-run。"""
    push = time_cmd(["git", "push", "--dry-run", "origin", "HEAD:main"])
    fetch = time_cmd(["git", "fetch", "--dry-run", "origin"])
    return {"push": push, "fetch": fetch}


def poke_payload_valid(payload, whitelist):
    """契约校验：reason 必须含 enable-tasks；tasks 必须是白名单里的非空列表。"""
    if not isinstance(payload, dict):
        return False, "payload 不是对象"
    reason = str(payload.get("reason") or "")
    if "enable-tasks" not in reason:
        return False, "reason 缺 enable-tasks（发出去会被 accepted:true 静默忽略）"
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return False, "tasks 必须是非空列表"
    bad = [t for t in tasks if t not in whitelist]
    if bad:
        return False, "任务不在白名单：%s" % bad[:3]
    return True, "ok"


def _stub_poke(hits):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            hits.append(body)
            ok, why = poke_payload_valid(body, {"HQ-ProductionClaim", "FluxGroup-NatsBus"})
            resp = {"accepted": bool(ok), "wakes": ["HQ-ProductionClaim:WAKE"] if ok else [],
                    "why": why}
            data = json.dumps(resp).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def measure_poke():
    hits = []
    srv, port = _stub_poke(hits)
    url = "http://127.0.0.1:%d/poke" % port
    good = {"reason": "enable-tasks: cmd-latency probe", "tasks": ["HQ-ProductionClaim"]}

    def call(payload):
        t0 = time.time()
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            body = json.loads(r.read())
        return round((time.time() - t0) * 1000, 1), body

    ms, resp = call(good)
    bad_ms, bad_resp = call({"action": "enable-tasks"})   # 历史错法：字段不存在
    srv.shutdown()
    srv.server_close()
    return {"rtt_ms": ms, "resp": resp, "wrong_shape": {"rtt_ms": bad_ms, "resp": bad_resp},
            "valid_good": poke_payload_valid(good, {"HQ-ProductionClaim"}),
            "valid_bad": poke_payload_valid({"action": "enable-tasks"}, {"HQ-ProductionClaim"})}


def listeners(nodes):
    """探每台机 8790 是否有 agent 在听（0.6s 超时，不打扰）。"""
    out = {}
    for n in nodes:
        host = n.get("tailnet_ip") or n.get("host")
        if not host:
            continue
        s = socket.socket()
        s.settimeout(0.6)
        try:
            s.connect((host, 8790))
            out[n.get("id")] = True
        except Exception:
            out[n.get("id")] = False
        finally:
            s.close()
    return out


def analyse():
    nodes = (load(NODES, {}) or {}).get("nodes") or []
    enabled = [n for n in nodes if n.get("enabled")]
    git = measure_git()
    poke = measure_poke()
    listen = listeners(enabled)
    tick = tick_s()

    push_s, fetch_s = git["push"]["sec"], git["fetch"]["sec"]
    # 端到端：git 通道 = push + 平均等半个 tick + fetch
    git_avg = round(push_s + tick / 2 + fetch_s, 1)
    git_worst = round(push_s + tick + fetch_s, 1)
    # poke 通道 = poke RTT + fetch（数据仍在 git）+ 应用
    poke_ms = poke["rtt_ms"]
    poke_e2e = round(poke_ms / 1000 + fetch_s + 1.0, 1)

    reachable = sum(1 for v in listen.values() if v)
    checks = [
        {"k": "poke 载荷合规（reason 含 enable-tasks + 白名单任务）", "ok": poke["valid_good"][0],
         "detail": poke["valid_good"][1]},
        {"k": "错误载荷必须被拒（防 accepted:true 静默吞掉）", "ok": poke["valid_bad"][0] is False,
         "detail": poke["valid_bad"][1]},
        {"k": "poke 单跳 ≤ %.0fs" % BUDGET["poke_s"], "ok": poke_ms / 1000 <= BUDGET["poke_s"],
         "detail": "%.0fms" % poke_ms},
        {"k": "P0 紧急路径 ≤ %.0fs" % BUDGET["p0_total_s"], "ok": poke_e2e <= BUDGET["p0_total_s"],
         "detail": "%.1fs（poke+fetch+应用）" % poke_e2e},
        {"k": "常规卡路径 ≤ %.0fs" % BUDGET["tick_total_s"], "ok": git_worst <= BUDGET["tick_total_s"],
         "detail": "avg %.1fs / worst %.1fs（tick %ss）" % (git_avg, git_worst, tick)},
        {"k": "至少一台机能收命令（8790 可连）", "ok": reachable > 0,
         "detail": "%d/%d 台在听" % (reachable, len(listen))},
    ]
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "git": git, "poke": poke, "tick_s": tick, "listen": listen,
            "e2e": {"git_avg_s": git_avg, "git_worst_s": git_worst, "poke_s": poke_e2e},
            "checks": checks, "budget": BUDGET,
            "verdict": "命令面可用" if reachable else
                       "命令面当前不可达：8790 全无监听（自启仍暂停），命令只能躺在 git 里等人来拉"}


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    wl = {"HQ-ProductionClaim"}
    chk("合规载荷通过", poke_payload_valid({"reason": "enable-tasks", "tasks": ["HQ-ProductionClaim"]}, wl)[0])
    chk("缺 enable-tasks 被拒",
        poke_payload_valid({"reason": "please wake", "tasks": ["HQ-ProductionClaim"]}, wl)[0] is False)
    chk("空 tasks 被拒", poke_payload_valid({"reason": "enable-tasks", "tasks": []}, wl)[0] is False)
    chk("越界任务被拒", poke_payload_valid({"reason": "enable-tasks", "tasks": ["rm -rf /"]}, wl)[0] is False)
    chk("历史错法 {action:...} 被拒", poke_payload_valid({"action": "enable-tasks"}, wl)[0] is False)
    chk("预算单调：poke < P0 < 常规", BUDGET["poke_s"] <= BUDGET["p0_total_s"] <= BUDGET["tick_total_s"])
    rep = analyse()
    chk("分析产出 6 条判据", len(rep["checks"]) == 6, len(rep["checks"]))
    chk("未监听时判决必须如实说不可达",
        not rep["verdict"].startswith("命令面可用") or any(rep["listen"].values()),
        rep["verdict"])
    print("[cmd_latency] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rep = analyse()
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(rep["verdict"])
        g = rep["git"]
        print("  git 通道：push %.2fs / fetch %.2fs / 脉节奏 %ss → 平均 %.1fs，最差 %.1fs"
              % (g["push"]["sec"], g["fetch"]["sec"], rep["tick_s"],
                 rep["e2e"]["git_avg_s"], rep["e2e"]["git_worst_s"]))
        print("  poke 通道：单跳 %.0fms → P0 端到端 %.1fs" % (rep["poke"]["rtt_ms"], rep["e2e"]["poke_s"]))
        print("  在听 8790：%s" % rep["listen"])
        for c in rep["checks"]:
            print("   %s %s（%s）" % ("ok  " if c["ok"] else "FAIL", c["k"], c.get("detail")))
    try:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 0 if all(c["ok"] for c in rep["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
