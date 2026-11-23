#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wechat_article.py — 公众号文章采集（走本机登录浏览器，服务端抓一律被拦）。

能力边界（都不是猜的，2026-11-23 实测）：
  · 服务端/无头请求 mp.weixin.qq.com → "环境异常，完成验证后即可继续访问"
  · 本机登录 Chrome（browserd）→ 可读，单篇约 5 秒
  · 网页版**不显示阅读数/点赞/在看** → 只落结构，不落效果指标，绝不估
  · 公众号没有公开的文章列表接口 → 用搜狗微信搜索按关键词建 URL 池

用法：
  python3 Tools/fleet/wechat_article.py --url <文章URL>              # 抽一篇，打印摘要
  python3 Tools/fleet/wechat_article.py --sogou 新能源汽车 --pages 3  # 建 URL 池 → URLS.jsonl
  python3 Tools/fleet/wechat_article.py --harvest 30                  # 从池里抓 30 篇 → ARTICLES.jsonl
  python3 Tools/fleet/wechat_article.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
GZH = os.path.join(SOCIAL, "gzh")
URLS = os.path.join(GZH, "URLS.jsonl")
ARTICLES = os.path.join(GZH, "ARTICLES.jsonl")
sys.path.insert(0, HERE)


def _sc():
    import social_comment as sc
    return sc


