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
GATEWAY_DEFAULT = "http://100.75.133.10:8792"
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


def _is_loopback(url):
    return any(h in url for h in LOOPBACK)


def generate(prompt, model=None, endpoint=None, timeout=120, cls=None, think=False,
             num_predict=None, max_age_s=60):
    """返回 {"ok","text","why","rc"}。rc: 0 成功 / 3 缺令牌(缺料) / 1 真故障 / 4 熔断中。

    cls 用来选座位（与 LOCAL-MODEL-POLICY.duties 对齐），未知 cls 走主力档，
    **绝不默认拉大的**（35B 一驻留就 swap）。
    """
    url = base_for(endpoint)
    if not model:
        model = _model_for(cls)
    if not think:
        pass
    now = time.time()
    if _COOLDOWN.get(url, 0) > now:
        return {"ok": False, "rc": 4, "text": "",
                "why": "熔断中：%ds 后再试（避免空打网关）" % int(_COOLDOWN[url] - now)}

    tok = token()
    if not tok and not _is_loopback(url) and not _is_tailnet(url):
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
        return (duties.get("resident") or {}).get("model") or "qwen3.5:4b-mlx"
    except Exception:
        return "qwen3.5:4b-mlx"


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
    r = generate(a.prompt, endpoint=a.endpoint, cls=a.cls)
    print("[llm-client] rc=%d ok=%s %s" % (r["rc"], r["ok"], r["text"] or r["why"]))
    return r["rc"]


if __name__ == "__main__":
    raise SystemExit(main())