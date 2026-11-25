#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""harvest_weread.py — 公众号第二个入口：走微信读书 Web 接口取「最新一篇」。

为什么要有这条（2026-11-25，CEO「你采集的不止公众号哦 / 采集也要去 GitHub 找工具」）：
  公众号后台 appmsg 有账号级频控（200013，新号最严），发现通道也全封。
  但微信读书 Web 有另一个入口（实测来源＝rachelos/we-mp-rss，MIT）：
    GET /api/mp/cover?bookId=MP_WXS_xxx  → 该号「最新一篇」的 reviewId + 标题
    GET /web/mp/content?reviewId=xxx     → 正文 HTML（含 #js_content）
  它**只能拿最新一篇、回补不了历史**（旧列表接口 /web/mp/articles 已废弃，恒 -2041）。
  所以它的定位是「让订阅的号持续进语料」，不是「补 200 篇差额」。

  不装对方整套 Web 服务（FastAPI+SQLite+调度+UI），只取这两个接口——
  我们只需要文章，不需要第二个后台。语料口径与 wechat_article 完全一致：
  同一个 mp.weixin.qq.com/s/<token> 得到同一个 uid，所以两条路采到同一篇不会重复。

凭据（必须人给，不代做）：
  · 浏览器登录 https://weread.qq.com，打开任意公众号页面
  · DevTools → Network → 找 /api/mp/cover 请求 → 复制完整 Cookie（新版不需要 x-wr-ticket）
  · 存成 ~/.fluxgroup/weread-cookie.txt（或设环境变量 WEREAD_COOKIE）
  · 订阅号清单存 ~/.fluxgroup/weread-books.json：[{"bookId":"MP_WXS_xxx","name":"42号车库"}]

用法：
  harvest_weread.py --status                 # 看凭据/清单/已采情况，不联网
  harvest_weread.py --once                   # 每个号取最新一篇
  harvest_weread.py --book MP_WXS_xxx --once # 只跑一个号
  harvest_weread.py --self-test              # 不联网
退出码：0 成功 / 2 没新文章 / 3 无凭据 / 5 认证失效（要重贴 cookie）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import wechat_article as W                    # 复用 uid / 文体判定 / 语料写入

