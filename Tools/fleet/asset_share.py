#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_share.py - 只读素材共享服务（执行机自取用）。

绑定回环，由 asset_relay.py 转发到内网；需 X-Flux-Token。
只暴露 /assets(移动盘 FluxAssets) 与 /media(仓内 media) 两个白名单根。
"""
import argparse
import json
import os
import posixpath
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _asset_root():
    """资产根按 ASSET-STORE.json 解析（primary=本机固定盘）。
    以前写死 /Volumes/移动硬盘/FluxAssets，盘一拔这个服务就对外提供空目录。"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import vault
        return vault.store_roots()[0]
    except Exception:
        return os.path.expanduser("~/FluxAssets")


ROOTS = {"/assets": _asset_root(),
         "/media": os.path.join(ROOT_REPO, "media")}


def token():
    t = os.environ.get("FLUX_ASSET_TOKEN")
    if t:
        return t.strip()
    p = os.path.expanduser("~/.fluxgroup-asset-token")
    return open(p).read().strip() if os.path.exists(p) else ""


class H(BaseHTTPRequestHandler):
    server_version = "FluxAssetShare/1"

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _resolve(self, path):
        u = urllib.parse.urlparse(path).path
        for key, base in ROOTS.items():
            if u == key or u.startswith(key + "/"):
                rel = posixpath.normpath(u[len(key):].lstrip("/"))
                if rel.startswith(".."):
                    return None
                full = os.path.join(base, "" if rel == "." else rel)
                if not os.path.abspath(full).startswith(os.path.abspath(base)):
                    return None
                return full
        return None

    def do_GET(self):
        tok = token()
        if tok and self.headers.get("X-Flux-Token") != tok:
            return self._json(401, {"error": "bad or missing token"})
        if self.path == "/health":
            return self._json(200, {"error": "ok"})
        full = self._resolve(self.path)
        if not full:
            return self._json(404, {"error": "path not in whitelist /assets /media"})
        if os.path.isdir(full):
            items = []
            for n in sorted(os.listdir(full))[:500]:
                p = os.path.join(full, n)
                try:
                    items.append({"name": n, "dir": os.path.isdir(p),
                                  "bytes": 0 if os.path.isdir(p) else os.path.getsize(p)})
                except OSError:
                    pass
            return self._json(200, {"path": self.path, "items": items})
        if not os.path.isfile(full):
            return self._json(404, {"error": "not found"})
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(os.path.getsize(full)))
        self.end_headers()
        try:
            with open(full, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    self.wfile.write(chunk)
        except PermissionError:
            # TCC 未授权时读不到内容：必须显式暴露，不能静默给 0 字节
            print("[share] TCC 拒绝读取 %s" % full)

    def log_message(self, fmt, *a):
        print("[share] %s %s" % (self.address_string(), fmt % a))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8791)
    a = ap.parse_args()
    if not token():
        print("[share] 缺 token（rc=2）")
        return 2
    print("[share] http://%s:%d 根=%s" % (a.host, a.port, list(ROOTS)))
    ThreadingHTTPServer((a.host, a.port), H).serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())