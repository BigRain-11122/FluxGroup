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


def _canon(url):
    """URL 归一化后再取 uid。

    2026-11-23 采集席实测：原实现直接 sha1(原串)，同一篇文章 9 种写法（?scene=、
    http/https、尾斜杠、#rd、参数换序、短链 vs 长链）得到 **9 个不同 uid**，
    而自检里那条"uid 稳定"写的是 _uid(u)==_uid(u)，恒真——假绿盖住了真缺陷。

    归一化规则：
      短链 /s/<token> → 只认 token；
      长链 /s?__biz=&mid=&idx= → 只认 biz+mid+idx（sn/chksm/scene 都是变体）。
    **已知局限**：短链不含 __biz，纯 URL 层无法与长链合一。彻底去重要等抓取成功后
    用页面回填 (account, publish_ts, title) 做二次键。这条不许假装已经解决。
    """
    from urllib.parse import urlsplit, parse_qs, urlunsplit
    u = urlsplit((url or "").strip())
    host = u.netloc.lower()
    if host.endswith("mp.weixin.qq.com"):
        path = u.path.rstrip("/")
        if path.startswith("/s/"):
            return "wx:tok:" + path[3:].strip("/")
        q = parse_qs(u.query)
        if path == "/s" and q.get("__biz") and q.get("mid") and q.get("idx"):
            return "wx:%s:%s:%s" % (q["__biz"][0], q["mid"][0], q["idx"][0])
    return urlunsplit((u.scheme or "https", host, u.path.rstrip("/"), "", ""))


def _uid(url):
    return hashlib.sha1(_canon(url).encode("utf-8")).hexdigest()[:16]


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


# 静态垂类源：由 gzh_corpus_expand.py 抓，语料落 ARTICLES-INDUSTRY.jsonl。
# 这里必须跳过——否则 gasgoo 链接会被送进公众号提取器找 #js_content，
# 每条必然卡满 25 秒超时（2026-11-25 实锚：71 条 × 25 秒 = 900 秒跑爆）。
STATIC_HOSTS = ("auto.gasgoo.com", "www.d1ev.com", "d1ev.com")
FAILED = os.path.join(GZH, "URLS-FAILED.jsonl")
DEAD_STRIKES = 2          # 同一链接失败这么多次就不再试


def _static_host(url):
    from urllib.parse import urlsplit
    host = urlsplit(url or "").netloc.lower()
    return any(host == h or host.endswith("." + h) for h in STATIC_HOSTS)


def failed_urls():
    """死链台账：返回已达 DEAD_STRIKES 次的 uid 集合。"""
    c = {}
    try:
        for line in open(FAILED, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            c[r.get("_uid")] = c.get(r.get("_uid"), 0) + 1
    except FileNotFoundError:
        pass
    return {u for u, n in c.items() if u and n >= DEAD_STRIKES}


def mark_failed(url, why):
    _append(FAILED, {"_uid": _uid(url), "url": url, "why": str(why)[:120],
                     "at": datetime.now().isoformat(timespec="seconds")})


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


def _browser():
    """统一的独立浏览器上下文（profile=browser-gzh，不碰养号线）。"""
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
    return mod, kw


def _strip_html(h):
    import re as _re
    t = _re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h or "", flags=_re.S | _re.I)
    t = _re.sub(r"<br\s*/?>|</p>|</div>", "\n", t, flags=_re.I)
    t = _re.sub(r"<[^>]+>", "", t)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
        t = t.replace(a, b)
    return "\n".join(x.strip() for x in t.split("\n") if x.strip())


