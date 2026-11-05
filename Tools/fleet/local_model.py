#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_model.py - 本机模型的唯一正门：本机调用优先，机队借用让路。

CEO 2026-11-05：「本机算力和内存、大模型什么的，要赋能本机的主控职责和别的，
然后才是赋能机队」。Ollama 的 NUM_PARALLEL=1，谁先占住谁先跑；机队经 11435 网关
借模型时，本机请求在 socket 层只能排队。所以本机调用必须先打个"让路"信号：
网关看到信号就拒绝机队新请求（429 local-busy），等本机这口气用完再放行。

三种身份（写进审计，可核验谁在用本机模型）：
  master  主控：派单判重、一屏摘要、根因归类——永远优先
  local   本机业务/轻量批：打标、ASR、本地判断——次优先
  fleet   机队借用：只许走网关，不经这里

用法：
  import local_model as lm
  txt = lm.generate(prompt, cls="master", timeout=90)
  vec = lm.embed(text, cls="master")
  lm.status()   # 近 24h 各类调用次数 + 当前是否本机在占用
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
HOLD = os.path.join(STATE, "local-model-hold.json")
AUDIT = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "local-model.jsonl")
URL = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"
HOLD_TTL_S = 45          # 主控一次生成可能在 30-60s，给足余量；过期自动失效，不留死锁
DEFAULT_MODEL = "\x00"


def _cfg():
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                  encoding="utf-8-sig") as f:
            return (json.load(f).get("duties") or {}).get("resident") or {}
    except Exception:
        return {}


def _model():
    if DEFAULT_MODEL != "\x00":
        return DEFAULT_MODEL
    return _cfg().get("model") or "qwen3.5:4b-mlx"


def _audit(row):
    row["ts"] = datetime.now().isoformat(timespec="seconds")
    try:
        os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
        with open(AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def hold(cls, why="", seconds=None):
    """声明"本机正在用模型"，网关据此对机队关门。失败不影响调用。"""
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(HOLD, "w", encoding="utf-8") as f:
            json.dump({"cls": cls, "why": why, "pid": os.getpid(),
                       "until": time.time() + float(seconds or HOLD_TTL_S)},
                      f, ensure_ascii=False)
    except Exception:
        pass


def release():
    try:
        os.remove(HOLD)
    except OSError:
        pass


def hold_active():
    """网关侧读这个：有未过期的本机占用 → 机队让路。"""
    try:
        with open(HOLD, encoding="utf-8") as f:
            d = json.load(f)
        return float(d.get("until") or 0) > time.time(), d
    except Exception:
        return False, {}


def _post(path, payload, timeout):
    req = urllib.request.Request(URL + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def generate(prompt, cls="master", model=None, timeout=90, keep_alive="15m",
             num_ctx=8192, temperature=0.2, think=False, why="", **opts):
    """本机生成。超时/失败返回 ""（调用方必须能接受空结果，不许编造）。"""
    hold(cls, why or prompt[:40])
    t0 = time.time()
    try:
        body = {"model": model or _model(), "prompt": prompt, "stream": False,
                "think": think, "keep_alive": keep_alive,
                "options": dict({"num_ctx": num_ctx, "temperature": temperature}, **opts)}
        out = (_post("/api/generate", body, timeout).get("response") or "").strip()
        _audit({"cls": cls, "op": "generate", "model": body["model"],
                "sec": round(time.time() - t0, 1), "chars": len(out), "why": why})
        return out
    except Exception as e:
        _audit({"cls": cls, "op": "generate", "err": str(e)[:120], "why": why})
        return ""
    finally:
        release()


def embed(text, cls="master", model=None, timeout=5, why=""):
    """嵌入向量。失败抛异常（语义判重的调用方自己做熔断）。"""
    hold(cls, why or "embed", seconds=20)
    t0 = time.time()
    try:
        body = {"model": model or (_cfg().get("embedding") or {}).get("model")
                or "qwen3-embedding:0.6b", "prompt": (text or "")[:800]}
        v = _post("/api/embeddings", body, timeout).get("embedding")
        _audit({"cls": cls, "op": "embed", "sec": round(time.time() - t0, 2), "why": why})
        return v
    finally:
        release()


def status(hours=24):
    """谁在用本机模型：近 N 小时按身份计数 + 当前占用状态。"""
    from collections import Counter
    cut = time.time() - hours * 3600
    by = Counter()
    errs = 0
    try:
        for line in open(AUDIT, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            try:
                if datetime.fromisoformat(r.get("ts")).timestamp() < cut:
                    continue
            except Exception:
                pass
            if r.get("err"):
                errs += 1
            by[r.get("cls") or "?"] += 1
    except FileNotFoundError:
        pass
    on, d = hold_active()
    return {"hours": hours, "calls_by_class": dict(by), "errors": errs,
            "local_hold": on, "hold_detail": d if on else {},
            "rule": "本机(master/local) > 机队(fleet)；机队只经 11435 网关"}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
    elif len(sys.argv) > 1 and sys.argv[1] == "ask":
        print(generate(" ".join(sys.argv[2:]), cls="master", why="cli"))
    else:
        print(__doc__)