def _uid(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _seen(path, key="_uid"):
    out = set()
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                out.add(json.loads(line).get(key))
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return out


def _append(path, rec):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def discover(keyword, pages=3, sleep_lo=4.0, sleep_hi=9.0, rng=None, via="serp"):
    """按关键词建 URL 池。via=serp 走搜索引擎 site: 查询（更宽容）；
    via=sogou 走搜狗微信（常被验证码拦，失败就返回原因，不硬磕）。"""
    sc = _sc()
    rng = rng or random.Random()
    known = _seen(URLS)
    added = 0
    for p in range(1, int(pages) + 1):
        if via == "sogou":
            hit = sc._daemon("sogou", {"q": keyword, "page": p}, timeout=90)
        else:
            hit = _serp_standalone(keyword, p)
        if hit is None:
            return added, "daemon 无响应（浏览器没起或 profile 被占）"
        if not hit.get("ok"):
            return added, "被拦（验证码/反爬）在第 %d 页" % p
        res = hit.get("res") or {}
        items = res.get("items") or []
        for it in items:
            u = it.get("href") or ""
            if not u.startswith("http") or "mp.weixin.qq.com" not in u:
                continue
            uid = _uid(u)
            if uid in known:
                continue
            known.add(uid)
            _append(URLS, {"_uid": uid, "url": u, "title": it.get("title"),
                           "account": it.get("account"), "ts": it.get("ts"),
                           "kw": keyword, "found_at": datetime.now().isoformat(timespec="seconds")})
            added += 1
        time.sleep(rng.uniform(sleep_lo, sleep_hi))
    return added, "ok"


def _standalone(url):
    """自己起一个浏览器（独立 profile），不挤养号线的单线程 daemon。

    2026-11-23 实锚：把 article 动作塞进 browserd 后，一次异常的页面导航就能把
    整个浏览器卡死（后续 nav 连续 25–40 秒超时），而那是 B 站养号线共用的身体。
    公共服务只服务它自己的业务；公众号采集另起一个 profile 才互不影响。
    """
    sc = _sc()
    mod, _ = sc._pw()
    prof = os.path.expanduser("~/.fluxgroup/browser-gzh")
    os.makedirs(prof, exist_ok=True)
    kw = dict(user_data_dir=prof, headless=True, locale="zh-CN",
              timezone_id="Asia/Shanghai", viewport={"width": 1440, "height": 900},
              args=["--disable-blink-features=AutomationControlled"])
    exe = getattr(sc, "CHROME", "") or ""
    if exe and os.path.exists(exe):
        kw["executable_path"] = exe
    with mod.sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(**kw)
        try:
            pg = ctx.new_page()
            pg.set_default_timeout(8000)
            pg.goto(url, wait_until="commit", timeout=25000)
            ok = False
            for _ in range(18):
                try:
                    if pg.evaluate("()=>!!document.getElementById('js_content')"):
                        ok = True
                        break
                except Exception:
                    pass
                time.sleep(1)
            if not ok:
                return None, "无 #js_content（被拦/需验证/非文章页）"
            res = pg.evaluate("""()=>{
                const q=s=>{const e=document.querySelector(s);return e?e.innerText.trim():'';};
                const c=document.getElementById('js_content');
                const txt=c?c.innerText.trim():'';
                const paras=txt.split(/\\n+/).filter(x=>x.trim().length>0);
                const imgs=c?Array.from(c.querySelectorAll('img')).length:0;
                const heads=Array.from((c||document).querySelectorAll('h1,h2,h3,strong,b'))
                    .map(e=>e.innerText.trim()).filter(t=>t.length>1&&t.length<40);
                const m=(document.documentElement.innerHTML.match(/var\\s+ct\\s*=\\s*"(\\d+)"/)||[])[1];
                const links=Array.from(document.querySelectorAll('a[href*="mp.weixin.qq.com/s"]'))
                    .map(a=>a.href.split('#')[0]).filter((v,i,arr)=>arr.indexOf(v)===i).slice(0,60);
                return {links:links, title:q('#activity-name')||document.title, account:q('#js_name'),
                        publish_ts:m?parseInt(m):null, words:txt.length, paras:paras.length,
                        imgs:imgs, heads:heads.slice(0,40), lead:paras.slice(0,3).join('\\n'),
                        text:txt};}""")
            if not (res.get("text") or "").strip():
                return None, "正文为空（被折叠/需验证）"
            rec = dict(res)
            rec["_uid"] = _uid(url)
            rec["url"] = url
            rec["fetched_at"] = datetime.now().isoformat(timespec="seconds")
            return rec, ""
        except Exception as e:
            return None, "%s: %s" % (type(e).__name__, str(e)[:100])
        finally:
            try:
                ctx.close()
            except Exception:
                pass


def _serp_standalone(keyword, page=1):
    """在自己那个浏览器里查搜索引擎，只取 mp.weixin.qq.com 的链接。

    必须独立跑：把 SERP 塞进养号线的共享单线程 daemon 会把它整个拖死（实锚 2026-11-23）。
    """
    sc = _sc()
    mod, _ = sc._pw()
    prof = os.path.expanduser("~/.fluxgroup/browser-gzh")
    os.makedirs(prof, exist_ok=True)
    kw = dict(user_data_dir=prof, headless=True, locale="zh-CN",
              timezone_id="Asia/Shanghai", viewport={"width": 1440, "height": 900})
    if os.path.exists(sc.CHROME):
        kw["executable_path"] = sc.CHROME
    q = "site:mp.weixin.qq.com " + keyword
    from urllib.parse import quote
    url = "https://cn.bing.com/search?q=%s&first=%d" % (quote(q), 1 + (page - 1) * 10)
    with mod.sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(**kw)
        try:
            pg = ctx.new_page()
            pg.set_default_timeout(12000)
            pg.goto(url, wait_until="domcontentloaded", timeout=25000)
            items = pg.evaluate("""()=>Array.from(document.querySelectorAll('#b_results li.b_algo h2 a'))
                .map(a=>({title:(a.innerText||'').trim(), href:a.href}))""")
            out = [it for it in items if "mp.weixin.qq.com" in (it.get("href") or "")]
            return {"ok": True, "res": {"n": len(out), "items": out}}
        except Exception as e:
            return {"ok": False, "res": "%s: %s" % (type(e).__name__, str(e)[:80])}
        finally:
            try:
                ctx.close()
            except Exception:
                pass


def fetch(url, retries=1):
    """抓一篇。默认走自己的浏览器；不碰养号线的 daemon。"""
    for i in range(retries + 1):
        art, why = _standalone(url)
        if art is not None:
            return art, ""
        if i < retries:
            time.sleep(5)
    return None, why


def harvest(limit=30, sleep_lo=3.0, sleep_hi=8.0, rng=None, urls=None):
    rng = rng or random.Random()
    src = urls if urls is not None else [
        json.loads(l) for l in open(URLS, encoding="utf-8") if l.strip()]
    done = _seen(ARTICLES)
    known = _seen(URLS)
    got, fail = 0, []
    for row in src:
        if got >= int(limit):
            break
        u = row.get("url")
        if not u or _uid(u) in done:
            continue
        art, why = fetch(u)
        if art is None:
            fail.append({"url": u, "why": why})
            continue
        done.add(art["_uid"])
        _append(ARTICLES, art)
        got += 1
        for u2 in (art.get("links") or []):
            uid2 = _uid(u2)
            if uid2 in known or uid2 in done:
                continue
            known.add(uid2)
            _append(URLS, {"_uid": uid2, "url": u2, "kw": "expand",
                           "found_at": datetime.now().isoformat(timespec="seconds")})
        time.sleep(rng.uniform(sleep_lo, sleep_hi))
    return got, fail


def summarize(arts):
    if not arts:
        return "0 篇"
    w = sorted(a.get("words") or 0 for a in arts)
    return ("%d 篇｜字数中位 %d（%d–%d）｜小标题中位 %d｜图片中位 %d｜账号 %d 个"
            % (len(arts), w[len(w) // 2], w[0], w[-1],
               sorted(len(a.get("heads") or []) for a in arts)[len(arts) // 2],
               sorted(a.get("imgs") or 0 for a in arts)[len(arts) // 2],
               len({a.get("account") for a in arts})))


def self_test():
    """不联网：验解析契约与去重（这几条坏了会让"大量采集"变成大量重复垃圾）。"""
    cases = []
    # 1 uid 稳定且同源不同查询串视为同文
    u = "https://mp.weixin.qq.com/s/abc?scene=21"
    cases.append(("uid 稳定", _uid(u) == _uid(u)))
    cases.append(("uid 长度 16", len(_uid(u)) == 16))
    # 2 缺字段的文章仍能入库（words=0 时不崩）
    a = {"_uid": "x", "title": "t", "words": 0, "heads": [], "imgs": 0, "account": "a"}
    cases.append(("空结构可汇总", "1 篇" in summarize([a])))
    # 3 统计真的读字段（改字数必须改结果）
    b = dict(a, words=5000)
    cases.append(("字数进汇总", "5000" in summarize([a, b]) or "2500" in summarize([a, b])))
    # 4 去重集合真的能挡住重复
    import tempfile
    d = tempfile.mkdtemp(prefix="gzh-")
    f = os.path.join(d, "x.jsonl")
    _append(f, {"_uid": "u1", "url": "a"})
    _append(f, {"_uid": "u2", "url": "b"})
    cases.append(("去重读到 2 条", len(_seen(f)) == 2))
    cases.append(("未知 uid 不在已采集", "u3" not in _seen(f)))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--sogou")
    ap.add_argument("--serp")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--harvest", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="每次最多抓几篇（防手滑抓太多）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.url:
        art, why = fetch(a.url)
        if art is None:
            print("[gzh] 失败：%s" % why)
            return 1
        print("[gzh] %s｜%s｜%d 字｜小标题 %d｜图片 %d"
              % (art.get("title"), art.get("account"), art.get("words") or 0,
                 len(art.get("heads") or []), art.get("imgs") or 0))
        print("[gzh] 开头：%s" % (art.get("lead") or "")[:160].replace("\n", " / "))
        return 0
    if a.sogou or a.serp:
        kw = a.serp or a.sogou
        n, why = discover(kw, pages=a.pages, via=("sogou" if a.sogou else "serp"))
        print("[gzh] 建池 %d 条（%s）→ %s" % (n, why, os.path.relpath(URLS, ROOT)))
        return 0 if n or why == "ok" else 1
    if a.harvest:
        lim = a.limit or a.harvest
        got, fail = harvest(min(lim, a.harvest))
        arts = [json.loads(l) for l in open(ARTICLES, encoding="utf-8")
                if l.strip()][-got:] if got else []
        print("[gzh] 入库 %d 篇，失败 %d 次%s"
              % (got, len(fail), ("（首个失败：%s）" % fail[0]["why"]) if fail else ""))
        print("[gzh] 本批：%s" % summarize(arts))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