BASE = "https://weread.qq.com"
COOKIE_FILE = os.path.expanduser("~/.fluxgroup/weread-cookie.txt")
BOOKS_FILE = os.path.expanduser("~/.fluxgroup/weread-books.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
AUTH_ERRCODES = (-2010, -2012, -2041)     # 认证失效/风控/接口废弃：不重试，直接报要人
MIN_TEXT = 200


class AuthError(RuntimeError):
    """凭据失效：必须人重新贴 cookie，脚本不该重试。"""


def cookie():
    c = (os.environ.get("WEREAD_COOKIE") or "").strip()
    if c:
        return c
    try:
        return open(COOKIE_FILE, encoding="utf-8").read().strip()
    except FileNotFoundError:
        return ""


def books():
    try:
        data = json.load(open(BOOKS_FILE, encoding="utf-8"))
    except FileNotFoundError:
        return []
    out = []
    for r in data if isinstance(data, list) else []:
        bid = str(r.get("bookId") or "").strip()
        if bid:
            out.append({"bookId": bid, "name": str(r.get("name") or "")[:40]})
    return out


# ---------------- 纯函数：好测的部分 ----------------

def token_from_review_id(review_id, book_id=""):
    """reviewId 形如 MP_WXS_<bookId>_<token>；微信读书把 token 里的 '_' 写成 '~'。

    实测（2026-09-23 上游记录）：149 篇含 '~' 的链接全部「参数错误」，
    还原成 '_' 后 100% 可打开。顺序有讲究：先按 '_' 拆前缀，再还原 '~'。
    """
    rid = str(review_id or "").strip()
    if not rid:
        return ""
    token = rid
    prefix = f"{book_id}_" if book_id else ""
    if prefix and rid.startswith(prefix):
        token = rid[len(prefix):]
    elif "_" in token:
        token = token.split("_")[-1]
    return token.replace("~", "_")


def mp_url_from_review_id(review_id, book_id=""):
    from urllib.parse import quote
    tok = token_from_review_id(review_id, book_id)
    return f"https://mp.weixin.qq.com/s/{quote(tok, safe='')}" if tok else ""


def extract_body(html):
    """从 #js_content 取正文纯文本 + 小标题 + 图片数。取不到就返回空，不编。"""
    if not html:
        return {"text": "", "heads": [], "imgs": 0, "paras": 0}
    try:
        from bs4 import BeautifulSoup
    except Exception:                                   # noqa: BLE001
        return {"text": "", "heads": [], "imgs": 0, "paras": 0}
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one("#js_content") or soup.select_one(".rich_media_content")
    if node is None:
        return {"text": "", "heads": [], "imgs": 0, "paras": 0}
    for bad in node.select("script, style"):
        bad.decompose()
    imgs = len(node.select("img"))
    heads = [h.get_text(strip=True) for h in node.select("h1,h2,h3,strong,b")]
    heads = [h for h in heads if 1 < len(h) < 40][:40]
    text = node.get_text("\n", strip=True)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    paras = [p for p in text.split("\n") if p.strip()]
    return {"text": text, "heads": heads, "imgs": imgs, "paras": len(paras)}


def classify_error(code):
    """接口返回码 → 人话。认不出的错误不许当成「没新文章」。"""
    try:
        code = int(code or 0)
    except (TypeError, ValueError):
        return "unknown", "未知返回码，按失败处理"
    if code == 0:
        return "ok", ""
    if code in AUTH_ERRCODES:
        return "auth", "微信读书认不出这个 Cookie（%d）：要人重新登录并重贴" % code
    return "error", "接口报错 %d" % code


# ---------------- 网络部分 ----------------

def _get(path, params, timeout=30):
    import urllib.request
    from urllib.parse import urlencode
    ck = cookie()
    if not ck:
        raise AuthError("没有 Cookie：把 weread.qq.com 的 Cookie 存到 %s" % COOKIE_FILE)
    url = "%s%s?%s" % (BASE, path, urlencode(params))
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Cookie": ck, "Referer": BASE + "/",
        "Accept": "application/json, text/plain, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def latest_of(book_id):
    """取该号最新一篇：返回 {reviewId,title,url}。认证失效抛 AuthError。"""
    raw = _get("/api/mp/cover", {"bookId": book_id})
    try:
        payload = json.loads(raw)
    except ValueError:
        raise RuntimeError("cover 不是 JSON（可能被风控页拦了）") from None
    kind, why = classify_error(payload.get("errCode", payload.get("errcode", 0)))
    if kind == "auth":
        raise AuthError(why)
    if kind == "error":
        raise RuntimeError(why)
    rid = (payload.get("reviewId") or "").strip()
    if not rid:
        return None
    return {"reviewId": rid, "title": (payload.get("title") or "").strip(),
            "url": mp_url_from_review_id(rid, book_id)}


def content_of(review_id):
    return extract_body(_get("/web/mp/content", {"reviewId": review_id}))


def harvest_once(only_book="", delay=2.0, verbose=True):
    """每个号取最新一篇 → 进 ARTICLES.jsonl。已入库的跳过（按 uid）。"""
    bl = books()
    if only_book:
        bl = [{"bookId": only_book, "name": ""}]
    if not bl:
        return {"got": 0, "skip": 0, "fail": 0,
                "why": "没有订阅清单：写 %s" % BOOKS_FILE}
    done = W._seen(W.ARTICLES)
    got = skip = fail = 0
    for b in bl:
        bid = b["bookId"]
        try:
            latest = latest_of(bid)
        except AuthError as e:
            return {"got": got, "skip": skip, "fail": fail, "why": str(e), "auth": True}
        except Exception as e:                          # noqa: BLE001
            fail += 1
            if verbose:
                print("  %-14s 取不到：%s" % (b["name"] or bid, str(e)[:60]))
            continue
        if not latest:
            skip += 1
            continue
        uid = W._uid(latest["url"])
        if uid in done:
            skip += 1
            if verbose:
                print("  %-14s 无新文章（%s）" % (b["name"] or bid, latest["title"][:20]))
            continue
        try:
            body = content_of(latest["reviewId"])
        except AuthError as e:
            return {"got": got, "skip": skip, "fail": fail, "why": str(e), "auth": True}
        except Exception as e:                          # noqa: BLE001
            fail += 1
            if verbose:
                print("  %-14s 正文取不到：%s" % (b["name"] or bid, str(e)[:60]))
            continue
        text = body["text"]
        if len(re.sub(r"\s", "", text)) < MIN_TEXT:
            fail += 1
            if verbose:
                print("  %-14s 正文过短（%d 字），不入库" % (b["name"] or bid, len(text)))
            continue
        paras = [p for p in text.split("\n") if p.strip()]
        art = {"_uid": uid, "url": latest["url"],
               "title": (latest["title"] or "")[:150],
               "account": b["name"] or "", "words": len(re.sub(r"\s", "", text)),
               "paras": body["paras"], "imgs": body["imgs"], "heads": body["heads"],
               "lead": "\n".join(paras[:3]), "text": text,
               "via": "weread", "mirror": False,
               "fetched_at": datetime.now().isoformat(timespec="seconds")}
        art["genre"], art["genre_why"] = W.genre_of(art)
        W._append(W.ARTICLES, art)
        done.add(uid)
        got += 1
        if verbose:
            print("  %-14s 入库 %d 字｜%s｜genre=%s"
                  % (b["name"] or bid, art["words"], art["title"][:24], art["genre"]))
        time.sleep(delay)
    return {"got": got, "skip": skip, "fail": fail, "why": ""}


# ---------------- 自检（不联网） ----------------

COVER_OK = json.dumps({"reviewId": "MP_WXS_abc123_ySsAk3lUFT0Wh~9IZCtr-g", "title": "座舱屏幕越做越大"}, ensure_ascii=False)
COVER_AUTH = json.dumps({"errCode": -2012, "errMsg": "login required"})
COVER_EMPTY = json.dumps({"errCode": 0})

CONTENT_HTML = """<html><body><div id="js_content">
<h2>先看层数</h2>
<p>常用功能在第几层，比屏幕多大更重要。三层以内能到，就算合格。</p>
<p>把空调从三级菜单提到一级，同样操作的耗时从 4.2 秒降到 1.6 秒。</p>
<img src="a.png"><script>var x=1</script>
<strong>结论</strong>
<p>这一段是正文的最后一句，用来确保字数够。</p></div></body></html>"""


def self_test():
    cases = []

    # 1 reviewId → 原文链接：'~' 必须还原成 '_'，且前缀拆分要在还原之前
    rid = "MP_WXS_abc123_ySsAk3lUFT0Wh~9IZCtr-g"
    tok = token_from_review_id(rid, "MP_WXS_abc123")
    cases.append(("token 里的 ~ 还原成 _", tok == "ySsAk3lUFT0Wh_9IZCtr-g"))
    cases.append(("拼出的原文链接是 mp.weixin 短链",
                  mp_url_from_review_id(rid, "MP_WXS_abc123").startswith(
                      "https://mp.weixin.qq.com/s/")))
    cases.append(("负控[空 reviewId] 返回空", mp_url_from_review_id("", "x") == ""))
    cases.append(("不带 bookId 也能取最后一段",
                  token_from_review_id("MP_WXS_a_b~c") == "b_c"))

    # 2 正文抽取：拿到真句、丢掉 script、抽出小标题、数到图片
    body = extract_body(CONTENT_HTML)
    cases.append(("正文取到关键句", "4.2 秒降到 1.6 秒" in body["text"]))
    cases.append(("script 未混入正文", "var x=1" not in body["text"]))
    cases.append(("小标题被抽出", "先看层数" in body["heads"]))
    cases.append(("图片数正确", body["imgs"] == 1))
    cases.append(("负控[没有 #js_content] 返回空正文", extract_body("<html><body><p>x</p></body></html>")["text"] == ""))
    cases.append(("负控[空 HTML] 不崩", extract_body("")["text"] == ""))

    # 3 返回码分类：认证失效必须单独一类，不许当「没新文章」
    cases.append(("正常码判 ok", classify_error(0)[0] == "ok"))
    cases.append(("-2012 判认证", classify_error(-2012)[0] == "auth"))
    cases.append(("-2041 判认证（接口已废弃）", classify_error(-2041)[0] == "auth"))
    cases.append(("负控[陌生错误码] 不许判成 ok", classify_error(-9999)[0] != "ok"))

    # 4 凭据缺失必须明确报错，而不是静默返回 0 篇
    saved_env, saved_file = os.environ.get("WEREAD_COOKIE"), COOKIE_FILE
    try:
        os.environ.pop("WEREAD_COOKIE", None)
        globals()["COOKIE_FILE"] = "/nonexistent/x"
        cases.append(("无 Cookie 时 cookie() 返回空", cookie() == ""))
        raised = False
        try:
            _get("/api/mp/cover", {"bookId": "MP_WXS_x"})
        except AuthError:
            raised = True
        except Exception:
            raised = False
        cases.append(("负控[无凭据] 必须抛 AuthError 而不是返回空", raised))
    finally:
        globals()["COOKIE_FILE"] = saved_file
        if saved_env is not None:
            os.environ["WEREAD_COOKIE"] = saved_env

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def _rows(path):
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def status():
    ck = cookie()
    bl = books()
    print("[weread] Cookie：%s" % ("已配置（%d 字符）" % len(ck) if ck else "缺（存到 %s）" % COOKIE_FILE))
    print("[weread] 订阅清单：%d 个号（%s）" % (len(bl), BOOKS_FILE))
    for b in bl[:12]:
        print("   %-16s %s" % (b["name"] or "-", b["bookId"]))
    n = sum(1 for r in _rows(W.ARTICLES) if r.get("via") == "weread")
    print("[weread] 已由这条路入库：%d 篇" % n)
    print("[weread] 能力边界：只取每个号最新一篇，历史补不回来（旧列表接口已废弃恒 -2041）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--book", default="")
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.status:
        return status()
    if a.once:
        if not cookie():
            print("[weread] 无凭据：把 weread.qq.com 的 Cookie 存到 %s" % COOKIE_FILE)
            return 3
        r = harvest_once(a.book, a.delay)
        if r.get("auth"):
            print("[weread] 认证失效：%s" % r["why"])
            return 5
        if r["why"]:
            print("[weread] %s" % r["why"])
            return 3
        print("[weread] 入库 %d 篇｜跳过 %d｜失败 %d" % (r["got"], r["skip"], r["fail"]))
        return 0 if r["got"] else 2
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
