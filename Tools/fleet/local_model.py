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
# 端点阶梯（2026-11-11 CEO 令：算力大脑是机队本地能力中心，主控只做轻量赋能）：
#   显式环境变量 > MODEL-COMPUTE.json 的 gateways（按 order）> 本机 11434
# 不做这一步的话，所有 agent 的推理都会压在 MacBook 的 32G 统一内存上。
COMPUTE = os.path.join(ROOT, "cph4", "fleet", "MODEL-COMPUTE.json")
URL = os.environ.get("OLLAMA_URL") or ""          # 显式覆盖；空=走阶梯
HEALTH_TTL_S = 30
_HEALTH = {"ts": 0.0, "url": ""}
HOLD_TTL_S = 45          # 主控一次生成可能在 30-60s，给足余量；过期自动失效，不留死锁
DEFAULT_MODEL = "\x00"


def local_station():
    """本机是哪台：FLEET_STATION 环境变量 > hostname 匹配 STATIONS > None。"""
    st = os.environ.get("FLEET_STATION")
    if st:
        return st
    try:
        import socket
        host = socket.gethostname().lower()
        with open(os.path.join(ROOT, "cph4", "fleet", "STATIONS.json"), encoding="utf-8") as f:
            for s in json.load(f).get("stations") or []:
                h = (s.get("hostname") or "").lower()
                if h and (h == host or host.startswith(h.split(".")[0])):
                    return s.get("id")
    except Exception:
        pass
    return None


def gateways():
    """按 order 返回候选端点。显式 URL 优先。
    阶梯=本机(0) -> 算力大脑(1) -> 主控(2)：本地闭环优先，升级才出机器。"""
    if URL:
        return [URL]
    try:
        with open(COMPUTE, encoding="utf-8") as f:
            gs = json.load(f).get("gateways") or []
        out = [g["url"] for g in sorted(gs, key=lambda g: g.get("order", 99)) if g.get("url")]
        return out or ["http://127.0.0.1:11434"]
    except Exception:
        return ["http://127.0.0.1:11434"]


def _alive(url, timeout=1.2):
    try:
        with urllib.request.urlopen(url + "/api/tags", timeout=timeout) as r:
            r.read(64)
        return True
    except Exception:
        return False


# 端点"标签活着但生成长挂"时（2026-11-11 压测实锚），探活永远骗过判定：
# 旧实现只会在调用方 timeout 上白等满再返回空串，不会切备用端点。
# 所以调用失败一次就把该端点降级 BAD_TTL_S 秒，期间选端点跳过它。
_BAD = {}
BAD_TTL_S = 120


def _demote(url, secs=BAD_TTL_S):
    if url:
        _BAD[url] = time.time() + secs


def _healthy(url):
    return _BAD.get(url, 0) <= time.time()


def _next_alive(exclude=""):
    """跳过已降级/刚失败的端点，返回下一个探活通过的端点；没有则空串。"""
    for u in gateways():
        if u == exclude or not _healthy(u):
            continue
        if _alive(u):
            return u
    return ""


def endpoint():
    """选一个活着的端点，30s 内复用结果（避免每次调用都探活）。
    全都探不通时返回最后一个候选，让调用方拿到真实错误而不是假装成功。"""
    now = time.time()
    if _HEALTH["url"] and now - _HEALTH["ts"] < HEALTH_TTL_S and _healthy(_HEALTH["url"]):
        return _HEALTH["url"]
    gs = gateways()
    order = [u for u in gs if _healthy(u)] or gs
    for u in order:
        if _alive(u):
            _HEALTH.update({"ts": now, "url": u})
            return u
    fallback = order[-1] if order else "http://127.0.0.1:11434"
    _HEALTH.update({"ts": now, "url": fallback})
    return fallback


def _cfg():
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                  encoding="utf-8-sig") as f:
            return (json.load(f).get("duties") or {}).get("resident") or {}
    except Exception:
        return {}


# 座位路由（2026-11-07 CEO「不要只加载一个大的」）：任务按难度分三档，别用大炮打蚊子，
# 也别拿 1.7B 去干需要 8B 的判断。座位定义在 LOCAL-MODEL-POLICY.duties。
SEAT_BY_CLS = {
    "triage": "triage", "class": "triage", "classify": "triage", "tag": "triage",
    "quick": "triage", "filter": "triage",
    "deep": "big", "review": "big", "code": "big",
    "rewrite": "big", "longform": "big", "creative": "big",
}


def _duties():
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                  encoding="utf-8-sig") as f:
            return json.load(f).get("duties") or {}
    except Exception:
        return {}


def seat_of(cls):
    return SEAT_BY_CLS.get(str(cls or "").lower(), "resident")


def _model():
    if DEFAULT_MODEL != "\x00":
        return DEFAULT_MODEL
    return _cfg().get("model") or "qwen3.5:4b-mlx"


