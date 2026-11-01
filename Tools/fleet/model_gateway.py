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
MAX_CONC = int(os.environ.get("GATEWAY_MAX_CONC", "3"))
MAX_CTX = int(os.environ.get("GATEWAY_MAX_CTX", "8192"))
AUDIT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "cph4", "fleet", "dispatcher", "events.jsonl")
TOKENS = {}
for pair in (os.environ.get("ROUTER_TOKENS") or "").split(","):
    if ":" in pair:
        n, t = pair.split(":", 1)
        TOKENS[t.strip()] = n.strip()
SEM = threading.Semaphore(MAX_CONC)
STATS = {"ok": 0, "rejected": 0, "inflight": 0, "peak": 0}


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
            return self._json(200, {"ok": True, "max_conc": MAX_CONC, **STATS})
        if self.path.startswith("/stats"):
            return self._json(200, STATS)
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
        opts = body.setdefault("options", {})
        opts["num_ctx"] = min(int(opts.get("num_ctx") or MAX_CTX), MAX_CTX)
        if not SEM.acquire(timeout=30):
            STATS["rejected"] += 1
            audit({"kind": "gateway", "caller": caller, "rejected": "busy"})
            return self._json(429, {"error": "gateway busy, retry"})
        STATS["inflight"] += 1
        STATS["peak"] = max(STATS["peak"], STATS["inflight"])
        t0 = time.time()
        try:
            path = "/api/chat" if self.path.startswith("/v1") else "/api/generate"
            req = urllib.request.Request(UP + path, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as r:
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
    print("[gateway] listening on 0.0.0.0:%d max_conc=%d max_ctx=%d" % (PORT, MAX_CONC, MAX_CTX))
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()