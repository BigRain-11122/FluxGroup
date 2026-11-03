#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""warm_models.py - 按内存实况保活常驻模型（有闸，不是无条件加载）。

为什么（2026-11-03 CEO：「本机还有很多内存余量，是否可以加载一些常驻模型，去处理轻量需求」）：
  答案不是"能就加载"，而是"按余量决定加不加载"。这台机的内存与 CEO 办公应用共用同一池，
  无条件塞模型会把他正常办公拖进 swap。所以做法是：每轮看一次真实余量，
  够就保活、不够就让它自然卸载，并把决定与数字写进回执——谁都能复核。

判据：
  1. memory_pressure 的空闲百分比 < 25% → 不保活（记 reason=low-memory）
  2. 模型已在 ollama ps 里 → 只续 keep_alive，不重复加载
  3. 只有策略文件里声明的 resident / embedding 两个档位会被保活（不许临时决定加档）

用法：
  python3 warm_models.py [--dry] [--keep 30m] [--min-free-pct 25] [--out receipts/warm-*.json]
Exit: 0 已按余量处理（含"故意不加载"）；1 模型不在本地（需先 pull）；2 读不到策略。
"""
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
sys.path.insert(0, HERE)
_host = os.environ.get("OLLAMA_HOST") or "127.0.0.1:11434"
# 环境里的 OLLAMA_HOST 常写成 127.0.0.1:11434（无协议头），urlopen 会直接报
# "unknown url type"——2026-11-03 实测踩过，别假设它带 scheme。
HOST = _host if "://" in _host else "http://" + _host


def policy():
    try:
        import model_policy as mp
        return mp.resident(), mp.embedding()
    except Exception:
        try:
            d = json.load(open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                               encoding="utf-8-sig"))
            du = d.get("duties") or {}
            return (du.get("resident") or {}).get("model"), (du.get("embedding") or {}).get("model")
        except Exception:
            return None, None


def free_pct():
    """系统级空闲百分比。memory_pressure 是最接近"能不能再装东西"的口径。"""
    try:
        r = subprocess.run(["memory_pressure", "-Q"], capture_output=True, text=True, timeout=20)
        m = re.search(r"free percentage:\s*(\d+)%", r.stdout or "")
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def loaded():
    try:
        r = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=30)
        return {ln.split()[0] for ln in (r.stdout or "").splitlines()[1:] if ln.strip()}
    except Exception:
        return set()


def post(path, body, timeout=180):
    req = urllib.request.Request(HOST + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def keep_alive(model, ka, role="resident"):
    """发一个最小请求把 keep_alive 钉住，不产生实质推理。

    embedding 模型不接受 /api/generate（实测 HTTP 400），必须走 /api/embed——
    按角色分流，别用一个接口套所有模型。
    """
    try:
        if role == "embedding":
            post("/api/embed", {"model": model, "input": "warm", "keep_alive": ka})
        else:
            post("/api/generate", {"model": model, "prompt": "", "stream": False,
                                   "keep_alive": ka, "think": False,
                                   "options": {"num_predict": 1}})
        return True, "ok"
    except Exception as e:
        return False, str(e)[:120]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--keep", default="30m")
    ap.add_argument("--min-free-pct", type=int, default=25)
    ap.add_argument("--also-embedding", dest="also_embedding", action="store_true",
                    help="同时保活 embedding（会挤掉 resident，默认不开）")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)

    res, emb = policy()
    if not res:
        print("读不到策略里的 resident 档（rc=2）")
        return 2
    fp = free_pct()
    have = loaded()
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "spec": "WARM-MODELS-v1",
           "free_pct": fp, "threshold": a.min_free_pct, "keep_alive": a.keep,
           "loaded_before": sorted(have), "actions": [], "verdict": "OK"}

    if fp is not None and fp < a.min_free_pct:
        out["verdict"] = "SKIP-LOW-MEMORY"
        out["reason"] = "空闲 %d%% < %d%%，不保活（把内存留给 CEO 办公与主控脉）" % (fp, a.min_free_pct)
    else:
        # 2026-11-03 实测：本机 ollama 同一时刻只能有一个模型在跑——4B(MLX) 常驻时
        # /api/embed 会挂死 60s 不返回；先卸 4B，embedding 0.077s 返回。
        # 所以策略是"单一常驻"：只保活 resident，embedding 由需要它的工具自己按需加载。
        pairs = [("resident", res)]
        if a.also_embedding:
            pairs.append(("embedding", emb))
        for role, model in pairs:
            if not model:
                continue
            if model in have:
                out["actions"].append({"role": role, "model": model, "action": "renew"})
            else:
                out["actions"].append({"role": role, "model": model, "action": "warm"})
            if a.dry:
                continue
            ok, why = keep_alive(model, a.keep, role)
            if not ok:
                out["verdict"] = "FAILED"
                out["actions"][-1]["error"] = why
                if "not found" in why or "pull" in why:
                    out["actions"][-1]["hint"] = "模型不在本地：先 ollama pull %s" % model

    out["loaded_after"] = sorted(loaded())
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("WARM %s  free=%s%%  before=%s" % (out["verdict"], fp, ",".join(sorted(have)) or "-"))
    for act in out["actions"]:
        print("  %-9s %-22s %s%s" % (act["role"], act["model"], act["action"],
                                     (" ! " + act["error"]) if act.get("error") else ""))
    if out.get("reason"):
        print("  " + out["reason"])
    print("  after=%s" % (",".join(out["loaded_after"]) or "-"))
    return 0 if out["verdict"] in ("OK", "SKIP-LOW-MEMORY") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))