def _unload(model):
    """把某个模型立刻卸掉（keep_alive=0），失败静默——不让清理动作影响主流程。"""
    try:
        _post("/api/generate", {"model": model, "keep_alive": 0}, 30)
    except Exception:
        try:
            import urllib.request as _u
            req = _u.Request(endpoint() + "/api/generate", method="POST",
                             data=json.dumps({"model": model, "keep_alive": 0}).encode())
            req.add_header("Content-Type", "application/json")
            _u.urlopen(req, timeout=30).read()
        except Exception:
            pass


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
    req = urllib.request.Request(endpoint() + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def generate(prompt, cls="master", model=None, timeout=90, keep_alive="15m",
             num_ctx=8192, temperature=0.2, think=False, why="", **opts):
    """本机生成。超时/失败返回 ""（调用方必须能接受空结果，不许编造）。"""
    hold(cls, why or prompt[:40])
    t0 = time.time()
    seat = seat_of(cls)
    cfg = _duties().get(seat) or {}
    if model is None:
        model = cfg.get("model") or _model()
    # keep_alive 的 0 是"用完即卸"的合法值，不能用 `or` 取默认值——
    # 假值会把 0 吞成 15m/30m，模型就在没活时常驻吃内存（2026-11-11 CEO「不能闲着还常驻」）。
    kv = cfg.get("keep_alive")
    if seat == "triage":
        keep_alive = keep_alive if kv is None else kv
        num_ctx = min(int(cfg.get("num_ctx") or num_ctx), num_ctx)
    elif seat == "big":
        keep_alive = "30m" if kv is None else kv
        num_ctx = min(int(cfg.get("num_ctx") or 8192), num_ctx)
    else:
        keep_alive = keep_alive if kv is None else kv
    try:
        body = {"model": model, "prompt": prompt, "stream": False,
                "think": think, "keep_alive": keep_alive,
                "options": dict({"num_ctx": num_ctx, "temperature": temperature}, **opts)}
        out = (_post("/api/generate", body, timeout).get("response") or "").strip()
        _audit({"cls": cls, "seat": seat, "op": "generate", "model": body["model"],
                "sec": round(time.time() - t0, 1), "chars": len(out), "why": why})
        return out
    except Exception as e:
        # 探活只测 /api/tags，端点可能"标签活着、生成长挂"：降级它并换备用端点重试一次，
        # 否则每次调用都要白等满 timeout 再返回空串（2026-11-11 压测实锚）。
        dead = endpoint()
        _demote(dead)
        alt = _next_alive(exclude=dead)
        if alt:
            left = max(3, int(timeout - (time.time() - t0)))
            try:
                out = (_post("/api/generate", body, left).get("response") or "").strip()
                _audit({"cls": cls, "seat": seat, "op": "generate-retry", "model": body["model"],
                        "sec": round(time.time() - t0, 1), "chars": len(out),
                        "from": dead, "to": alt, "why": why})
                return out
            except Exception as e2:
                _demote(alt)
                _audit({"cls": cls, "op": "generate-retry", "err": str(e2)[:120],
                        "endpoint": alt, "why": why})
        _audit({"cls": cls, "op": "generate", "err": str(e)[:120],
                "endpoint": dead, "why": why})
        return ""
    finally:
        release()


_EMB_CACHE = {}
_EMB_CACHE_PATH = None


def _emb_cache_path():
    global _EMB_CACHE_PATH
    if _EMB_CACHE_PATH is None:
        import os as _os
        root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        _EMB_CACHE_PATH = _os.path.join(root, "cph4", "fleet", "state", "embed-cache.json")
    return _EMB_CACHE_PATH


def _emb_cached(key):
    """同一段文本的向量只算一次（2026-11-05 实测：一天 3.6 万次 embeddings，全是重复算同一批卡）。"""
    global _EMB_CACHE
    if not _EMB_CACHE:
        try:
            import json as _json
            _EMB_CACHE = _json.load(open(_emb_cache_path(), encoding="utf-8"))
        except Exception:
            _EMB_CACHE = {}
    return _EMB_CACHE.get(key)


def _emb_store(key, vec, cap=6000):
    global _EMB_CACHE
    try:
        import json as _json
        _EMB_CACHE[key] = vec
        if len(_EMB_CACHE) > cap:                      # 简单封顶：丢最早的一半
            for k in list(_EMB_CACHE)[: len(_EMB_CACHE) - cap // 2]:
                _EMB_CACHE.pop(k, None)
        tmp = _emb_cache_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            _json.dump(_EMB_CACHE, f, ensure_ascii=False)
        import os as _os
        _os.replace(tmp, _emb_cache_path())
    except Exception:
        pass


def embed(text, cls="master", model=None, timeout=5, why=""):
    """嵌入向量。失败抛异常（语义判重的调用方自己做熔断）。

    带内容哈希缓存：重复文本（同一批卡在多轮判重里反复出现）直接命中，不再打模型。
    """
    import hashlib as _hl
    key = _hl.sha256(((model or "") + "|" + (text or "")[:800]).encode("utf-8")).hexdigest()[:24]
    hit = _emb_cached(key)
    if hit:
        _audit({"cls": cls, "op": "embed-cache-hit", "why": why})
        return hit
    hold(cls, why or "embed", seconds=20)
    t0 = time.time()
    try:
        body = {"model": model or (_cfg().get("embedding") or {}).get("model")
                or "qwen3-embedding:0.6b", "prompt": (text or "")[:800]}
        v = _post("/api/embeddings", body, timeout).get("embedding")
        _audit({"cls": cls, "op": "embed", "sec": round(time.time() - t0, 2), "why": why})
        if v:
            _emb_store(key, v)
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