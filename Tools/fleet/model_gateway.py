#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_gateway.py - the one door the fleet uses to borrow bm-m's model.

Raw Ollama on 0.0.0.0:11434 is an unauthenticated memory bomb: any box can open 32 parallel
long-context calls and swap the Mac to death. This proxy adds exactly four things and
nothing else: token auth, a hard concurrency cap (= model slots), a forced context ceiling,
and one audit line per request.

  POST /v1/chat/completions   (OpenAI-compatible passthrough)
  POST /api/generate          (Ollama passthrough)
  GET  /healthz
  GET  /stats

Run:  ROUTER_TOKENS="bm-b:tok1,bm-c:tok2" python3 Tools/fleet/model_gateway.py --port 11435
"""
import json, os, sys, threading, time, urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UP = "http://127.0.0.1:11434"
PORT = int(os.environ.get("GATEWAY_PORT", "11435"))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _local_cfg():
    """本机算力优先级（唯一源=AUTONOMY-CONFIG.json local_priority）。
    CEO 2026-11-05：本机先赋能主控和本机业务，机队排最后。这道网关只管机队那一段。"""
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "AUTONOMY-CONFIG.json"),
                  encoding="utf-8-sig") as f:
            return json.load(f).get("local_priority") or {}
    except Exception:
        return {}


LP = _local_cfg()
MAX_CONC = int(os.environ.get("GATEWAY_MAX_CONC") or LP.get("fleet_max_conc") or 1)
MAX_CTX = int(os.environ.get("GATEWAY_MAX_CTX") or LP.get("fleet_max_ctx") or 8192)
FLEET_TIMEOUT_S = float(LP.get("fleet_timeout_s") or 120)
MIN_FREE_GB = float(LP.get("min_free_gb_for_fleet") or 7.0)
WHITELIST = set(LP.get("fleet_model_whitelist") or [])
AUDIT = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "events.jsonl")
TOKENS = {}
for pair in (os.environ.get("ROUTER_TOKENS") or "").split(","):
    if ":" in pair:
        n, t = pair.split(":", 1)
        TOKENS[t.strip()] = n.strip()
SEM = threading.Semaphore(MAX_CONC)
STATS = {"ok": 0, "rejected": 0, "inflight": 0, "peak": 0}


def free_gb():
    """可用内存（free+inactive+speculative）。与 mac_loadout 同口径，不另立算法。"""
    try:
        import subprocess
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
        vals, page = {}, 16384
        for line in out.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                try:
                    vals[k.strip()] = int(v.strip().rstrip("."))
                except ValueError:
                    pass
        return round((vals.get("Pages free", 0) + vals.get("Pages inactive", 0)
                      + vals.get("Pages speculative", 0)) * page / (1024 ** 3), 1)
    except Exception:
        return -1.0


def audit(row):
    row["ts"] = datetime.now().isoformat(timespec="seconds")
    try:
        with open(AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/healthz"):
            return self._json(200, {"ok": True, "max_conc": MAX_CONC, "free_gb": free_gb(),
                                    "ranking": "本机直连优先 > 机队借用", **STATS})
        if self.path.startswith("/stats"):
            return self._json(200, {"max_conc": MAX_CONC, "max_ctx": MAX_CTX,
                                    "min_free_gb": MIN_FREE_GB,
                                    "fleet_timeout_s": FLEET_TIMEOUT_S,
                                    "whitelist": sorted(WHITELIST),
                                    "free_gb": free_gb(), **STATS})
        self._json(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        auth = (self.headers.get("Authorization") or "").replace("Bearer ", "").strip()
        caller = TOKENS.get(auth)
        if not caller:
            STATS["rejected"] += 1
            return self._json(401, {"error": "bad or missing token"})
        try:
            body = json.loads(raw or b"{}")
        except Exception:
            return self._json(400, {"error": "bad json"})
        model = str(body.get("model") or "")
        if WHITELIST and model not in WHITELIST:
            STATS["rejected"] += 1
            audit({"kind": "gateway", "caller": caller, "model": model,
                   "rejected": "model-not-whitelisted"})
            return self._json(403, {"error": "model not allowed for fleet: %s" % model,
                                    "allowed": sorted(WHITELIST),
                                    "why": "本机模型先服务主控；机队只许借常驻/嵌入这些轻档"})
        # 本机让路信号（CEO 2026-11-05：本机先赋能主控，然后才是机队）。
        # 主控/本机业务经 local_model 调用时会写 HOLD；机队此时一律让路，
        # 等这口气用完（最长 45s，自动过期，不留死锁）。
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import local_model as _lm
            _held, _hd = _lm.hold_active()
        except Exception:
            _held, _hd = False, {}
        if _held:
            STATS["rejected"] += 1
            audit({"kind": "gateway", "caller": caller, "model": model,
                   "rejected": "local-priority", "hold": _hd.get("cls")})
            return self._json(429, {"error": "local priority in effect, retry",
                                    "who": _hd.get("cls"),
                                    "why": "本机主控/业务正在用模型"})
        _free = free_gb()
        if MIN_FREE_GB and _free >= 0 and _free < MIN_FREE_GB:
            STATS["rejected"] += 1
            audit({"kind": "gateway", "caller": caller, "model": model,
                   "rejected": "low-mem", "free_gb": _free})
            return self._json(503, {"error": "local memory reserved for master/office",
                                    "free_gb": _free, "need_gb": MIN_FREE_GB})
        opts = body.setdefault("options", {})
        opts["num_ctx"] = min(int(opts.get("num_ctx") or MAX_CTX), MAX_CTX)
        if not SEM.acquire(timeout=15):
            STATS["rejected"] += 1
            audit({"kind": "gateway", "caller": caller, "rejected": "busy"})
            return self._json(429, {"error": "gateway busy, retry"})
        STATS["inflight"] += 1
        STATS["peak"] = max(STATS["peak"], STATS["inflight"])
        t0 = time.time()
        try:
            path = "/api/chat" if self.path.startswith("/v1") else "/api/generate"
            # 嵌入是机队最想借的能力（判重/检索），必须也能过这道门；原来只映射
            # generate/chat，于是借嵌入的请求被当生成转过去，Ollama 回 400。
            for _p in ("/api/embeddings", "/api/embed"):
                if self.path.startswith(_p):
                    path = _p
                    break
            req = urllib.request.Request(UP + path, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=FLEET_TIMEOUT_S) as r:
                out = r.read()
            STATS["ok"] += 1
            audit({"kind": "gateway", "caller": caller, "model": body.get("model"),
                   "sec": round(time.time() - t0, 1), "ctx": opts["num_ctx"]})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
        except Exception as e:
            audit({"kind": "gateway", "caller": caller, "error": str(e)[:120]})
            self._json(502, {"error": str(e)[:120]})
        finally:
            STATS["inflight"] -= 1
            SEM.release()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if "--port" in sys.argv:
        PORT = int(sys.argv[sys.argv.index("--port") + 1])
    if not TOKENS:
        print("[gateway] WARN: no ROUTER_TOKENS set -> every request will be rejected")
    print("[gateway] 优先级：本机直连 > 机队借用；机队 max_conc=%d max_ctx=%d "
          "deadline=%.0fs min_free=%.1fGB whitelist=%s"
          % (MAX_CONC, MAX_CTX, FLEET_TIMEOUT_S, MIN_FREE_GB, ",".join(sorted(WHITELIST)) or "-"))
    print("[gateway] listening on 0.0.0.0:%d" % PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()