def discover_chejiahao(author_id, pages=1, rng=None, limit=40, scrolls=8):
    """车家号作者页取文章链接（对标对象本人的镜像）。

    2026-11-25 实测纠正：作者页是**无限滚动**，不是分页——
    `?page=2` 返回的仍是第一屏同一批内容（实测两次首条完全相同），
    所以原「按 page 翻页」写法只能拿到 49 条。滚动加载后同一页能出 **102** 条。
    pages 参数保留但只作为滚动次数的下限，避免调用方改代码。

    2026-11-23 实测：详情页正文在 __NEXT_DATA__ 的 articleContent.content（HTML），
    比公众号网页稳定，不需要登录。标注为"镜像"：只用于学写法，不声称是公众号原文。
    """
    rng = rng or random.Random()
    mod, kw = _browser()
    known = _seen(URLS)
    added = 0
    n_scroll = max(int(scrolls), int(pages) * 2, 6)
    with mod.sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(**kw)
        try:
            pg = ctx.new_page()
            pg.set_default_timeout(15000)
            pg.goto("https://chejiahao.autohome.com.cn/authors/%s" % author_id,
                    wait_until="domcontentloaded", timeout=35000)
            pg.wait_for_timeout(2500)

            # 滚到底触发懒加载，直到连续 3 次不再增长（或滚满次数）
            # 坑：单次等待 <2.5s 时懒加载还没回来，会被误判成"已到底"而提前收工
            last, stall = 0, 0
            for i in range(n_scroll):
                n = pg.evaluate("document.querySelectorAll('a[href*=\"/info/\"]').length")
                if n > last:
                    last, stall = n, 0
                else:
                    stall += 1
                    if stall >= 3:
                        break
                pg.evaluate("window.scrollTo(0,document.body.scrollHeight)")
                pg.wait_for_timeout(int(rng.uniform(2500, 3200)))

            items = pg.evaluate("""()=>Array.from(document.querySelectorAll('a'))
                .map(a=>({t:(a.innerText||'').trim(), h:a.href.split('#')[0]}))
                .filter(x=>/\\/info\\/\\d+/.test(x.h) && x.t.length>8)""")
            seen_here = set()
            for it in items:
                u = it["h"]
                if u in seen_here:
                    continue
                seen_here.add(u)
                uid = _uid(u)
                if uid in known or added >= limit:
                    continue
                known.add(uid)
                _append(URLS, {"_uid": uid, "url": u, "title": it["t"],
                               "source": "chejiahao", "mirror": True,
                               "author_id": str(author_id),
                               "found_at": datetime.now().isoformat(timespec="seconds")})
                added += 1
            print("[gzh] 作者页滚动 %d 次，可见 %d 条，新增入库 %d 条"
                  % (i + 1, len(items), added))
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    return added


def _extract_chejiahao(pg):
    """从 __NEXT_DATA__ 取 articleContent：标题/正文/发布时间/作者。"""
    raw = pg.evaluate("()=>{const e=document.getElementById('__NEXT_DATA__');"
                      "return e?e.textContent:''}")
    if not raw:
        return None, "无 __NEXT_DATA__"
    try:
        j = json.loads(raw)
    except Exception as e:
        return None, "NEXT_DATA 解析失败：%s" % str(e)[:60]

    def walk(o):
        if isinstance(o, dict):
            if "articleContent" in o and isinstance(o["articleContent"], dict):
                return o["articleContent"]
            for v in o.values():
                r = walk(v)
                if r:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = walk(v)
                if r:
                    return r
        return None

    ac = walk(j)
    if not ac:
        return None, "NEXT_DATA 里没有 articleContent"
    html = ac.get("content") or ""
    text = _strip_html(html)
    if len(text) < 100:
        return None, "正文过短（%d 字）" % len(text)
    heads = []
    try:
        import re as _re
        heads = [x.strip() for x in _re.findall(r"<(?:h[1-3]|strong|b)[^>]*>(.*?)</", html, _re.S)]
        heads = [_strip_html(h) for h in heads if 1 < len(_strip_html(h)) < 40][:40]
    except Exception:
        pass
    paras = [x for x in text.split("\n") if x.strip()]
    return {"title": ac.get("title") or "", "account": ac.get("authorName") or "42号车库(镜像)",
            "publish_ts": ac.get("publishTime") or ac.get("createTime"),
            "words": len(text), "paras": len(paras), "imgs": html.count("<img"),
            "heads": heads, "lead": "\n".join(paras[:3]), "text": text,
            "mirror": True}, ""


def fetch(url, retries=1):
    """抓一篇。默认走自己的浏览器；不碰养号线的 daemon。"""
    from urllib.parse import urlsplit as _us
    host = _us(url).netloc.lower()
    for i in range(retries + 1):
        art, why = (_fetch_chejiahao(url) if "autohome.com.cn" in host else _standalone(url))
        if art is not None:
            return art, ""
        if i < retries:
            time.sleep(5)
    return None, why


