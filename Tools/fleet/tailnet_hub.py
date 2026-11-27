#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tailnet_hub.py - 主控侧的 tailnet 直收站：机队状态与产物高频直达，不经过 git。

为什么（CEO 2026-11-06「不能机队 tailscal 局域网之间高频同步吗？」）：
  实测 git 是瓶颈：远端推主干长期 rejected/分叉，产物留在对方盘上，主控只能看到
  NATS 里的"FAILED"三个字。Tailscale 是直连局域网，延迟毫秒级；用它做状态与产物
  的实时通道，git 只当归档，才是这套机队该有的形态。

端点（只绑 tailnet + 回环，无写操作面）：
  GET  /health                     → {ok, node, ts}
  POST /status   {node,job,state,out_bytes,deliverable_bytes,rc,error_class,...}
                                   → state/lane-status/<node>.json（覆盖=最新）
  POST /artifact {node,job,path,size,sha,data(base64,<=4MB)}
                                   → state/artifacts/<node>/<basename>（只收小件；
                                     大媒体走 git 分支/移动盘，不在这条通道上搬）

用法：
  python3 Tools/fleet/tailnet_hub.py --port 8791 --host 0.0.0.0
Exit: 常驻
"""
import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ST = os.path.join(ROOT, "cph4", "fleet", "state")
MAX_ART = 4 * 1024 * 1024
STATS = {"status": 0, "artifact": 0, "rejected": 0}


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


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
        if self.path.startswith("/health"):
            return self._json(200, {"ok": True, "node": "bm-m",
                                    "ts": datetime.now().isoformat(timespec="seconds"),
                                    **STATS})
        self._json(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_ART + 65536:
            STATS["rejected"] += 1
            return self._json(413, {"error": "too large"})
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            STATS["rejected"] += 1
            return self._json(400, {"error": "bad json"})
        node = str(body.get("node") or "?")
        if self.path.startswith("/status"):
            body["received_at"] = datetime.now().isoformat(timespec="seconds")
            _write(os.path.join(ST, "lane-status", node + ".json"), body)
            if body.get("job") and body.get("rc") is not None:
                _write(os.path.join(ST, "remote-receipts",
                                    "%s-%s.json" % (body.get("job"), node)), body)
            STATS["status"] += 1
            return self._json(200, {"ok": True})
        if self.path.startswith("/artifact"):
            data = body.get("data") or ""
            if not data:
                STATS["rejected"] += 1
                return self._json(400, {"error": "no data"})
            try:
                raw = base64.b64decode(data)
            except Exception:
                STATS["rejected"] += 1
                return self._json(400, {"error": "bad base64"})
            if len(raw) > MAX_ART:
                STATS["rejected"] += 1
                return self._json(413, {"error": "artifact too large"})
            name = os.path.basename(str(body.get("path") or body.get("job") or "a.bin"))
            d = os.path.join(ST, "artifacts", node)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name)
            with open(p, "wb") as f:
                f.write(raw)
            sha = hashlib.sha256(raw).hexdigest()[:16]
            _write(p + ".meta.json", {"node": node, "job": body.get("job"),
                                      "path": body.get("path"), "size": len(raw),
                                      "sha256_16": sha,
                                      "ts": datetime.now().isoformat(timespec="seconds")})
            STATS["artifact"] += 1
            return self._json(200, {"ok": True, "stored": p, "sha256_16": sha})
        STATS["rejected"] += 1
        self._json(404, {"error": "not found"})

    def log_message(self, *a):
        pass


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8791)
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args(argv)
    ThreadingHTTPServer((a.host, a.port), H).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))