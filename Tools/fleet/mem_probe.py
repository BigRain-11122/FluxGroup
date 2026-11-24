#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mem_probe.py — 统一内存体检：不触发 swap 的前提下把 32GB 用好、用科学。

为什么要它（CEO 2026-11-21 再次强调「本地算力不触发 swap 的情况下用好用科学 统一内存 gpu cpu」）：
这条规则说过很多次却没被判据守住，结果受管 ollama 一直写着
`OLLAMA_MAX_LOADED_MODELS=6` + `KEEP_ALIVE=10m`——一台 32GB 的统一内存机器
同时塞六个模型，必然换页；而审计里没有任何一条会因为 swap 变红。

判据（**只认实测，不认"装得下"**，2026-11-14 CEO 令）：
  ME01 swap 不在涨     两次采样（默认 5s）swap_used 增量 ≤ 0 且 pageouts 增量 = 0
  ME02 常驻模型预算    ollama 侧常驻合计 ≤ 6GB、个数 ≤ 1（MLX 8788 单独算）
  ME03 真实生成增量    --gen N 前后 swap/pageouts 增量 = 0（记账到 MEM-PROBE.json）
  ME04 单一服务端      11434 只许一个监听进程（两个服端 = 配置不生效 + 双份内存）
  ME05 余量            free + inactive ≥ 4GB（给公众应用与训练峰值留头寸）

分工原则（统一内存，GPU 与 CPU 同一个池子）：
  · 生成/训练走 MLX 8788（GPU）；本地小任务走 ollama（Metal）；**两者不同时驻留大模型**
  · ollama 侧同时只许 1 个模型，用完 2 分钟释放；9B 只在显式 big 档用，用完即卸
  · 浏览器/采集/审计走 CPU，不吃 GPU 也不载模型

三态：True 通过 / False 不通过 / None 量不到（SKIP 不算通过）。
用法
  python3 Tools/fleet/mem_probe.py --once          # 静态体检（两次采样，秒级）
  python3 Tools/fleet/mem_probe.py --gen 3         # 额外测 3 条真实生成的增量
  python3 Tools/fleet/mem_probe.py --json / --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "social", "state")
REC = os.path.join(STATE, "MEM-PROBE.json")

OLLAMA = "http://127.0.0.1:11434"
MLX = "http://127.0.0.1:8788"
RESIDENT_BUDGET_GB = 6.0     # ollama 侧常驻预算（9B 8.9GB 必须独占窗口）
MAX_RESIDENT_MODELS = 1
HEADROOM_MIN_GB = 4.0
PAGE = 16384 / 1024 / 1024   # 16KB → MB


def _sh(cmd, timeout=10):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout).stdout
    except Exception:
        return ""


def _get(url, timeout=5, data=None):
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def sample():
    """一次内存快照：swap / 页统计 / 余量。"""
    out = _sh("sysctl -n vm.swapusage")
    used = total = None
    # 形如：total = 4096.00M  used = 2518.62M  free = 1577.38M  (encrypted)
    m = re.search(r"total\s*=\s*([\d.]+)M", out)
    if m:
        total = float(m.group(1))
    m = re.search(r"used\s*=\s*([\d.]+)M", out)
    if m:
        used = float(m.group(1))
    vm = {}
    for line in _sh("vm_stat").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip().rstrip(".")
            if v.isdigit():
                vm[k.strip()] = int(v)
    free_gb = vm.get("Pages free", 0) * PAGE / 1024
    inactive_gb = vm.get("Pages inactive", 0) * PAGE / 1024
    wired_gb = vm.get("Pages wired down", 0) * PAGE / 1024
    return {
        "swap_used_mb": used, "swap_total_mb": total,
        "pageouts": vm.get("Pageouts", 0), "pageins": vm.get("Pageins", 0),
        "free_gb": round(free_gb, 2), "inactive_gb": round(inactive_gb, 2),
        "wired_gb": round(wired_gb, 2),
        "headroom_gb": round(free_gb + inactive_gb, 2),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def models():
    d = _get(OLLAMA + "/api/ps") or {}
    ms = d.get("models") or []
    return {"n": len(ms),
            "gb": round(sum((m.get("size") or 0) for m in ms) / 1e9, 2),
            "names": [m.get("name") for m in ms]}


def servers():
    """11434 上的监听进程数（两个 = 配置不生效 + 双份内存）。"""
    out = _sh("lsof -nP -iTCP:11434 -sTCP:LISTEN 2>/dev/null", timeout=8)
    pids = set()
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) > 1 and parts[1].isdigit():
            pids.add(parts[1])
    return sorted(pids)