def discover_authors_from(urls, limit=6, rng=None):
    """从文章页反查作者主页 id（车家号作者链接是 /Authors/<id>，**大写 A**）。

    为什么需要：作者页单屏只给约 49 条带标题的文章链接，滚动加载的是内容不是新链接
    （实测 102 个锚点里仅 49 个有标题，滚到底仍是 49）。所以「200 篇」靠单作者拿不到，
    必须扩作者数——而作者 id 只能从文章页反查。
    坑：正则写成小写 /authors/ 会永远匹配 0 个（2026-11-25 实锚）。
    """
    rng = rng or random.Random()
    mod, kw = _browser()
    found = {}
    with mod.sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(**kw)
        try:
            pg = ctx.new_page()
            pg.set_default_timeout(20000)
            for u in urls[:limit]:
                try:
                    pg.goto(u, wait_until="domcontentloaded", timeout=35000)
                    pg.wait_for_timeout(int(rng.uniform(2000, 3000)))
                    ids = pg.evaluate(
                        """()=>Array.from(document.querySelectorAll('a')).map(a=>a.href)
                             .map(h=>{const m=h.match(/\\/Authors\\/(\\d+)/i);return m?m[1]:null})
                             .filter(Boolean)""")
                    for i in ids:
                        found.setdefault(i, 0)
                        found[i] += 1
                except Exception:  # noqa: BLE001
                    continue
                time.sleep(rng.uniform(1.5, 3))
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    return sorted(found.items(), key=lambda kv: -kv[1])


