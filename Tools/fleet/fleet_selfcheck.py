#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_selfcheck.py - 任意机器一条命令自检：能不能按集团规则开工。

用法（三平台同一份）：
  python3 Tools/fleet/fleet_selfcheck.py --node bm-a
  python3 Tools/fleet/fleet_selfcheck.py --node bm-c --json out.json

检查项（全部只读，除心跳文件外不写）：
  1 仓库：git 可用、分支、领先/落后、冲突标记
  2 车道：lanes/<node>.json 存在、心跳龄、在办卡数
  3 服务：Ollama 11434（可选）、网关 8792 令牌（可选）
  4 回执面：queue-receipts 可写
  5 资源：磁盘可用、内存可用（尽力）
  6 规则：正典文件在（AI.md / docs/governance.md / cph4/cadence.md）

退出：0 全 PASS；1 有 WARN；2 有 FAIL。
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")


def sh(args, timeout=60):
    try:
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def age(p):
    try:
        return round(time.time() - os.path.getmtime(p))
    except OSError:
        return None


def git_checks(rows):
    rc, out = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    rows.append(("git_branch", "PASS" if rc == 0 else "FAIL", out.strip()[:60] or "no git"))
    rc, out = sh(["git", "status", "--porcelain"])
    uu = [l for l in out.splitlines() if l[:2] == "UU"]
    rows.append(("git_conflicts", "PASS" if not uu else "FAIL", "UU=%d" % len(uu)))
    sh(["git", "fetch", "--quiet", "origin", "main"], timeout=60)
    rc, out = sh(["git", "rev-list", "--count", "HEAD..origin/main"])
    behind = int(out.strip() or 0) if rc == 0 and out.strip().isdigit() else -1
    rows.append(("git_behind", "PASS" if 0 <= behind <= 50 else "WARN",
                 "behind=%s" % behind))


def lane_checks(node, rows):
    p = os.path.join(F, "lanes", "%s.json" % node)
    if not os.path.exists(p):
        rows.append(("lane_file", "FAIL", "missing %s" % p))
        return
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        rows.append(("lane_file", "FAIL", "unreadable %s" % str(e)[:50]))
        return
    ts = d.get("ts")
    a = None
    try:
        a = round(time.time() - time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S")))
    except Exception:
        pass
    rows.append(("lane_heartbeat", "PASS" if (a is not None and a < 3600) else "WARN",
                 "age=%ss jobs=%d" % (a, len(d.get("jobs") or []))))


def service_checks(rows):
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3).read(10)
        rows.append(("ollama", "PASS", "11434 ok"))
    except Exception:
        rows.append(("ollama", "WARN", "11434 unreachable (无本地模型或未装)"))
    tok = os.path.expanduser("~/.fluxgroup-llm-token")
    rows.append(("llm_token", "PASS" if os.path.isfile(tok) else "WARN",
                 "present=%s" % os.path.isfile(tok)))
    try:
        req = urllib.request.Request("http://127.0.0.1:8792/api/chat",
                                     data=b'{"model":"qwen3.5:4b-mlx","messages":[{"role":"user","content":"ok"}],"stream":false,"options":{"num_predict":1}}',
                                     headers={"Content-Type": "application/json",
                                              "X-Flux-Token": open(tok).read().strip()})
        urllib.request.urlopen(req, timeout=10).read(10)
        rows.append(("gateway", "PASS", "8792 ok"))
    except Exception as e:
        rows.append(("gateway", "WARN", "8792 %s" % str(e)[:50]))


def resource_checks(rows):
    du = shutil.disk_usage(ROOT)
    free_gb = round(du.free / 1024 ** 3, 1)
    rows.append(("disk", "PASS" if free_gb > 10 else "FAIL", "free=%.1fGB" % free_gb))
    # 内存：尽力，不依赖 psutil
    try:
        if sys.platform == "darwin":
            out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
            pages = {}
            for line in out.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    try:
                        pages[k.strip()] = int(v.strip().rstrip("."))
                    except ValueError:
                        pass
            free = (pages.get("Pages free", 0) + pages.get("Pages inactive", 0)) * 16384 / 1024 ** 3
        elif os.path.exists("/proc/meminfo"):
            m = {}
            for line in open("/proc/meminfo"):
                k, v = line.split(":", 1)
                m[k.strip()] = int(v.split()[0])
            free = (m.get("MemAvailable", 0)) / 1024 ** 2
        else:
            free = -1
    except Exception:
        free = -1
    rows.append(("memory", "PASS" if free > 2 or free < 0 else "WARN", "free=%.1fGB" % free))


def rule_checks(rows):
    need = ["AI.md", os.path.join("docs", "governance.md"), os.path.join("cph4", "cadence.md")]
    missing = [p for p in need if not os.path.exists(os.path.join(ROOT, p))]
    rows.append(("canon", "PASS" if not missing else "FAIL", "missing=%s" % (missing or "-")))
    rec = os.path.join(F, "queue-receipts")
    w = os.path.isdir(rec) and os.access(rec, os.W_OK)
    rows.append(("receipts", "PASS" if w else "FAIL", "writable=%s" % w))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default=os.environ.get("FLEET_NODE") or socket.gethostname().lower())
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    rows = []
    git_checks(rows)
    lane_checks(a.node, rows)
    service_checks(rows)
    resource_checks(rows)
    rule_checks(rows)
    fails = [r for r in rows if r[1] == "FAIL"]
    warns = [r for r in rows if r[1] == "WARN"]
    print("node=%s host=%s" % (a.node, socket.gethostname()))
    for n, st, d in rows:
        print("%-4s %-16s %s" % (st, n, d))
    print("-- %d PASS / %d WARN / %d FAIL" % (len(rows) - len(fails) - len(warns), len(warns), len(fails)))
    if a.json:
        json.dump({"node": a.node, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "checks": [{"id": n, "status": st, "detail": d} for n, st, d in rows]},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 2 if fails else (1 if warns else 0)


if __name__ == "__main__":
    sys.exit(main())