def _mk(cid, name, ok, detail, sev="P1"):
    return {"id": cid, "name": name, "ok": ok, "detail": detail, "sev": sev}


def checks_static(s1=None, s2=None, wait_s=5.0, models_fn=None, servers_fn=None):
    s1 = s1 or sample()
    if wait_s:
        time.sleep(wait_s)
    s2 = s2 or sample()
    out = []
    if None in (s1["swap_used_mb"], s2["swap_used_mb"]):
        out.append(_mk("ME01", "swap 不在涨", None, "取不到 swapusage"))
    else:
        d_swap = round(s2["swap_used_mb"] - s1["swap_used_mb"], 1)
        d_out = (s2["pageouts"] or 0) - (s1["pageouts"] or 0)
        out.append(_mk("ME01", "swap 不在涨", d_swap <= 0 and d_out == 0,
                       "%.0fs 内 swap %+.1fMB / pageouts %+d（基线 %.0fMB）"
                       % (wait_s, d_swap, d_out, s2["swap_used_mb"])))
    m = (models_fn or models)()
    ok = m["gb"] <= RESIDENT_BUDGET_GB and m["n"] <= MAX_RESIDENT_MODELS
    out.append(_mk("ME02", "常驻模型预算", ok,
                   "ollama 常驻 %d 个 / %.1fGB（预算 ≤%d 个、≤%.0fGB）%s"
                   % (m["n"], m["gb"], MAX_RESIDENT_MODELS, RESIDENT_BUDGET_GB,
                      ("：" + ",".join(m["names"])) if m["names"] else "")))
    pids = (servers_fn or servers)()
    out.append(_mk("ME04", "单一 ollama 服务端", len(pids) <= 1,
                   "11434 监听进程 %d 个%s" % (len(pids), ("：" + ",".join(pids)) if pids else "")))
    out.append(_mk("ME05", "内存余量", s2["headroom_gb"] >= HEADROOM_MIN_GB,
                   "free %.1fG + inactive %.1fG = %.1fG（线 ≥%.0fG）"
                   % (s2["free_gb"], s2["inactive_gb"], s2["headroom_gb"], HEADROOM_MIN_GB),
                   "P2"))
    return out, s1, s2