def expand_once(limit=6, rng=None):
    """两跳扩池：访问池内文章 → ①反查作者 id ②收推荐 /info/ 链接回池。

    为什么必须两跳：作者页只给约 49 条，单作者到不了 200 篇；
    而推荐位只暴露 /info/（不暴露作者），所以要先拿推荐文，再从推荐文反查作者。
    """
    rng = rng or random.Random()
    rows = []
    if os.path.exists(URLS):
        for line in open(URLS, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:  # noqa: BLE001
                    pass
    known = _seen(URLS)
    # 坑（2026-11-25 实锚）：原来用 r.get("visited") 过滤，但从来没写过这个字段，
    # 于是每一轮都重复访问最前面那几篇 → 永远在原地打转，扩不出新作者。
    # 正解=单独一个访问台账，跑过就记，跨轮次可续。
    visited_path = os.path.expanduser("~/.fluxgroup/cj-visited.json")
    visited = set()
    if os.path.exists(visited_path):
        try:
            visited = set(json.load(open(visited_path, encoding="utf-8")))
        except Exception:  # noqa: BLE001
            visited = set()
    todo = [r for r in rows if "/info/" in (r.get("url") or "")
            and r.get("url") not in visited][:limit]
    authors, added = {}, 0
    mod, kw = _browser()
    with mod.sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(**kw)
        try:
            pg = ctx.new_page(); pg.set_default_timeout(20000)
            for r in todo:
                try:
                    pg.goto(r["url"], wait_until="domcontentloaded", timeout=35000)
                    pg.wait_for_timeout(int(rng.uniform(2000, 3000)))
                    got = pg.evaluate(r"""()=>{
                      const hrefs=Array.from(document.querySelectorAll('a')).map(a=>a.href);
                      const auth=hrefs.map(h=>{const m=h.match(/\/Authors\/(\d+)/i);return m?m[1]:null}).filter(Boolean);
                      const info=hrefs.filter(h=>/\/info\/\d+/.test(h));
                      return {auth:[...new Set(auth)], info:[...new Set(info)]};}""")
                    for a in got.get("auth") or []:
                        authors[a] = authors.get(a, 0) + 1
                    for u in got.get("info") or []:
                        if u == r["url"]:
                            continue
                        uid = _uid(u)
                        if uid in known or added >= 60:
                            continue
                        known.add(uid); added += 1
                        _append(URLS, {"_uid": uid, "url": u, "title": "",
                                       "source": "chejiahao", "mirror": True,
                                       "author_id": (got.get("auth") or [None])[0],
                                       "found_at": datetime.now().isoformat(timespec="seconds")})
                except Exception:  # noqa: BLE001
                    continue
                visited.add(r["url"])
                time.sleep(rng.uniform(1.5, 3))
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    try:
        os.makedirs(os.path.dirname(visited_path), exist_ok=True)
        json.dump(sorted(visited), open(visited_path, "w", encoding="utf-8"),
                  ensure_ascii=False)
    except Exception:  # noqa: BLE001
        pass
    return authors, added


def _fetch_chejiahao(url):
    mod, kw = _browser()
    with mod.sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(**kw)
        try:
            pg = ctx.new_page()
            pg.set_default_timeout(12000)
            pg.goto(url, wait_until="domcontentloaded", timeout=35000)
            pg.wait_for_timeout(2500)
            art, why = _extract_chejiahao(pg)
            if art is None:
                return None, why
            art.update({"_uid": _uid(url), "url": url,
                        "fetched_at": datetime.now().isoformat(timespec="seconds")})
            return art, ""
        except Exception as e:
            return None, "%s: %s" % (type(e).__name__, str(e)[:80])
        finally:
            try:
                ctx.close()
            except Exception:
                pass


# 语料错配的真问题不是题材（通稿也在讲车），而是**文体**：公告/基准发布 vs 编辑式车评。
# 两次踩坑记录：①按"汽车词"判 → CLUE 的《汽车大模型测评基准发布》被判对味（词对文体全错）；
# ②按"第一人称"判 → 42号车库是第三人称编辑体，"我"=0，反被判 unknown。
# 现用结构与语气：标题语气（疑问/判断）+ 公告标记 + 章节骨架（背景/方法/指标/征集）。
# 诚实边界：样本只有 3 个账号 10 篇，这是**保守初版**，标注了 unknown 就默认不用。
PRESS_MARKS = ("发布", "公告", "丨", "结果发布", "方案发布", "正式上线", "圆满", "揭牌",
               "测评基准", "基准发布",
               "启动征集", "签约", "据悉", "通讯员", "白皮书", "标准", "榜单", "获奖", "峰会")
PRESS_BODY = ("测评背景", "主办单位", "承办", "联合发布", "征集", "本方案", "指标体系",
              "测试范围", "报名", "参评")
REVIEW_BODY = ("试驾", "坐进", "开起来", "车主", "续航", "油耗", "电耗", "后排", "后备箱",
               "提车", "落地价", "二手", "保值", "对比", "SUV", "MPV")
REVIEW_TITLE = ("？", "?", "怎么", "为什么", "该不该", "值不值", "要不要", "能不能",
                "建议", "避坑", "答案", "必答", "选车")


def genre_of(art):
    """这篇是什么文体？返回 (genre, why)。

    review  = 编辑式车评/选购（可作风格样本）
    press   = 公告/基准/通稿（**禁用**：拿它标定文风，训出来就是公文腔）
    unknown = 拿不准（默认不用，宁缺不脏）
    """
    title = str(art.get("title") or "")
    lead = str(art.get("lead") or "")[:300]
    text = str(art.get("text") or "")[:3000]
    heads = " ".join(str(h) for h in (art.get("heads") or []))
    sc_press = sum(1 for m in PRESS_MARKS if m in title)
    sc_press += 2 * sum(1 for m in PRESS_BODY if m in lead or m in text or m in heads)
    sc_review = sum(1 for m in REVIEW_TITLE if m in title)
    sc_review += sum(1 for m in REVIEW_BODY if m in lead or m in text)
    why = "通稿分 %d（标题%d）／车评分 %d（标题%d）" % (
        sc_press, sum(1 for m in PRESS_MARKS if m in title), sc_review,
        sum(1 for m in REVIEW_TITLE if m in title))
    if sc_press >= 3 and sc_press >= sc_review:
        return "press", why
    if sc_review >= 3 and sc_review > sc_press:
        return "review", why
    return "unknown", why


BLOCKLIST = os.path.join(GZH, "ACCOUNT-BLOCKLIST.json")
BLOCK_MIN = 3      # 同一账号采够这么多篇仍全是通稿/未知，就不再吃采集配额


def account_stats(arts):
    """按账号统计文体分布：{账号: {"n","press","review","unknown"}}。"""
    out = {}
    for a in arts:
        k = (a.get("account") or "").strip()
        if not k:
            continue
        d = out.setdefault(k, {"n": 0, "press": 0, "review": 0, "unknown": 0})
        d["n"] += 1
        g = a.get("genre") or "unknown"
        d[g] = d.get(g, 0) + 1
    return out


def blocked_accounts(arts=None):
    """采够 BLOCK_MIN 篇、且一篇车评都没有的账号 → 拉黑（不再采它的新链接）。

    判据来自实测：CLUE中文语言理解测评基准 被采了 4 篇，全是"汽车大模型测评基准发布"，
    这是 NLP 基准公告，不是车评。不拉黑它就会一直占采集配额、还把通稿喂进语料池。
    """
    arts = arts if arts is not None else [json.loads(l) for l in open(ARTICLES, encoding="utf-8") if l.strip()]
    out = {}
    for acct, d in account_stats(arts).items():
        if d["n"] >= BLOCK_MIN and d.get("review", 0) == 0:
            out[acct] = {"n": d["n"], "press": d.get("press", 0), "unknown": d.get("unknown", 0)}
    return out


def write_blocklist():
    out = blocked_accounts()
    os.makedirs(GZH, exist_ok=True)
    with open(BLOCKLIST, "w", encoding="utf-8") as f:
        json.dump({"_why": "采够 %d 篇仍无车评的账号，后续链接不再采" % BLOCK_MIN,
                   "accounts": out}, f, ensure_ascii=False, indent=1)
    return out


def harvest(limit=30, sleep_lo=3.0, sleep_hi=8.0, rng=None, urls=None,
            budget_secs=540, max_attempts=None):
    """从池里抓一批。

    三个必须有的刹车（2026-11-25 实锚：一次 `--harvest 8` 把 900 秒预算跑爆，
    循环记 CRASHED）：
      1. **整批墙钟预算** budget_secs：到点就收工退 0，绝不拖死调用方；
      2. **尝试上限** max_attempts：limit 是"入库几篇"不是"看几条链接"，
         池里死链多时只按 limit 循环会一路扫到池底；
      3. **死链台账** URLS-FAILED：同一个链接连续失败 2 次就不再试，
         否则每次都排在队头，形成永久队头阻塞。

    静态垂类源（盖世/第一电动）不在这里抓：它们归 gzh_corpus_expand.py，
    语料分开落盘、训练时分开口径；这里遇到只跳过并计数，不记失败。
    """
    rng = rng or random.Random()
    t0 = time.time()
    src = urls if urls is not None else [
        json.loads(l) for l in open(URLS, encoding="utf-8") if l.strip()]
    done = _seen(ARTICLES)
    # 同一篇文章会从不同种子/展开链接进来（实测池里 3 篇重复、标题逐字相同），
    # 只按 URL 去重拦不住。标题+账号做二次键。
    titles = {((a.get("title") or "").strip(), (a.get("account") or "").strip())
              for a in (json.loads(l) for l in open(ARTICLES, encoding="utf-8") if l.strip())}
    known = _seen(URLS)
    _bl = blocked_accounts()      # 一次算完，别在循环里反复读语料池
    dead = failed_urls()          # 已经死了两轮的链接，不再占队头
    attempts_cap = max_attempts if max_attempts is not None else max(2 * int(limit), 8)
    got, fail, skip_static, attempts, stopped = 0, [], 0, 0, "pool-exhausted"
    for row in src:
        if got >= int(limit):
            stopped = "limit"
            break
        if attempts >= attempts_cap:
            stopped = "attempts"
            break
        if time.time() - t0 > budget_secs:
            stopped = "budget"
            break
        u = row.get("url")
        if not u or _uid(u) in done:
            continue
        if _static_host(u):
            skip_static += 1
            continue
        if _uid(u) in dead:
            fail.append({"url": u, "why": "死链台账（已失败 2 次）"})
            continue
        if row.get("account") and row.get("account") in _bl:
            fail.append({"url": u, "why": "账号已止损（%s）" % row.get("account")})
            continue
        attempts += 1
        art, why = fetch(u)
        if art is None:
            fail.append({"url": u, "why": why})
            mark_failed(u, why)
            continue
        done.add(art["_uid"])
        art["genre"], art["genre_why"] = genre_of(art)
        tkey = ((art.get("title") or "").strip(), (art.get("account") or "").strip())
        if tkey in titles:
            fail.append({"url": u, "why": "重复篇（标题+账号已在池里）"})
            continue
        titles.add(tkey)
        _append(ARTICLES, art)
        got += 1
        for u2 in (art.get("links") or []):
            uid2 = _uid(u2)
            if uid2 in known or uid2 in done:
                continue
            known.add(uid2)
            _append(URLS, {"_uid": uid2, "url": u2, "kw": "expand",
                           "account": art.get("account"),   # 记账号：池里才知道这条属于谁
                           "found_at": datetime.now().isoformat(timespec="seconds")})
        time.sleep(rng.uniform(sleep_lo, sleep_hi))
    stats = {"secs": round(time.time() - t0, 1), "attempts": attempts,
             "skip_static": skip_static, "stopped": stopped, "budget": budget_secs}
    return got, fail, stats


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
    tok = "https://mp.weixin.qq.com/s/U5QJ0w8OMUkyOa-lS08FHw"
    cases.append(("负控：同文不同 scene 必须同 uid",
                  _uid(tok + "?scene=21") == _uid(tok)))
    cases.append(("负控：http/https 必须同 uid",
                  _uid(tok.replace("https://", "http://")) == _uid(tok)))
    cases.append(("负控：尾斜杠/#rd 必须同 uid",
                  _uid(tok + "/#rd") == _uid(tok)))
    long1 = ("https://mp.weixin.qq.com/s?__biz=MzA5&mid=2247507112&idx=1&sn=aa&scene=21")
    long2 = ("https://mp.weixin.qq.com/s?__biz=MzA5&mid=2247507112&idx=1&chksm=bb&scene=1")
    cases.append(("负控：长链变体必须同 uid", _uid(long1) == _uid(long2)))
    cases.append(("已知局限：短链与长链仍不同（如实记）", _uid(tok) != _uid(long1)))
    cases.append(("uid 长度 16", len(_uid(tok)) == 16))
    # 2 缺字段的文章仍能入库（words=0 时不崩）
    a = {"_uid": "x", "title": "t", "words": 0, "heads": [], "imgs": 0, "account": "a"}
    cases.append(("空结构可汇总", "1 篇" in summarize([a])))
    # 3 统计真的读字段（改字数必须改结果）
    b = dict(a, words=5000)
    cases.append(("字数进汇总", "5000" in summarize([a, b]) or "2500" in summarize([a, b])))
    # 4 去重集合真的能挡住重复
    import tempfile
    d = tempfile.mkdtemp(prefix="gzh-")
    # 整个自检期间死链台账指向临时文件：自检不许写生产状态（2026-11-25 踩过）
    global FAILED
    saved_failed = FAILED
    FAILED = os.path.join(d, "failed.jsonl")
    f = os.path.join(d, "x.jsonl")
    _append(f, {"_uid": "u1", "url": "a"})
    _append(f, {"_uid": "u2", "url": "b"})
    cases.append(("去重读到 2 条", len(_seen(f)) == 2))
    cases.append(("未知 uid 不在已采集", "u3" not in _seen(f)))

    # 5 静态垂类源必须被识别出来（2026-11-25 实锚：71 条 gasgoo 链接被送进
    #   公众号提取器，每条卡满 25 秒，一次 900 秒预算直接跑爆）
    cases.append(("静态源[盖世] 被识别", _static_host("https://auto.gasgoo.com/news/202611/x.shtml")))
    cases.append(("静态源[第一电动] 被识别", _static_host("https://www.d1ev.com/news/shuju/312498")))
    cases.append(("负控[公众号] 不被误判静态", not _static_host("https://mp.weixin.qq.com/s/abc")))
    cases.append(("负控[车家号] 不被误判静态",
                  not _static_host("https://chejiahao.autohome.com.cn/info/26906205")))
    cases.append(("负控[仿冒域名] 不算静态源",
                  not _static_host("https://evil-d1ev.com/news/shuju/1")))

    # 6 死链台账：失败 1 次还试，失败 2 次就不试（否则队头永久阻塞）
    # 整个自检期间 FAILED 一律指向临时文件——2026-11-25 踩过：自检往生产台账
    # 写了 18 行「桩失败」，第二次跑就自己被这些假死链判红，还污染了真实数据。
    u1 = "https://chejiahao.autohome.com.cn/info/111111"
    mark_failed(u1, "timeout")
    cases.append(("死链 1 次→仍会重试", _uid(u1) not in failed_urls()))
    mark_failed(u1, "timeout")
    cases.append(("死链 2 次→不再重试", _uid(u1) in failed_urls()))
    cases.append(("负控[别的链接] 不受影响",
                  _uid("https://chejiahao.autohome.com.cn/info/222222") not in failed_urls()))

    # 7 预算/尝试上限真的会刹车（不联网：fetch 换成恒失败的桩）
    global fetch
    saved_fetch = fetch
    try:
        fetch = lambda url, retries=1: (None, "桩失败")
        pool = os.path.join(d, "pool.jsonl")
        for i in range(20):
            _append(pool, {"url": "https://chejiahao.autohome.com.cn/info/%d" % (900000 + i)})
        rows = [json.loads(l) for l in open(pool, encoding="utf-8")]
        g, fl, st = harvest(limit=5, budget_secs=0, rng=random.Random(0),
                            urls=rows, max_attempts=3)
        cases.append(("预算 0 秒→立刻收工且不抓任何一篇", g == 0 and st["attempts"] == 0
                      and st["stopped"] == "budget"))
        g2, fl2, st2 = harvest(limit=5, budget_secs=60, rng=random.Random(0),
                               urls=rows, max_attempts=3)
        cases.append(("尝试上限 3→只试 3 次就收工", st2["attempts"] == 3
                      and st2["stopped"] == "attempts"))
        cases.append(("负控[不应跑到池底]", len(fl2) <= 4))
    finally:
        fetch = saved_fetch
        FAILED = saved_failed

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
    ap.add_argument("--cj-author", help="车家号作者 id（对标对象镜像）")
    ap.add_argument("--cj-expand", type=int, default=0,
                    help="两跳扩池：访问 N 篇池内文章，反查作者并收推荐链接")
    ap.add_argument("--cj-discover", type=int, default=0,
                    help="从池里取 N 篇文章反查作者 id（车家号 /Authors/<id>）")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--scrolls", type=int, default=8,
                    help="作者页滚动加载次数（车家号是无限滚动，?page=N 无效）")
    ap.add_argument("--harvest", type=int, default=0)
    ap.add_argument("--budget-secs", type=int, default=540,
                    help="整批墙钟预算：到点收工退 0，绝不拖死调用方（默认 540）")
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
    if a.cj_expand:
        auth, added = expand_once(a.cj_expand)
        print("[gzh] 两跳扩池：文章 %d 篇 → 新作者 %d 个 / 新链接 %d 条"
              % (a.cj_expand, len(auth), added))
        for aid, hits in sorted(auth.items(), key=lambda kv: -kv[1])[:10]:
            print("   /Authors/%s  出现 %d 次" % (aid, hits))
        return 0
    if a.cj_discover:
        rows = []
        if os.path.exists(URLS):
            for line in open(URLS, encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:  # noqa: BLE001
                    pass
        urls = [r.get("url") for r in rows if "/info/" in (r.get("url") or "")]
        pairs = discover_authors_from(urls, limit=a.cj_discover)
        print("[gzh] 反查到作者 %d 个：" % len(pairs))
        for aid, hits in pairs[:12]:
            print("   /Authors/%s  出现 %d 次" % (aid, hits))
        return 0
    if a.cj_author:
        n = discover_chejiahao(a.cj_author, pages=a.pages, scrolls=a.scrolls, limit=(a.limit or 40))
        print("[gzh] 车家号建池 %d 条 → %s" % (n, os.path.relpath(URLS, ROOT)))
        return 0 if n else 1
    if a.sogou or a.serp:
        kw = a.serp or a.sogou
        n, why = discover(kw, pages=a.pages, via=("sogou" if a.sogou else "serp"))
        print("[gzh] 建池 %d 条（%s）→ %s" % (n, why, os.path.relpath(URLS, ROOT)))
        return 0 if n or why == "ok" else 1
    if a.harvest:
        # 平台租约：不是公众号时段就让位（退 75=可重试；绝不当成 FAIL 进退避）
        try:
            sys.path.insert(0, HERE)
            import res_alloc
            rc, why = res_alloc.may("gzh")
        except Exception as e:
            rc, why = 0, "仲裁器不可用（%s）：放行" % type(e).__name__
        if rc != 0:
            print("[gzh] 让位/拒绝 rc=%d：%s" % (rc, why))
            return 75 if rc == 75 else 76
        lim = a.limit or a.harvest
        got, fail, st = harvest(min(lim, a.harvest), budget_secs=a.budget_secs)
        arts = [json.loads(l) for l in open(ARTICLES, encoding="utf-8")
                if l.strip()][-got:] if got else []
        print("[gzh] 入库 %d 篇，失败 %d 次，跳过静态源 %d 条"
              % (got, len(fail), st["skip_static"]))
        print("[gzh] 本拍 %.1f 秒 / 尝试 %d 次 / 收工原因 %s（预算 %d 秒）"
              % (st["secs"], st["attempts"], st["stopped"], st["budget"]))
        if fail:
            print("[gzh] 首个失败：%s" % fail[0]["why"])
        if got:
            print("[gzh] 本批：%s" % summarize(arts))
        # 预算到点收工不是失败：已入库的照算，退 0 让循环继续下一拍。
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
