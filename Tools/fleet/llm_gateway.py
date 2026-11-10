#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llm_gateway.py - 本地大模型对机队的唯一入口（带认证/白名单/并发/驻留策略）。

CEO 2026-11-08：「我希望机队也能调用你的本地大模型能力」。

为什么要这道门（不是直接把 11434 开给机队）：
  · ollama 裸端口无认证：tailnet 上任何设备都能请求 35B（24GB）→ 主控直接换页；
  · 也无白名单：机队里写死的老模型名（qwen3:4b-instruct / qwen3.5:4b）会把对照档
    拉起来顶掉常驻主力——这正是"三模型驻留 10.4GB"那类事故的入口；
  · 还无驻留策略：远端一句 keep_alive=30m 就能把模型长期钉在内存里。
所以：**11434 只绑回环，对外只有 8792 这道门**，门里做四件事：
  1) 令牌认证（X-Flux-Token，与 ~/.fluxgroup-llm-token 比对）；
  2) 模型白名单取自 LOCAL-MODEL-POLICY.json（只允许策略里声明的模型）；
  3) keep_alive 与 num_ctx 由策略强制覆盖（远端无权钉模型）；
  4) 并发上限（默认 2，超出 429），并记账 state/llm-gateway.jsonl。

用法：
  python3 Tools/fleet/llm_gateway.py --host 0.0.0.0 --port 8792
退出码：0 正常；2 配置/令牌缺失（不许裸奔启动）。
"""
import argparse
import json
import os
import ipaddress
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
POLICY = os.path.join(F, "LOCAL-MODEL-POLICY.json")
UPSTREAM = "http://127.0.0.1:11434"
TOKEN_FILE = os.path.expanduser("~/.fluxgroup-llm-token")
MAX_CONCURRENT = 2
PASS_PATHS = ("/api/generate", "/api/chat", "/api/embed", "/api/embeddings", "/api/tags")
_SEM = threading.BoundedSemaphore(MAX_CONCURRENT)


def policy():
    try:
        with open(POLICY, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def allowlist():
    """策略里声明过的模型才算合法。座位 -> (model, keep_alive, num_ctx)。"""
    d = policy()
    out = {}
    # 封存档与对照档绝不放给机队：35B 一驻留就 swap 24GB；对照档（qwen3:4b-instruct）
    # 一被拉起来就顶掉常驻主力——这两类正是"多模型挤在一起"的入口。
    DENY_SEATS = {"sealed", "alternative"}
    for seat, cfg in (d.get("duties") or {}).items():
        if seat in DENY_SEATS or not isinstance(cfg, dict):
            continue      # duties 里混进说明性字符串时不许把网关搞崩（本轮实锚）
        m = cfg.get("model")
        if not m:
            continue
        # keep_alive=0 是"用完即卸"的合法策略；`or "5m"` 会把 0 变成 5 分钟钉住模型，
        # 与 model_plan 的 E-KEEPALIVE 判据打架（阶段每轮报红）
        _ka = cfg.get("keep_alive")
        _ka = "0" if _ka in (0, "0") else str(_ka if _ka is not None else "5m")
        out[m] = {"seat": seat,
                  "keep_alive": _ka,
                  "num_ctx": int(cfg.get("num_ctx") or 8192)}
    # 矩阵里出现但策略没写的档也拦（宁可拒绝，不让机队拉野模型）
    return out


def token():
    try:
        return open(TOKEN_FILE).read().strip()
    except Exception:
        return ""


def log(row):
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(os.path.join(STATE, "llm-gateway.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


class H(BaseHTTPRequestHandler):
    server_version = "FluxLLMGateway/1"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _deny(self, code, why, model=None):
        # 记 UA 与端口：2026-11-08 有 830 次无令牌调用，只看 IP 分不清是哪个进程，
        # 补上 UA 后下次就能点名（谁在空打网关，一目了然）。
        log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "deny": why,
             "model": model, "caller": self.client_address[0],
             "port": self.client_address[1] if len(self.client_address) > 1 else None,
             "path": self.path.split("?")[0],
             "ua": (self.headers.get("User-Agent") or "")[:80]})
        self._send(code, {"error": why})

    def _trusted_peer(self):
        """2026-11-10 CEO 选 B：Tailscale 内网（100.64.0.0/10）与本机回环免令牌。
        只认这两个范围，公网/普通局域网仍然要令牌。"""
        try:
            ip = ipaddress.ip_address(self.client_address[0])
        except Exception:
            return False
        if ip.is_loopback:
            return True
        return ip in ipaddress.ip_network("100.64.0.0/10")

    def do_GET(self):
        if self.path.split("?")[0] not in PASS_PATHS:
            return self._deny(404, "path not allowed")
        if (token() and self.headers.get("X-Flux-Token") != token()
                and not self._trusted_peer()):
            return self._deny(401, "bad or missing X-Flux-Token")
        try:
            with urllib.request.urlopen(UPSTREAM + self.path, timeout=15) as r:
                self._send(200, json.loads(r.read().decode() or "{}"))
        except Exception as e:
            self._deny(502, "upstream: %s" % str(e)[:80])

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in PASS_PATHS:
            return self._deny(404, "path not allowed")
        if (token() and self.headers.get("X-Flux-Token") != token()
                and not self._trusted_peer()):
            return self._deny(401, "bad or missing X-Flux-Token")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n).decode() or "{}")
        except Exception:
            return self._deny(400, "bad json")

        model = str(body.get("model") or "")
        allow = allowlist()
        if model not in allow:
            # 只报允许清单的前几个，避免把整张表吐给远端
            return self._deny(403, "model not allowed; use one of: %s"
                              % ",".join(sorted(allow)[:4]), model)
        spec = allow[model]
        # 策略强制：远端无权改 keep_alive / num_ctx（否则一句 30m 就把模型钉死）
        body["keep_alive"] = spec["keep_alive"]
        opts = body.get("options") or {}
        opts["num_ctx"] = min(int(opts.get("num_ctx") or spec["num_ctx"]), spec["num_ctx"])
        body["options"] = opts
        body.setdefault("stream", False)

        if not _SEM.acquire(blocking=False):
            return self._deny(429, "busy: %d concurrent calls in flight" % MAX_CONCURRENT, model)
        t0 = time.time()
        try:
            req = urllib.request.Request(UPSTREAM + path,
                                         data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = r.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "path": path, "model": model,
                 "seat": spec["seat"], "caller": self.client_address[0],
                 "sec": round(time.time() - t0, 1), "bytes": len(raw)})
        except urllib.error.HTTPError as e:
            # 把上游的真实错误体带出来，否则只剩 "500 Internal Server Error" 无处可查
            try:
                det = e.read().decode()[:200]
            except Exception:
                det = ""
            self._deny(502, "upstream %s: %s" % (e.code, det), model)
        except Exception as e:
            self._deny(502, "upstream: %s" % str(e)[:100], model)
        finally:
            _SEM.release()

    def log_message(self, *a):
        pass


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8792)
    a = ap.parse_args(argv)

    if not token():
        print("[llm-gateway] 拒绝裸奔：缺 %s（不设令牌就等于把模型白送出去）" % TOKEN_FILE)
        return 2
    if not allowlist():
        print("[llm-gateway] 拒绝启动：LOCAL-MODEL-POLICY 里没有可放出的模型")
        return 2
    srv = ThreadingHTTPServer((a.host, a.port), H)
    print("[llm-gateway] http://%s:%d -> %s · 允许 %d 个模型"
          % (a.host, a.port, UPSTREAM, len(allowlist())))
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))