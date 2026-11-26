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
    if kind not in ("post", "browse", "danmaku", "like", "roots", "roots2", "nav", "hot", "aid"):
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
    if kind == "like" and not payload.get("aid"):
        # 参数缺失要在开/取上下文之前就拒：拿不到浏览器也能给出确定的答复，
        # 否则 --self-test 会被"profile 被占用"打断，测不到动作本身。
        return {"ok": False, "res": "缺 aid"}
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
    # 2026-11-24：曾在 daemon 里加过 ownworks（开空间页抓作品），实测把单线程卡死——
    # 一个 goto 挂住就挡住发帖与浏览全线。读作品改成独立进程 own_videos.py，别再往这里加导航类动作。
    if kind == "aid":
        # bvid → aid：同源 fetch，不导航、不签名。匿名直连接口会被挡（2026-11-24 实锚），
        # 登录态里 fetch 才拿得到；本地 base58 解码试过但模板位序记不准，不拿错数冒险。
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        if "bilibili.com" not in (pg.url or ""):
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=30000)
        bv = payload.get("bvid") or ""
        raw = pg.evaluate("""async(b)=>{const r=await fetch(
            'https://api.bilibili.com/x/web-interface/view?bvid='+b,
            {credentials:'include'});return await r.text();}""", bv)
        try:
            d = json.loads(raw or "{}")
            aid = ((d.get("data") or {}).get("aid")) or 0
        except Exception:
            aid = 0
        return {"ok": bool(aid), "res": {"aid": aid, "raw_code": (json.loads(raw or '{}') or {}).get("code") if raw else None}}
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
    if kind == "roots2":
        # 纯接口取 root 评论：**不导航**。原 roots 会 goto 视频页，导航一慢就把单线程堵死，
        # 实测把整条回复线拖成 5 分钟无输出（2026-11-24）。这里只要页面在 bilibili 域内即可。
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        if "bilibili.com" not in (pg.url or ""):
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=20000)
        aid = payload.get("aid")
        limit = int(payload.get("limit") or 20)
        def _fetch_once():
            return pg.evaluate("""async(d)=>{const r=await fetch('https://api.bilibili.com/x/v2/reply'
                +'?type=1&oid='+d.aid+'&pn=1&ps='+d.ps+'&sort=1',{credentials:'include'});
                return await r.text();}""", {"aid": aid, "ps": min(50, limit)})

        raw = _fetch_once()
        try:
            d = json.loads(raw or "{}")
        except Exception:
            d = {}
        if not d or d.get("code") is None:
            # 页面被别的流程带走了（发帖/浏览会换页），同源 fetch 会拿到非 JSON。
            # 回首页重试一次就够——不做无限重试，也不让这步挡住单线程太久。
            try:
                pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=20000)
                raw = _fetch_once()
                d = json.loads(raw or "{}")
            except Exception:
                d = {}
        reps = ((d.get("data") or {}).get("replies") or [])[:limit]
        out = [{"rpid": str(x.get("rpid")),
                "author": ((x.get("member") or {}).get("uname") or ""),
                "text": ((x.get("content") or {}).get("message") or ""),
                "rcount": int(x.get("rcount") or 0),
                "ctime": int(x.get("ctime") or 0),
                "like": int(x.get("like") or 0)} for x in reps]
        return {"ok": True, "res": {"code": d.get("code"), "replies": out}}
    if kind == "roots":
        res = sc._roots_in(ctx, payload.get("aid"), limit=int(payload.get("limit") or 20))
        return {"ok": True, "res": res}
    if kind == "like":
        # 点赞也要走这里：user_agent.like() 原本自己 _launch() 一个浏览器，
        # 而这个常驻进程 24 小时握着 profile 锁 → 养号守护每次都「让路」，
        # 点赞与弹幕长期为 0（2026-11-26 实锚：两号 赞0 弹幕0，日志全是
        # 「profile 在采集手里」）。动作很轻，在已登录上下文里同源 fetch 即可。
        aid = payload.get("aid")
        if not aid:
            return {"ok": False, "res": "缺 aid"}
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            if "bilibili.com" not in (pg.url or ""):
                pg.goto("https://www.bilibili.com/video/av%s" % aid,
                        wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        cookies = {c["name"]: c["value"] for c in ctx.cookies()}
        csrf = cookies.get("bili_jct", "")
        if not csrf:
            return {"ok": False, "res": "缺 csrf（bili_jct），登录态失效"}
        if payload.get("dry"):
            return {"ok": True, "res": {"dry": True, "aid": aid}}
        body = "aid=%s&like=1&csrf=%s" % (aid, csrf)
        try:
            hit = pg.evaluate("""async (body)=>{
                const r=await fetch('https://api.bilibili.com/x/web-interface/archive/like',
                  {method:'POST',credentials:'include',
                   headers:{'Content-Type':'application/x-www-form-urlencoded'},
                   body:body});
                return {status:r.status, text:await r.text()};}""", body)
            doc = json.loads((hit or {}).get("text") or "{}")
        except Exception as e:
            return {"ok": False, "res": "%s: %s" % (type(e).__name__, str(e)[:120])}
        ok = (hit or {}).get("status") == 200 and doc.get("code") == 0
        return {"ok": bool(ok), "res": {"code": doc.get("code"),
                                        "message": doc.get("message")}}
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
    # like 进了白名单就不能再被当未知动作；缺 aid 必须在开浏览器之前就拒
    cases["like 已受支持（不被当未知动作）"] = ("未知动作" not in str(op({"op": "like"})["res"]))
    cases["like 缺 aid 直接拒"] = (op({"op": "like"})["ok"] is False)
    os.environ["FLUX_BROWSERD"] = "http://127.0.0.1:1"
    import social_comment as sc
    sc.BROWSERD = "http://127.0.0.1:1"
    cases["不在时客户端回落"] = (sc._daemon("post", {"aid": 1}, timeout=2) is None)
    cases["不在时 like 也回落"] = (sc._daemon("like", {"aid": 1}, timeout=2) is None)
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
