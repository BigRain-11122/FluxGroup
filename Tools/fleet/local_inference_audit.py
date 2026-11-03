#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_inference_audit.py - 每台机的本地推理栈体检 + 可选的参数落盘（跨系统：Windows/macOS/Linux）。

为什么（CEO 2026-11-03「机队电脑不同系统也要同时优化」）：
  在 Mac 上查出三件事都可能在 Windows 机上重演，而且更难发现——
  a) 真正监听 11434 的可能不是我们配的那个进程（app 自带的 job 抢端口，参数全不生效）；
  b) 并发与常驻参数没按实测设（并发不加速只多吃 KV；keep_alive 比节奏还短等于每次冷载）；
  c) 向量层用的是弱模型（同样的活判不出同一件事）。
  本工具只做三件：量（先事实）→ 判（对照判据给 PASS/GAPS）→ 落盘（--apply 才动配置，动完复测）。

用法：
  python3 Tools/fleet/local_inference_audit.py --node bm-b
  python3 Tools/fleet/local_inference_audit.py --node bm-b --apply     # 落盘并复测
输出：cph4/fleet/queue-receipts/inference-audit-<node>-<date>.json
Exit: 0 = 无 GAPS；2 = 有 GAPS 待修（不是故障）
"""
import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
POLICY_DIR = os.path.join(ROOT, "cph4", "fleet", "model-policy")

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

WANT = {"OLLAMA_NUM_PARALLEL": "1", "OLLAMA_KEEP_ALIVE": "15m",
        "OLLAMA_MAX_LOADED_MODELS": "1", "OLLAMA_CONTEXT_LENGTH": "8192"}
PROMPT = "你是机队判断席，只依据证据回答，不超过 40 字，格式：动作｜理由。\n证据：" + \
         ("队列 OPEN=3 RUNNING=2 FAILED=6；线 duanju 停摆 70h。" * 12) + "\n问题：先派哪条线？"


def sh(cmd, timeout=25):
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                           text=True, timeout=timeout)
        return (r.returncode, (r.stdout or "") + (r.stderr or ""))
    except Exception as e:
        return (-1, str(e))


def http_json(path, body=None, timeout=180):
    url = URL + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# ---- 事实采集 ---------------------------------------------------------------
def port_owner():
    """谁在监听 11434。这条最要紧：监听者不是我们配的进程，参数全不生效。"""
    if IS_WIN:
        rc, out = sh('netstat -ano | findstr :11434')
        pids = set()
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[-1].isdigit() and "LISTEN" in line.upper():
                pids.add(parts[-1])
        rows = []
        for pid in sorted(pids):
            rc2, name = sh('tasklist /FI "PID eq %s" /FO CSV /NH' % pid)
            rows.append({"pid": pid, "image": (name or "").split(",")[0].strip('"')})
        return rows
    rc, out = sh("lsof -nP -iTCP:11434 -sTCP:LISTEN")
    rows = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            rows.append({"pid": parts[1], "image": parts[0], "proto": parts[-2] if len(parts) > 2 else ""})
    return rows


def server_env():
    """服务进程实际拿到的环境变量（不是我们以为的）。"""
    env = {}
    if IS_MAC:
        rc, out = sh("ps eww -A 2>/dev/null | grep -m1 'ollama serve'")
        for tok in out.split():
            if tok.startswith("OLLAMA_"):
                k, _, v = tok.partition("=")
                env[k] = v
        if not env:
            p = os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.ollama.plist")
            if os.path.exists(p):
                try:
                    import plistlib
                    d = plistlib.load(open(p, "rb"))
                    env = dict((d.get("EnvironmentVariables") or {}))
                    env["_source"] = "plist(未在进程里读到)"
                except Exception:
                    pass
    elif IS_WIN:
        rc, out = sh('reg query "HKCU\\Environment"')
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].upper().startswith("OLLAMA_"):
                env[parts[0]] = parts[-1]
        env["_source"] = "HKCU\\Environment"
    else:
        rc, out = sh("ps eww -A | grep -m1 'ollama serve'")
        for tok in out.split():
            if tok.startswith("OLLAMA_"):
                k, _, v = tok.partition("=")
                env[k] = v
    return env


def models():
    try:
        d = http_json("/api/tags", timeout=15)
    except Exception as e:
        return [], "ollama api: %s" % str(e)[:60]
    return [{"name": m.get("name"), "size_gb": round((m.get("size") or 0) / 1e9, 2)}
            for m in (d.get("models") or [])], None


def runner_of(model):
    """哪个引擎在跑（mlx / llamacpp）。看 ps 的 RUNNER 列，取不到就 None。"""
    rc, out = sh("ollama ps")
    for line in out.splitlines()[1:]:
        parts = line.split()
        if parts and parts[0] == model:
            for tok in parts:
                if tok in ("mlx", "llamacpp"):
                    return tok
    return None


# ---- 测量 -------------------------------------------------------------------
def gen(model, prompt=PROMPT, npredict=48, keep_alive=None):
    body = {"model": model, "prompt": prompt, "stream": False, "think": False,
            "options": {"temperature": 0, "num_predict": npredict, "num_ctx": 8192}}
    if keep_alive is not None:
        body["keep_alive"] = keep_alive
    t0 = time.time()
    d = http_json("/api/generate", body)
    wall = time.time() - t0
    ec, ed = d.get("eval_count") or 0, d.get("eval_duration") or 0
    pc, pd = d.get("prompt_eval_count") or 0, d.get("prompt_eval_duration") or 0
    return {"wall": round(wall, 2),
            "decode_tok_s": round(ec / (ed / 1e9), 1) if ed else None,
            "prefill_tok_s": round(pc / (pd / 1e9), 1) if pd else None,
            "load_s": round((d.get("load_duration") or 0) / 1e9, 2)}


def measure(model):
    out = {"model": model}
    try:
        gen(model, npredict=8)                       # 预热
        runs = [gen(model) for _ in range(3)]
        sp = [r["decode_tok_s"] for r in runs if r["decode_tok_s"]]
        out["decode_tok_s"] = round(sorted(sp)[len(sp) // 2], 1) if sp else None
        out["engine"] = runner_of(model)
        # 前缀缓存：同一前缀连发两次，第二次应显著更快
        a = gen(model, PROMPT, 24)
        b = gen(model, PROMPT, 24)
        out["prefix_cache"] = {"first_wall": a["wall"], "second_wall": b["wall"],
                               "hit": bool(a["wall"] and b["wall"] and b["wall"] < a["wall"] * 0.8)}
        # 并发：3 个并发 vs 3 个串行（相等=并发无收益，只多占 KV）
        import threading
        t0 = time.time()
        for _ in range(3):
            gen(model, npredict=32)
        seq = round(time.time() - t0, 2)
        box = []
        def w():
            box.append(gen(model, npredict=32))
        t0 = time.time()
        th = [threading.Thread(target=w) for _ in range(3)]
        for t in th:
            t.start()
        for t in th:
            t.join()
        par = round(time.time() - t0, 2)
        out["concurrency"] = {"serial_3": seq, "parallel_3": par,
                              "speedup": round(seq / par, 2) if par else None}
    except Exception as e:
        out["error"] = str(e)[:120]
    return out


def embedding_check():
    """向量层：维度 + 三对真重复是否仍能分辨（模型换了也能立刻看出来）。"""
    for m in ("qwen3-embedding:0.6b", "nomic-embed-text:latest", "bge-m3:latest"):
        try:
            def emb(t):
                d = http_json("/api/embed", {"model": m, "input": t}, timeout=60)
                return d["embeddings"][0]
            import math
            def cos(a, b):
                return sum(x * y for x, y in zip(a, b)) / (
                    math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) + 1e-9)
            pairs = [("配音质检（全量回执）", "配音质检（全量回执）复跑"),
                     ("交付闸（重复/静止/抖动/闪烁）", "交付闸（重复/静止/抖动/闪烁）-R2"),
                     ("音色数据集准入（反播音腔的第一道门）", "音色库数据集准入检查")]
            sims = [round(cos(emb(a), emb(b)), 3) for a, b in pairs]
            return {"model": m, "dim": len(emb("x")), "true_dupe_sims": sims,
                    "usable": all(s >= 0.72 for s in sims)}
        except Exception:
            continue
    return {"model": None, "usable": False, "why": "没有可用的 embedding 模型"}


# ---- 判 + 落盘 ---------------------------------------------------------------
def judge(rep):
    gaps = []
    env = rep.get("server_env") or {}
    for k, v in WANT.items():
        got = env.get(k)
        if got is None:
            gaps.append("env-missing:%s(应为 %s)" % (k, v))
        elif str(got) != v:
            gaps.append("env-value:%s=%s(应为 %s)" % (k, got, v))
    owner = rep.get("port_owner") or []
    if len(owner) > 1:
        gaps.append("port-双监听:%s" % ",".join("%s/%s" % (o.get("image"), o.get("pid")) for o in owner))
    m = rep.get("measure") or {}
    if not m.get("decode_tok_s"):
        gaps.append("measure-failed")
    elif m["decode_tok_s"] < 15:
        gaps.append("decode-slow:%.1f tok/s < 15" % m["decode_tok_s"])
    emb = rep.get("embedding") or {}
    if not emb.get("usable"):
        gaps.append("embedding-unusable:%s" % emb.get("model"))
    # 根因提示：有参数要求但不在服务环境里，且端口被别的镜像占着
    if any(g.startswith("env-missing") for g in gaps) and owner:
        gaps.append("hint:真正监听 11434 的是 %s，参数可能没落到它身上"
                    % ",".join(str(o.get("image")) for o in owner))
    return gaps


def apply_tuning(node):
    """只落两条已被实测证明的：NUM_PARALLEL=1、KEEP_ALIVE=15m。落完必须复测。"""
    done = []
    if IS_WIN:
        for k, v in (("OLLAMA_NUM_PARALLEL", "1"), ("OLLAMA_KEEP_ALIVE", "15m")):
            sh('setx %s %s' % (k, v))
            done.append("setx %s=%s" % (k, v))
        sh('taskkill /F /IM "ollama app.exe"')
        sh('taskkill /F /IM ollama.exe')
        for cand in (os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"),
                     "ollama app.exe", "ollama serve"):
            rc, _ = sh('start "" "%s"' % cand, timeout=10)
            if rc == 0:
                done.append("restart:%s" % cand)
                break
    elif IS_MAC:
        p = os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.ollama.plist")
        if os.path.exists(p):
            import plistlib
            d = plistlib.load(open(p, "rb"))
            env = d.setdefault("EnvironmentVariables", {})
            for k, v in (("OLLAMA_NUM_PARALLEL", "1"), ("OLLAMA_KEEP_ALIVE", "15m")):
                env[k] = v
                done.append("plist %s=%s" % (k, v))
            plistlib.dump(d, open(p, "wb"))
            uid = str(os.getuid())
            sh("launchctl bootout gui/%s/com.fluxgroup.ollama" % uid)
            time.sleep(2)
            sh("launchctl bootstrap gui/%s %s" % (uid, p))
            done.append("launchctl restart")
    else:
        done.append("未实现该系统的落盘（只有 Windows/macOS）")
    # 等 API 回来
    for _ in range(20):
        try:
            http_json("/api/version", timeout=3)
            break
        except Exception:
            time.sleep(1)
    return done


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default=os.environ.get("FLEET_NODE", platform.node()))
    ap.add_argument("--model", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--daily", action="store_true",
                    help="一天只跑一次（今天已有回执就跳过）")
    a = ap.parse_args(argv)

    out = a.out or os.path.join(OUT_DIR, "inference-audit-%s-%s.json"
                                % (a.node, time.strftime("%Y%m%d")))
    if a.daily and os.path.exists(out):
        print(json.dumps({"skipped": "already ran today", "out": os.path.relpath(out, ROOT)},
                         ensure_ascii=False))
        return 0
    t0 = time.time()
    ms, merr = models()
    pick = a.model
    if not pick and ms:
        installed = set(m["name"] for m in ms)
        # 先按本机策略的现役档；装不上才退到"最小的非 embedding 档"
        want = None
        for p in (os.path.join(POLICY_DIR, "%s.json" % a.node),
                  os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json")):
            try:
                d = json.load(open(p, encoding="utf-8"))
                want = ((d.get("duties") or {}).get("resident") or {}).get("model")
                if want:
                    break
            except Exception:
                continue
        if want and want in installed:
            pick = want
        else:
            cand = [m for m in ms if "embed" not in (m["name"] or "").lower()]
            pick = sorted(cand, key=lambda m: m["size_gb"] or 0)[0]["name"] if cand else ms[0]["name"]
    rep = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "node": a.node,
           "os": platform.platform(), "python": platform.python_version(),
           "endpoint": URL, "models": ms, "models_error": merr,
           "port_owner": port_owner(), "server_env": server_env(),
           "measure": measure(pick) if pick else {"error": "没有可用模型"},
           "embedding": embedding_check()}
    rep["gaps"] = judge(rep)
    if a.apply and rep["gaps"]:
        rep["applied"] = apply_tuning(a.node)
        rep["server_env_after"] = server_env()
        rep["measure_after"] = measure(pick) if pick else {}
        rep["gaps_after"] = judge(dict(rep, server_env=rep["server_env_after"],
                                       measure=rep["measure_after"]))
    rep["verdict"] = "GAPS" if rep.get("gaps_after", rep["gaps"]) else "PASS"
    rep["seconds"] = round(time.time() - t0, 1)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print(json.dumps({"node": a.node, "model": pick, "verdict": rep["verdict"],
                      "gaps": rep.get("gaps_after", rep["gaps"]),
                      "decode_tok_s": (rep.get("measure") or {}).get("decode_tok_s"),
                      "engine": (rep.get("measure") or {}).get("engine"),
                      "out": os.path.relpath(out, ROOT)}, ensure_ascii=False, indent=1))
    return 0 if rep["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))