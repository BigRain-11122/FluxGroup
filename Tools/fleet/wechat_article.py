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


def discover_chejiahao(author_id, pages=1, rng=None, limit=40):
    """车家号作者页取文章链接（对标对象本人的镜像，公开可翻页）。

    2026-11-23 实测：作者页 287 个链接里有 /info/<id>，详情页正文在 __NEXT_DATA__ 的
    articleContent.content（HTML），比公众号网页稳定，不需要登录。
    标注为"镜像"：只用于学写法，不声称是公众号原文。
    """
    rng = rng or random.Random()
    mod, kw = _browser()
    known = _seen(URLS)
    added = 0
    with mod.sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(**kw)
        try:
            pg = ctx.new_page()
            pg.set_default_timeout(15000)
            for page in range(1, int(pages) + 1):
                url = ("https://chejiahao.autohome.com.cn/authors/%s" % author_id
                       + ("?page=%d" % page if page > 1 else ""))
                pg.goto(url, wait_until="domcontentloaded", timeout=35000)
                pg.wait_for_timeout(2500)
                items = pg.evaluate("""()=>Array.from(document.querySelectorAll('a'))
                    .map(a=>({t:(a.innerText||'').trim(), h:a.href.split('#')[0]}))
                    .filter(x=>/\/info\/\d+/.test(x.h) && x.t.length>8)""")
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
                time.sleep(rng.uniform(3, 6))
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


def harvest(limit=30, sleep_lo=3.0, sleep_hi=8.0, rng=None, urls=None):
    rng = rng or random.Random()
    src = urls if urls is not None else [
        json.loads(l) for l in open(URLS, encoding="utf-8") if l.strip()]
    done = _seen(ARTICLES)
    # 同一篇文章会从不同种子/展开链接进来（实测池里 3 篇重复、标题逐字相同），
    # 只按 URL 去重拦不住。标题+账号做二次键。
    titles = {((a.get("title") or "").strip(), (a.get("account") or "").strip())
              for a in (json.loads(l) for l in open(ARTICLES, encoding="utf-8") if l.strip())}
    known = _seen(URLS)
    _bl = blocked_accounts()      # 一次算完，别在循环里反复读语料池
    got, fail = 0, []
    for row in src:
        if got >= int(limit):
            break
        u = row.get("url")
        if not u or _uid(u) in done:
            continue
        if row.get("account") and row.get("account") in _bl:
            fail.append({"url": u, "why": "账号已止损（%s）" % row.get("account")})
            continue
        art, why = fetch(u)
        if art is None:
            fail.append({"url": u, "why": why})
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
    ap.add_argument("--cj-author", help="车家号作者 id（对标对象镜像）")
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
    if a.cj_author:
        n = discover_chejiahao(a.cj_author, pages=a.pages)
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
