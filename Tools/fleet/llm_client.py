#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llm_client.py - 机队调本地大模型的唯一客户端（令牌/端点/退避都在这里）。

为什么要有它（2026-11-08 实测）：
  · 网关 8792 今天被打了 835 次，**成功 6 次、被拒 817 次**，原因几乎全是
    `bad or missing X-Flux-Token`；而全仓 `token_env: FLUX_LLM_TOKEN` 只有 4 处
    **声明**、零个读取者 —— 配置是装饰品，所以"机队能调本地大模型"一直没通电。
  · 更糟的是没有钥匙时它仍然每 40 秒重试一次，一晚上空打 800 次：
    既刷不出结果，又把网关日志变成噪音，还让人误判"网关坏了"。

三条纪律（与 llm_selftest 同一口径）：
  1) 没令牌=缺料(rc=3)，不是故障；**先本地判、不发请求**，绝不空打；
  2) 端点解析顺序：参数 → FLUX_LLM_BASE → 策略/节点声明 → 本机回环；
     非回环一律走网关（裸 11434 无认证无白名单，会把常驻主力顶掉）；
  3) 同一个进程里失败过一次就退避 300s（熔断），避免把网关刷成日志洪水。

用法：
  from llm_client import generate
  r = generate("写一句理由", cls="resident")     # r = {"ok":bool,"text":..,"why":..,"rc":..}
命令行自检：
  python3 Tools/fleet/llm_client.py --probe
