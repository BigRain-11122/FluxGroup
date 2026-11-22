#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_daemon.py — 常驻浏览器：一个已登录上下文，采集/发评/弹幕共用。

为什么要它（CEO 2026-11-22「快点弄好」）：每次发评论都 `new` 一个 Chromium，
冷启动约 30 秒——一拍里一半时间是开机器的钱，不是干活的钱。真人不会为了
说一句话先打开一个浏览器再登录。常驻之后：同一个上下文里开一个标签页，
3–5 秒发完就走。

设计（刻意做小）：
  · 单线程 HTTP 服务（127.0.0.1:8791），Playwright sync API 线程亲和，不并发。
  · 每个账号一个 context（profile 隔离），空闲 60 分钟自动关掉。
    为什么不是 10 分钟：关掉之后下一次要冷启动 ~20 秒，而一个 Chromium 只占 ~500MB；
    白天统一内存余量 >8GB，留着比"每次都冷启"划算（2026-11-22 实测 19.7s → 3.6s）。
  · 只做三件事：browse / post / danmaku（其余仍走原路径）。
  · 任何异常都不退出进程：记日志、返回 {ok:false}，调用方回落冷启动。

用法
  python3 Tools/fleet/browser_daemon.py                 # 前台（launchd 用）
  python3 Tools/fleet/browser_daemon.py --once browse --url <u> [--account acct1]
  python3 Tools/fleet/browser_daemon.py --state
  python3 Tools/fleet/browser_daemon.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

PORT = int(os.environ.get("FLUX_BROWSERD_PORT") or 8791)
IDLE_S = int(os.environ.get("FLUX_BROWSERD_IDLE_S") or 3600)

_PW = {"mod": None, "browser": None, "ctx": {}, "last": {}, "started": 0}


def _pw():
    if _PW["mod"] is None:
        import social_comment as sc
        mod, _stealth = sc._pw()
        _PW["mod"] = mod
        _PW["started"] = time.time()
    return _PW["mod"]


def ctx_for(account, profile=None):
    """取（或建）该账号的常驻上下文；空闲超时先关掉旧的。

    一个进程只持有一个 profile 的上下文；两个号就是两个 key（profile 不同）。
    """
    import social_comment as sc
    # 键必须是**规范化后的 profile 路径**：同一 profile 两个 key 会开两个上下文，
    # 第二个必然 ProcessSingleton 失败（2026-11-22 实锚）。
    key = profile or getattr(sc, "PROF", "") or account or "default"
    old = _PW["ctx"].get(key)
    if old is not None and (time.time() - _PW["last"].get(key, 0)) > IDLE_S:
        try:
            old.close()
        except Exception:
            pass
        _PW["ctx"].pop(key, None)
    cur = _PW["ctx"].get(key)
    if cur is None:
        mod = _pw()
        if _PW["browser"] is None:
            _PW["browser"] = mod.sync_playwright().start()
        p = _PW["browser"]
        try:
            cur = sc._launch(p, prof=key)
        except Exception as e:
            # profile 被别的进程（会话里的浏览器）占着：交给调用方回落，不在这里死等
            raise RuntimeError("profile busy: %s" % str(e)[:60])
        _PW["ctx"][key] = cur
    _PW["last"][key] = time.time()
    return cur


def op(payload):
    """执行一个动作。返回 {ok, res}；异常一律转成 ok:false，不拖垮服务。"""
    import social_comment as sc
    kind = payload.get("op")
    if kind not in ("post", "browse", "danmaku", "roots"):
        return {"ok": False, "res": "未知动作 %r" % kind}
    ctx = ctx_for(payload.get("account"), payload.get("profile"))
    _PW["last"][payload.get("profile") or payload.get("account") or "default"] = time.time()
    if kind == "post":
        ok, res = sc._post_in(ctx, payload.get("aid"), payload.get("root"),
                              payload.get("message") or "",
                              dry=bool(payload.get("dry")),
                              read_first=bool(payload.get("read_first")))
        return {"ok": bool(ok), "res": res if isinstance(res, (str, dict)) else str(res)[:400]}
    if kind == "browse":
        ok, res = sc._browse_in(ctx, payload.get("url"),
                                seconds=payload.get("seconds"),
                                harvest=bool(payload.get("harvest", True)))
        return {"ok": bool(ok), "res": res}
    if kind == "roots":
        res = sc._roots_in(ctx, payload.get("aid"), limit=int(payload.get("limit") or 20))
        return {"ok": True, "res": res}
    if kind == "danmaku":
        # 复用同一个 page 发弹幕：直接调接口（已登录上下文里同源 fetch）
        ok, res = sc._danmaku_in(ctx, payload.get("aid"), payload.get("text") or "",
                                 progress_ms=payload.get("progress_ms"),
                                 dry=bool(payload.get("dry")))
        return {"ok": bool(ok), "res": res if isinstance(res, (str, dict)) else str(res)[:400]}
    return {"ok": False, "res": "未知动作 %r" % kind}


def state():
    return {"ok": True,
            "accounts": {k: {"idle_s": round(time.time() - v, 1)}
                         for k, v in _PW["last"].items()},
            "uptime_s": round(time.time() - _PW["started"], 1) if _PW["started"] else 0,
            "port": PORT}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, doc):
        body = json.dumps(doc, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/state"):
            self._send(200, state())
        else:
            self._send(404, {"ok": False})

    def do_POST(self):
        if not self.path.startswith("/op"):
            self._send(404, {"ok": False})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(n).decode() or "{}")
            t0 = time.time()
            res = op(payload)
            res["secs"] = round(time.time() - t0, 1)
            self._send(200, res)
        except Exception as e:
            self._send(200, {"ok": False, "res": "%s: %s" % (type(e).__name__, str(e)[:120])})

    def log_message(self, *a):
        pass


def self_test():
    """负控：未知动作必须 ok:false；没有 daemon 时客户端必须回落（返回 None）。"""
    cases = {}
    cases["未知动作拒绝"] = (op({"op": "nope"})["ok"] is False)
    os.environ["FLUX_BROWSERD"] = "http://127.0.0.1:1"
    import social_comment as sc
    sc.BROWSERD = "http://127.0.0.1:1"
    cases["不在时客户端回落"] = (sc._daemon("post", {"aid": 1}, timeout=2) is None)
    os.environ.pop("FLUX_BROWSERD", None)
    ok = all(cases.values())
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "cases": cases},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--once", default="", help="一次性执行：post/browse/danmaku")
    ap.add_argument("--account", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--aid", type=int, default=0)
    ap.add_argument("--root", type=int, default=0)
    ap.add_argument("--text", default="")
    ap.add_argument("--seconds", type=float, default=0)
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.state:
        print(json.dumps(state(), ensure_ascii=False, indent=1))
        return 0
    if a.once:
        p = {"op": a.once, "account": a.account}
        if a.url:
            p["url"] = a.url
        if a.aid:
            p["aid"] = a.aid
        if a.root:
            p["root"] = a.root
        if a.text:
            p["text"] = a.text
            p["message"] = a.text
        if a.seconds:
            p["seconds"] = a.seconds
        print(json.dumps(op(p), ensure_ascii=False)[:400])
        return 0
    srv = HTTPServer(("127.0.0.1", PORT), H)
    print("[browserd] listening 127.0.0.1:%d（空闲 %ds 关上下文）" % (PORT, IDLE_S), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