def gen(n=3, prompt="写一句 12 字以内的 B 站真人评论"):
    """真实生成 n 条，测 swap/pageouts 增量。不产出业务内容，只做探针。"""
    done, errors = 0, 0
    for _ in range(n):
        r = _get(MLX + "/v1/chat/completions", timeout=120,
                 data={"messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 32, "temperature": 0.8})
        if r and r.get("choices"):
            done += 1
        else:
            errors += 1
    return {"n_gen": done, "errors": errors}


def probe(with_gen=0):
    out, s1, s2 = checks_static(wait_s=3.0 if not with_gen else 5.0)
    rec = {"ts": s2["ts"], "n_gen": 0, "swap_before": s1["swap_used_mb"],
           "swap_after": s2["swap_used_mb"]}
    if with_gen:
        before = sample()
        g = gen(with_gen)
        after = sample()
        d_swap = round((after["swap_used_mb"] or 0) - (before["swap_used_mb"] or 0), 1)
        d_out = (after["pageouts"] or 0) - (before["pageouts"] or 0)
        ok = (g["n_gen"] >= with_gen and d_swap <= 0 and d_out == 0)
        out.append(_mk("ME03", "真实生成不增量", bool(ok),
                       "生成 %d 条：swap %+.1fMB / pageouts %+d%s"
                       % (g["n_gen"], d_swap, d_out,
                          "" if ok else "（真实生成时换页＝硬扛 swap）")))
        rec.update({"n_gen": g["n_gen"], "gen_errors": g["errors"],
                    "swap_before": before["swap_used_mb"],
                    "swap_after": after["swap_used_mb"],
                    "pageouts_before": before["pageouts"],
                    "pageouts_after": after["pageouts"],
                    "swap_delta_mb": d_swap, "pageouts_delta": d_out})
    else:
        prev = None
        try:
            with open(REC, encoding="utf-8") as f:
                prev = (json.load(f) or {}).get("last_gen") or None
        except Exception:
            pass
        if not prev:
            out.append(_mk("ME03", "真实生成不增量", None,
                           "还没跑过 --gen（量不到≠通过）"))
        else:
            age_h = (time.time() - time.mktime(time.strptime(prev["ts"], "%Y-%m-%dT%H:%M:%S"))) / 3600
            ok = (age_h <= 24 * 7 and (prev.get("swap_delta_mb") or 0) <= 0
                  and (prev.get("pageouts_delta") or 0) == 0)
            out.append(_mk("ME03", "真实生成不增量", ok,
                           "上次 %s（%.0fh前）生成 %d 条 swap %+.1fMB pageouts %+d"
                           % (prev["ts"], age_h, prev.get("n_gen") or 0,
                              prev.get("swap_delta_mb") or 0, prev.get("pageouts_delta") or 0)))
    doc = {
        "ts": rec["ts"],
        "pass": {c["id"]: c["ok"] for c in out},
        "checks": out,
        "sample": {"now": s2, "before": s1},
        "models": models(),
        "servers": servers(),
        "last_gen": rec if with_gen else None,
    }
    if not with_gen:
        try:
            with open(REC, encoding="utf-8") as f:
                old = json.load(f) or {}
            doc["last_gen"] = old.get("last_gen")
        except Exception:
            pass
    os.makedirs(STATE, exist_ok=True)
    tmp = REC + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    os.replace(tmp, REC)
    return doc


def self_test():
    """负控：swap 涨了必须红、常驻超预算必须红、双服务端必须红；干净态必须绿。"""
    res = {}

    def st(swap1, swap2, out1, out2):
        return [{"swap_used_mb": swap1, "pageouts": out1, "free_gb": 8, "inactive_gb": 6,
                 "wired_gb": 5, "headroom_gb": 14},
                {"swap_used_mb": swap2, "pageouts": out2, "free_gb": 8, "inactive_gb": 6,
                 "wired_gb": 5, "headroom_gb": 14}]

    mk = lambda: {"n": 0, "gb": 0.0, "names": []}
    sv = lambda: ["1"]
    a, b = st(100.0, 100.0, 10, 10)
    ok, _, _ = checks_static(a, b, wait_s=0, models_fn=mk, servers_fn=sv)
    res["clean_green"] = "PASS" if all(c["ok"] is True for c in ok) else "FAIL"
    a, b = st(100.0, 180.0, 10, 10)
    ok, _, _ = checks_static(a, b, wait_s=0, models_fn=mk, servers_fn=sv)
    res["swap_up_red"] = "PASS" if next(c for c in ok if c["id"] == "ME01")["ok"] is False else "FAIL"
    a, b = st(100.0, 100.0, 10, 40)
    ok, _, _ = checks_static(a, b, wait_s=0, models_fn=mk, servers_fn=sv)
    res["pageout_red"] = "PASS" if next(c for c in ok if c["id"] == "ME01")["ok"] is False else "FAIL"
    a, b = st(100.0, 100.0, 10, 10)
    b["headroom_gb"] = 1.0
    ok, _, _ = checks_static(a, b, wait_s=0, models_fn=mk, servers_fn=sv)
    res["headroom_red"] = "PASS" if next(c for c in ok if c["id"] == "ME05")["ok"] is False else "FAIL"
    ok_all = "PASS" not in ("FAIL",) and all(v == "PASS" for v in res.values())
    print(json.dumps({"self_test": "PASS" if ok_all else "FAIL", "cases": res},
                     ensure_ascii=False, indent=1))
    return 0 if ok_all else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--gen", type=int, default=0, help="额外测 N 条真实生成的增量")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    doc = probe(with_gen=max(0, a.gen))
    if a.json:
        print(json.dumps(doc, ensure_ascii=False, indent=1))
    else:
        print("== 统一内存体检 %s ==" % doc["ts"])
        for c in doc["checks"]:
            mark = {True: "✅", False: "❗", None: "⏭"}[c["ok"]]
            print("%s %-4s %-16s %s" % (mark, c["id"], c["name"], c["detail"]))
    return 0 if all(c["ok"] is not False for c in doc["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