"""
import json
import os
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOKEN_FILE = os.path.expanduser("~/.fluxgroup-llm-token")
# 2026-11-18 D-20261117-03：8792 已不是网关（现为 BigCompute resident_qa_server 的
# qwen3.6-35b QA 服务），默认停指该端口，改本地优先；找不到网关时如实报 GATEWAY-ABSENT。
GATEWAY_DEFAULT = "http://127.0.0.1:11434"
LOOPBACK = ("127.0.0.1", "localhost", "::1")
_COOLDOWN = {}          # base -> 解冻时刻
COOLDOWN_S = 300


def _is_tailnet(url):
    """2026-11-10 CEO 选 B：Tailscale 内网免令牌。100.64.0.0/10 视为可信邻居。"""
    try:
        import ipaddress
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        return ipaddress.ip_address(host) in ipaddress.ip_network("100.64.0.0/10")
    except Exception:
        return False


def token():
    """令牌来源：环境变量优先（便于一次性注入），其次令牌文件（权限 600、不入 git）。"""
    v = (os.environ.get("FLUX_LLM_TOKEN") or "").strip()
    if v:
        return v
    try:
        return open(os.path.expanduser(os.environ.get("FLUX_LLM_TOKEN_FILE") or TOKEN_FILE)).read().strip()
    except Exception:
        return ""


def base_for(endpoint=None):
    """端点解析：显式参数 > 环境变量 > 本机回环。非回环一律视为网关。"""
    if endpoint:
        return endpoint.rstrip("/")
    env = (os.environ.get("FLUX_LLM_BASE") or "").strip()
    if env:
        return env.rstrip("/")
    return "http://127.0.0.1:11434"


# 网关端口：走网关就必须带 X-Flux-Token（2026-11-08 实锚：一天被拒 830 次）。
# 2026-11-18：8792 已降级为他司 QA 服务，从网关端口表移除——「端口活着」不等于
# 「网关活着」，是否为网关一律由 probe_service() 自证身份判定。
GATEWAY_PORTS = set()


def _port_of(url):
    try:
        from urllib.parse import urlparse
        return urlparse(url).port
    except Exception:
        return None


def _needs_token(url):
    """需要令牌的判定：非回环，且（不是 tailnet 或 是网关端口）。"""
    if _is_loopback(url):
        return False
    if _is_tailnet(url) and _port_of(url) not in GATEWAY_PORTS:
        return False
    return True


def _is_loopback(url):
    return any(h in url for h in LOOPBACK)


def probe_service(url=None, timeout=5):
    """探活须自证身份（D-20261117-03）：/health 必须自报网关标识才算 available。

    返回 {"verdict": "GATEWAY-OK"|"NOT-GATEWAY"|"GATEWAY-ABSENT"|"UNAVAILABLE", ...}
    只看端口是否活着会把「他司 QA 服务」当成网关，故非 gateway 标识一律不计可用。
    """
    url = (url or base_for()).rstrip("/")
    try:
        with urllib.request.urlopen(url + "/health", timeout=timeout) as r:
            raw = r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 端口在答话但没有 /health 身份面：服务活着≠网关活着。
            return {"verdict": "NOT-GATEWAY", "url": url, "identity": "no /health (404)",
                    "why": "端口活着但不是网关，不计入 available"}
        return {"verdict": "UNAVAILABLE", "url": url, "why": "http %d" % e.code}
    except Exception as e:
        return {"verdict": "GATEWAY-ABSENT", "url": url,
                "why": "%s: %s" % (type(e).__name__, str(e)[:60])}
    marker = ""
    try:
        d = json.loads(raw or "{}")
        marker = " ".join(str(d.get(k) or "") for k in ("service", "name", "role", "gateway"))
    except Exception:
        marker = raw[:200]
    low = marker.lower()
    if "gateway" in low or "llm_gateway" in low:
        return {"verdict": "GATEWAY-OK", "url": url, "identity": marker[:80]}
    return {"verdict": "NOT-GATEWAY", "url": url, "identity": (marker or raw[:80])[:80],
            "why": "端口活着但不是网关，不计入 available"}


def generate(prompt, model=None, endpoint=None, timeout=120, cls=None, think=False,
             num_predict=None, max_age_s=60):
    """返回 {"ok","text","why","rc"}。rc: 0 成功 / 3 缺令牌(缺料) / 1 真故障 / 4 熔断中。

    cls 用来选座位（与 LOCAL-MODEL-POLICY.duties 对齐），未知 cls 走主力档，
    **绝不默认拉大的**（35B 一驻留就 swap）。
    """
    url = base_for(endpoint)
    if not model:
        model = _model_for(cls)
        if any(h in url for h in LOOPBACK):
            model = _resolve_local(model)
    if not think:
        pass
    now = time.time()
    if _COOLDOWN.get(url, 0) > now:
        return {"ok": False, "rc": 4, "text": "",
                "why": "熔断中：%ds 后再试（避免空打网关）" % int(_COOLDOWN[url] - now)}

    tok = token()
    if not tok and _needs_token(url):
        # 缺料就地判死：不发请求、不进熔断、不计故障
        return {"ok": False, "rc": 3, "text": "",
                "why": "本机没有令牌（%s 或 FLUX_LLM_TOKEN），不走网关" % TOKEN_FILE}

    body = {"model": model, "prompt": prompt, "stream": False, "think": bool(think)}
    if num_predict:
        body["options"] = {"num_predict": int(num_predict)}
    req = urllib.request.Request(url + "/api/generate", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    if tok:
        req.add_header("X-Flux-Token", tok)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode() or "{}")
        text = (d.get("response") or "").strip()
        if not text:
            _COOLDOWN[url] = now + COOLDOWN_S
            return {"ok": False, "rc": 1, "text": "", "why": "空回复（模型未产出）"}
        return {"ok": True, "rc": 0, "text": text, "why": ""}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read().decode() or "{}").get("error", "")
        except Exception:
            pass
        if e.code == 401:
            return {"ok": False, "rc": 3, "text": "",
                    "why": "网关拒绝令牌（本机串与主控不一致）"}
        if e.code == 403:
            return {"ok": False, "rc": 1, "text": "",
                    "why": "档位不在白名单：%s（改座位，不要改网关）" % detail[:60]}
        _COOLDOWN[url] = now + COOLDOWN_S
        return {"ok": False, "rc": 1, "text": "", "why": "http %d %s" % (e.code, detail[:60])}
    except Exception as e:
        _COOLDOWN[url] = now + COOLDOWN_S
        return {"ok": False, "rc": 1, "text": "",
                "why": "%s: %s" % (type(e).__name__, str(e)[:80])}


def _model_for(cls):
    """座位 → 模型，读 LOCAL-MODEL-POLICY 单一源；取不到就用主力档，不猜大的。"""
    try:
        d = json.load(open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                           encoding="utf-8"))
        duties = d.get("duties") or {}
        seat = cls if isinstance(cls, str) and cls in duties else "resident"
        m = (duties.get(seat) or {}).get("model")
        if m:
            return m
        return (duties.get("resident") or {}).get("model") or "qwen3.5:4b"
    except Exception:
        return "qwen3.5:4b"


_LOCAL_MODELS = {}


def _local_models():
    """本机 ollama 模型名集合（进程内缓存一次）。查不到=None，不参与判定，避免误伤远端网关。"""
    if "v" in _LOCAL_MODELS:
        return _LOCAL_MODELS["v"]
    try:
        import subprocess
        out = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        names = {ln.split()[0] for ln in (out.stdout or "").splitlines()[1:] if ln.split()}
        _LOCAL_MODELS["v"] = names or None
    except Exception:
        _LOCAL_MODELS["v"] = None
    return _LOCAL_MODELS["v"]


def _resolve_local(model):
    """座位模型名一致性闸（2026-11-18 迭代项）：名字不在本机 ollama list 就换同族可用档，
    并印 MODEL-SUBSTITUTED——禁止静默用不存在的模型空打（此前 qwen3.5:4b-mlx 即此病）。"""
    names = _local_models()
    if not names or model in names:
        return model
    for cand in ("qwen3.5:4b", "qwen3.5:9b", "qwen3.5:2b"):
        if cand in names:
            print("[llm-client] MODEL-SUBSTITUTED %s -> %s" % (model, cand))
            return cand
    print("[llm-client] MODEL-SUBSTITUTED %s -> (本机无可替代档)" % model)
    return model


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--prompt", default="只回答两个字：收到")
    ap.add_argument("--endpoint", default="")
    ap.add_argument("--cls", default="resident")
    a = ap.parse_args()
    if not a.probe:
        r = generate(a.prompt, endpoint=a.endpoint, cls=a.cls)
        print(json.dumps(r, ensure_ascii=False))
        return r["rc"]
    t = token()
    print("[llm-client] base=%s token=%s model=%s"
          % (base_for(a.endpoint), ("present len=%d" % len(t)) if t else "MISSING",
             _model_for(a.cls)))
    print("[llm-client] identity=%s" % json.dumps(probe_service(a.endpoint), ensure_ascii=False))
    r = generate(a.prompt, endpoint=a.endpoint, cls=a.cls)
    print("[llm-client] rc=%d ok=%s %s" % (r["rc"], r["ok"], r["text"] or r["why"]))
    return r["rc"]


if __name__ == "__main__":
    raise SystemExit(main())