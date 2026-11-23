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


OPS_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), ".codely-cli", "state", "browserd-ops.jsonl")


def _log_op(kind, t0, note=""):
    """每次动作落一行耗时：单线程到底被谁占着，只能靠每个动作的真实秒数说话。"""
    try:
        with open(OPS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "op": kind,
                                "secs": round(time.time() - t0, 2),
                                "note": str(note)[:60]}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def op(payload):
    """执行一个动作。返回 {ok, res, svc_ms}；异常一律转成 ok:false，不拖垮服务。

    svc_ms = daemon 内真正干活的时间。客户端拿"自己的总往返"减去它，
    才是排队时间——否则"发帖 43 秒"永远分不清是动作慢还是排在别人后面
    （2026-11-23 实锚：post_s 已扣 lock_wait_s，却仍含 daemon 内排队）。
    """
    _t0 = time.time()
    out = _op(payload)
    try:
        out["svc_ms"] = int((time.time() - _t0) * 1000)
    except Exception:
        pass
    return out


def _op(payload):
    import social_comment as sc
    kind = payload.get("op")
    if kind not in ("post", "browse", "danmaku", "roots", "nav", "hot"):
        return {"ok": False, "res": "未知动作 %r" % kind}
    # 发帖优先：practice_tick 在调用 post 前会立一个 POST-PENDING 标记。
    # 常驻浏览器是单线程，任何动作排进去都占着唯一线程；发帖排在后面就是 90 秒。
    # 2026-11-22 实测：只让 browse 让路不够——采评论（hot）/取楼中楼（roots）同样是重活，
    # 发帖仍被压在 77–98 秒。凡是"可推迟"的动作在标记期内一律让路，只有 post 自己不让。
    if kind != "post":
        try:
            mk = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), ".codely-cli", "state", "POST-PENDING")
            if os.path.exists(mk):
                age = time.time() - os.path.getmtime(mk)
                if age < 180:
                    return {"ok": False, "res": "post-pending（%s 让路给发帖，%.0fs 前立的）" % (kind, age)}
        except Exception:
            pass
    ctx = ctx_for(payload.get("account"), payload.get("profile"))
    _PW["last"][payload.get("profile") or payload.get("account") or "default"] = time.time()
    if kind == "hot":
        # 取"按热度排序"的评论（sort=2）。匿名 urllib 打这个接口会 412
        # （2026-11-22 实测采到第 60 个视频就被限），而登录上下文里同源 fetch 与真人
        # 翻评论区是同一条路径，稳定且带真 cookie。
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        if "bilibili.com" not in (pg.url or ""):
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=30000)
        txt = pg.evaluate("""async(a)=>{
            const u='https://api.bilibili.com/x/v2/reply?type=1&oid='+a.aid
              +'&sort=2&ps=20&pn='+a.pn;
            const r=await fetch(u,{credentials:'include'});
            return await r.text();}""", {"aid": payload.get("aid"), "pn": payload.get("pn") or 1})
        return {"ok": True, "res": txt}
    if kind == "nav":
        # 登录态核验也走常驻上下文：2026-11-22 实锚——daemon 把 profile 打开后，
        # 会话自己再 launch 一次就 ProcessSingleton，整天只剩 profile_busy。
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        # 必须有 bilibili 源页：在 about:blank 里 fetch api.bilibili.com 会
        # "Failed to fetch"（2026-11-22 实测 11 秒后抛 TypeError）。
        if "bilibili.com" not in (pg.url or ""):
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=30000)
        res = pg.evaluate("""async()=>{const r=await fetch(
            'https://api.bilibili.com/x/web-interface/nav',{credentials:'include'});
            const j=await r.json();const d=j.data||{};
            return {isLogin:!!d.isLogin, mid:d.mid, uname:d.uname};}""")
        return {"ok": True, "res": res}
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
            _log_op(payload.get("op"), t0, res.get("res"))
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
